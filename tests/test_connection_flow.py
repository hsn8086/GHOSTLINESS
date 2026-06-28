import asyncio
from typing import cast

from ghostliness.config import GhostlinessConfig, NetworkConfig, ServerConfig
from ghostliness.protocol.containers import PacketContainer
from ghostliness.protocol.registry import PacketDirection, PacketState
from ghostliness.protocol.versions import JAVA_26_2
from ghostliness.server import GhostlinessServer
from ghostliness.server.connection import Connection, _payload_hex


async def test_connection_methods_emit_configuration_and_play_packets():
    config = GhostlinessConfig(
        server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
        network=NetworkConfig(compression_threshold=-1),
    )
    server = GhostlinessServer(config)
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet.name),
        direction=PacketDirection.CLIENTBOUND,
    )
    connection = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, _MemoryWriter()),
    )

    login_start = PacketContainer(
        JAVA_26_2.get_by_name("serverbound.login_start"),
        {"name": "Tester", "uuid": None},
    )
    await connection._handle_login_start(login_start)
    await connection._start_configuration()
    await connection.enter_play()

    assert "clientbound.login_success" in sent_packets
    assert "clientbound.registry_data" in sent_packets
    assert "clientbound.finish_configuration" in sent_packets
    assert "clientbound.login" in sent_packets
    assert "clientbound.game_event" in sent_packets
    assert "clientbound.map_chunk" in sent_packets
    assert "clientbound.position" in sent_packets
    assert sent_packets.count("clientbound.set_player_inventory") == 3
    assert "clientbound.set_held_slot" in sent_packets
    assert connection.state == PacketState.PLAY


async def test_connection_ignores_interact_packet_without_disconnect():
    config = GhostlinessConfig(
        server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
        network=NetworkConfig(compression_threshold=-1),
    )
    server = GhostlinessServer(config)
    writer = _MemoryWriter()
    connection = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, writer),
        state=PacketState.PLAY,
    )

    packet = PacketContainer(
        JAVA_26_2.get_by_name("serverbound.interact"),
        {
            "entity_id": 42,
            "hand": 0,
            "hand_name": "main_hand",
            "location": {"x": 0.0, "y": 0.0, "z": 0.0},
            "using_secondary_action": False,
        },
    )

    await connection._dispatch(packet)

    assert writer.data == bytearray()
    assert writer.closed is False


async def test_connection_handles_container_close_without_disconnect():
    config = GhostlinessConfig(
        server=ServerConfig(host="127.0.0.1", port=0),
        network=NetworkConfig(compression_threshold=-1),
    )
    server = GhostlinessServer(config)
    writer = _MemoryWriter()
    connection = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, writer),
        state=PacketState.PLAY,
    )

    packet = PacketContainer(
        JAVA_26_2.get_by_name("serverbound.container_close"),
        {"container_id": 0},
    )

    await connection._dispatch(packet)

    assert writer.data == bytearray()
    assert writer.closed is False


def test_payload_hex_is_capped_for_logs():
    assert _payload_hex(bytes(range(4))) == "00010203"
    assert _payload_hex(bytes(range(70))) == f"{bytes(range(64)).hex()}...(+6 bytes)"


class _MemoryWriter:
    def __init__(self) -> None:
        self.data = bytearray()
        self.closed = False

    def get_extra_info(self, name: str):
        if name == "peername":
            return ("memory", 0)
        return None

    def write(self, data: bytes) -> None:
        self.data.extend(data)

    async def drain(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True
        return None

    async def wait_closed(self) -> None:
        return None
