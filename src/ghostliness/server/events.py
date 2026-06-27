from __future__ import annotations

from dataclasses import dataclass

from ghostliness.protocol.containers import PacketContainer
from ghostliness.server.player import Player


@dataclass(slots=True)
class PacketEvent:
    connection_id: str
    packet: PacketContainer


@dataclass(slots=True)
class PlayerJoinEvent:
    player: Player


@dataclass(slots=True)
class PlayerQuitEvent:
    player: Player
    reason: str
