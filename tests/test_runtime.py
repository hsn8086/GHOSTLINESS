from __future__ import annotations

import asyncio
from typing import cast

from ghostliness.auth import offline_uuid
from ghostliness.config import GhostlinessConfig, ServerConfig, WorldConfig
from ghostliness.items import DIRT_ITEM_ID, GRASS_BLOCK_ITEM_ID, STONE_ITEM_ID, ItemStack
from ghostliness.protocol.containers import PacketContainer
from ghostliness.protocol.framing import decode_frame
from ghostliness.protocol.registry import PacketDirection, PacketState
from ghostliness.protocol.types import Buffer
from ghostliness.protocol.versions import JAVA_26_2
from ghostliness.server import GhostlinessServer
from ghostliness.server.connection import Connection
from ghostliness.server.events import PlayerJoinEvent, PlayerQuitEvent
from ghostliness.server.player import PlayerPose
from ghostliness.world import (
    AIR,
    DIRT,
    GRASS_BLOCK,
    STONE,
    BlockPosition,
    BlockState,
    ChunkPosition,
    Position,
)
from ghostliness.world_data import WORLD_HEIGHT, WORLD_MIN_Y, encode_empty_chunk_data


async def _enter_test_connection(server: GhostlinessServer) -> Connection:
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
    return connection


def _decode_clientbound_packets(writer: _MemoryWriter) -> list[PacketContainer]:
    buffer = Buffer(bytes(writer.data))
    packets = []
    while buffer.remaining:
        frame_length = buffer.read_varint()
        frame = buffer.read(frame_length)
        packets.append(
            decode_frame(
                JAVA_26_2,
                PacketState.PLAY,
                PacketDirection.CLIENTBOUND,
                frame,
            )
        )
    return packets


def _decode_clientbound_names(writer: _MemoryWriter) -> list[str]:
    return [packet.name for packet in _decode_clientbound_packets(writer)]


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
    assert sent_packets.count("clientbound.set_player_inventory") == 3
    assert "clientbound.set_held_slot" in sent_packets
    assert session.player.inventory.hotbar[0].item_id == STONE_ITEM_ID
    assert session.player.inventory.hotbar[1].item_id == DIRT_ITEM_ID
    assert session.player.inventory.hotbar[2].item_id == GRASS_BLOCK_ITEM_ID
    assert session.player.inventory.selected_slot == 0
    assert session.chunk_center == ChunkPosition(0, 0)
    assert session.sent_chunks == {ChunkPosition(0, 0)}
    assert join_events[0].session is session

    await server.runtime.remove_player(connection.connection_id, "test")

    assert server.runtime.get_session(connection.connection_id) is None
    assert connection.connection_id not in server.players
    assert quit_events[0].reason == "test"
    assert quit_events[0].session is session


