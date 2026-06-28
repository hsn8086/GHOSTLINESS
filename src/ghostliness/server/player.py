from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from ghostliness.auth import GameProfile
from ghostliness.items import PlayerInventory
from ghostliness.world import BlockPosition, Position


class PlayerPose(StrEnum):
    STANDING = "standing"
    SNEAKING = "sneaking"


@dataclass(frozen=True, slots=True)
class AxisAlignedBoundingBox:
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    def intersects_block(self, position: BlockPosition) -> bool:
        return (
            self.min_x < position.x + 1
            and self.max_x > position.x
            and self.min_y < position.y + 1
            and self.max_y > position.y
            and self.min_z < position.z + 1
            and self.max_z > position.z
        )


@dataclass(slots=True)
class PlayerInput:
    forward: bool = False
    backward: bool = False
    left: bool = False
    right: bool = False
    jump: bool = False
    shift: bool = False
    sprint: bool = False


@dataclass(slots=True)
class Player:
    profile: GameProfile
    position: Position
    connection_id: str
    entity_id: int = 1
    inventory: PlayerInventory = field(default_factory=PlayerInventory)
    gamemode: int = 1
    on_ground: bool = False
    sprinting: bool = False
    sneaking: bool = False
    pose: PlayerPose = PlayerPose.STANDING
    input: PlayerInput = field(default_factory=PlayerInput)

    @property
    def name(self) -> str:
        return self.profile.username

    @property
    def bounding_box(self) -> AxisAlignedBoundingBox:
        half_width = 0.3
        height = 1.5 if self.pose == PlayerPose.SNEAKING else 1.8
        return AxisAlignedBoundingBox(
            min_x=self.position.x - half_width,
            min_y=self.position.y,
            min_z=self.position.z - half_width,
            max_x=self.position.x + half_width,
            max_y=self.position.y + height,
            max_z=self.position.z + half_width,
        )

    def set_sneaking(self, sneaking: bool) -> None:
        self.sneaking = sneaking
        self.pose = PlayerPose.SNEAKING if sneaking else PlayerPose.STANDING
