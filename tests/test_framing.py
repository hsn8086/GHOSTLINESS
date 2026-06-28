import pytest

from ghostliness.items import DIRT_ITEM_ID, STONE_ITEM_ID, ItemStack
from ghostliness.protocol.containers import PacketContainer
from ghostliness.protocol.framing import decode_frame, encode_frame, encode_payload
from ghostliness.protocol.registry import PacketDirection, PacketState
from ghostliness.protocol.types import Buffer, Writer, encode_varint
from ghostliness.protocol.versions import JAVA_26_2
from ghostliness.world import AIR


def test_decode_handshake_frame():
    writer = Writer()
    writer.write_varint(0)
    writer.write_varint(JAVA_26_2.protocol_version)
    writer.write_string("localhost")
    writer.write_unsigned_short(25565)
    writer.write_varint(2)
    payload = writer.to_bytes()
    frame = encode_varint(len(payload)) + payload

    packet = decode_frame(
        JAVA_26_2,
        PacketState.HANDSHAKING,
        PacketDirection.SERVERBOUND,
        frame[1:],
    )

    assert packet.name == "serverbound.handshake"
    assert packet.fields["server_address"] == "localhost"
    assert packet.fields["server_port"] == 25565
    assert packet.fields["next_state"] == 2


def test_protocol_version_targets_latest_release_number():
    assert JAVA_26_2.minecraft_version == "26.2"
    assert JAVA_26_2.protocol_version == 776


def test_26_2_play_clientbound_packet_ids_match_vanilla_registration_order():
    expected_ids = {
        "clientbound.block_changed_ack": 0x04,
        "clientbound.block_update": 0x08,
        "clientbound.chunk_batch_finished": 0x0B,
        "clientbound.chunk_batch_start": 0x0C,
        "clientbound.forget_level_chunk": 0x25,
        "clientbound.game_event": 0x26,
        "clientbound.keep_alive": 0x2C,
        "clientbound.map_chunk": 0x2D,
        "clientbound.login": 0x31,
        "clientbound.position": 0x48,
        "clientbound.update_view_position": 0x5E,
        "clientbound.update_view_distance": 0x5F,
        "clientbound.spawn_position": 0x61,
        "clientbound.set_held_slot": 0x69,
        "clientbound.set_player_inventory": 0x6C,
        "clientbound.system_chat": 0x79,
    }

    for packet_name, packet_id in expected_ids.items():
        assert JAVA_26_2.get_by_name(packet_name).packet_id == packet_id


