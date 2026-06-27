from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loguru import logger

from ghostliness.auth import GameProfile
from ghostliness.server.events import PlayerJoinEvent, PlayerQuitEvent
from ghostliness.server.player import Player
from ghostliness.world import Chunk, ChunkPosition, Position, World
from ghostliness.world_data import (
    WORLD_NAMES,
    empty_heightmaps,
    empty_light_masks,
    encode_empty_chunk_data,
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

    async def send_chat(self, content: dict[str, object]) -> None:
        await self.connection.send_chat(content)


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

    async def close(self) -> None:
        self.storage.close()

    async def _send_initial_play_state(self, session: PlayerSession) -> None:
        connection = session.connection
        view_distance = self.server.config.server.view_distance
        spawn = self.world.spawn
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
        await connection.send("clientbound.update_view_position", {"chunk_x": 0, "chunk_z": 0})
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
        await connection.send("clientbound.chunk_batch_start", {})
        sent_chunks = 0
        for chunk_x in range(-view_distance, view_distance + 1):
            for chunk_z in range(-view_distance, view_distance + 1):
                chunk = self.get_chunk(ChunkPosition(chunk_x, chunk_z))
                await connection.send(
                    "clientbound.map_chunk",
                    {
                        "x": chunk.position.x,
                        "z": chunk.position.z,
                        "heightmaps": empty_heightmaps(),
                        "chunk_data": encode_empty_chunk_data(),
                        "lights": empty_light_masks(),
                    },
                )
                sent_chunks += 1
        logger.info("initial chunks sent id={} count={}", connection.connection_id, sent_chunks)
        await connection.send("clientbound.chunk_batch_finished", {"batch_size": sent_chunks})
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
