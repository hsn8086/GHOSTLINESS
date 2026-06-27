from __future__ import annotations

from dataclasses import dataclass

from ghostliness.auth import GameProfile
from ghostliness.world import Position


@dataclass(slots=True)
class Player:
    profile: GameProfile
    position: Position
    connection_id: str

    @property
    def name(self) -> str:
        return self.profile.username
