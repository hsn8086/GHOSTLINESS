from __future__ import annotations

from dataclasses import dataclass, field

from ghostliness.auth import GameProfile
from ghostliness.items import PlayerInventory
from ghostliness.world import Position


@dataclass(slots=True)
class Player:
    profile: GameProfile
    position: Position
    connection_id: str
    entity_id: int = 1
    inventory: PlayerInventory = field(default_factory=PlayerInventory)

    @property
    def name(self) -> str:
        return self.profile.username
