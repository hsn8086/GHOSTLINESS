from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from math import floor, isclose

from ghostliness.items import MAX_STACK_SIZE, ItemStack
from ghostliness.protocol.versions.java_26_2 import ITEM_ENTITY_TYPE_ID
from ghostliness.world import BlockPosition, Position

ITEM_ENTITY_WIDTH = 0.25
ITEM_ENTITY_HEIGHT = 0.25
ITEM_ENTITY_GRAVITY = 0.04
ITEM_ENTITY_AIR_DRAG = 0.98
ITEM_ENTITY_GROUND_FRICTION = 0.5880000114
ITEM_ENTITY_GROUND_BOUNCE = -0.5
ITEM_ENTITY_PICKUP_DELAY_TICKS = 10
ITEM_ENTITY_LIFETIME_TICKS = 6000
ITEM_ENTITY_MERGE_RADIUS_XZ = 0.5
ITEM_ENTITY_MERGE_RADIUS_Y = ITEM_ENTITY_HEIGHT
ITEM_ENTITY_PICKUP_RADIUS = 1.0


@dataclass(slots=True)
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def horizontal_length_sqr(self) -> float:
        return self.x * self.x + self.z * self.z


@dataclass(frozen=True, slots=True)
class EntityBox:
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    def moved(self, dx: float, dy: float, dz: float) -> EntityBox:
        return EntityBox(
            self.min_x + dx,
            self.min_y + dy,
            self.min_z + dz,
            self.max_x + dx,
            self.max_y + dy,
            self.max_z + dz,
        )

    def intersects_block(self, position: BlockPosition) -> bool:
        return (
            self.min_x < position.x + 1
            and self.max_x > position.x
            and self.min_y < position.y + 1
            and self.max_y > position.y
            and self.min_z < position.z + 1
            and self.max_z > position.z
        )

    def block_positions(self) -> Iterable[BlockPosition]:
        min_x = floor(self.min_x)
        max_x = floor(self.max_x - 1e-7)
        min_y = floor(self.min_y)
        max_y = floor(self.max_y - 1e-7)
        min_z = floor(self.min_z)
        max_z = floor(self.max_z - 1e-7)
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                for z in range(min_z, max_z + 1):
                    yield BlockPosition(x, y, z)


@dataclass(slots=True)
class Entity:
    entity_id: int
    uuid: uuid.UUID
    type_id: int
    position: Position
    velocity: Vec3 = field(default_factory=Vec3)
    on_ground: bool = False
    removed: bool = False

    @property
    def chunk_x(self) -> int:
        return floor(self.position.x) // 16

    @property
    def chunk_z(self) -> int:
        return floor(self.position.z) // 16