async def test_runtime_sends_generated_flat_chunk_data(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="flat"),
        )
    )
    map_chunks = []
    server.protocol.add_packet_listener(
        lambda packet: map_chunks.append(packet.fields)
        if packet.name == "clientbound.map_chunk"
        else None,
        direction=PacketDirection.CLIENTBOUND,
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

    assert len(map_chunks) == 1
    assert map_chunks[0]["chunk_data"] != encode_empty_chunk_data()
    assert len(cast(bytes, map_chunks[0]["chunk_data"])) > len(encode_empty_chunk_data())
    assert map_chunks[0]["heightmaps"] != []


def test_runtime_generates_missing_chunks(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(world=WorldConfig(path=str(tmp_path / "world"), generator="void"))
    )

    chunk = server.runtime.get_chunk(ChunkPosition(4, 5))

    assert chunk.position == ChunkPosition(4, 5)
    assert chunk.generated_by == "void"


def test_runtime_chunk_window_uses_square_radius_and_stable_order(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(world=WorldConfig(path=str(tmp_path / "world"), generator="void"))
    )
    center = ChunkPosition(0, 0)
    window = server.runtime.chunk_window(center, 1)

    assert window == {
        ChunkPosition(-1, -1),
        ChunkPosition(-1, 0),
        ChunkPosition(-1, 1),
        ChunkPosition(0, -1),
        ChunkPosition(0, 0),
        ChunkPosition(0, 1),
        ChunkPosition(1, -1),
        ChunkPosition(1, 0),
        ChunkPosition(1, 1),
    }
    assert server.runtime.ordered_chunk_window(window, center) == [
        ChunkPosition(0, 0),
        ChunkPosition(-1, 0),
        ChunkPosition(0, -1),
        ChunkPosition(0, 1),
        ChunkPosition(1, 0),
        ChunkPosition(-1, -1),
        ChunkPosition(-1, 1),
        ChunkPosition(1, -1),
        ChunkPosition(1, 1),
    ]


def test_runtime_player_position_maps_to_chunk_with_floor_semantics(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(world=WorldConfig(path=str(tmp_path / "world"), generator="void"))
    )

    assert server.runtime.chunk_position_for_player(Position(x=15.9, z=15.9)) == ChunkPosition(0, 0)
    assert server.runtime.chunk_position_for_player(Position(x=16.0, z=0.0)) == ChunkPosition(1, 0)
    assert server.runtime.chunk_position_for_player(Position(x=-0.1, z=0.0)) == ChunkPosition(-1, 0)


async def test_runtime_player_movement_updates_position_rotation_and_ground_state(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    connection = await _enter_test_connection(server)
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None

    await server.runtime.handle_player_movement(
        connection.connection_id,
        {"x": 3.0, "y": 70.5, "z": -2.0, "yaw": 90.0, "pitch": 45.0, "flags": 1},
    )

    assert session.player.position.x == 3.0
    assert session.player.position.y == 70.5
    assert session.player.position.z == -2.0
    assert session.player.position.yaw == 90.0
    assert session.player.position.pitch == 45.0
    assert session.player.on_ground is True

    await server.runtime.handle_player_movement(
        connection.connection_id,
        {"yaw": 180.0, "pitch": -10.0, "flags": 0},
    )

    assert session.player.position.x == 3.0
    assert session.player.position.y == 70.5
    assert session.player.position.z == -2.0
    assert session.player.position.yaw == 180.0
    assert session.player.position.pitch == -10.0
    assert session.player.on_ground is False


async def test_runtime_spawns_visible_players_for_each_other(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    first_writer = _MemoryWriter()
    first = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, first_writer),
    )
    first.profile = await server.authenticator.authenticate_offline(
        "RuntimeOne",
        offline_uuid("RuntimeOne"),
    )
    await first.enter_play()

    second_writer = _MemoryWriter()
    second = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, second_writer),
    )
    second.profile = await server.authenticator.authenticate_offline(
        "RuntimeTwo",
        offline_uuid("RuntimeTwo"),
    )
    await second.enter_play()

    first_session = server.runtime.get_session(first.connection_id)
    second_session = server.runtime.get_session(second.connection_id)
    assert first_session is not None
    assert second_session is not None
    assert first_session.player.entity_id in second_session.visible_entities
    assert second_session.player.entity_id in first_session.visible_entities

    first_packets = _decode_clientbound_packets(first_writer)
    second_packets = _decode_clientbound_packets(second_writer)
    assert "clientbound.player_info_update" in [packet.name for packet in first_packets]
    assert "clientbound.add_entity" in [packet.name for packet in first_packets]
    assert "clientbound.player_info_update" in [packet.name for packet in second_packets]
    assert "clientbound.add_entity" in [packet.name for packet in second_packets]
    assert any(
        packet.name == "clientbound.add_entity"
        and packet.fields["entity_id"] == second_session.player.entity_id
        for packet in first_packets
    )
    assert any(
        packet.name == "clientbound.add_entity"
        and packet.fields["entity_id"] == first_session.player.entity_id
        for packet in second_packets
    )


async def test_runtime_broadcasts_player_teleport_to_visible_viewers(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    first_writer = _MemoryWriter()
    first = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, first_writer),
    )
    first.profile = await server.authenticator.authenticate_offline("RuntimeOne")
    await first.enter_play()
    second_writer = _MemoryWriter()
    second = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, second_writer),
    )
    second.profile = await server.authenticator.authenticate_offline("RuntimeTwo")
    await second.enter_play()
    first_writer.data.clear()
    second_writer.data.clear()

    first_session = server.runtime.get_session(first.connection_id)
    assert first_session is not None
    await server.runtime.handle_player_movement(
        first.connection_id,
        {"x": 2.5, "y": 66.0, "z": 3.5, "yaw": 30.0, "pitch": 10.0, "flags": 1},
    )

    assert _decode_clientbound_names(first_writer) == []
    second_packets = _decode_clientbound_packets(second_writer)
    assert [packet.name for packet in second_packets] == ["clientbound.teleport_entity"]
    assert second_packets[0].fields["entity_id"] == first_session.player.entity_id


