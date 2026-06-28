import asyncio
from typing import cast

from ghostliness.auth import offline_uuid
from ghostliness.config import GhostlinessConfig, ServerConfig, WorldConfig
from ghostliness.items import DIRT_ITEM_ID, GRASS_BLOCK_ITEM_ID, STONE_ITEM_ID, ItemStack
from ghostliness.protocol.containers import PacketContainer
from ghostliness.protocol.registry import PacketDirection
from ghostliness.protocol.versions import JAVA_26_2
from ghostliness.server import GhostlinessServer
from ghostliness.server.connection import Connection
from ghostliness.server.events import PlayerJoinEvent, PlayerQuitEvent
from ghostliness.world import (
    AIR,
    DIRT,
    GRASS_BLOCK,
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
