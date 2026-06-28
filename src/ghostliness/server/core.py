from __future__ import annotations

import asyncio
import contextlib
import time
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from ghostliness.auth import Authenticator
from ghostliness.config import GhostlinessConfig
from ghostliness.events import EventBus
from ghostliness.plugins import PluginLoader
from ghostliness.protocol.manager import ProtocolManager
from ghostliness.protocol.registry import PacketRegistry
from ghostliness.protocol.versions import JAVA_26_2
from ghostliness.server.connection import Connection
from ghostliness.server.player import Player
from ghostliness.server.runtime import GameRuntime
from ghostliness.world import World
from ghostliness.world_storage import WorldStorage, create_world_storage


@dataclass(slots=True)
class GhostlinessServer:
    config: GhostlinessConfig = field(default_factory=GhostlinessConfig)
    registry: PacketRegistry = JAVA_26_2
    events: EventBus = field(init=False)
    protocol: ProtocolManager = field(init=False)
    authenticator: Authenticator = field(init=False)
    world: World = field(init=False)
    storage: WorldStorage = field(init=False)
    runtime: GameRuntime = field(init=False)
    players: dict[str, Player] = field(init=False)
    connections: dict[str, Connection] = field(init=False)
    _server: asyncio.Server | None = field(init=False, default=None)
    _tick_task: asyncio.Task[None] | None = field(init=False, default=None)
    _plugin_loader: PluginLoader = field(init=False)

    def __post_init__(self) -> None:
        self.events = EventBus()
        self.protocol = ProtocolManager()
        self.authenticator = Authenticator(self.config.auth.mode)
        self.world = World(name=self.config.world.name, generator=self.config.world.generator)
        self.storage = create_world_storage(
            self.config.world.storage,
            Path(self.config.world.path),
        )
        self.runtime = GameRuntime(self, self.world, self.storage)
        self.players = self.runtime.players
        self.connections: dict[str, Connection] = {}
        self._server: asyncio.Server | None = None
        self._tick_task: asyncio.Task[None] | None = None
        self._plugin_loader = PluginLoader(self)

    async def start(self) -> None:
        if self.config.plugins.enabled:
            await self._plugin_loader.load_all(self.config.plugins.paths)
        self._server = await asyncio.start_server(
            self._handle_client,
            self.config.server.host,
            self.config.server.port,
        )
        sockets = ", ".join(str(sock.getsockname()) for sock in self._server.sockets or ())
        logger.info(
            "GHOSTLINESS listening sockets={} motd={!r} max_players={} auth={}",
            sockets,
            self.config.server.motd,
            self.config.server.max_players,
            self.config.auth.mode,
        )
        self._tick_task = asyncio.create_task(self._tick_loop(), name="ghostliness-tick")

    async def serve_forever(self) -> None:
        await self.start()
        if self._server is None:
            raise RuntimeError("server did not start")
        async with self._server:
            await self._server.serve_forever()

    async def stop(self) -> None:
        if self._tick_task is not None:
            self._tick_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._tick_task
            self._tick_task = None
        await self._plugin_loader.disable_all()
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        await self.runtime.close()
        logger.info("GHOSTLINESS stopped")

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        connection = Connection(self, reader, writer)
        self.connections[connection.connection_id] = connection
        try:
            await connection.run()
        finally:
            self.connections.pop(connection.connection_id, None)

    async def _tick_loop(self) -> None:
        while True:
            await self.events.publish("tick", self)
            await self.runtime.tick()
            now = time.monotonic()
            for connection in list(self.connections.values()):
                if connection.player is None:
                    continue
                if (
                    connection.pending_keep_alive_id is not None
                    and now - connection.last_keep_alive_sent > 30
                ):
                    logger.warning("keepalive timeout id={}", connection.connection_id)
                    await connection.disconnect({"text": "Timed out"})
                    continue
                if (
                    connection.pending_keep_alive_id is None
                    and now - connection.last_keep_alive_sent > 15
                ):
                    await connection.send_keep_alive()
            await asyncio.sleep(0.05)