async def test_runtime_removes_player_entity_when_out_of_view_and_on_disconnect(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    first_writer = _MemoryWriter()
    first = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, first_writer),
    )
    first.profile = await server.authenticator.authenticate_offline("RuntimeOne")
    await first.enter_play()
    second_writer = _MemoryWriter()
    second = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, second_writer),
    )
    second.profile = await server.authenticator.authenticate_offline("RuntimeTwo")
    await second.enter_play()
    first_session = server.runtime.get_session(first.connection_id)
    second_session = server.runtime.get_session(second.connection_id)
    assert first_session is not None
    assert second_session is not None
    first_writer.data.clear()
    second_writer.data.clear()

    await server.runtime.handle_player_movement(
        second.connection_id,
        {"x": 16.0, "y": 65.0, "z": 0.0, "yaw": 0.0, "pitch": 0.0},
    )

    assert second_session.player.entity_id not in first_session.visible_entities
    first_packets = _decode_clientbound_packets(first_writer)
    assert [packet.name for packet in first_packets] == [
        "clientbound.remove_entities",
        "clientbound.player_info_remove",
    ]
    assert first_packets[0].fields["entity_ids"] == [second_session.player.entity_id]
    assert first_session.player.entity_id not in second_session.visible_entities

    await server.runtime.handle_player_movement(
        second.connection_id,
        {"x": 0.0, "y": 65.0, "z": 0.0, "yaw": 0.0, "pitch": 0.0},
    )
    first_writer.data.clear()
    second_writer.data.clear()

    await server.runtime.remove_player(second.connection_id, "test")

    first_packets = _decode_clientbound_packets(first_writer)
    assert [packet.name for packet in first_packets] == [
        "clientbound.remove_entities",
        "clientbound.player_info_remove",
    ]
    assert first_packets[0].fields["entity_ids"] == [second_session.player.entity_id]


