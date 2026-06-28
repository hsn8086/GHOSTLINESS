from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from math import floor
from typing import TYPE_CHECKING, cast

from loguru import logger

from ghostliness.auth import GameProfile
from ghostliness.blocks import can_place_against, can_replace, hardness, is_air, is_known
from ghostliness.items import DEFAULT_TEST_HOTBAR, block_for_item_stack
from ghostliness.server.events import PlayerJoinEvent, PlayerQuitEvent
from ghostliness.server.player import Player
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

    async def send_chat(self, content: dict[str, object]) -> None:
        await self.connection.send_chat(content)


def _position_int(position: Mapping[str, object], axis: str) -> int:
    value = position[axis]
    if isinstance(value, int | float | str):
        return int(value)
    raise TypeError(f"invalid block position {axis}: {value!r}")


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
        player_x = floor(player.position.x)
        player_y = floor(player.position.y)
        player_z = floor(player.position.z)
        return position in {
            BlockPosition(player_x, player_y, player_z),
            BlockPosition(player_x, player_y + 1, player_z),
        }

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
                "gamemode": 1,
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
