from ghostliness.protocol.containers import PacketContainer
from ghostliness.protocol.framing import decode_frame, encode_frame, encode_payload
from ghostliness.protocol.registry import PacketDirection, PacketState
from ghostliness.protocol.types import Buffer, Writer, encode_varint
from ghostliness.protocol.versions import JAVA_26_2


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
        "clientbound.chunk_batch_finished": 0x0B,
        "clientbound.chunk_batch_start": 0x0C,
        "clientbound.game_event": 0x26,
        "clientbound.keep_alive": 0x2C,
        "clientbound.map_chunk": 0x2D,
        "clientbound.login": 0x31,
        "clientbound.position": 0x48,
        "clientbound.update_view_position": 0x5E,
        "clientbound.update_view_distance": 0x5F,
        "clientbound.spawn_position": 0x61,
        "clientbound.system_chat": 0x79,
    }

    for packet_name, packet_id in expected_ids.items():
        assert JAVA_26_2.get_by_name(packet_name).packet_id == packet_id


def test_26_2_play_serverbound_packet_ids_match_vanilla_registration_order():
    expected_ids = {
        "serverbound.teleport_confirm": 0x00,
        "serverbound.chunk_batch_received": 0x0B,
        "serverbound.client_tick_end": 0x0D,
        "serverbound.play_settings": 0x0E,
        "serverbound.configuration_acknowledged": 0x10,
        "serverbound.keep_alive": 0x1C,
        "serverbound.position": 0x1E,
        "serverbound.position_look": 0x1F,
        "serverbound.rotation": 0x20,
        "serverbound.status_only": 0x21,
        "serverbound.player_loaded": 0x2C,
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
