from __future__ import annotations

import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from math import cos, isfinite, radians, sin
from typing import TYPE_CHECKING, cast

from loguru import logger

from ghostliness.auth import GameProfile
from ghostliness.blocks import (
    can_place_against,
    can_replace,
    hardness,
    is_air,
    is_known,
    is_solid,
    item_id_for_block_state,
)
from ghostliness.items import DEFAULT_TEST_HOTBAR, ItemStack, block_for_item_stack
from ghostliness.protocol.versions.java_26_2 import (
    ENTITY_DATA_SERIALIZER_ITEM_STACK,
    ITEM_ENTITY_DATA_ITEM,
    ITEM_ENTITY_TYPE_ID,
)
from ghostliness.server.entities import (
    ITEM_ENTITY_PICKUP_DELAY_TICKS,
    Entity,
    ItemEntity,
    Vec3,
)
from ghostliness.server.events import PlayerJoinEvent, PlayerQuitEvent
from ghostliness.server.player import Player, PlayerInput
from ghostliness.world import (
    AIR,
    BlockPosition,
    BlockState,
    Chunk,
    ChunkPosition,
    Position,
    World,
    chunk_position_from_block,
    chunk_position_from_world,
    local_block_position,
)
from ghostliness.world_data import (
    WORLD_HEIGHT,
    WORLD_MIN_Y,
    WORLD_NAMES,
    empty_light_masks,
    encode_chunk_data,
    heightmaps_for_chunk,
)
from ghostliness.world_storage import WorldStorage

if TYPE_CHECKING:
    from ghostliness.server.connection import Connection
    from ghostliness.server.core import GhostlinessServer


@dataclass(slots=True)
class PlayerSession:
    player: Player
    connection: Connection
    joined_at: float = field(default_factory=time.monotonic)
    loaded: bool = False
    chunk_center: ChunkPosition | None = None
    sent_chunks: set[ChunkPosition] = field(default_factory=set)
    visible_entities: set[int] = field(default_factory=set)

    async def send_chat(self, content: dict[str, object]) -> None:
        await self.connection.send_chat(content)


def _position_int(position: Mapping[str, object], axis: str) -> int:
    value = position[axis]
    if isinstance(value, int | float | str):
        return int(value)
    raise TypeError(f"invalid block position {axis}: {value!r}")


def _float_field(fields: Mapping[str, object], key: str, default: float) -> float:
    value = fields.get(key, default)
    if isinstance(value, int | float | str):
        return float(value)
    return default


def _int_field(fields: Mapping[str, object], key: str, default: int) -> int:
    value = fields.get(key, default)
    if isinstance(value, int | float | str):
        return int(value)
    return default


def _in_world_bounds(position: BlockPosition) -> bool:
    return WORLD_MIN_Y <= position.y < WORLD_MIN_Y + WORLD_HEIGHT


_DIRECTION_OFFSETS = (
    (0, -1, 0),
    (0, 1, 0),
    (0, 0, -1),
    (0, 0, 1),
    (-1, 0, 0),
    (1, 0, 0),
)
_MAX_PLAYER_XZ = 30_000_000.0
_PLAYER_Y_MARGIN = 64.0


