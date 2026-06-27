from __future__ import annotations

import json
import uuid
from typing import Any

from ghostliness.protocol.registry import (
    PacketDirection,
    PacketRegistry,
    PacketState,
    PacketType,
)
from ghostliness.protocol.types import Buffer, Writer
from ghostliness.world_data import (
    OVERWORLD_DIMENSION_ID,
    WORLD_NAMES,
    empty_heightmaps,
    empty_light_masks,
    encode_empty_chunk_data,
)

MINECRAFT_VERSION = "26.2"

# The numeric protocol ID for Minecraft Java 26.2 must be verified when the
# registry is updated from authoritative protocol data. Keeping the value in
# this module prevents version assumptions leaking into server logic.
PROTOCOL_VERSION = 776


def _decode_handshake(buffer: Buffer) -> dict[str, Any]:
    fields = {
        "protocol_version": buffer.read_varint(),
        "server_address": buffer.read_string(255),
        "server_port": buffer.read_unsigned_short(),
        "next_state": buffer.read_varint(),
    }
    buffer.ensure_consumed()
    return fields


def _decode_status_request(buffer: Buffer) -> dict[str, Any]:
    buffer.ensure_consumed()
    return {}


def _decode_ping_request(buffer: Buffer) -> dict[str, Any]:
    fields = {"payload": buffer.read_long()}
    buffer.ensure_consumed()
    return fields


def _decode_login_start(buffer: Buffer) -> dict[str, Any]:
    fields: dict[str, Any] = {"name": buffer.read_string(16)}
    if buffer.remaining == 16:
        fields["uuid"] = buffer.read_uuid()
    elif buffer.remaining >= 1:
        has_uuid = buffer.read_bool()
        fields["uuid"] = buffer.read_uuid() if has_uuid else None
    else:
        fields["uuid"] = None
    buffer.ensure_consumed()
    return fields


def _decode_login_acknowledged(buffer: Buffer) -> dict[str, Any]:
    buffer.ensure_consumed()
    return {}


def _decode_configuration_acknowledged(buffer: Buffer) -> dict[str, Any]:
    buffer.ensure_consumed()
    return {}


def _decode_custom_payload(buffer: Buffer) -> dict[str, Any]:
    fields = {"channel": buffer.read_string(), "data": buffer.read(buffer.remaining)}
    buffer.ensure_consumed()
    return fields


def _decode_select_known_packs(buffer: Buffer) -> dict[str, Any]:
    packs = []
    for _ in range(buffer.read_varint()):
        packs.append(
            {
                "namespace": buffer.read_string(),
                "id": buffer.read_string(),
                "version": buffer.read_string(),
            }
        )
    buffer.ensure_consumed()
    return {"packs": packs}


def _decode_settings(buffer: Buffer) -> dict[str, Any]:
    fields: dict[str, Any] = {"locale": buffer.read_string(16)}
    fields["view_distance"] = buffer.read_byte()
    fields["chat_mode"] = buffer.read_varint()
    fields["chat_colors"] = buffer.read_bool()
    fields["displayed_skin_parts"] = buffer.read_unsigned_byte()
    fields["main_hand"] = buffer.read_varint()
    if buffer.remaining:
        fields["text_filtering_enabled"] = buffer.read_bool()
    if buffer.remaining:
        fields["allow_server_listings"] = buffer.read_bool()
    if buffer.remaining:
        fields["particle_status"] = buffer.read_varint()
    buffer.ensure_consumed()
    return fields


def _decode_empty(buffer: Buffer) -> dict[str, Any]:
    buffer.ensure_consumed()
    return {}


def _decode_keep_alive_response(buffer: Buffer) -> dict[str, Any]:
    fields = {"keep_alive_id": buffer.read_long()}
    buffer.ensure_consumed()
    return fields


def _decode_teleport_confirm(buffer: Buffer) -> dict[str, Any]:
    fields = {"teleport_id": buffer.read_varint()}
    buffer.ensure_consumed()
    return fields


def _decode_position(buffer: Buffer) -> dict[str, Any]:
    fields = {
        "x": buffer.read_double(),
        "y": buffer.read_double(),
        "z": buffer.read_double(),
        "flags": buffer.read_byte(),
    }
    buffer.ensure_consumed()
    return fields


def _decode_position_look(buffer: Buffer) -> dict[str, Any]:
    fields = {
        "x": buffer.read_double(),
        "y": buffer.read_double(),
        "z": buffer.read_double(),
        "yaw": buffer.read_float(),
        "pitch": buffer.read_float(),
        "flags": buffer.read_byte(),
    }
    buffer.ensure_consumed()
    return fields


