from __future__ import annotations

import asyncio
import contextlib
import itertools
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger

from ghostliness.auth import GameProfile
from ghostliness.items import ItemStack, hotbar_index_from_creative_slot
from ghostliness.protocol.containers import PacketContainer
from ghostliness.protocol.errors import PacketDecodeError, ProtocolError
from ghostliness.protocol.framing import decode_frame, encode_frame, read_frame
from ghostliness.protocol.registry import PacketDirection, PacketState
from ghostliness.server.events import PacketEvent
from ghostliness.server.player import Player
from ghostliness.world_data import empty_tags, minimal_registries

if TYPE_CHECKING:
    from ghostliness.server.core import GhostlinessServer


_CONNECTION_IDS = itertools.count(1)


@dataclass(slots=True)
class Connection:
    server: GhostlinessServer
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    state: PacketState = PacketState.HANDSHAKING
    compression_threshold: int = -1
    profile: GameProfile | None = None
    player: Player | None = None
    connection_id: str = ""
    pending_teleport_id: int = 0
    pending_keep_alive_id: int | None = None
    last_keep_alive_sent: float = 0.0

    def __post_init__(self) -> None:
        peer = self.writer.get_extra_info("peername")
        self.connection_id = f"{next(_CONNECTION_IDS)}:{peer!r}"

    async def run(self) -> None:
        logger.info("connection opened id={} state={}", self.connection_id, self.state.value)
        try:
            while not self.reader.at_eof():
                frame = await read_frame(self.reader)
                packet = decode_frame(
                    self.server.registry,
                    self.state,
                    PacketDirection.SERVERBOUND,
                    frame,
                    self.compression_threshold,
                )
                logger.debug(
                    "packet recv id={} state={} name={} fields={}",
                    self.connection_id,
                    self.state.value,
                    packet.name,
                    _loggable_fields(packet.fields),
                )
                await self.server.events.publish(
                    "packet_receive", PacketEvent(self.connection_id, packet)
                )
                packet = await self.server.protocol.notify(packet, PacketDirection.SERVERBOUND)
                if packet.cancelled:
                    logger.debug(
                        "packet cancelled id={} direction=serverbound name={}",
                        self.connection_id,
                        packet.name,
                    )
                    continue
                await self._dispatch(packet)
        except (asyncio.IncompleteReadError, ConnectionResetError):
            logger.info("connection closed by client id={}", self.connection_id)
        except (PacketDecodeError, ProtocolError) as exc:
            logger.exception("protocol error id={} error={}", self.connection_id, exc)
            await self.disconnect({"text": str(exc)})
        except Exception as exc:
            logger.exception("unexpected connection error id={} error={}", self.connection_id, exc)
            await self.disconnect({"text": "Internal server error"})
        finally:
            await self.close()

    async def _dispatch(self, packet: PacketContainer) -> None:
        match packet.name:
            case "serverbound.handshake":
                await self._handle_handshake(packet)
            case "serverbound.status_request":
                await self._handle_status_request()
            case "serverbound.ping_request":
                await self.send("clientbound.ping_response", {"payload": packet.fields["payload"]})
                await self.close()
            case "serverbound.login_start":
                await self._handle_login_start(packet)
            case "serverbound.login_acknowledged":
                self.state = PacketState.CONFIGURATION
                logger.info("login acknowledged id={} -> configuration", self.connection_id)
                await self._start_configuration()
            case "serverbound.finish_configuration":
                logger.info("configuration acknowledged id={} -> play", self.connection_id)
                await self.enter_play()
            case "serverbound.config_settings" | "serverbound.play_settings":
                await self.server.events.publish(
                    "client_settings", PacketEvent(self.connection_id, packet)
                )
            case "serverbound.config_custom_payload":
                logger.debug(
                    "configuration custom payload id={} channel={} bytes={}",
                    self.connection_id,
                    packet.fields.get("channel"),
                    len(packet.fields.get("data", b"")),
                )
            case "serverbound.config_keep_alive":
                await self._handle_keep_alive_response(packet)
            case "serverbound.select_known_packs":
                logger.info(
                    "known packs selected id={} count={}",
                    self.connection_id,
                    len(packet.fields.get("packs", [])),
                )
                await self.server.events.publish(
                    "select_known_packs", PacketEvent(self.connection_id, packet)
                )
            case "serverbound.keep_alive":
                await self._handle_keep_alive_response(packet)
            case "serverbound.teleport_confirm":
                if packet.fields.get("teleport_id") == self.pending_teleport_id:
                    logger.info(
                        "teleport confirmed id={} teleport_id={}",
                        self.connection_id,
                        packet.fields.get("teleport_id"),
                    )
                    self.pending_teleport_id = 0
                else:
                    logger.warning(
                        "unexpected teleport confirm id={} received={} pending={}",
                        self.connection_id,
                        packet.fields.get("teleport_id"),
                        self.pending_teleport_id,
                    )
            case "serverbound.chunk_batch_received":
                logger.debug(
                    "chunk batch received id={} desired_chunks_per_tick={}",
                    self.connection_id,
                    packet.fields.get("desired_chunks_per_tick"),
                )
            case "serverbound.player_loaded":
                self.server.runtime.mark_player_loaded(self.connection_id)
            case "serverbound.set_carried_item":
                self._handle_set_carried_item(packet)
            case "serverbound.set_creative_mode_slot":
                self._handle_set_creative_mode_slot(packet)
            case "serverbound.container_close":
                logger.debug(
                    "container close id={} container_id={}",
                    self.connection_id,
                    packet.fields.get("container_id"),
                )
            case "serverbound.client_tick_end":
                logger.trace("client tick end id={}", self.connection_id)
            case (
                "serverbound.position"
                | "serverbound.position_look"
                | "serverbound.rotation"
                | "serverbound.status_only"
            ):
                await self._update_player_position(packet)
            case "serverbound.player_action":
                logger.debug(
                    "player action id={} action={} action_name={} position={} "
                    "direction={} direction_name={} sequence={}",
                    self.connection_id,
                    packet.fields.get("action"),
                    packet.fields.get("action_name"),
                    packet.fields.get("position"),
                    packet.fields.get("direction"),
                    packet.fields.get("direction_name"),
                    packet.fields.get("sequence"),
                )
                await self.server.runtime.handle_player_action(
                    self.connection_id,
                    str(packet.fields["action_name"])
                    if packet.fields.get("action_name") is not None
                    else None,
                    packet.fields["position"],
                    int(packet.fields["sequence"]),
                )
            case "serverbound.player_command":
                logger.debug(
                    "player command id={} entity_id={} action={} action_name={} data={}",
                    self.connection_id,
                    packet.fields.get("entity_id"),
                    packet.fields.get("action"),
                    packet.fields.get("action_name"),
                    packet.fields.get("data"),
                )
                self.server.runtime.handle_player_command(
                    self.connection_id,
                    str(packet.fields["action_name"])
                    if packet.fields.get("action_name") is not None
                    else None,
                )
            case "serverbound.player_input":
                logger.trace(
                    "player input id={} flags={} forward={} backward={} "
                    "left={} right={} jump={} shift={} sprint={}",
                    self.connection_id,
                    packet.fields.get("flags"),
                    packet.fields.get("forward"),
                    packet.fields.get("backward"),
                    packet.fields.get("left"),
                    packet.fields.get("right"),
                    packet.fields.get("jump"),
                    packet.fields.get("shift"),
                    packet.fields.get("sprint"),
                )
                self.server.runtime.handle_player_input(self.connection_id, packet.fields)
            case "serverbound.interact":
                logger.debug(
                    "interact id={} entity_id={} hand={} hand_name={} location={} "
                    "using_secondary_action={}",
                    self.connection_id,
                    packet.fields.get("entity_id"),
                    packet.fields.get("hand"),
                    packet.fields.get("hand_name"),
                    packet.fields.get("location"),
                    packet.fields.get("using_secondary_action"),
                )
            case "serverbound.swing":
                logger.debug(
                    "swing id={} hand={} hand_name={}",
                    self.connection_id,
                    packet.fields.get("hand"),
                    packet.fields.get("hand_name"),
                )
            case "serverbound.use_item_on":
                logger.debug(
                    "use item on id={} hand={} hand_name={} hit_result={} sequence={}",
                    self.connection_id,
                    packet.fields.get("hand"),
                    packet.fields.get("hand_name"),
                    packet.fields.get("hit_result"),
                    packet.fields.get("sequence"),
                )
                await self.server.runtime.handle_use_item_on(
                    self.connection_id,
                    int(packet.fields["hand"]),
                    packet.fields["hit_result"],
                    int(packet.fields["sequence"]),
                )
            case "serverbound.use_item":
                logger.debug(
                    "use item id={} hand={} hand_name={} sequence={} y_rot={} x_rot={}",
                    self.connection_id,
                    packet.fields.get("hand"),
                    packet.fields.get("hand_name"),
                    packet.fields.get("sequence"),
                    packet.fields.get("y_rot"),
                    packet.fields.get("x_rot"),
                )
                await self.send(
                    "clientbound.block_changed_ack",
                    {"sequence": int(packet.fields["sequence"])},
                )
            case "serverbound.configuration_acknowledged":
                await self.server.events.publish(
                    "configuration_acknowledged", PacketEvent(self.connection_id, packet)
                )
            case _:
                ignored_bytes = packet.fields.get("ignored_bytes")
                if isinstance(ignored_bytes, int):
                    logger.debug(
                        "ignored packet id={} state={} name={} payload_bytes={} payload_hex={}",
                        self.connection_id,
                        self.state.value,
                        packet.name,
                        ignored_bytes,
                        _payload_hex(packet.raw_payload),
                    )
                    return
                logger.debug(
                    "unhandled packet id={} state={} name={}",
                    self.connection_id,
                    self.state.value,
                    packet.name,
                )

    async def _handle_handshake(self, packet: PacketContainer) -> None:
        next_state = int(packet.fields["next_state"])
        if next_state == 1:
            self.state = PacketState.STATUS
        elif next_state == 2:
            self.state = PacketState.LOGIN
        else:
            raise ProtocolError(f"unsupported next state: {next_state}")
        logger.info(
            "handshake id={} protocol={} address={} port={} next_state={}",
            self.connection_id,
            packet.fields.get("protocol_version"),
            packet.fields.get("server_address"),
            packet.fields.get("server_port"),
            self.state.value,
        )

    async def _handle_status_request(self) -> None:
        response = {
            "version": {
                "name": self.server.registry.minecraft_version,
                "protocol": self.server.registry.protocol_version,
            },
            "players": {
                "max": self.server.config.server.max_players,
                "online": len(self.server.players),
                "sample": [
                    {"name": player.name, "id": str(player.profile.uuid)}
                    for player in self.server.players.values()
                ][:12],
            },
            "description": {"text": self.server.config.server.motd},
            "enforcesSecureChat": False,
        }
        await self.send("clientbound.status_response", {"response": response})
        logger.info("status response sent id={}", self.connection_id)

    async def _handle_login_start(self, packet: PacketContainer) -> None:
        username = str(packet.fields["name"])
        client_uuid = packet.fields.get("uuid")
        profile = await self.server.authenticator.authenticate(username, client_uuid)
        self.profile = profile
        logger.info(
            "login start id={} username={} uuid={} online={}",
            self.connection_id,
            profile.username,
            profile.uuid,
            profile.online,
        )
        if self.server.config.network.compression_threshold >= 0:
            self.compression_threshold = self.server.config.network.compression_threshold
            await self.send(
                "clientbound.set_compression",
                {"threshold": self.server.config.network.compression_threshold},
                compression_threshold=-1,
            )
        await self.send(
            "clientbound.login_success",
            {
                "uuid": profile.uuid,
                "username": profile.username,
                "properties": profile.properties,
                "session_id": profile.uuid,
            },
        )
        logger.info("login success sent id={} username={}", self.connection_id, profile.username)

    async def _start_configuration(self) -> None:
        logger.info("configuration start id={}", self.connection_id)
        for registry in minimal_registries():
            await self.send("clientbound.registry_data", registry)
            entries = registry.get("entries", [])
            logger.debug(
                "registry sent id={} registry={} entries={}",
                self.connection_id,
                registry.get("id"),
                len(entries) if isinstance(entries, list) else 0,
            )
        await self.send("clientbound.feature_flags", {"features": ["minecraft:vanilla"]})
        await self.send("clientbound.tags", {"tags": empty_tags()})
        await self.send("clientbound.select_known_packs", {"packs": []})
        await self.send("clientbound.finish_configuration", {})
        logger.info("configuration finish sent id={}", self.connection_id)

    async def enter_play(self) -> None:
        if self.profile is None:
            raise ProtocolError("cannot enter play without a profile")
        self.state = PacketState.PLAY
        await self.server.runtime.enter_play(self, self.profile)

    async def send_chat(self, content: dict[str, object]) -> None:
        await self.send("clientbound.system_chat", {"content": content, "overlay": False})

    async def send_keep_alive(self) -> None:
        keep_alive_id = int(time.time_ns() // 1_000_000)
        self.pending_keep_alive_id = keep_alive_id
        self.last_keep_alive_sent = time.monotonic()
        await self.send(
            "clientbound.keep_alive",
            {"keep_alive_id": keep_alive_id},
        )
        logger.debug("keepalive sent id={} keep_alive_id={}", self.connection_id, keep_alive_id)

    def _handle_set_carried_item(self, packet: PacketContainer) -> None:
        if self.player is None:
            logger.debug(
                "set carried item before player attached id={} slot={}",
                self.connection_id,
                packet.fields.get("slot"),
            )
            return
        slot = int(packet.fields["slot"])
        if not self.player.inventory.set_selected_slot(slot):
            logger.warning("invalid carried item slot id={} slot={}", self.connection_id, slot)
            return
        stack = self.player.inventory.selected_stack()
        logger.debug(
            "carried item selected id={} slot={} item={} count={} supported={}",
            self.connection_id,
            slot,
            stack.item_name,
            stack.count,
            stack.components_supported,
        )

    def _handle_set_creative_mode_slot(self, packet: PacketContainer) -> None:
        if self.player is None:
            logger.debug(
                "creative slot before player attached id={} slot_num={}",
                self.connection_id,
                packet.fields.get("slot_num"),
            )
            return

        slot_num = int(packet.fields["slot_num"])
        stack = packet.fields["item_stack"]
        if not isinstance(stack, ItemStack):
            logger.warning(
                "creative slot packet without decoded item stack id={} slot_num={}",
                self.connection_id,
                slot_num,
            )
            return

        hotbar_slot = hotbar_index_from_creative_slot(slot_num)
        if hotbar_slot is None:
            logger.trace(
                "creative slot ignored id={} slot_num={} item={} count={}",
                self.connection_id,
                slot_num,
                stack.item_name,
                stack.count,
            )
            return

        self.player.inventory.set_hotbar_slot(hotbar_slot, stack)
        logger.debug(
            "creative hotbar slot set id={} slot_num={} hotbar_slot={} item={} count={} "
            "supported={} component_bytes={}",
            self.connection_id,
            slot_num,
            hotbar_slot,
            stack.item_name,
            stack.count,
            stack.components_supported,
            len(stack.component_patch_bytes),
        )

    async def _handle_keep_alive_response(self, packet: PacketContainer) -> None:
        keep_alive_id = int(packet.fields["keep_alive_id"])
        if self.pending_keep_alive_id == keep_alive_id:
            self.pending_keep_alive_id = None
            logger.debug("keepalive ack id={} keep_alive_id={}", self.connection_id, keep_alive_id)
        else:
            logger.warning(
                "unexpected keepalive id={} received={} pending={}",
                self.connection_id,
                keep_alive_id,
                self.pending_keep_alive_id,
            )
        await self.server.events.publish(
            "keep_alive_response",
            PacketEvent(self.connection_id, packet),
        )

    async def _update_player_position(self, packet: PacketContainer) -> None:
        await self.server.runtime.handle_player_movement(self.connection_id, packet.fields)

    async def send(
        self,
        packet_name: str,
        fields: dict[str, object],
        *,
        compression_threshold: int | None = None,
    ) -> None:
        packet_type = self.server.registry.get_by_name(packet_name)
        packet = PacketContainer(packet_type, fields)
        packet = await self.server.protocol.notify(packet, PacketDirection.CLIENTBOUND)
        if packet.cancelled:
            logger.debug(
                "packet cancelled id={} direction=clientbound name={}",
                self.connection_id,
                packet.name,
            )
            return
        await self.server.events.publish("packet_send", PacketEvent(self.connection_id, packet))
        threshold = (
            self.compression_threshold
            if compression_threshold is None
            else compression_threshold
        )
        self.writer.write(encode_frame(packet, threshold))
        await self.writer.drain()
        logger.debug(
            "packet send id={} state={} name={} fields={}",
            self.connection_id,
            packet.packet_type.state.value,
            packet.name,
            _loggable_fields(packet.fields),
        )

    async def disconnect(self, reason: dict[str, object]) -> None:
        packet_name = "clientbound.login_disconnect" if self.state == PacketState.LOGIN else None
        if packet_name is not None:
            await self.send(packet_name, {"reason": reason})
        logger.info("disconnect id={} reason={}", self.connection_id, reason)
        await self.close()

    async def close(self) -> None:
        if self.player is not None:
            await self.server.runtime.remove_player(self.connection_id, "disconnect")
            self.player = None
        self.writer.close()
        with contextlib.suppress(ConnectionError):
            await self.writer.wait_closed()
        logger.info("connection closed id={}", self.connection_id)


def _loggable_fields(fields: Mapping[str, object]) -> dict[str, object]:
    return {key: _loggable_value(value) for key, value in fields.items()}


def _loggable_value(value: object) -> object:
    if isinstance(value, bytes | bytearray):
        return f"<{len(value)} bytes>"
    if isinstance(value, dict):
        return {str(key): _loggable_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        items = [_loggable_value(item) for item in value[:8]]
        if len(value) > 8:
            items.append(f"<{len(value) - 8} more items>")
        return items
    return value


def _payload_hex(payload: bytes, limit: int = 64) -> str:
    if len(payload) <= limit:
        return payload.hex()
    return f"{payload[:limit].hex()}...(+{len(payload) - limit} bytes)"