def test_26_2_play_serverbound_packet_ids_match_vanilla_registration_order():
    expected_ids = {
        "serverbound.teleport_confirm": 0x00,
        "serverbound.attack": 0x01,
        "serverbound.block_entity_tag_query": 0x02,
        "serverbound.select_bundle_item": 0x03,
        "serverbound.change_difficulty": 0x04,
        "serverbound.change_game_mode": 0x05,
        "serverbound.chat_ack": 0x06,
        "serverbound.chat_command": 0x07,
        "serverbound.chat_command_signed": 0x08,
        "serverbound.chat": 0x09,
        "serverbound.chat_session_update": 0x0A,
        "serverbound.chunk_batch_received": 0x0B,
        "serverbound.client_command": 0x0C,
        "serverbound.client_tick_end": 0x0D,
        "serverbound.play_settings": 0x0E,
        "serverbound.command_suggestion": 0x0F,
        "serverbound.configuration_acknowledged": 0x10,
        "serverbound.container_button_click": 0x11,
        "serverbound.container_click": 0x12,
        "serverbound.container_close": 0x13,
        "serverbound.container_slot_state_changed": 0x14,
        "serverbound.cookie_response": 0x15,
        "serverbound.play_custom_payload": 0x16,
        "serverbound.debug_subscription_request": 0x17,
        "serverbound.edit_book": 0x18,
        "serverbound.entity_tag_query": 0x19,
        "serverbound.interact": 0x1A,
        "serverbound.jigsaw_generate": 0x1B,
        "serverbound.keep_alive": 0x1C,
        "serverbound.lock_difficulty": 0x1D,
        "serverbound.position": 0x1E,
        "serverbound.position_look": 0x1F,
        "serverbound.rotation": 0x20,
        "serverbound.status_only": 0x21,
        "serverbound.move_vehicle": 0x22,
        "serverbound.paddle_boat": 0x23,
        "serverbound.pick_item_from_block": 0x24,
        "serverbound.pick_item_from_entity": 0x25,
        "serverbound.play_ping_request": 0x26,
        "serverbound.place_recipe": 0x27,
        "serverbound.player_abilities": 0x28,
        "serverbound.player_action": 0x29,
        "serverbound.player_command": 0x2A,
        "serverbound.player_input": 0x2B,
        "serverbound.player_loaded": 0x2C,
        "serverbound.pong": 0x2D,
        "serverbound.recipe_book_change_settings": 0x2E,
        "serverbound.recipe_book_seen_recipe": 0x2F,
        "serverbound.rename_item": 0x30,
        "serverbound.resource_pack": 0x31,
        "serverbound.seen_advancements": 0x32,
        "serverbound.select_trade": 0x33,
        "serverbound.set_beacon": 0x34,
        "serverbound.set_carried_item": 0x35,
        "serverbound.set_command_block": 0x36,
        "serverbound.set_command_minecart": 0x37,
        "serverbound.set_creative_mode_slot": 0x38,
        "serverbound.set_game_rule": 0x39,
        "serverbound.set_jigsaw_block": 0x3A,
        "serverbound.set_structure_block": 0x3B,
        "serverbound.set_test_block": 0x3C,
        "serverbound.sign_update": 0x3D,
        "serverbound.spectator_action": 0x3E,
        "serverbound.swing": 0x3F,
        "serverbound.teleport_to_entity": 0x40,
        "serverbound.test_instance_block_action": 0x41,
        "serverbound.use_item_on": 0x42,
        "serverbound.use_item": 0x43,
        "serverbound.custom_click_action": 0x44,
    }

    for packet_name, packet_id in expected_ids.items():
        assert JAVA_26_2.get_by_name(packet_name).packet_id == packet_id


def test_decode_login_start_with_direct_uuid_from_real_client_payload():
    payload = bytes.fromhex("0768736e38303836b0427ad9f4e7421db31a91ea0982c96c")
    packet_type = JAVA_26_2.get_by_name("serverbound.login_start")
    assert packet_type.decoder is not None

    fields = packet_type.decoder(Buffer(payload))

    assert fields["name"] == "hsn8086"
    assert str(fields["uuid"]) == "b0427ad9-f4e7-421d-b31a-91ea0982c96c"


def test_encode_login_success_includes_26_2_session_id():
    profile_uuid = "b0427ad9-f4e7-421d-b31a-91ea0982c96c"
    session_id = "12345678-1234-5678-9234-567812345678"
    packet_type = JAVA_26_2.get_by_name("clientbound.login_success")
    payload = encode_payload(
        packet_type,
        {
            "uuid": profile_uuid,
            "username": "hsn8086",
            "properties": (),
            "session_id": session_id,
        },
    )

    buffer = Buffer(payload)
    assert buffer.read_varint() == 0x02
    assert str(buffer.read_uuid()) == profile_uuid
    assert buffer.read_string(16) == "hsn8086"
    assert buffer.read_varint() == 0
    assert str(buffer.read_uuid()) == session_id
    buffer.ensure_consumed()


def test_encode_play_login_includes_26_2_online_mode_flag():
    packet_type = JAVA_26_2.get_by_name("clientbound.login")
    payload = encode_payload(
        packet_type,
        {
            "entity_id": 1,
            "world_names": ("minecraft:overworld",),
            "max_players": 20,
            "view_distance": 2,
            "simulation_distance": 2,
            "gamemode": 1,
            "dimension_name": "minecraft:overworld",
            "online_mode": False,
            "enforces_secure_chat": False,
        },
    )

    buffer = Buffer(payload)
    assert buffer.read_varint() == 0x31
    assert buffer.read_int() == 1
    assert buffer.read_bool() is False
    assert buffer.read_varint() == 1
    assert buffer.read_string() == "minecraft:overworld"
    assert buffer.read_varint() == 20
    assert buffer.read_varint() == 2
    assert buffer.read_varint() == 2
    assert buffer.read_bool() is False
    assert buffer.read_bool() is True
    assert buffer.read_bool() is False

    assert buffer.read_varint() == 0
    assert buffer.read_string() == "minecraft:overworld"
    assert buffer.read_long() == 0
    assert buffer.read_byte() == 1
    assert buffer.read_byte() == 255
    assert buffer.read_bool() is False
    assert buffer.read_bool() is True
    assert buffer.read_bool() is False
    assert buffer.read_varint() == 0
    assert buffer.read_varint() == 63

    assert buffer.read_bool() is False
    assert buffer.read_bool() is False
    buffer.ensure_consumed()


