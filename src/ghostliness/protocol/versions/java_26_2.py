from __future__ import annotations

import json
import uuid
from typing import Any

from ghostliness.items import AIR_ITEM_ID, ITEM_NAMES_BY_ID, ItemStack
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
    block_state_to_protocol_id,
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


def _decode_ignored_payload(buffer: Buffer) -> dict[str, Any]:
    payload = buffer.read(buffer.remaining)
    return {"ignored_bytes": len(payload)}


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


def _decode_player_input(buffer: Buffer) -> dict[str, Any]:
    flags = buffer.read_byte()
    fields = {
        "flags": flags,
        "forward": bool(flags & 0x01),
        "backward": bool(flags & 0x02),
        "left": bool(flags & 0x04),
        "right": bool(flags & 0x08),
        "jump": bool(flags & 0x10),
        "shift": bool(flags & 0x20),
        "sprint": bool(flags & 0x40),
    }
    buffer.ensure_consumed()
    return fields


_PLAYER_COMMAND_ACTIONS = (
    "stop_sleeping",
    "start_sprinting",
    "stop_sprinting",
    "start_riding_jump",
    "stop_riding_jump",
    "open_inventory",
    "start_fall_flying",
)


def _decode_player_command(buffer: Buffer) -> dict[str, Any]:
    entity_id = buffer.read_varint()
    action = buffer.read_varint()
    fields = {
        "entity_id": entity_id,
        "action": action,
        "action_name": _enum_name(_PLAYER_COMMAND_ACTIONS, action),
        "data": buffer.read_varint(),
    }
    buffer.ensure_consumed()
    return fields


_PLAYER_ACTIONS = (
    "start_destroy_block",
    "abort_destroy_block",
    "stop_destroy_block",
    "drop_all_items",
    "drop_item",
    "release_use_item",
    "swap_item_with_offhand",
    "stab",
)

_DIRECTIONS = ("down", "up", "north", "south", "west", "east")


def _decode_player_action(buffer: Buffer) -> dict[str, Any]:
    action = buffer.read_varint()
    x, y, z = buffer.read_position()
    direction = buffer.read_unsigned_byte()
    fields = {
        "action": action,
        "action_name": _enum_name(_PLAYER_ACTIONS, action),
        "position": {"x": x, "y": y, "z": z},
        "direction": direction,
        "direction_name": _enum_name(_DIRECTIONS, direction),
        "sequence": buffer.read_varint(),
    }
    buffer.ensure_consumed()
    return fields


_INTERACTION_HANDS = ("main_hand", "off_hand")


def _decode_set_carried_item(buffer: Buffer) -> dict[str, Any]:
    fields = {"slot": buffer.read_short()}
    buffer.ensure_consumed()
    return fields


def _decode_set_creative_mode_slot(buffer: Buffer) -> dict[str, Any]:
    fields = {
        "slot_num": buffer.read_short(),
        "item_stack": _decode_item_stack(buffer),
    }
    buffer.ensure_consumed()
    return fields


def _decode_container_close(buffer: Buffer) -> dict[str, Any]:
    fields = {"container_id": buffer.read_varint()}
    buffer.ensure_consumed()
    return fields


def _decode_use_item_on(buffer: Buffer) -> dict[str, Any]:
    hand = buffer.read_varint()
    fields = {
        "hand": hand,
        "hand_name": _enum_name(_INTERACTION_HANDS, hand),
        "hit_result": _decode_block_hit_result(buffer),
        "sequence": buffer.read_varint(),
    }
    buffer.ensure_consumed()
    return fields


def _decode_use_item(buffer: Buffer) -> dict[str, Any]:
    hand = buffer.read_varint()
    fields = {
        "hand": hand,
        "hand_name": _enum_name(_INTERACTION_HANDS, hand),
        "sequence": buffer.read_varint(),
        "y_rot": buffer.read_float(),
        "x_rot": buffer.read_float(),
    }
    buffer.ensure_consumed()
    return fields


def _decode_item_stack(buffer: Buffer) -> ItemStack:
    count = buffer.read_varint()
    if count <= 0:
        return ItemStack.empty()

    item_id = buffer.read_varint()
    component_patch_start = buffer.pos
    added_count = buffer.read_varint()
    if added_count != 0:
        component_patch = buffer.data[component_patch_start:]
        buffer.read(buffer.remaining)
        return ItemStack(
            item_id=item_id,
            count=count,
            components_supported=False,
            component_patch_bytes=component_patch,
        )

    removed_count = buffer.read_varint()
    if removed_count != 0:
        component_patch = buffer.data[component_patch_start:]
        buffer.read(buffer.remaining)
        return ItemStack(
            item_id=item_id,
            count=count,
            components_supported=False,
            component_patch_bytes=component_patch,
        )

    return ItemStack(item_id=item_id, count=count)