async def test_runtime_player_movement_rejects_invalid_coordinates(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    connection = await _enter_test_connection(server)
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None
    before = Position(
        x=session.player.position.x,
        y=session.player.position.y,
        z=session.player.position.z,
        yaw=session.player.position.yaw,
        pitch=session.player.position.pitch,
    )

    await server.runtime.handle_player_movement(
        connection.connection_id,
        {"x": float("nan"), "y": 70.0, "z": 0.0, "flags": 1},
    )
    await server.runtime.handle_player_movement(
        connection.connection_id,
        {"x": 30_000_001.0, "y": 70.0, "z": 0.0, "flags": 1},
    )
    await server.runtime.handle_player_movement(
        connection.connection_id,
        {"x": 0.0, "y": WORLD_MIN_Y + WORLD_HEIGHT + 65.0, "z": 0.0, "flags": 1},
    )

    assert session.player.position == before
    assert session.player.on_ground is False


async def test_runtime_player_input_and_command_update_state(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    connection = await _enter_test_connection(server)
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None

    server.runtime.handle_player_input(
        connection.connection_id,
        {
            "forward": True,
            "backward": False,
            "left": True,
            "right": False,
            "jump": True,
            "shift": True,
            "sprint": True,
        },
    )
    server.runtime.handle_player_command(connection.connection_id, "start_sprinting")

    assert session.player.input.forward is True
    assert session.player.input.left is True
    assert session.player.input.jump is True
    assert session.player.input.shift is True
    assert session.player.input.sprint is True
    assert session.player.sneaking is True
    assert session.player.pose == PlayerPose.SNEAKING
    assert session.player.sprinting is True

    server.runtime.handle_player_input(connection.connection_id, {"shift": False})
    server.runtime.handle_player_command(connection.connection_id, "stop_sprinting")

    assert session.player.sneaking is False
    assert session.player.pose == PlayerPose.STANDING
    assert session.player.sprinting is False


async def test_runtime_initial_chunk_window_uses_spawn_chunk(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    server.world.spawn.x = 32.0
    server.world.spawn.z = -0.1
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
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
    assert session.chunk_center == ChunkPosition(2, -1)
    assert session.sent_chunks == {ChunkPosition(2, -1)}
    update_view_positions = [
        packet.fields
        for packet in sent_packets
        if packet.name == "clientbound.update_view_position"
    ]
    map_chunks = [
        packet.fields for packet in sent_packets if packet.name == "clientbound.map_chunk"
    ]
    assert update_view_positions[-1] == {"chunk_x": 2, "chunk_z": -1}
    assert [(fields["x"], fields["z"]) for fields in map_chunks] == [(2, -1)]


async def test_runtime_same_chunk_movement_does_not_resend_chunks(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
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
    sent_packets.clear()

    await connection._update_player_position(
        PacketContainer(
            JAVA_26_2.get_by_name("serverbound.position"),
            {"x": 1.0, "y": 65.0, "z": 1.0, "flags": 0},
        )
    )

    assert [packet.name for packet in sent_packets] == []


async def test_runtime_cross_chunk_movement_loads_and_unloads_delta(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=1),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
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
    sent_packets.clear()

    await connection._update_player_position(
        PacketContainer(
            JAVA_26_2.get_by_name("serverbound.position"),
            {"x": 16.0, "y": 65.0, "z": 0.0, "flags": 0},
        )
    )

    assert session.chunk_center == ChunkPosition(1, 0)
    assert session.sent_chunks == server.runtime.chunk_window(ChunkPosition(1, 0), 1)
    assert [packet.name for packet in sent_packets] == [
        "clientbound.update_view_position",
        "clientbound.forget_level_chunk",
        "clientbound.forget_level_chunk",
        "clientbound.forget_level_chunk",
        "clientbound.chunk_batch_start",
        "clientbound.map_chunk",
        "clientbound.map_chunk",
        "clientbound.map_chunk",
        "clientbound.chunk_batch_finished",
    ]
    assert sent_packets[0].fields == {"chunk_x": 1, "chunk_z": 0}
    assert [(packet.fields["x"], packet.fields["z"]) for packet in sent_packets[1:4]] == [
        (-1, 0),
        (-1, -1),
        (-1, 1),
    ]
    assert [(packet.fields["x"], packet.fields["z"]) for packet in sent_packets[5:8]] == [
        (2, 0),
        (2, -1),
        (2, 1),
    ]
    assert sent_packets[-1].fields == {"batch_size": 3}


async def test_runtime_negative_cross_chunk_movement_updates_center(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
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
    sent_packets.clear()

    await connection._update_player_position(
        PacketContainer(
            JAVA_26_2.get_by_name("serverbound.position"),
            {"x": -0.1, "y": 65.0, "z": 0.0, "flags": 0},
        )
    )

    assert session.chunk_center == ChunkPosition(-1, 0)
    assert session.sent_chunks == {ChunkPosition(-1, 0)}
    assert [packet.name for packet in sent_packets] == [
        "clientbound.update_view_position",
        "clientbound.forget_level_chunk",
        "clientbound.chunk_batch_start",
        "clientbound.map_chunk",
        "clientbound.chunk_batch_finished",
    ]
    assert sent_packets[0].fields == {"chunk_x": -1, "chunk_z": 0}
    assert sent_packets[1].fields == {"x": 0, "z": 0}
    assert sent_packets[3].fields["x"] == -1
    assert sent_packets[3].fields["z"] == 0


async def test_runtime_player_action_destroys_block_and_persists_chunk(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="flat"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
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
    sent_packets.clear()

    await server.runtime.handle_player_action(
        connection.connection_id,
        "start_destroy_block",
        {"x": -1, "y": 64, "z": -1},
        9,
    )

    chunk = server.runtime.get_chunk(ChunkPosition(-1, -1))
    assert chunk.get_block(BlockPosition(15, 64, 15)) == AIR

    persisted = server.storage.load_chunk(ChunkPosition(-1, -1))
    assert persisted is not None
    assert persisted.get_block(BlockPosition(15, 64, 15)) == AIR

    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 9}
    assert sent_packets[1].fields == {
        "position": {"x": -1, "y": 64, "z": -1},
        "state": AIR,
    }
    assert len(server.runtime.entities) == 0


async def test_runtime_survival_block_destroy_spawns_visible_item_drop_in_loaded_chunk(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="flat"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
    )
    connection = await _enter_test_connection(server)
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None
    session.player.gamemode = 0
    sent_packets.clear()

    await server.runtime.handle_player_action(
        connection.connection_id,
        "start_destroy_block",
        {"x": 1, "y": 64, "z": 1},
        24,
    )

    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
        "clientbound.add_entity",
        "clientbound.set_entity_data",
    ]
    assert sent_packets[2].fields["entity_type_id"] == 71
    assert sent_packets[3].fields["entries"][0]["value"] == ItemStack(
        item_id=GRASS_BLOCK_ITEM_ID,
        count=1,
    )


async def test_runtime_creative_block_destroy_does_not_spawn_item_drop(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="flat"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
    )
    connection = await _enter_test_connection(server)
    sent_packets.clear()

    await server.runtime.handle_player_action(
        connection.connection_id,
        "start_destroy_block",
        {"x": 1, "y": 64, "z": 1},
        25,
    )

    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert server.runtime.entities == {}


async def test_runtime_player_action_rejects_air_without_saving_chunk(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
    )
    connection = await _enter_test_connection(server)
    sent_packets.clear()

    await server.runtime.handle_player_action(
        connection.connection_id,
        "start_destroy_block",
        {"x": 1, "y": 64, "z": 1},
        14,
    )

    chunk = server.runtime.get_chunk(ChunkPosition(0, 0))
    assert chunk.get_block(BlockPosition(1, 64, 1)) == AIR
    assert server.storage.load_chunk(ChunkPosition(0, 0)) is None
    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 14}
    assert sent_packets[1].fields == {
        "position": {"x": 1, "y": 64, "z": 1},
        "state": AIR,
    }


async def test_runtime_player_action_rejects_out_of_world_without_saving_chunk(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="flat"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
    )
    connection = await _enter_test_connection(server)
    sent_packets.clear()
    out_of_world_y = WORLD_MIN_Y + WORLD_HEIGHT

    await server.runtime.handle_player_action(
        connection.connection_id,
        "start_destroy_block",
        {"x": 1, "y": out_of_world_y, "z": 1},
        15,
    )

    assert server.storage.load_chunk(ChunkPosition(0, 0)) is None
    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 15}
    assert sent_packets[1].fields == {
        "position": {"x": 1, "y": out_of_world_y, "z": 1},
        "state": AIR,
    }


async def test_runtime_player_action_rejects_unknown_block_without_saving_chunk(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
    )
    connection = await _enter_test_connection(server)
    unknown_state = BlockState("ghostliness:unknown")
    chunk = server.runtime.get_chunk(ChunkPosition(0, 0))
    chunk.set_block(BlockPosition(1, 65, 1), unknown_state)
    sent_packets.clear()

    await server.runtime.handle_player_action(
        connection.connection_id,
        "start_destroy_block",
        {"x": 1, "y": 65, "z": 1},
        16,
    )

    assert chunk.get_block(BlockPosition(1, 65, 1)) == unknown_state
    assert server.storage.load_chunk(ChunkPosition(0, 0)) is None
    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 16}
    assert sent_packets[1].fields == {
        "position": {"x": 1, "y": 65, "z": 1},
        "state": unknown_state,
    }


async def test_runtime_use_item_on_places_selected_hotbar_block_and_persists_chunk(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="flat"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
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
    session.player.inventory.set_hotbar_slot(0, ItemStack(item_id=DIRT_ITEM_ID, count=64))
    sent_packets.clear()

    await server.runtime.handle_use_item_on(
        connection.connection_id,
        0,
        {
            "position": {"x": 1, "y": 64, "z": 0},
            "direction": 1,
            "direction_name": "up",
            "cursor": {"x": 0.5, "y": 1.0, "z": 0.5},
            "inside": False,
            "world_border_hit": False,
        },
        10,
    )

    chunk = server.runtime.get_chunk(ChunkPosition(0, 0))
    assert chunk.get_block(BlockPosition(1, 65, 0)) == DIRT

    persisted = server.storage.load_chunk(ChunkPosition(0, 0))
    assert persisted is not None
    assert persisted.get_block(BlockPosition(1, 65, 0)) == DIRT

    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 10}
    assert sent_packets[1].fields == {
        "position": {"x": 1, "y": 65, "z": 0},
        "state": DIRT,
    }
    assert session.player.inventory.selected_stack().count == 64


async def test_runtime_use_item_on_occupied_target_acks_and_rolls_back_block(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="flat"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
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
    session.player.inventory.set_hotbar_slot(0, ItemStack(item_id=DIRT_ITEM_ID, count=64))
    sent_packets.clear()

    await server.runtime.handle_use_item_on(
        connection.connection_id,
        0,
        {
            "position": {"x": 0, "y": 63, "z": 0},
            "direction": 1,
            "direction_name": "up",
            "cursor": {"x": 0.5, "y": 1.0, "z": 0.5},
            "inside": False,
            "world_border_hit": False,
        },
        11,
    )

    chunk = server.runtime.get_chunk(ChunkPosition(0, 0))
    assert chunk.get_block(BlockPosition(0, 64, 0)) == GRASS_BLOCK
    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 11}
    assert sent_packets[1].fields == {
        "position": {"x": 0, "y": 64, "z": 0},
        "state": GRASS_BLOCK,
    }


async def test_runtime_use_item_on_unsupported_item_acks_and_sends_real_target(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="flat"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
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
    session.player.inventory.set_hotbar_slot(0, ItemStack.empty())
    sent_packets.clear()

    await server.runtime.handle_use_item_on(
        connection.connection_id,
        0,
        {
            "position": {"x": 1, "y": 64, "z": 0},
            "direction": 1,
            "direction_name": "up",
            "cursor": {"x": 0.5, "y": 1.0, "z": 0.5},
            "inside": False,
            "world_border_hit": False,
        },
        12,
    )

    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 12}
    assert sent_packets[1].fields == {
        "position": {"x": 1, "y": 65, "z": 0},
        "state": AIR,
    }


async def test_runtime_use_item_on_air_support_acks_and_sends_real_target(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
    )
    connection = await _enter_test_connection(server)
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None
    session.player.inventory.set_hotbar_slot(0, ItemStack(item_id=DIRT_ITEM_ID, count=64))
    sent_packets.clear()

    await server.runtime.handle_use_item_on(
        connection.connection_id,
        0,
        {
            "position": {"x": 2, "y": 64, "z": 0},
            "direction": 1,
            "direction_name": "up",
            "cursor": {"x": 0.5, "y": 1.0, "z": 0.5},
            "inside": False,
            "world_border_hit": False,
        },
        17,
    )

    chunk = server.runtime.get_chunk(ChunkPosition(0, 0))
    assert chunk.get_block(BlockPosition(2, 65, 0)) == AIR
    assert server.storage.load_chunk(ChunkPosition(0, 0)) is None
    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 17}
    assert sent_packets[1].fields == {
        "position": {"x": 2, "y": 65, "z": 0},
        "state": AIR,
    }