def test_encode_level_chunks_load_start_game_event():
    packet_type = JAVA_26_2.get_by_name("clientbound.game_event")
    payload = encode_payload(packet_type, {"event": 13, "param": 0.0})

    buffer = Buffer(payload)
    assert buffer.read_varint() == 0x26
    assert buffer.read_unsigned_byte() == 13
    assert buffer.read_float() == 0.0
    buffer.ensure_consumed()


def test_encode_block_changed_ack():
    packet_type = JAVA_26_2.get_by_name("clientbound.block_changed_ack")
    payload = encode_payload(packet_type, {"sequence": 7})

    buffer = Buffer(payload)
    assert buffer.read_varint() == 0x04
    assert buffer.read_varint() == 7
    buffer.ensure_consumed()


def test_encode_block_update():
    packet_type = JAVA_26_2.get_by_name("clientbound.block_update")
    payload = encode_payload(
        packet_type,
        {
            "position": {"x": 1, "y": 64, "z": -2},
            "state": AIR,
        },
    )

    buffer = Buffer(payload)
    assert buffer.read_varint() == 0x08
    assert buffer.read_position() == (1, 64, -2)
    assert buffer.read_varint() == 0
    buffer.ensure_consumed()


def test_encode_forget_level_chunk():
    packet_type = JAVA_26_2.get_by_name("clientbound.forget_level_chunk")
    payload = encode_payload(packet_type, {"x": 1, "z": -2})

    buffer = Buffer(payload)
    assert buffer.read_varint() == 0x25
    assert buffer.read_long() == -8589934591
    buffer.ensure_consumed()


def test_encode_empty_item_stack_for_set_player_inventory():
    packet_type = JAVA_26_2.get_by_name("clientbound.set_player_inventory")
    payload = encode_payload(
        packet_type,
        {"slot": 8, "contents": ItemStack.empty()},
    )

    buffer = Buffer(payload)
    assert buffer.read_varint() == 0x6C
    assert buffer.read_varint() == 8
    assert buffer.read_varint() == 0
    buffer.ensure_consumed()


def test_encode_plain_item_stack_for_set_player_inventory():
    packet_type = JAVA_26_2.get_by_name("clientbound.set_player_inventory")
    payload = encode_payload(
        packet_type,
        {"slot": 1, "contents": ItemStack(item_id=DIRT_ITEM_ID, count=64)},
    )

    buffer = Buffer(payload)
    assert buffer.read_varint() == 0x6C
    assert buffer.read_varint() == 1
    assert buffer.read_varint() == 64
    assert buffer.read_varint() == DIRT_ITEM_ID
    assert buffer.read_varint() == 0
    assert buffer.read_varint() == 0
    buffer.ensure_consumed()


def test_encode_set_held_slot():
    packet_type = JAVA_26_2.get_by_name("clientbound.set_held_slot")
    payload = encode_payload(packet_type, {"slot": 2})

    buffer = Buffer(payload)
    assert buffer.read_varint() == 0x69
    assert buffer.read_varint() == 2
    buffer.ensure_consumed()


def test_decode_play_chunk_batch_received_from_client():
    writer = Writer()
    writer.write_varint(0x0B)
    writer.write_float(12.5)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.chunk_batch_received"
    assert packet.fields["desired_chunks_per_tick"] == 12.5


def test_decode_play_player_input_from_client():
    writer = Writer()
    writer.write_varint(0x2B)
    writer.write_byte(0x51)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.player_input"
    assert packet.fields["flags"] == 0x51
    assert packet.fields["forward"] is True
    assert packet.fields["backward"] is False
    assert packet.fields["left"] is False
    assert packet.fields["right"] is False
    assert packet.fields["jump"] is True
    assert packet.fields["shift"] is False
    assert packet.fields["sprint"] is True