@dataclass(slots=True)
class ItemEntity(Entity):
    stack: ItemStack = field(default_factory=ItemStack.empty)
    age: int = 0
    pickup_delay: int = ITEM_ENTITY_PICKUP_DELAY_TICKS
    metadata_dirty: bool = False

    @classmethod
    def create(
        cls,
        *,
        entity_id: int,
        entity_uuid: uuid.UUID,
        position: Position,
        stack: ItemStack,
        velocity: Vec3 | None = None,
        pickup_delay: int = ITEM_ENTITY_PICKUP_DELAY_TICKS,
    ) -> ItemEntity:
        return cls(
            entity_id=entity_id,
            uuid=entity_uuid,
            type_id=ITEM_ENTITY_TYPE_ID,
            position=position,
            velocity=velocity or Vec3(),
            stack=stack,
            pickup_delay=pickup_delay,
        )

    @property
    def box(self) -> EntityBox:
        half = ITEM_ENTITY_WIDTH / 2.0
        return EntityBox(
            self.position.x - half,
            self.position.y,
            self.position.z - half,
            self.position.x + half,
            self.position.y + ITEM_ENTITY_HEIGHT,
            self.position.z + half,
        )

    def tick(self, is_solid_block: Callable[[BlockPosition], bool]) -> bool:
        if self.stack.is_empty:
            self.removed = True
            return False
        if self.pickup_delay > 0 and self.pickup_delay != 32767:
            self.pickup_delay -= 1

        before = (self.position.x, self.position.y, self.position.z)
        before_velocity = (self.velocity.x, self.velocity.y, self.velocity.z)

        self.velocity.y -= ITEM_ENTITY_GRAVITY
        moved = self._move(is_solid_block)
        drag = ITEM_ENTITY_AIR_DRAG
        horizontal_drag = drag * ITEM_ENTITY_GROUND_FRICTION if self.on_ground else drag
        self.velocity.x *= horizontal_drag
        self.velocity.y *= drag
        self.velocity.z *= horizontal_drag
        if self.on_ground and self.velocity.y < 0.0:
            self.velocity.y *= ITEM_ENTITY_GROUND_BOUNCE

        self.age += 1
        if self.age >= ITEM_ENTITY_LIFETIME_TICKS:
            self.removed = True

        return (
            moved
            or any(
                not isclose(now, previous, abs_tol=1e-7)
                for now, previous in zip(
                    (self.velocity.x, self.velocity.y, self.velocity.z),
                    before_velocity,
                    strict=True,
                )
            )
            or (self.position.x, self.position.y, self.position.z) != before
        )

    def can_merge_with(self, other: ItemEntity) -> bool:
        return (
            self is not other
            and not self.removed
            and not other.removed
            and self.pickup_delay != 32767
            and other.pickup_delay != 32767
            and self.age < ITEM_ENTITY_LIFETIME_TICKS
            and other.age < ITEM_ENTITY_LIFETIME_TICKS
            and self.stack.can_stack_with(other.stack)
            and self.stack.count + other.stack.count <= MAX_STACK_SIZE
            and abs(self.position.x - other.position.x) <= ITEM_ENTITY_MERGE_RADIUS_XZ
            and abs(self.position.y - other.position.y) <= ITEM_ENTITY_MERGE_RADIUS_Y
            and abs(self.position.z - other.position.z) <= ITEM_ENTITY_MERGE_RADIUS_XZ
        )

    def merge_from(self, other: ItemEntity) -> bool:
        if not self.can_merge_with(other):
            return False
        self.stack = self.stack.with_count(self.stack.count + other.stack.count)
        self.pickup_delay = max(self.pickup_delay, other.pickup_delay)
        self.age = min(self.age, other.age)
        self.metadata_dirty = True
        other.removed = True
        return True

    def within_pickup_range(self, position: Position) -> bool:
        dx = self.position.x - position.x
        dy = self.position.y - (position.y + 0.5)
        dz = self.position.z - position.z
        return dx * dx + dy * dy + dz * dz <= ITEM_ENTITY_PICKUP_RADIUS * ITEM_ENTITY_PICKUP_RADIUS

    def _move(self, is_solid_block: Callable[[BlockPosition], bool]) -> bool:
        original = (self.position.x, self.position.y, self.position.z)
        dx = self._clip_axis("x", self.velocity.x, is_solid_block)
        self.position.x += dx
        dy = self._clip_axis("y", self.velocity.y, is_solid_block)
        self.position.y += dy
        dz = self._clip_axis("z", self.velocity.z, is_solid_block)
        self.position.z += dz

        self.on_ground = self.velocity.y < 0.0 and dy != self.velocity.y
        if dx != self.velocity.x:
            self.velocity.x = 0.0
        if dy != self.velocity.y:
            self.velocity.y = 0.0
        if dz != self.velocity.z:
            self.velocity.z = 0.0
        return (self.position.x, self.position.y, self.position.z) != original

    def _clip_axis(
        self,
        axis: str,
        delta: float,
        is_solid_block: Callable[[BlockPosition], bool],
    ) -> float:
        if delta == 0.0:
            return 0.0
        low = 0.0
        high = delta
        if delta < 0.0:
            low, high = delta, 0.0
        for _ in range(12):
            mid = (low + high) / 2.0
            if self._collides(axis, mid, is_solid_block):
                if delta > 0.0:
                    high = mid
                else:
                    low = mid
            elif delta > 0.0:
                low = mid
            else:
                high = mid
        clipped = low if delta > 0.0 else high
        if abs(clipped) < 1e-6:
            return 0.0
        return clipped

    def _collides(
        self,
        axis: str,
        delta: float,
        is_solid_block: Callable[[BlockPosition], bool],
    ) -> bool:
        dx = delta if axis == "x" else 0.0
        dy = delta if axis == "y" else 0.0
        dz = delta if axis == "z" else 0.0
        moved = self.box.moved(dx, dy, dz)
        return any(
            moved.intersects_block(position)
            for position in moved.block_positions()
            if is_solid_block(position)
        )