async def test_runtime_use_item_on_out_of_world_acks_and_sends_hit_block(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
    )
    connection = await _enter_test_connection(server)
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None
    session.player.inventory.set_hotbar_slot(0, ItemStack(item_id=DIRT_ITEM_ID, count=64))
    sent_packets.clear()
    hit_y = WORLD_MIN_Y + WORLD_HEIGHT - 1

    await server.runtime.handle_use_item_on(
        connection.connection_id,
        0,
        {
            "position": {"x": 2, "y": hit_y, "z": 0},
            "direction": 1,
            "direction_name": "up",
            "cursor": {"x": 0.5, "y": 1.0, "z": 0.5},
            "inside": False,
            "world_border_hit": False,
        },
        18,
    )

    assert server.storage.load_chunk(ChunkPosition(0, 0)) is None
    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 18}
    assert sent_packets[1].fields == {
        "position": {"x": 2, "y": hit_y, "z": 0},
        "state": AIR,
    }


async def test_runtime_use_item_on_player_collision_acks_and_sends_real_target(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="flat"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
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
    session.player.inventory.set_hotbar_slot(0, ItemStack(item_id=DIRT_ITEM_ID, count=64))
    sent_packets.clear()

    await server.runtime.handle_use_item_on(
        connection.connection_id,
        0,
        {
            "position": {"x": 0, "y": 64, "z": 0},
            "direction": 1,
            "direction_name": "up",
            "cursor": {"x": 0.5, "y": 1.0, "z": 0.5},
            "inside": False,
            "world_border_hit": False,
        },
        13,
    )

    chunk = server.runtime.get_chunk(ChunkPosition(0, 0))
    assert chunk.get_block(BlockPosition(0, 65, 0)) == AIR
    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 13}
    assert sent_packets[1].fields == {
        "position": {"x": 0, "y": 65, "z": 0},
        "state": AIR,
    }