def test_decode_play_player_command_from_client():
    writer = Writer()
    writer.write_varint(0x2A)
    writer.write_varint(1)
    writer.write_varint(1)
    writer.write_varint(0)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.player_command"
    assert packet.fields == {
        "entity_id": 1,
        "action": 1,
        "action_name": "start_sprinting",
        "data": 0,
    }


def test_decode_play_player_action_from_client():
    writer = Writer()
    writer.write_varint(0x29)
    writer.write_varint(0)
    writer.write_position(1, 64, -2)
    writer.write_byte(1)
    writer.write_varint(7)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.player_action"
    assert packet.fields == {
        "action": 0,
        "action_name": "start_destroy_block",
        "position": {"x": 1, "y": 64, "z": -2},
        "direction": 1,
        "direction_name": "up",
        "sequence": 7,
    }


def test_decode_play_interact_with_zero_location_from_client():
    writer = Writer()
    writer.write_varint(0x1A)
    writer.write_varint(42)
    writer.write_varint(0)
    writer.write_byte(0)
    writer.write_bool(True)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.interact"
    assert packet.fields == {
        "entity_id": 42,
        "hand": 0,
        "hand_name": "main_hand",
        "location": {"x": 0.0, "y": 0.0, "z": 0.0},
        "using_secondary_action": True,
    }


def test_decode_play_interact_with_lp_vec3_location_from_client():
    writer = Writer()
    writer.write_varint(0x1A)
    writer.write_varint(42)
    writer.write_varint(1)
    writer.write(bytes.fromhex("f1ff5ffffffa"))
    writer.write_bool(False)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.interact"
    assert packet.fields["entity_id"] == 42
    assert packet.fields["hand"] == 1
    assert packet.fields["hand_name"] == "off_hand"
    assert packet.fields["location"] == {
        "x": pytest.approx(0.5, abs=0.0001),
        "y": pytest.approx(1.0, abs=0.0001),
        "z": pytest.approx(-0.25, abs=0.0001),
    }
    assert packet.fields["using_secondary_action"] is False


def test_decode_play_swing_from_client():
    writer = Writer()
    writer.write_varint(0x3F)
    writer.write_varint(0)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.swing"
    assert packet.fields == {"hand": 0, "hand_name": "main_hand"}


def test_decode_play_ignored_set_game_rule_from_client():
    writer = Writer()
    writer.write_varint(0x39)
    writer.write(bytes.fromhex("01020304"))

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.set_game_rule"
    assert packet.fields == {"ignored_bytes": 4}


def test_decode_play_container_close_from_client():
    writer = Writer()
    writer.write_varint(0x13)
    writer.write_varint(0)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.container_close"
    assert packet.fields == {"container_id": 0}


def test_decode_play_set_carried_item_from_client():
    writer = Writer()
    writer.write_varint(0x35)
    writer.write_short(2)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.set_carried_item"
    assert packet.fields == {"slot": 2}


def test_decode_play_set_creative_mode_slot_empty_stack_from_client():
    writer = Writer()
    writer.write_varint(0x38)
    writer.write_short(36)
    writer.write_varint(0)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.set_creative_mode_slot"
    assert packet.fields["slot_num"] == 36
    stack = packet.fields["item_stack"]
    assert isinstance(stack, ItemStack)
    assert stack.is_empty


def test_decode_play_set_creative_mode_slot_plain_stack_from_client():
    writer = Writer()
    writer.write_varint(0x38)
    writer.write_short(38)
    writer.write_varint(64)
    writer.write_varint(DIRT_ITEM_ID)
    writer.write_varint(0)
    writer.write_varint(0)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.set_creative_mode_slot"
    assert packet.fields["slot_num"] == 38
    stack = packet.fields["item_stack"]
    assert isinstance(stack, ItemStack)
    assert stack.item_id == DIRT_ITEM_ID
    assert stack.count == 64
    assert stack.components_supported is True
    assert stack.component_patch_bytes == b""