def _encode_item_stack(writer: Writer, stack: ItemStack) -> None:
    if stack.is_empty:
        writer.write_varint(0)
        return
    if stack.item_id == AIR_ITEM_ID or stack.item_id not in ITEM_NAMES_BY_ID:
        raise ValueError(f"cannot encode unsupported item id: {stack.item_id}")
    if not stack.components_supported or stack.component_patch_bytes:
        raise ValueError(f"cannot encode item stack with unsupported components: {stack.item_id}")
    writer.write_varint(int(stack.count))
    writer.write_varint(int(stack.item_id))
    writer.write_varint(0)
    writer.write_varint(0)


def _decode_block_hit_result(buffer: Buffer) -> dict[str, Any]:
    x, y, z = buffer.read_position()
    direction = buffer.read_varint()
    return {
        "position": {"x": x, "y": y, "z": z},
        "direction": direction,
        "direction_name": _enum_name(_DIRECTIONS, direction),
        "cursor": {
            "x": buffer.read_float(),
            "y": buffer.read_float(),
            "z": buffer.read_float(),
        },
        "inside": buffer.read_bool(),
        "world_border_hit": buffer.read_bool(),
    }


def _decode_interact(buffer: Buffer) -> dict[str, Any]:
    entity_id = buffer.read_varint()
    hand = buffer.read_varint()
    fields = {
        "entity_id": entity_id,
        "hand": hand,
        "hand_name": _enum_name(_INTERACTION_HANDS, hand),
        "location": _decode_lp_vec3(buffer),
        "using_secondary_action": buffer.read_bool(),
    }
    buffer.ensure_consumed()
    return fields


def _decode_swing(buffer: Buffer) -> dict[str, Any]:
    hand = buffer.read_varint()
    fields = {"hand": hand, "hand_name": _enum_name(_INTERACTION_HANDS, hand)}
    buffer.ensure_consumed()
    return fields


def _decode_lp_vec3(buffer: Buffer) -> dict[str, float]:
    first = buffer.read_unsigned_byte()
    if first == 0:
        return {"x": 0.0, "y": 0.0, "z": 0.0}

    second = buffer.read_unsigned_byte()
    high = int.from_bytes(buffer.read(4), "big", signed=False)
    packed = (high << 16) | (second << 8) | first

    scale = first & 0x03
    if first & 0x04:
        scale |= buffer.read_varint() << 2

    return {
        "x": _unpack_lp_vec3_component(packed >> 3) * scale,
        "y": _unpack_lp_vec3_component(packed >> 18) * scale,
        "z": _unpack_lp_vec3_component(packed >> 33) * scale,
    }


def _unpack_lp_vec3_component(value: int) -> float:
    quantized = min(value & 0x7FFF, 32766)
    return quantized * 2.0 / 32766.0 - 1.0


def _enum_name(names: tuple[str, ...], value: int) -> str | None:
    if 0 <= value < len(names):
        return names[value]
    return None


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


