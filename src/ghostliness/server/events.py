from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ghostliness.protocol.containers import PacketContainer
from ghostliness.server.player import Player

if TYPE_CHECKING:
    from ghostliness.server.runtime import PlayerSession


@dataclass(slots=True)
class PacketEvent:
    connection_id: str
    packet: PacketContainer


@dataclass(slots=True)
class PlayerJoinEvent:
    player: Player
    session: PlayerSession | None = None


@dataclass(slots=True)
class PlayerQuitEvent:
    player: Player
    reason: str
    session: PlayerSession | None = None