def test_decode_play_set_creative_mode_slot_unsupported_components_from_client():
    writer = Writer()
    writer.write_varint(0x38)
    writer.write_short(36)
    writer.write_varint(1)
    writer.write_varint(STONE_ITEM_ID)
    writer.write_varint(1)
    writer.write_varint(99)
    writer.write(bytes.fromhex("010203"))

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.set_creative_mode_slot"
    stack = packet.fields["item_stack"]
    assert isinstance(stack, ItemStack)
    assert stack.item_id == STONE_ITEM_ID
    assert stack.count == 1
    assert stack.components_supported is False
    assert stack.component_patch_bytes == bytes.fromhex("0163010203")


def test_decode_play_use_item_on_from_client():
    writer = Writer()
    writer.write_varint(0x42)
    writer.write_varint(0)
    writer.write_position(1, 64, -2)
    writer.write_varint(1)
    writer.write_float(0.5)
    writer.write_float(1.0)
    writer.write_float(0.25)
    writer.write_bool(False)
    writer.write_bool(True)
    writer.write_varint(7)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.use_item_on"
    assert packet.fields == {
        "hand": 0,
        "hand_name": "main_hand",
        "hit_result": {
            "position": {"x": 1, "y": 64, "z": -2},
            "direction": 1,
            "direction_name": "up",
            "cursor": {"x": 0.5, "y": 1.0, "z": 0.25},
            "inside": False,
            "world_border_hit": True,
        },
        "sequence": 7,
    }


def test_decode_play_use_item_from_client():
    writer = Writer()
    writer.write_varint(0x43)
    writer.write_varint(1)
    writer.write_varint(8)
    writer.write_float(90.0)
    writer.write_float(45.0)

    packet = decode_frame(
        JAVA_26_2,
        PacketState.PLAY,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.use_item"
    assert packet.fields == {
        "hand": 1,
        "hand_name": "off_hand",
        "sequence": 8,
        "y_rot": 90.0,
        "x_rot": 45.0,
    }


def test_decode_configuration_custom_payload():
    writer = Writer()
    writer.write_varint(0x02)
    writer.write_string("minecraft:brand")
    writer.write_string("vanilla")

    packet = decode_frame(
        JAVA_26_2,
        PacketState.CONFIGURATION,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.config_custom_payload"
    assert packet.fields["channel"] == "minecraft:brand"
    assert packet.fields["data"] == b"\x07vanilla"


def test_decode_select_known_packs_payload():
    writer = Writer()
    writer.write_varint(0x07)
    writer.write_varint(1)
    writer.write_string("minecraft")
    writer.write_string("core")
    writer.write_string("26.2")

    packet = decode_frame(
        JAVA_26_2,
        PacketState.CONFIGURATION,
        PacketDirection.SERVERBOUND,
        writer.to_bytes(),
    )

    assert packet.name == "serverbound.select_known_packs"
    assert packet.fields["packs"] == [
        {"namespace": "minecraft", "id": "core", "version": "26.2"}
    ]


def test_encode_status_response_frame():
    packet_type = JAVA_26_2.get_by_name("clientbound.status_response")
    frame = encode_frame(
        PacketContainer(
            packet_type,
            {
                "response": {
                    "version": {"name": "26.2", "protocol": JAVA_26_2.protocol_version},
                    "players": {"max": 20, "online": 0},
                    "description": {"text": "hello"},
                }
            },
        )
    )

    assert frame
    packet = decode_frame(
        JAVA_26_2,
        PacketState.STATUS,
        PacketDirection.CLIENTBOUND,
        frame[1:],
    )
    assert packet.name == "clientbound.status_response"


def test_encode_play_initialization_packets():
    for name, fields in [
        (
            "clientbound.login",
            {
                "entity_id": 1,
                "world_names": ("minecraft:overworld",),
                "max_players": 20,
                "view_distance": 2,
                "simulation_distance": 2,
            },
        ),
        ("clientbound.update_view_position", {"chunk_x": 0, "chunk_z": 0}),
        ("clientbound.spawn_position", {"x": 0, "y": 64, "z": 0}),
        ("clientbound.game_event", {"event": 13, "param": 0.0}),
        ("clientbound.position", {"teleport_id": 1, "x": 0.0, "y": 64.0, "z": 0.0}),
        ("clientbound.map_chunk", {"x": 0, "z": 0}),
    ]:
        packet_type = JAVA_26_2.get_by_name(name)
        assert encode_frame(PacketContainer(packet_type, fields))
