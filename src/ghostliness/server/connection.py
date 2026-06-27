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
from ghostliness.protocol.containers import PacketContainer
from ghostliness.protocol.errors import PacketDecodeError, ProtocolError
from ghostliness.protocol.framing import decode_frame, encode_frame, read_frame
from ghostliness.protocol.registry import PacketDirection, PacketState
from ghostliness.server.events import PacketEvent, PlayerJoinEvent, PlayerQuitEvent
from ghostliness.server.player import Player
from ghostliness.world import Position
from ghostliness.world_data import (
    WORLD_NAMES,
    empty_heightmaps,
    empty_light_masks,
    empty_tags,
    encode_empty_chunk_data,
    minimal_registries,
)

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
                logger.info("player loaded id={}", self.connection_id)
            case "serverbound.client_tick_end":
                logger.trace("client tick end id={}", self.connection_id)
            case (
                "serverbound.position"
                | "serverbound.position_look"
                | "serverbound.rotation"
                | "serverbound.status_only"
            ):
                self._update_player_position(packet)
            case "serverbound.configuration_acknowledged":
                await self.server.events.publish(
                    "configuration_acknowledged", PacketEvent(self.connection_id, packet)
                )
            case _:
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
        player = Player(
            profile=self.profile,
            position=Position(),
            connection_id=self.connection_id,
        )
        self.player = player
        self.server.players[self.connection_id] = player
        self.last_keep_alive_sent = time.monotonic()
        logger.info("enter play id={} username={}", self.connection_id, player.name)
        await self._send_initial_play_state()
        await self.send_chat({"text": f"Welcome, {player.name}"})
        await self.server.events.publish("player_join", PlayerJoinEvent(player))
        logger.info("player join published id={} username={}", self.connection_id, player.name)

    async def _send_initial_play_state(self) -> None:
        view_distance = self.server.config.server.view_distance
        spawn = self.server.world.spawn
        logger.info(
            "play init start id={} view_distance={} spawn=({}, {}, {})",
            self.connection_id,
            view_distance,
            spawn.x,
            spawn.y,
            spawn.z,
        )
        await self.send(
            "clientbound.login",
            {
                "entity_id": 1,
                "world_names": WORLD_NAMES,
                "max_players": self.server.config.server.max_players,
                "view_distance": view_distance,
                "simulation_distance": view_distance,
                "gamemode": 1,
                "dimension_name": "minecraft:overworld",
                "online_mode": self.server.config.server.online_mode,
            },
        )
        await self.send("clientbound.update_view_distance", {"view_distance": view_distance})
        await self.send("clientbound.update_view_position", {"chunk_x": 0, "chunk_z": 0})
        await self.send(
            "clientbound.spawn_position",
            {
                "dimension": "minecraft:overworld",
                "x": int(spawn.x),
                "y": int(spawn.y),
                "z": int(spawn.z),
            },
        )
        await self.send(
            "clientbound.game_event",
            {"event": 13, "param": 0.0},
        )
        await self.send("clientbound.chunk_batch_start", {})
        sent_chunks = 0
        for chunk_x in range(-view_distance, view_distance + 1):
            for chunk_z in range(-view_distance, view_distance + 1):
                await self.send(
                    "clientbound.map_chunk",
                    {
                        "x": chunk_x,
                        "z": chunk_z,
                        "heightmaps": empty_heightmaps(),
                        "chunk_data": encode_empty_chunk_data(),
                        "lights": empty_light_masks(),
                    },
                )
                sent_chunks += 1
        logger.info("initial chunks sent id={} count={}", self.connection_id, sent_chunks)
        await self.send("clientbound.chunk_batch_finished", {"batch_size": sent_chunks})
        self.pending_teleport_id = 1
        await self.send(
            "clientbound.position",
            {
                "teleport_id": self.pending_teleport_id,
                "x": spawn.x,
                "y": spawn.y,
                "z": spawn.z,
                "yaw": spawn.yaw,
                "pitch": spawn.pitch,
            },
        )
        logger.info(
            "play init complete id={} teleport_id={}",
            self.connection_id,
            self.pending_teleport_id,
        )

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

    def _update_player_position(self, packet: PacketContainer) -> None:
        if self.player is None:
            return
        if "x" in packet.fields:
            self.player.position.x = float(packet.fields["x"])
        if "y" in packet.fields:
            self.player.position.y = float(packet.fields["y"])
        if "z" in packet.fields:
            self.player.position.z = float(packet.fields["z"])
        if "yaw" in packet.fields:
            self.player.position.yaw = float(packet.fields["yaw"])
        if "pitch" in packet.fields:
            self.player.position.pitch = float(packet.fields["pitch"])
        logger.trace(
            "position update id={} x={} y={} z={} yaw={} pitch={}",
            self.connection_id,
            self.player.position.x,
            self.player.position.y,
            self.player.position.z,
            self.player.position.yaw,
            self.player.position.pitch,
        )

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
            await self.server.events.publish(
                "player_quit",
                PlayerQuitEvent(self.player, "disconnect"),
            )
            self.server.players.pop(self.connection_id, None)
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