class GameRuntime:
    def __init__(
        self,
        server: GhostlinessServer,
        world: World,
        storage: WorldStorage,
    ) -> None:
        self.server = server
        self.world = world
        self.storage = storage
        self.sessions: dict[str, PlayerSession] = {}
        self.players: dict[str, Player] = {}
        self.entities: dict[int, Entity] = {}
        self.chunks: dict[ChunkPosition, Chunk] = {}
        self._entity_ids = iter(range(1, 2_147_483_647))

    async def enter_play(self, connection: Connection, profile: GameProfile) -> PlayerSession:
        player = Player(
            profile=profile,
            position=Position(
                x=self.world.spawn.x,
                y=self.world.spawn.y,
                z=self.world.spawn.z,
                yaw=self.world.spawn.yaw,
                pitch=self.world.spawn.pitch,
            ),
            connection_id=connection.connection_id,
            entity_id=next(self._entity_ids),
        )
        session = PlayerSession(player=player, connection=connection)
        self.sessions[connection.connection_id] = session
        self.players[connection.connection_id] = player
        connection.player = player
        connection.last_keep_alive_sent = time.monotonic()

        logger.info("enter play id={} username={}", connection.connection_id, player.name)
        await self._send_initial_play_state(session)
        await self.sync_entity_visibility()
        await session.send_chat({"text": f"Welcome, {player.name}"})
        await self.server.events.publish("player_join", PlayerJoinEvent(player, session))
        logger.info(
            "player join published id={} username={}",
            connection.connection_id,
            player.name,
        )
        return session

    async def remove_player(self, connection_id: str, reason: str) -> None:
        session = self.sessions.pop(connection_id, None)
        self.players.pop(connection_id, None)
        if session is None:
            return
        await self._remove_player_entity_from_viewers(session)
        await self.server.events.publish(
            "player_quit",
            PlayerQuitEvent(session.player, reason, session),
        )

    def get_session(self, connection_id: str) -> PlayerSession | None:
        return self.sessions.get(connection_id)

    def mark_player_loaded(self, connection_id: str) -> None:
        session = self.sessions.get(connection_id)
        if session is None:
            return
        session.loaded = True
        logger.info("player loaded id={} username={}", connection_id, session.player.name)

    def get_chunk(self, position: ChunkPosition) -> Chunk:
        chunk = self.chunks.get(position)
        if chunk is not None:
            return chunk
        chunk = self.storage.load_chunk(position)
        if chunk is None:
            chunk = self.world.generate_chunk(position)
        self.chunks[position] = chunk
        return chunk

    def save_chunk(self, chunk: Chunk) -> None:
        self.chunks[chunk.position] = chunk
        self.storage.save_chunk(chunk)

    def chunk_position_for_player(self, position: Position) -> ChunkPosition:
        return chunk_position_from_world(position.x, position.z)

    def chunk_position_for_entity(self, entity: Entity) -> ChunkPosition:
        return chunk_position_from_world(entity.position.x, entity.position.z)

    def chunk_window(self, center: ChunkPosition, radius: int) -> set[ChunkPosition]:
        radius = max(0, int(radius))
        return {
            ChunkPosition(center.x + chunk_x, center.z + chunk_z)
            for chunk_x in range(-radius, radius + 1)
            for chunk_z in range(-radius, radius + 1)
        }

    def ordered_chunk_window(
        self,
        chunks: set[ChunkPosition],
        center: ChunkPosition,
    ) -> list[ChunkPosition]:
        return sorted(
            chunks,
            key=lambda chunk: (
                max(abs(chunk.x - center.x), abs(chunk.z - center.z)),
                abs(chunk.x - center.x) + abs(chunk.z - center.z),
                chunk.x,
                chunk.z,
            ),
        )

    async def handle_player_moved(self, connection_id: str) -> None:
        session = self.sessions.get(connection_id)
        if session is None:
            return
        center = self.chunk_position_for_player(session.player.position)
        await self.sync_chunk_window(session, center)
        await self.sync_entity_visibility()
        await self._try_pickup_items(session)

    async def handle_player_movement(
        self,
        connection_id: str,
        fields: Mapping[str, object],
    ) -> None:
        session = self.sessions.get(connection_id)
        if session is None:
            return

        player = session.player
        x = _float_field(fields, "x", player.position.x)
        y = _float_field(fields, "y", player.position.y)
        z = _float_field(fields, "z", player.position.z)
        yaw = _float_field(fields, "yaw", player.position.yaw)
        pitch = _float_field(fields, "pitch", player.position.pitch)

        if not self._valid_player_state(x, y, z, yaw, pitch):
            logger.warning(
                "invalid player movement id={} x={} y={} z={} yaw={} pitch={} fields={}",
                connection_id,
                x,
                y,
                z,
                yaw,
                pitch,
                dict(fields),
            )
            return

        player.position.x = x
        player.position.y = y
        player.position.z = z
        player.position.yaw = yaw
        player.position.pitch = pitch
        if "flags" in fields:
            player.on_ground = bool(_int_field(fields, "flags", 0) & 0x01)
        logger.trace(
            "position update id={} x={} y={} z={} yaw={} pitch={} on_ground={}",
            connection_id,
            player.position.x,
            player.position.y,
            player.position.z,
            player.position.yaw,
            player.position.pitch,
            player.on_ground,
        )
        viewers_before = self._visible_viewer_ids(player.entity_id)
        await self.handle_player_moved(connection_id)
        await self._broadcast_player_teleport(
            session,
            only_viewer_connection_ids=viewers_before,
        )

    async def sync_entity_visibility(self) -> None:
        sessions = sorted(
            self.sessions.values(),
            key=lambda item: item.player.entity_id,
        )
        sessions_by_entity_id = {session.player.entity_id: session for session in sessions}
        for viewer in sessions:
            desired_players = {
                target.player.entity_id
                for target in sessions
                if target is not viewer and self._player_visible_to(viewer, target)
            }
            desired_entities = {
                entity.entity_id
                for entity in self.entities.values()
                if not entity.removed and self._entity_visible_to(viewer, entity)
            }
            desired = desired_players | desired_entities
            to_remove = viewer.visible_entities - desired
            to_add = desired - viewer.visible_entities

            if to_remove:
                await self._send_remove_entities(viewer, to_remove, sessions_by_entity_id)
                viewer.visible_entities -= to_remove

            if to_add:
                player_targets = [
                    sessions_by_entity_id[entity_id]
                    for entity_id in sorted(to_add)
                    if entity_id in sessions_by_entity_id
                ]
                await self._send_player_info_update(viewer, player_targets)
                for target in player_targets:
                    await self._send_add_player_entity(viewer, target)
                    viewer.visible_entities.add(target.player.entity_id)
                for entity_id in sorted(to_add):
                    entity = self.entities.get(entity_id)
                    if entity is None:
                        continue
                    await self._send_add_entity(viewer, entity)
                    viewer.visible_entities.add(entity.entity_id)

    def handle_player_input(
        self,
        connection_id: str,
        fields: Mapping[str, object],
    ) -> None:
        session = self.sessions.get(connection_id)
        if session is None:
            return
        player = session.player
        player.input = PlayerInput(
            forward=bool(fields.get("forward", False)),
            backward=bool(fields.get("backward", False)),
            left=bool(fields.get("left", False)),
            right=bool(fields.get("right", False)),
            jump=bool(fields.get("jump", False)),
            shift=bool(fields.get("shift", False)),
            sprint=bool(fields.get("sprint", False)),
        )
        player.set_sneaking(player.input.shift)
        logger.trace(
            "player input id={} forward={} backward={} left={} right={} jump={} "
            "shift={} sprint={} sneaking={}",
            connection_id,
            player.input.forward,
            player.input.backward,
            player.input.left,
            player.input.right,
            player.input.jump,
            player.input.shift,
            player.input.sprint,
            player.sneaking,
        )

    def handle_player_command(
        self,
        connection_id: str,
        action_name: str | None,
    ) -> None:
        session = self.sessions.get(connection_id)
        if session is None:
            return
        match action_name:
            case "start_sprinting":
                session.player.sprinting = True
            case "stop_sprinting":
                session.player.sprinting = False
            case _:
                logger.debug(
                    "player command ignored id={} action_name={}",
                    connection_id,
                    action_name,
                )

    def _valid_player_state(
        self,
        x: float,
        y: float,
        z: float,
        yaw: float,
        pitch: float,
    ) -> bool:
        return (
            isfinite(x)
            and isfinite(y)
            and isfinite(z)
            and isfinite(yaw)
            and isfinite(pitch)
            and abs(x) <= _MAX_PLAYER_XZ
            and abs(z) <= _MAX_PLAYER_XZ
            and WORLD_MIN_Y - _PLAYER_Y_MARGIN
            <= y
            <= WORLD_MIN_Y + WORLD_HEIGHT + _PLAYER_Y_MARGIN
        )

    def _player_visible_to(
        self,
        viewer: PlayerSession,
        target: PlayerSession,
    ) -> bool:
        target_center = self.chunk_position_for_player(target.player.position)
        if viewer.sent_chunks:
            return target_center in viewer.sent_chunks
        center = viewer.chunk_center or self.chunk_position_for_player(viewer.player.position)
        radius = self.server.config.server.view_distance
        return target_center in self.chunk_window(center, radius)

    def _entity_visible_to(self, viewer: PlayerSession, entity: Entity) -> bool:
        target_center = self.chunk_position_for_entity(entity)
        if viewer.sent_chunks:
            return target_center in viewer.sent_chunks
        center = viewer.chunk_center or self.chunk_position_for_player(viewer.player.position)
        radius = self.server.config.server.view_distance
        return target_center in self.chunk_window(center, radius)

    def _visible_viewer_ids(self, entity_id: int) -> set[str]:
        return {
            session.connection.connection_id
            for session in self.sessions.values()
            if entity_id in session.visible_entities
        }

    async def _send_player_info_update(
        self,
        viewer: PlayerSession,
        targets: list[PlayerSession],
    ) -> None:
        if not targets:
            return
        await viewer.connection.send(
            "clientbound.player_info_update",
            {"entries": [self._player_info_entry(target.player) for target in targets]},
        )
        logger.debug(
            "player info update sent viewer={} targets={}",
            viewer.connection.connection_id,
            [target.player.entity_id for target in targets],
        )

    async def _send_add_player_entity(
        self,
        viewer: PlayerSession,
        target: PlayerSession,
    ) -> None:
        player = target.player
        await viewer.connection.send(
            "clientbound.add_entity",
            {
                "entity_id": player.entity_id,
                "uuid": player.profile.uuid,
                "x": player.position.x,
                "y": player.position.y,
                "z": player.position.z,
                "yaw": player.position.yaw,
                "pitch": player.position.pitch,
                "head_yaw": player.position.yaw,
            },
        )
        logger.debug(
            "player entity spawned viewer={} target={} target_conn={} x={} y={} z={}",
            viewer.connection.connection_id,
            player.entity_id,
            target.connection.connection_id,
            player.position.x,
            player.position.y,
            player.position.z,
        )

    async def _send_add_entity(self, viewer: PlayerSession, entity: Entity) -> None:
        if isinstance(entity, ItemEntity):
            await self._send_add_item_entity(viewer, entity)
            return
        logger.debug(
            "entity spawn skipped viewer={} entity={} type={}",
            viewer.connection.connection_id,
            entity.entity_id,
            entity.type_id,
        )

    async def _send_add_item_entity(self, viewer: PlayerSession, entity: ItemEntity) -> None:
        await viewer.connection.send(
            "clientbound.add_entity",
            {
                "entity_id": entity.entity_id,
                "uuid": entity.uuid,
                "entity_type_id": ITEM_ENTITY_TYPE_ID,
                "x": entity.position.x,
                "y": entity.position.y,
                "z": entity.position.z,
                "dx": entity.velocity.x,
                "dy": entity.velocity.y,
                "dz": entity.velocity.z,
            },
        )
        await self._send_item_entity_data(viewer, entity)
        logger.debug(
            "item entity spawned viewer={} entity={} item={} count={} x={} y={} z={}",
            viewer.connection.connection_id,
            entity.entity_id,
            entity.stack.item_name,
            entity.stack.count,
            entity.position.x,
            entity.position.y,
            entity.position.z,
        )

    async def _send_item_entity_data(self, viewer: PlayerSession, entity: ItemEntity) -> None:
        await viewer.connection.send(
            "clientbound.set_entity_data",
            {
                "entity_id": entity.entity_id,
                "entries": [
                    {
                        "id": ITEM_ENTITY_DATA_ITEM,
                        "serializer_id": ENTITY_DATA_SERIALIZER_ITEM_STACK,
                        "value": entity.stack,
                    }
                ],
            },
        )

    async def _send_remove_entities(
        self,
        viewer: PlayerSession,
        entity_ids: set[int],
        sessions_by_entity_id: Mapping[int, PlayerSession],
    ) -> None:
        if not entity_ids:
            return
        ordered_entity_ids = sorted(entity_ids)
        await viewer.connection.send(
            "clientbound.remove_entities",
            {"entity_ids": ordered_entity_ids},
        )
        profile_ids = [
            sessions_by_entity_id[entity_id].player.profile.uuid
            for entity_id in ordered_entity_ids
            if entity_id in sessions_by_entity_id
        ]
        if profile_ids:
            await viewer.connection.send(
                "clientbound.player_info_remove",
                {"profile_ids": profile_ids},
            )
        logger.debug(
            "player entities removed viewer={} targets={}",
            viewer.connection.connection_id,
            ordered_entity_ids,
        )

    async def _remove_player_entity_from_viewers(self, removed: PlayerSession) -> None:
        sessions_by_entity_id = {removed.player.entity_id: removed}
        for viewer in self.sessions.values():
            if removed.player.entity_id not in viewer.visible_entities:
                continue
            await self._send_remove_entities(
                viewer,
                {removed.player.entity_id},
                sessions_by_entity_id,
            )
            viewer.visible_entities.discard(removed.player.entity_id)

    async def _broadcast_player_teleport(
        self,
        target: PlayerSession,
        *,
        only_viewer_connection_ids: set[str] | None = None,
    ) -> None:
        player = target.player
        for viewer in self.sessions.values():
            if viewer is target:
                continue
            if (
                only_viewer_connection_ids is not None
                and viewer.connection.connection_id not in only_viewer_connection_ids
            ):
                continue
            if player.entity_id not in viewer.visible_entities:
                continue
            await viewer.connection.send(
                "clientbound.teleport_entity",
                {
                    "entity_id": player.entity_id,
                    "x": player.position.x,
                    "y": player.position.y,
                    "z": player.position.z,
                    "yaw": player.position.yaw,
                    "pitch": player.position.pitch,
                    "on_ground": player.on_ground,
                },
            )
            logger.trace(
                "player entity teleport viewer={} target={} x={} y={} z={} yaw={} pitch={}",
                viewer.connection.connection_id,
                player.entity_id,
                player.position.x,
                player.position.y,
                player.position.z,
                player.position.yaw,
                player.position.pitch,
            )

    async def _broadcast_entity_motion(self, entity: Entity) -> None:
        for viewer in self.sessions.values():
            if entity.entity_id not in viewer.visible_entities:
                continue
            await viewer.connection.send(
                "clientbound.teleport_entity",
                {
                    "entity_id": entity.entity_id,
                    "x": entity.position.x,
                    "y": entity.position.y,
                    "z": entity.position.z,
                    "dx": entity.velocity.x,
                    "dy": entity.velocity.y,
                    "dz": entity.velocity.z,
                    "on_ground": entity.on_ground,
                },
            )
            await viewer.connection.send(
                "clientbound.set_entity_motion",
                {
                    "entity_id": entity.entity_id,
                    "dx": entity.velocity.x,
                    "dy": entity.velocity.y,
                    "dz": entity.velocity.z,
                },
            )

    async def _broadcast_item_entity_data(self, entity: ItemEntity) -> None:
        for viewer in self.sessions.values():
            if entity.entity_id in viewer.visible_entities:
                await self._send_item_entity_data(viewer, entity)

    def _player_info_entry(self, player: Player) -> dict[str, object]:
        return {
            "uuid": player.profile.uuid,
            "username": player.name,
            "properties": player.profile.properties,
            "gamemode": player.gamemode,
            "listed": True,
            "latency": 0,
            "display_name": None,
            "list_order": 0,
            "show_hat": True,
        }

    async def sync_chunk_window(
        self,
        session: PlayerSession,
        center: ChunkPosition,
        *,
        initial: bool = False,
    ) -> None:
        if not initial and session.chunk_center == center:
            return

        radius = self.server.config.server.view_distance
        desired_chunks = self.chunk_window(center, radius)
        chunks_to_load = desired_chunks - session.sent_chunks
        chunks_to_unload = session.sent_chunks - desired_chunks
        old_center = session.chunk_center

        session.chunk_center = center
        await session.connection.send(
            "clientbound.update_view_position",
            {"chunk_x": center.x, "chunk_z": center.z},
        )
        logger.debug(
            "chunk window sync id={} old_center={} new_center=({}, {}) "
            "initial={} load={} unload={}",
            session.connection.connection_id,
            old_center,
            center.x,
            center.z,
            initial,
            len(chunks_to_load),
            len(chunks_to_unload),
        )

        if chunks_to_unload:
            for chunk in self.ordered_chunk_window(chunks_to_unload, center):
                await session.connection.send(
                    "clientbound.forget_level_chunk",
                    {"x": chunk.x, "z": chunk.z},
                )
                logger.debug(
                    "chunk unloaded id={} chunk=({}, {})",
                    session.connection.connection_id,
                    chunk.x,
                    chunk.z,
                )

        if chunks_to_load:
            await session.connection.send("clientbound.chunk_batch_start", {})
            for chunk_position in self.ordered_chunk_window(chunks_to_load, center):
                await self._send_chunk(session, chunk_position)
            await session.connection.send(
                "clientbound.chunk_batch_finished",
                {"batch_size": len(chunks_to_load)},
            )

        session.sent_chunks = desired_chunks

    async def handle_player_action(
        self,
        connection_id: str,
        action_name: str | None,
        position: dict[str, object],
        sequence: int,
    ) -> None:
        session = self.sessions.get(connection_id)
        if session is None:
            return
        if action_name == "drop_item":
            await self._ack_block_change(session, sequence)
            await self._drop_selected_item(session, 1)
            return
        if action_name == "drop_all_items":
            await self._ack_block_change(session, sequence)
            await self._drop_selected_item(session, None)
            return
        if action_name not in {"start_destroy_block", "stop_destroy_block"}:
            await self._ack_block_change(session, sequence)
            return

        world_position = BlockPosition(
            _position_int(position, "x"),
            _position_int(position, "y"),
            _position_int(position, "z"),
        )
        if not _in_world_bounds(world_position):
            await self._ack_block_change(session, sequence)
            await self._send_block_update(session, world_position, AIR)
            logger.debug(
                "block destroy rejected id={} reason=out_of_world action={} world_pos={} "
                "sequence={}",
                connection_id,
                action_name,
                world_position.to_json(),
                sequence,
            )
            return

        chunk_position = chunk_position_from_block(world_position)
        local_position = local_block_position(world_position)
        chunk = self.get_chunk(chunk_position)
        before = chunk.get_block(local_position)

        if is_air(before):
            await self._ack_block_change(session, sequence)
            await self._send_block_update(session, world_position, before)
            logger.debug(
                "block destroy rejected id={} reason=air action={} world_pos={} sequence={}",
                connection_id,
                action_name,
                world_position.to_json(),
                sequence,
            )
            return

        if not is_known(before) or hardness(before) < 0:
            await self._ack_block_change(session, sequence)
            await self._send_block_update(session, world_position, before)
            logger.debug(
                "block destroy rejected id={} reason=unsupported_state action={} world_pos={} "
                "state={} sequence={}",
                connection_id,
                action_name,
                world_position.to_json(),
                before.name,
                sequence,
            )
            return

        chunk.set_block(local_position, AIR)
        self.save_chunk(chunk)

        await self._ack_block_change(session, sequence)
        await self._send_block_update(session, world_position, AIR)
        if session.player.gamemode != 1:
            await self._spawn_block_drop(before, world_position)
        logger.debug(
            "block destroyed id={} action={} world_pos={} chunk=({}, {}) local_pos={} before={}",
            connection_id,
            action_name,
            position,
            chunk_position.x,
            chunk_position.z,
            local_position,
            before.name,
        )

    async def _drop_selected_item(self, session: PlayerSession, count: int | None) -> None:
        stack = session.player.inventory.selected_stack()
        if stack.is_empty:
            logger.debug(
                "item drop ignored id={} reason=empty_slot slot={}",
                session.connection.connection_id,
                session.player.inventory.selected_slot,
            )
            return
        drop_count = stack.count if count is None else count
        removed = session.player.inventory.remove_from_selected(drop_count)
        if removed.is_empty:
            return
        await self._sync_hotbar_slot(session, session.player.inventory.selected_slot)
        velocity = self._drop_velocity(session.player)
        position = self._drop_position(session.player)
        await self.spawn_item_entity(removed, position, velocity=velocity)
        logger.debug(
            "item dropped id={} item={} count={} slot={} x={} y={} z={}",
            session.connection.connection_id,
            removed.item_name,
            removed.count,
            session.player.inventory.selected_slot,
            position.x,
            position.y,
            position.z,
        )

    async def _spawn_block_drop(self, state: BlockState, position: BlockPosition) -> None:
        item_id = item_id_for_block_state(state)
        if item_id is None:
            return
        await self.spawn_item_entity(
            ItemStack(item_id=item_id, count=1),
            Position(x=position.x + 0.5, y=position.y + 0.5, z=position.z + 0.5),
            velocity=Vec3(),
            pickup_delay=ITEM_ENTITY_PICKUP_DELAY_TICKS,
        )

    def _drop_position(self, player: Player) -> Position:
        yaw = radians(player.position.yaw)
        x = player.position.x - sin(yaw) * 0.3
        z = player.position.z + cos(yaw) * 0.3
        return Position(x=x, y=player.position.y + 1.0, z=z)

    def _drop_velocity(self, player: Player) -> Vec3:
        yaw = radians(player.position.yaw)
        pitch = radians(player.position.pitch)
        horizontal = cos(pitch)
        return Vec3(
            x=-sin(yaw) * horizontal * 0.3,
            y=-sin(pitch) * 0.3 + 0.1,
            z=cos(yaw) * horizontal * 0.3,
        )

    async def handle_use_item_on(
        self,
        connection_id: str,
        hand: int,
        hit_result: object,
        sequence: int,
    ) -> None:
        session = self.sessions.get(connection_id)
        if session is None:
            return
        if not isinstance(hit_result, dict):
            await self._ack_block_change(session, sequence)
            logger.warning(
                "invalid use item hit result id={} hit_result={}",
                connection_id,
                hit_result,
            )
            return

        hit_position_data = hit_result.get("position")
        if not isinstance(hit_position_data, dict):
            await self._ack_block_change(session, sequence)
            logger.warning(
                "invalid use item hit position id={} hit_result={}",
                connection_id,
                hit_result,
            )
            return
        hit_position_data = cast(Mapping[str, object], hit_position_data)

        hit_position = BlockPosition(
            _position_int(hit_position_data, "x"),
            _position_int(hit_position_data, "y"),
            _position_int(hit_position_data, "z"),
        )
        direction = hit_result.get("direction")
        direction_value = int(direction) if isinstance(direction, int | float | str) else -1
        target_position = self._placement_target(hit_position, direction_value)
        if target_position is None:
            await self._ack_block_change(session, sequence)
            await self._send_real_block_update(session, hit_position)
            logger.debug(
                "block place rejected id={} reason=invalid_direction hit_pos={} direction={} "
                "sequence={}",
                connection_id,
                hit_position.to_json(),
                direction,
                sequence,
            )
            return

        if not _in_world_bounds(target_position):
            await self._ack_block_change(session, sequence)
            await self._send_real_block_update(session, hit_position)
            logger.debug(
                "block place rejected id={} reason=out_of_world target={} sequence={}",
                connection_id,
                target_position.to_json(),
                sequence,
            )
            return

        stack = session.player.inventory.held_stack(hand)
        place_state = block_for_item_stack(stack)
        if place_state is None:
            await self._ack_block_change(session, sequence)
            await self._send_real_block_update(session, target_position)
            logger.debug(
                "block place rejected id={} reason=unsupported_item hand={} slot={} item={} "
                "count={} supported={} target={} sequence={}",
                connection_id,
                hand,
                session.player.inventory.selected_slot,
                stack.item_name,
                stack.count,
                stack.components_supported,
                target_position.to_json(),
                sequence,
            )
            return

        support_state = self._block_state_at(hit_position)
        if not can_place_against(support_state):
            await self._ack_block_change(session, sequence)
            await self._send_real_block_update(session, target_position)
            logger.debug(
                "block place rejected id={} reason=invalid_support hit={} support={} "
                "target={} sequence={}",
                connection_id,
                hit_position.to_json(),
                support_state.name,
                target_position.to_json(),
                sequence,
            )
            return

        if self._would_intersect_player(session.player, target_position):
            await self._ack_block_change(session, sequence)
            await self._send_real_block_update(session, target_position)
            logger.debug(
                "block place rejected id={} reason=player_collision target={} "
                "player=({}, {}, {}) sequence={}",
                connection_id,
                target_position.to_json(),
                session.player.position.x,
                session.player.position.y,
                session.player.position.z,
                sequence,
            )
            return

        chunk_position = chunk_position_from_block(target_position)
        local_position = local_block_position(target_position)
        chunk = self.get_chunk(chunk_position)
        before = chunk.get_block(local_position)
        if not can_replace(before):
            await self._ack_block_change(session, sequence)
            await self._send_block_update(session, target_position, before)
            logger.debug(
                "block place rejected id={} reason=occupied target={} before={} "
                "sequence={}",
                connection_id,
                target_position.to_json(),
                before.name,
                sequence,
            )
            return

        chunk.set_block(local_position, place_state)
        self.save_chunk(chunk)
        await self._ack_block_change(session, sequence)
        await self._send_block_update(session, target_position, place_state)
        logger.debug(
            "block placed id={} target={} chunk=({}, {}) local_pos={} item={} state={} sequence={}",
            connection_id,
            target_position.to_json(),
            chunk_position.x,
            chunk_position.z,
            local_position,
            stack.item_name,
            place_state.name,
            sequence,
        )

    async def close(self) -> None:
        self.storage.close()

    async def tick(self) -> None:
        moved_entities: list[Entity] = []
        for entity in list(self.entities.values()):
            if isinstance(entity, ItemEntity) and entity.tick(self._is_solid_block):
                moved_entities.append(entity)

        await self._merge_item_entities()
        for entity in moved_entities:
            if not entity.removed:
                await self._broadcast_entity_motion(entity)
        for entity in list(self.entities.values()):
            if isinstance(entity, ItemEntity) and entity.metadata_dirty and not entity.removed:
                await self._broadcast_item_entity_data(entity)
                entity.metadata_dirty = False

        removed_ids = {
            entity.entity_id for entity in self.entities.values() if entity.removed
        }
        if removed_ids:
            await self._remove_entities(removed_ids)

        for session in list(self.sessions.values()):
            await self._try_pickup_items(session)

    async def spawn_item_entity(
        self,
        stack: ItemStack,
        position: Position,
        *,
        velocity: Vec3 | None = None,
        pickup_delay: int = ITEM_ENTITY_PICKUP_DELAY_TICKS,
    ) -> ItemEntity:
        entity = ItemEntity.create(
            entity_id=next(self._entity_ids),
            entity_uuid=uuid.uuid4(),
            position=position,
            stack=stack,
            velocity=velocity,
            pickup_delay=pickup_delay,
        )
        self.entities[entity.entity_id] = entity
        await self.sync_entity_visibility()
        if entity.velocity.horizontal_length_sqr() > 0.0 or entity.velocity.y != 0.0:
            await self._broadcast_entity_velocity(entity)
        logger.debug(
            "item entity created entity={} item={} count={} x={} y={} z={}",
            entity.entity_id,
            stack.item_name,
            stack.count,
            position.x,
            position.y,
            position.z,
        )
        return entity

    async def _broadcast_entity_velocity(self, entity: Entity) -> None:
        for viewer in self.sessions.values():
            if entity.entity_id not in viewer.visible_entities:
                continue
            await viewer.connection.send(
                "clientbound.set_entity_motion",
                {
                    "entity_id": entity.entity_id,
                    "dx": entity.velocity.x,
                    "dy": entity.velocity.y,
                    "dz": entity.velocity.z,
                },
            )

    async def _merge_item_entities(self) -> None:
        items = [
            entity
            for entity in sorted(self.entities.values(), key=lambda item: item.entity_id)
            if isinstance(entity, ItemEntity) and not entity.removed
        ]
        for index, entity in enumerate(items):
            if entity.removed:
                continue
            for other in items[index + 1 :]:
                if entity.merge_from(other):
                    logger.debug(
                        "item entities merged target={} removed={} item={} count={}",
                        entity.entity_id,
                        other.entity_id,
                        entity.stack.item_name,
                        entity.stack.count,
                    )

    async def _try_pickup_items(self, session: PlayerSession) -> None:
        picked_ids: set[int] = set()
        for entity in sorted(self.entities.values(), key=lambda item: item.entity_id):
            if not isinstance(entity, ItemEntity) or entity.removed:
                continue
            if entity.pickup_delay > 0 or not entity.within_pickup_range(session.player.position):
                continue
            before_hotbar = list(session.player.inventory.hotbar)
            if not session.player.inventory.add_stack(entity.stack):
                logger.trace(
                    "item pickup rejected id={} entity={} reason=inventory_full item={} count={}",
                    session.connection.connection_id,
                    entity.entity_id,
                    entity.stack.item_name,
                    entity.stack.count,
                )
                continue
            await self._sync_changed_hotbar(session, before_hotbar)
            for viewer in self.sessions.values():
                if entity.entity_id in viewer.visible_entities:
                    await viewer.connection.send(
                        "clientbound.take_item_entity",
                        {
                            "item_id": entity.entity_id,
                            "player_id": session.player.entity_id,
                            "amount": entity.stack.count,
                        },
                    )
            entity.removed = True
            picked_ids.add(entity.entity_id)
            logger.debug(
                "item picked up id={} entity={} item={} count={}",
                session.connection.connection_id,
                entity.entity_id,
                entity.stack.item_name,
                entity.stack.count,
            )
        if picked_ids:
            await self._remove_entities(picked_ids)

    async def _remove_entities(self, entity_ids: set[int]) -> None:
        sessions_by_entity_id = {
            session.player.entity_id: session for session in self.sessions.values()
        }
        for viewer in self.sessions.values():
            visible_removed = entity_ids & viewer.visible_entities
            if not visible_removed:
                continue
            await self._send_remove_entities(viewer, visible_removed, sessions_by_entity_id)
            viewer.visible_entities -= visible_removed
        for entity_id in entity_ids:
            self.entities.pop(entity_id, None)

    def _is_solid_block(self, position: BlockPosition) -> bool:
        return is_solid(self._block_state_at(position))

    async def _sync_hotbar_slot(self, session: PlayerSession, slot: int) -> None:
        await session.connection.send(
            "clientbound.set_player_inventory",
            {"slot": slot, "contents": session.player.inventory.hotbar[slot]},
        )

    async def _sync_changed_hotbar(
        self,
        session: PlayerSession,
        before_hotbar: list[ItemStack],
    ) -> None:
        for slot, stack in enumerate(session.player.inventory.hotbar):
            if slot >= len(before_hotbar) or before_hotbar[slot] != stack:
                await self._sync_hotbar_slot(session, slot)

    def _placement_target(
        self,
        hit_position: BlockPosition,
        direction: int,
    ) -> BlockPosition | None:
        if not 0 <= direction < len(_DIRECTION_OFFSETS):
            return None
        dx, dy, dz = _DIRECTION_OFFSETS[direction]
        return BlockPosition(hit_position.x + dx, hit_position.y + dy, hit_position.z + dz)

    def _would_intersect_player(self, player: Player, position: BlockPosition) -> bool:
        return player.bounding_box.intersects_block(position)

    async def _ack_block_change(self, session: PlayerSession, sequence: int) -> None:
        await session.connection.send("clientbound.block_changed_ack", {"sequence": sequence})

    async def _send_block_update(
        self,
        session: PlayerSession,
        position: BlockPosition,
        state: BlockState,
    ) -> None:
        await session.connection.send(
            "clientbound.block_update",
            {"position": position.to_json(), "state": state},
        )

    def _block_state_at(self, position: BlockPosition) -> BlockState:
        if not _in_world_bounds(position):
            return AIR
        chunk_position = chunk_position_from_block(position)
        local_position = local_block_position(position)
        chunk = self.get_chunk(chunk_position)
        return chunk.get_block(local_position)

    async def _send_real_block_update(
        self,
        session: PlayerSession,
        position: BlockPosition,
    ) -> None:
        await self._send_block_update(session, position, self._block_state_at(position))

    async def _send_chunk(self, session: PlayerSession, chunk_position: ChunkPosition) -> None:
        chunk = self.get_chunk(chunk_position)
        chunk_data = encode_chunk_data(chunk)
        heightmaps = heightmaps_for_chunk(chunk)
        logger.debug(
            "chunk encoded id={} chunk=({}, {}) generator={} blocks={} bytes={}",
            session.connection.connection_id,
            chunk.position.x,
            chunk.position.z,
            chunk.generated_by,
            len(chunk.blocks),
            len(chunk_data),
        )
        await session.connection.send(
            "clientbound.map_chunk",
            {
                "x": chunk.position.x,
                "z": chunk.position.z,
                "heightmaps": heightmaps,
                "chunk_data": chunk_data,
                "lights": empty_light_masks(),
            },
        )

    async def _send_initial_play_state(self, session: PlayerSession) -> None:
        connection = session.connection
        view_distance = self.server.config.server.view_distance
        spawn = self.world.spawn
        center = self.chunk_position_for_player(session.player.position)
        logger.info(
            "play init start id={} view_distance={} spawn=({}, {}, {})",
            connection.connection_id,
            view_distance,
            spawn.x,
            spawn.y,
            spawn.z,
        )
        await connection.send(
            "clientbound.login",
            {
                "entity_id": session.player.entity_id,
                "world_names": WORLD_NAMES,
                "max_players": self.server.config.server.max_players,
                "view_distance": view_distance,
                "simulation_distance": view_distance,
                "gamemode": session.player.gamemode,
                "dimension_name": "minecraft:overworld",
                "online_mode": self.server.config.server.online_mode,
            },
        )
        await connection.send("clientbound.update_view_distance", {"view_distance": view_distance})
        await self._sync_default_hotbar(session)
        await connection.send(
            "clientbound.spawn_position",
            {
                "dimension": "minecraft:overworld",
                "x": int(spawn.x),
                "y": int(spawn.y),
                "z": int(spawn.z),
            },
        )
        await connection.send("clientbound.game_event", {"event": 13, "param": 0.0})
        await self.sync_chunk_window(session, center, initial=True)
        logger.info(
            "initial chunks sent id={} count={} center=({}, {})",
            connection.connection_id,
            len(session.sent_chunks),
            center.x,
            center.z,
        )
        connection.pending_teleport_id = 1
        await connection.send(
            "clientbound.position",
            {
                "teleport_id": connection.pending_teleport_id,
                "x": spawn.x,
                "y": spawn.y,
                "z": spawn.z,
                "yaw": spawn.yaw,
                "pitch": spawn.pitch,
            },
        )
        logger.info(
            "play init complete id={} teleport_id={}",
            connection.connection_id,
            connection.pending_teleport_id,
        )

    async def _sync_default_hotbar(self, session: PlayerSession) -> None:
        session.player.inventory.load_default_test_hotbar()
        for slot, stack in enumerate(DEFAULT_TEST_HOTBAR):
            await session.connection.send(
                "clientbound.set_player_inventory",
                {"slot": slot, "contents": stack},
            )
        await session.connection.send(
            "clientbound.set_held_slot",
            {"slot": session.player.inventory.selected_slot},
        )
        logger.debug(
            "default hotbar synced id={} slots={} selected={}",
            session.connection.connection_id,
            len(DEFAULT_TEST_HOTBAR),
            session.player.inventory.selected_slot,
        )