def _decode_rotation(buffer: Buffer) -> dict[str, Any]:
    fields = {
        "yaw": buffer.read_float(),
        "pitch": buffer.read_float(),
        "flags": buffer.read_unsigned_byte(),
    }
    buffer.ensure_consumed()
    return fields


def _decode_status_only(buffer: Buffer) -> dict[str, Any]:
    fields = {"flags": buffer.read_unsigned_byte()}
    buffer.ensure_consumed()
    return fields


def _decode_chunk_batch_received(buffer: Buffer) -> dict[str, Any]:
    fields = {"desired_chunks_per_tick": buffer.read_float()}
    buffer.ensure_consumed()
    return fields


def _encode_status_response(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_string(json.dumps(fields["response"], separators=(",", ":")))


def _encode_ping_response(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_long(int(fields["payload"]))


def _encode_login_success(writer: Writer, fields: dict[str, Any]) -> None:
    player_uuid = fields["uuid"]
    if not isinstance(player_uuid, uuid.UUID):
        player_uuid = uuid.UUID(str(player_uuid))
    session_id = fields.get("session_id", player_uuid)
    if not isinstance(session_id, uuid.UUID):
        session_id = uuid.UUID(str(session_id))
    writer.write_uuid(player_uuid)
    writer.write_string(str(fields["username"]))
    properties = fields.get("properties", [])
    writer.write_varint(len(properties))
    for item in properties:
        writer.write_string(str(item["name"]))
        writer.write_string(str(item["value"]))
        signature = item.get("signature")
        writer.write_bool(signature is not None)
        if signature is not None:
            writer.write_string(str(signature))
    writer.write_uuid(session_id)


def _encode_set_compression(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_varint(int(fields["threshold"]))


def _encode_finish_configuration(writer: Writer, fields: dict[str, Any]) -> None:
    _ = fields


def _encode_disconnect(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_string(json.dumps(fields["reason"], separators=(",", ":")))


def _encode_keep_alive(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_long(int(fields["keep_alive_id"]))


def _encode_system_chat(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_anonymous_nbt(fields["content"])
    writer.write_bool(bool(fields.get("overlay", False)))


def _encode_game_event(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_unsigned_byte(int(fields["event"]))
    writer.write_float(float(fields.get("param", 0.0)))


def _encode_plugin_message(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_string(str(fields["channel"]))
    writer.write(bytes(fields.get("data", b"")))


def _encode_known_packs(writer: Writer, fields: dict[str, Any]) -> None:
    packs = fields.get("packs", [])
    writer.write_varint(len(packs))
    for pack in packs:
        writer.write_string(str(pack["namespace"]))
        writer.write_string(str(pack["id"]))
        writer.write_string(str(pack["version"]))


def _encode_registry_data(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_string(str(fields["id"]))
    entries = fields.get("entries", [])
    writer.write_varint(len(entries))
    for entry in entries:
        writer.write_string(str(entry["key"]))
        writer.write_optional_anonymous_nbt(entry.get("value"))


def _encode_feature_flags(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_string_array(tuple(str(item) for item in fields.get("features", ())))


def _encode_tags(writer: Writer, fields: dict[str, Any]) -> None:
    tags = fields.get("tags", [])
    writer.write_varint(len(tags))
    for tag_type in tags:
        writer.write_string(str(tag_type["tagType"]))
        values = tag_type.get("tags", [])
        writer.write_varint(len(values))
        for tag in values:
            writer.write_string(str(tag["tagName"]))
            entries = tag.get("entries", [])
            writer.write_varint(len(entries))
            for entry in entries:
                writer.write_varint(int(entry))


def _encode_join_game(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_int(int(fields.get("entity_id", 1)))
    writer.write_bool(bool(fields.get("is_hardcore", False)))
    writer.write_string_array(tuple(fields.get("world_names", WORLD_NAMES)))
    writer.write_varint(int(fields.get("max_players", 20)))
    writer.write_varint(int(fields.get("view_distance", 2)))
    writer.write_varint(int(fields.get("simulation_distance", 2)))
    writer.write_bool(bool(fields.get("reduced_debug_info", False)))
    writer.write_bool(bool(fields.get("enable_respawn_screen", True)))
    writer.write_bool(bool(fields.get("do_limited_crafting", False)))
    _write_spawn_info(writer, fields)
    writer.write_bool(bool(fields.get("online_mode", False)))
    writer.write_bool(bool(fields.get("enforces_secure_chat", False)))


def _encode_update_view_position(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_varint(int(fields.get("chunk_x", 0)))
    writer.write_varint(int(fields.get("chunk_z", 0)))


def _encode_update_view_distance(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_varint(int(fields.get("view_distance", 2)))


def _encode_spawn_position(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_string(str(fields.get("dimension", "minecraft:overworld")))
    writer.write_position(
        int(fields.get("x", 0)),
        int(fields.get("y", 64)),
        int(fields.get("z", 0)),
    )
    writer.write_float(float(fields.get("yaw", 0.0)))
    writer.write_float(float(fields.get("pitch", 0.0)))


def _encode_player_position(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_varint(int(fields.get("teleport_id", 1)))
    writer.write_double(float(fields.get("x", 0.0)))
    writer.write_double(float(fields.get("y", 64.0)))
    writer.write_double(float(fields.get("z", 0.0)))
    writer.write_double(float(fields.get("dx", 0.0)))
    writer.write_double(float(fields.get("dy", 0.0)))
    writer.write_double(float(fields.get("dz", 0.0)))
    writer.write_float(float(fields.get("yaw", 0.0)))
    writer.write_float(float(fields.get("pitch", 0.0)))
    writer.write_int(int(fields.get("flags", 0)))


def _encode_chunk_batch_start(writer: Writer, fields: dict[str, Any]) -> None:
    _ = writer, fields


def _encode_chunk_batch_finished(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_varint(int(fields.get("batch_size", 1)))


def _encode_map_chunk(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_int(int(fields.get("x", 0)))
    writer.write_int(int(fields.get("z", 0)))
    heightmaps = fields.get("heightmaps", empty_heightmaps())
    writer.write_varint(len(heightmaps))
    for heightmap in heightmaps:
        writer.write_varint(int(heightmap["type"]))
        data = heightmap.get("data", [])
        writer.write_varint(len(data))
        for value in data:
            writer.write_long(int(value))
    writer.write_byte_array(bytes(fields.get("chunk_data", encode_empty_chunk_data())))
    writer.write_varint(0)
    lights = empty_light_masks() | dict(fields.get("lights", {}))
    for key in ("skyLightMask", "blockLightMask", "emptySkyLightMask", "emptyBlockLightMask"):
        values = lights[key]
        writer.write_varint(len(values))
        for value in values:
            writer.write_long(int(value))
    for key in ("skyLight", "blockLight"):
        arrays = lights[key]
        writer.write_varint(len(arrays))
        for array in arrays:
            writer.write_byte_array(bytes(array))


def _write_spawn_info(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_varint(int(fields.get("dimension", OVERWORLD_DIMENSION_ID)))
    writer.write_string(str(fields.get("dimension_name", "minecraft:overworld")))
    writer.write_long(int(fields.get("hashed_seed", 0)))
    writer.write_byte(int(fields.get("gamemode", 1)))
    writer.write_unsigned_byte(int(fields.get("previous_gamemode", 255)))
    writer.write_bool(bool(fields.get("is_debug", False)))
    writer.write_bool(bool(fields.get("is_flat", True)))
    writer.write_bool(False)
    writer.write_varint(int(fields.get("portal_cooldown", 0)))
    writer.write_varint(int(fields.get("sea_level", 63)))


def _register(registry: PacketRegistry) -> PacketRegistry:
    register = registry.register
    sb = PacketDirection.SERVERBOUND
    cb = PacketDirection.CLIENTBOUND

    register(
        PacketType(PacketState.HANDSHAKING, sb, 0x00, "serverbound.handshake", _decode_handshake)
    )

    register(
        PacketType(
            PacketState.STATUS,
            sb,
            0x00,
            "serverbound.status_request",
            _decode_status_request,
        )
    )
    register(
        PacketType(PacketState.STATUS, sb, 0x01, "serverbound.ping_request", _decode_ping_request)
    )
    register(
        PacketType(
            PacketState.STATUS,
            cb,
            0x00,
            "clientbound.status_response",
            encoder=_encode_status_response,
        )
    )
    register(
        PacketType(
            PacketState.STATUS,
            cb,
            0x01,
            "clientbound.ping_response",
            encoder=_encode_ping_response,
        )
    )

    register(
        PacketType(PacketState.LOGIN, sb, 0x00, "serverbound.login_start", _decode_login_start)
    )
    register(
        PacketType(
            PacketState.LOGIN,
            sb,
            0x03,
            "serverbound.login_acknowledged",
            _decode_login_acknowledged,
        )
    )
    register(
        PacketType(
            PacketState.LOGIN,
            cb,
            0x02,
            "clientbound.login_success",
            encoder=_encode_login_success,
        )
    )
    register(
        PacketType(
            PacketState.LOGIN,
            cb,
            0x03,
            "clientbound.set_compression",
            encoder=_encode_set_compression,
        )
    )
    register(
        PacketType(
            PacketState.LOGIN,
            cb,
            0x00,
            "clientbound.login_disconnect",
            encoder=_encode_disconnect,
        )
    )

    register(
        PacketType(
            PacketState.CONFIGURATION,
            cb,
            0x01,
            "clientbound.config_plugin_message",
            encoder=_encode_plugin_message,
        )
    )
    register(
        PacketType(
            PacketState.CONFIGURATION,
            cb,
            0x02,
            "clientbound.config_disconnect",
            encoder=_encode_disconnect,
        )
    )
    register(
        PacketType(
            PacketState.CONFIGURATION,
            cb,
            0x03,
            "clientbound.finish_configuration",
            encoder=_encode_finish_configuration,
        )
    )
    register(
        PacketType(
            PacketState.CONFIGURATION,
            cb,
            0x07,
            "clientbound.registry_data",
            encoder=_encode_registry_data,
        )
    )
    register(
        PacketType(
            PacketState.CONFIGURATION,
            cb,
            0x0C,
            "clientbound.feature_flags",
            encoder=_encode_feature_flags,
        )
    )
    register(
        PacketType(
            PacketState.CONFIGURATION,
            cb,
            0x0D,
            "clientbound.tags",
            encoder=_encode_tags,
        )
    )
    register(
        PacketType(
            PacketState.CONFIGURATION,
            cb,
            0x0E,
            "clientbound.select_known_packs",
            encoder=_encode_known_packs,
        )
    )
    register(
        PacketType(
            PacketState.CONFIGURATION,
            sb,
            0x00,
            "serverbound.config_settings",
            _decode_settings,
        )
    )
    register(
        PacketType(
            PacketState.CONFIGURATION,
            sb,
            0x02,
            "serverbound.config_custom_payload",
            _decode_custom_payload,
        )
    )
    register(
        PacketType(
            PacketState.CONFIGURATION,
            sb,
            0x03,
            "serverbound.finish_configuration",
            _decode_configuration_acknowledged,
        )
    )
    register(
        PacketType(
            PacketState.CONFIGURATION,
            sb,
            0x04,
            "serverbound.config_keep_alive",
            _decode_keep_alive_response,
        )
    )
    register(
        PacketType(
            PacketState.CONFIGURATION,
            sb,
            0x07,
            "serverbound.select_known_packs",
            _decode_select_known_packs,
        )
    )

    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x00,
            "serverbound.teleport_confirm",
            _decode_teleport_confirm,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x0B,
            "serverbound.chunk_batch_received",
            _decode_chunk_batch_received,
        )
    )
    register(PacketType(PacketState.PLAY, sb, 0x0D, "serverbound.client_tick_end", _decode_empty))
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x0E,
            "serverbound.play_settings",
            _decode_settings,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x10,
            "serverbound.configuration_acknowledged",
            _decode_configuration_acknowledged,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x1C,
            "serverbound.keep_alive",
            _decode_keep_alive_response,
        )
    )
    register(PacketType(PacketState.PLAY, sb, 0x1E, "serverbound.position", _decode_position))
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x1F,
            "serverbound.position_look",
            _decode_position_look,
        )
    )
    register(PacketType(PacketState.PLAY, sb, 0x20, "serverbound.rotation", _decode_rotation))
    register(PacketType(PacketState.PLAY, sb, 0x21, "serverbound.status_only", _decode_status_only))
    register(PacketType(PacketState.PLAY, sb, 0x2C, "serverbound.player_loaded", _decode_empty))
    register(
        PacketType(
            PacketState.PLAY,
            cb,
            0x0B,
            "clientbound.chunk_batch_finished",
            encoder=_encode_chunk_batch_finished,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            cb,
            0x0C,
            "clientbound.chunk_batch_start",
            encoder=_encode_chunk_batch_start,
        )
    )
    register(
        PacketType(PacketState.PLAY, cb, 0x2C, "clientbound.keep_alive", encoder=_encode_keep_alive)
    )
    register(
        PacketType(PacketState.PLAY, cb, 0x2D, "clientbound.map_chunk", encoder=_encode_map_chunk)
    )
    register(
        PacketType(PacketState.PLAY, cb, 0x26, "clientbound.game_event", encoder=_encode_game_event)
    )
    register(PacketType(PacketState.PLAY, cb, 0x31, "clientbound.login", encoder=_encode_join_game))
    register(
        PacketType(
            PacketState.PLAY,
            cb,
            0x48,
            "clientbound.position",
            encoder=_encode_player_position,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            cb,
            0x5E,
            "clientbound.update_view_position",
            encoder=_encode_update_view_position,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            cb,
            0x5F,
            "clientbound.update_view_distance",
            encoder=_encode_update_view_distance,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            cb,
            0x61,
            "clientbound.spawn_position",
            encoder=_encode_spawn_position,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            cb,
            0x79,
            "clientbound.system_chat",
            encoder=_encode_system_chat,
        )
    )

    return registry


JAVA_26_2 = _register(PacketRegistry(PROTOCOL_VERSION, MINECRAFT_VERSION))