async def test_runtime_use_item_on_player_edge_collision_rejects_block(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="flat"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
    )
    connection = await _enter_test_connection(server)
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None
    session.player.position.x = 0.8
    session.player.position.y = 65.0
    session.player.position.z = 0.5
    session.player.inventory.set_hotbar_slot(0, ItemStack(item_id=DIRT_ITEM_ID, count=64))
    sent_packets.clear()

    await server.runtime.handle_use_item_on(
        connection.connection_id,
        0,
        {
            "position": {"x": 1, "y": 64, "z": 0},
            "direction": 1,
            "direction_name": "up",
            "cursor": {"x": 0.5, "y": 1.0, "z": 0.5},
            "inside": False,
            "world_border_hit": False,
        },
        19,
    )

    chunk = server.runtime.get_chunk(ChunkPosition(0, 0))
    assert chunk.get_block(BlockPosition(1, 65, 0)) == AIR
    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 19}
    assert sent_packets[1].fields == {
        "position": {"x": 1, "y": 65, "z": 0},
        "state": AIR,
    }


async def test_runtime_use_item_on_sneaking_uses_shorter_collision_height(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="flat"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
    )
    connection = await _enter_test_connection(server)
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None
    session.player.position.x = 2.5
    session.player.position.y = 65.5
    session.player.position.z = 0.5
    session.player.inventory.set_hotbar_slot(0, ItemStack(item_id=DIRT_ITEM_ID, count=64))
    chunk = server.runtime.get_chunk(ChunkPosition(0, 0))
    chunk.set_block(BlockPosition(2, 66, 0), STONE)
    sent_packets.clear()

    await server.runtime.handle_use_item_on(
        connection.connection_id,
        0,
        {
            "position": {"x": 2, "y": 66, "z": 0},
            "direction": 1,
            "direction_name": "up",
            "cursor": {"x": 0.5, "y": 1.0, "z": 0.5},
            "inside": False,
            "world_border_hit": False,
        },
        20,
    )

    assert chunk.get_block(BlockPosition(2, 67, 0)) == AIR
    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 20}
    assert sent_packets[1].fields == {
        "position": {"x": 2, "y": 67, "z": 0},
        "state": AIR,
    }

    session.player.set_sneaking(True)
    sent_packets.clear()

    await server.runtime.handle_use_item_on(
        connection.connection_id,
        0,
        {
            "position": {"x": 2, "y": 66, "z": 0},
            "direction": 1,
            "direction_name": "up",
            "cursor": {"x": 0.5, "y": 1.0, "z": 0.5},
            "inside": False,
            "world_border_hit": False,
        },
        21,
    )

    assert chunk.get_block(BlockPosition(2, 67, 0)) == DIRT
    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.block_update",
    ]
    assert sent_packets[0].fields == {"sequence": 21}
    assert sent_packets[1].fields == {
        "position": {"x": 2, "y": 67, "z": 0},
        "state": DIRT,
    }


