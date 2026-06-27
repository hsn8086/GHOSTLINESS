from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ghostliness.protocol.errors import UnknownPacketError
from ghostliness.protocol.types import Buffer, Writer


class PacketState(StrEnum):
    HANDSHAKING = "handshaking"
    STATUS = "status"
    LOGIN = "login"
    CONFIGURATION = "configuration"
    PLAY = "play"


class PacketDirection(StrEnum):
    SERVERBOUND = "serverbound"
    CLIENTBOUND = "clientbound"


PacketDecoder = Callable[[Buffer], dict[str, Any]]
PacketEncoder = Callable[[Writer, dict[str, Any]], None]


@dataclass(frozen=True, slots=True)
class PacketType:
    state: PacketState
    direction: PacketDirection
    packet_id: int
    name: str
    decoder: PacketDecoder | None = None
    encoder: PacketEncoder | None = None


class PacketRegistry:
    def __init__(self, protocol_version: int, minecraft_version: str) -> None:
        self.protocol_version = protocol_version
        self.minecraft_version = minecraft_version
        self._by_key: dict[tuple[PacketState, PacketDirection, int], PacketType] = {}
        self._by_name: dict[str, PacketType] = {}

    def register(self, packet_type: PacketType) -> PacketType:
        key = (packet_type.state, packet_type.direction, packet_type.packet_id)
        if key in self._by_key:
            raise ValueError(f"duplicate packet key: {key}")
        if packet_type.name in self._by_name:
            raise ValueError(f"duplicate packet name: {packet_type.name}")
        self._by_key[key] = packet_type
        self._by_name[packet_type.name] = packet_type
        return packet_type

    def get(
        self,
        state: PacketState,
        direction: PacketDirection,
        packet_id: int,
    ) -> PacketType:
        try:
            return self._by_key[(state, direction, packet_id)]
        except KeyError as exc:
            raise UnknownPacketError(
                f"unknown {direction.value} packet 0x{packet_id:02x} in {state.value}"
            ) from exc

    def get_by_name(self, name: str) -> PacketType:
        try:
            return self._by_name[name]
        except KeyError as exc:
            raise UnknownPacketError(f"unknown packet name: {name}") from exc

    def packets(self) -> Iterable[PacketType]:
        return self._by_key.values()