def _encode_block_changed_ack(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_varint(int(fields["sequence"]))


def _encode_block_update(writer: Writer, fields: dict[str, Any]) -> None:
    position = fields["position"]
    if not isinstance(position, dict):
        raise TypeError("block update position must be a dict")
    writer.write_position(int(position["x"]), int(position["y"]), int(position["z"]))
    writer.write_varint(block_state_to_protocol_id(fields["state"]))


def _encode_forget_level_chunk(writer: Writer, fields: dict[str, Any]) -> None:
    chunk_x = int(fields["x"])
    chunk_z = int(fields["z"])
    packed = ((chunk_z & 0xFFFFFFFF) << 32) | (chunk_x & 0xFFFFFFFF)
    if packed >= 1 << 63:
        packed -= 1 << 64
    writer.write_long(packed)


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


def _encode_set_held_slot(writer: Writer, fields: dict[str, Any]) -> None:
    writer.write_varint(int(fields["slot"]))


def _encode_set_player_inventory(writer: Writer, fields: dict[str, Any]) -> None:
    stack = fields["contents"]
    if not isinstance(stack, ItemStack):
        raise TypeError("set player inventory contents must be an ItemStack")
    writer.write_varint(int(fields["slot"]))
    _encode_item_stack(writer, stack)


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
            0x01,
            "serverbound.attack",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x02,
            "serverbound.block_entity_tag_query",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x03,
            "serverbound.select_bundle_item",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x04,
            "serverbound.change_difficulty",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x05,
            "serverbound.change_game_mode",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(PacketState.PLAY, sb, 0x06, "serverbound.chat_ack", _decode_ignored_payload)
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x07,
            "serverbound.chat_command",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x08,
            "serverbound.chat_command_signed",
            _decode_ignored_payload,
        )
    )
    register(PacketType(PacketState.PLAY, sb, 0x09, "serverbound.chat", _decode_ignored_payload))
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x0A,
            "serverbound.chat_session_update",
            _decode_ignored_payload,
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
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x0C,
            "serverbound.client_command",
            _decode_ignored_payload,
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
            0x0F,
            "serverbound.command_suggestion",
            _decode_ignored_payload,
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
            0x11,
            "serverbound.container_button_click",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x12,
            "serverbound.container_click",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x13,
            "serverbound.container_close",
            _decode_container_close,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x14,
            "serverbound.container_slot_state_changed",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x15,
            "serverbound.cookie_response",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x16,
            "serverbound.play_custom_payload",
            _decode_custom_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x17,
            "serverbound.debug_subscription_request",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(PacketState.PLAY, sb, 0x18, "serverbound.edit_book", _decode_ignored_payload)
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x19,
            "serverbound.entity_tag_query",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(PacketState.PLAY, sb, 0x1A, "serverbound.interact", _decode_interact)
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x1B,
            "serverbound.jigsaw_generate",
            _decode_ignored_payload,
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
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x1D,
            "serverbound.lock_difficulty",
            _decode_ignored_payload,
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
    register(
        PacketType(PacketState.PLAY, sb, 0x22, "serverbound.move_vehicle", _decode_ignored_payload)
    )
    register(
        PacketType(PacketState.PLAY, sb, 0x23, "serverbound.paddle_boat", _decode_ignored_payload)
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x24,
            "serverbound.pick_item_from_block",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x25,
            "serverbound.pick_item_from_entity",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x26,
            "serverbound.play_ping_request",
            _decode_ping_request,
        )
    )
    register(
        PacketType(PacketState.PLAY, sb, 0x27, "serverbound.place_recipe", _decode_ignored_payload)
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x28,
            "serverbound.player_abilities",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(PacketState.PLAY, sb, 0x29, "serverbound.player_action", _decode_player_action)
    )
    register(
        PacketType(PacketState.PLAY, sb, 0x2A, "serverbound.player_command", _decode_player_command)
    )
    register(
        PacketType(PacketState.PLAY, sb, 0x2B, "serverbound.player_input", _decode_player_input)
    )
    register(PacketType(PacketState.PLAY, sb, 0x2C, "serverbound.player_loaded", _decode_empty))
    register(
        PacketType(PacketState.PLAY, sb, 0x2D, "serverbound.pong", _decode_ignored_payload)
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x2E,
            "serverbound.recipe_book_change_settings",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x2F,
            "serverbound.recipe_book_seen_recipe",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(PacketState.PLAY, sb, 0x30, "serverbound.rename_item", _decode_ignored_payload)
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x31,
            "serverbound.resource_pack",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x32,
            "serverbound.seen_advancements",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x33,
            "serverbound.select_trade",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(PacketState.PLAY, sb, 0x34, "serverbound.set_beacon", _decode_ignored_payload)
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x35,
            "serverbound.set_carried_item",
            _decode_set_carried_item,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x36,
            "serverbound.set_command_block",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x37,
            "serverbound.set_command_minecart",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x38,
            "serverbound.set_creative_mode_slot",
            _decode_set_creative_mode_slot,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x39,
            "serverbound.set_game_rule",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x3A,
            "serverbound.set_jigsaw_block",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x3B,
            "serverbound.set_structure_block",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x3C,
            "serverbound.set_test_block",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x3D,
            "serverbound.sign_update",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x3E,
            "serverbound.spectator_action",
            _decode_ignored_payload,
        )
    )
    register(PacketType(PacketState.PLAY, sb, 0x3F, "serverbound.swing", _decode_swing))
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x40,
            "serverbound.teleport_to_entity",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x41,
            "serverbound.test_instance_block_action",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(PacketState.PLAY, sb, 0x42, "serverbound.use_item_on", _decode_use_item_on)
    )
    register(PacketType(PacketState.PLAY, sb, 0x43, "serverbound.use_item", _decode_use_item))
    register(
        PacketType(
            PacketState.PLAY,
            sb,
            0x44,
            "serverbound.custom_click_action",
            _decode_ignored_payload,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            cb,
            0x04,
            "clientbound.block_changed_ack",
            encoder=_encode_block_changed_ack,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            cb,
            0x08,
            "clientbound.block_update",
            encoder=_encode_block_update,
        )
    )
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
        PacketType(
            PacketState.PLAY,
            cb,
            0x25,
            "clientbound.forget_level_chunk",
            encoder=_encode_forget_level_chunk,
        )
    )
    register(
        PacketType(PacketState.PLAY, cb, 0x26, "clientbound.game_event", encoder=_encode_game_event)
    )
    register(
        PacketType(PacketState.PLAY, cb, 0x2C, "clientbound.keep_alive", encoder=_encode_keep_alive)
    )
    register(
        PacketType(PacketState.PLAY, cb, 0x2D, "clientbound.map_chunk", encoder=_encode_map_chunk)
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
            0x69,
            "clientbound.set_held_slot",
            encoder=_encode_set_held_slot,
        )
    )
    register(
        PacketType(
            PacketState.PLAY,
            cb,
            0x6C,
            "clientbound.set_player_inventory",
            encoder=_encode_set_player_inventory,
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