async def test_runtime_drop_item_spawns_item_entity_and_syncs_hotbar(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
    )
    connection = await _enter_test_connection(server)
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None
    session.player.inventory.set_hotbar_slot(0, ItemStack(item_id=DIRT_ITEM_ID, count=5))
    sent_packets.clear()

    await server.runtime.handle_player_action(
        connection.connection_id,
        "drop_item",
        {"x": 0, "y": 0, "z": 0},
        22,
    )

    assert session.player.inventory.hotbar[0] == ItemStack(item_id=DIRT_ITEM_ID, count=4)
    assert [packet.name for packet in sent_packets] == [
        "clientbound.block_changed_ack",
        "clientbound.set_player_inventory",
        "clientbound.add_entity",
        "clientbound.set_entity_data",
        "clientbound.set_entity_motion",
    ]
    assert sent_packets[1].fields == {
        "slot": 0,
        "contents": ItemStack(item_id=DIRT_ITEM_ID, count=4),
    }
    assert sent_packets[2].fields["entity_type_id"] == 71
    assert sent_packets[3].fields["entries"][0]["value"] == ItemStack(
        item_id=DIRT_ITEM_ID,
        count=1,
    )
    assert sent_packets[4].fields["dz"] > 0.0


async def test_runtime_drop_all_items_clears_selected_slot(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    sent_packets = []
    server.protocol.add_packet_listener(
        lambda packet: sent_packets.append(packet),
        direction=PacketDirection.CLIENTBOUND,
    )
    connection = await _enter_test_connection(server)
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None
    session.player.inventory.set_hotbar_slot(0, ItemStack(item_id=STONE_ITEM_ID, count=7))
    sent_packets.clear()

    await server.runtime.handle_player_action(
        connection.connection_id,
        "drop_all_items",
        {"x": 0, "y": 0, "z": 0},
        23,
    )

    assert session.player.inventory.hotbar[0].is_empty
    assert sent_packets[1].fields == {"slot": 0, "contents": ItemStack.empty()}
    assert sent_packets[3].fields["entries"][0]["value"] == ItemStack(
        item_id=STONE_ITEM_ID,
        count=7,
    )
    assert sent_packets[4].name == "clientbound.set_entity_motion"


async def test_runtime_pickup_item_adds_to_hotbar_and_removes_entity(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    writer = _MemoryWriter()
    connection = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, writer),
    )
    connection.profile = await server.authenticator.authenticate_offline("RuntimeTester")
    await connection.enter_play()
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None
    session.player.inventory.set_hotbar_slot(0, ItemStack(item_id=DIRT_ITEM_ID, count=63))
    entity = await server.runtime.spawn_item_entity(
        ItemStack(item_id=DIRT_ITEM_ID, count=1),
        Position(x=session.player.position.x, y=session.player.position.y + 0.5, z=0.0),
        pickup_delay=0,
    )
    writer.data.clear()

    await server.runtime.handle_player_movement(
        connection.connection_id,
        {
            "x": session.player.position.x,
            "y": session.player.position.y,
            "z": session.player.position.z,
            "yaw": 0.0,
            "pitch": 0.0,
        },
    )

    assert session.player.inventory.hotbar[0] == ItemStack(item_id=DIRT_ITEM_ID, count=64)
    assert entity.entity_id not in server.runtime.entities
    packets = _decode_clientbound_packets(writer)
    assert [packet.name for packet in packets] == [
        "clientbound.set_player_inventory",
        "clientbound.take_item_entity",
        "clientbound.remove_entities",
    ]
    assert packets[1].fields == {
        "item_id": entity.entity_id,
        "player_id": session.player.entity_id,
        "amount": 1,
    }


