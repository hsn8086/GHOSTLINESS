import asyncio
from typing import cast

from ghostliness.auth import offline_uuid
from ghostliness.config import GhostlinessConfig, ServerConfig, WorldConfig
from ghostliness.protocol.registry import PacketDirection
from ghostliness.server import GhostlinessServer
from ghostliness.server.connection import Connection
from ghostliness.server.events import PlayerJoinEvent, PlayerQuitEvent
from ghostliness.world import ChunkPosition


async def test_runtime_enters_play_and_removes_player(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world")),
        )
    )
    sent_packets = []
    join_events = []
    quit_events = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet.name),
        direction=PacketDirection.CLIENTBOUND,
    )
    server.events.subscribe(
        "player_join",
        lambda event: join_events.append(cast(PlayerJoinEvent, event)),
    )
    server.events.subscribe(
        "player_quit",
        lambda event: quit_events.append(cast(PlayerQuitEvent, event)),
    )
    connection = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, _MemoryWriter()),
    )
    connection.profile = await server.authenticator.authenticate_offline(
        "RuntimeTester",
        offline_uuid("RuntimeTester"),
    )

    await connection.enter_play()

    session = server.runtime.get_session(connection.connection_id)
    assert session is not None
    assert session.player.name == "RuntimeTester"
    assert server.players[connection.connection_id] is session.player
    assert "clientbound.login" in sent_packets
    assert "clientbound.map_chunk" in sent_packets
    assert "clientbound.position" in sent_packets
    assert join_events[0].session is session

    await server.runtime.remove_player(connection.connection_id, "test")

    assert server.runtime.get_session(connection.connection_id) is None
    assert connection.connection_id not in server.players
    assert quit_events[0].reason == "test"
    assert quit_events[0].session is session


def test_runtime_generates_missing_chunks(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(world=WorldConfig(path=str(tmp_path / "world"), generator="void"))
    )

    chunk = server.runtime.get_chunk(ChunkPosition(4, 5))

    assert chunk.position == ChunkPosition(4, 5)
    assert chunk.generated_by == "void"


class _MemoryWriter:
    def __init__(self) -> None:
        self.data = bytearray()

    def get_extra_info(self, name: str):
        if name == "peername":
            return ("memory", 0)
        return None

    def write(self, data: bytes) -> None:
        self.data.extend(data)

    async def drain(self) -> None:
        return None

    def close(self) -> None:
        return None

    async def wait_closed(self) -> None:
        return None