async def test_runtime_full_hotbar_rejects_item_pickup(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    writer = _MemoryWriter()
    connection = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, writer),
    )
    connection.profile = await server.authenticator.authenticate_offline("RuntimeTester")
    await connection.enter_play()
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None
    for slot in range(9):
        session.player.inventory.set_hotbar_slot(slot, ItemStack(item_id=DIRT_ITEM_ID, count=64))
    entity = await server.runtime.spawn_item_entity(
        ItemStack(item_id=STONE_ITEM_ID, count=1),
        Position(x=session.player.position.x, y=session.player.position.y + 0.5, z=0.0),
        pickup_delay=0,
    )
    writer.data.clear()

    await server.runtime.handle_player_movement(
        connection.connection_id,
        {
            "x": session.player.position.x,
            "y": session.player.position.y,
            "z": session.player.position.z,
            "yaw": 0.0,
            "pitch": 0.0,
        },
    )

    assert entity.entity_id in server.runtime.entities
    assert _decode_clientbound_names(writer) == []


async def test_runtime_removes_item_entity_when_out_of_view_without_player_info_remove(tmp_path):
    server = GhostlinessServer(
        GhostlinessConfig(
            server=ServerConfig(host="127.0.0.1", port=0, view_distance=0),
            world=WorldConfig(path=str(tmp_path / "world"), generator="void"),
        )
    )
    writer = _MemoryWriter()
    connection = Connection(
        server,
        cast(asyncio.StreamReader, object()),
        cast(asyncio.StreamWriter, writer),
    )
    connection.profile = await server.authenticator.authenticate_offline("RuntimeTester")
    await connection.enter_play()
    session = server.runtime.get_session(connection.connection_id)
    assert session is not None
    entity = await server.runtime.spawn_item_entity(
        ItemStack(item_id=STONE_ITEM_ID, count=1),
        Position(x=0.5, y=65.0, z=0.5),
        pickup_delay=10,
    )
    assert entity.entity_id in session.visible_entities
    writer.data.clear()

    await server.runtime.handle_player_movement(
        connection.connection_id,
        {"x": 16.0, "y": 65.0, "z": 0.0, "yaw": 0.0, "pitch": 0.0},
    )

    assert entity.entity_id not in session.visible_entities
    packets = _decode_clientbound_packets(writer)
    assert [packet.name for packet in packets] == [
        "clientbound.update_view_position",
        "clientbound.forget_level_chunk",
        "clientbound.chunk_batch_start",
        "clientbound.map_chunk",
        "clientbound.chunk_batch_finished",
        "clientbound.remove_entities",
    ]
    assert packets[-1].fields == {"entity_ids": [entity.entity_id]}


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
