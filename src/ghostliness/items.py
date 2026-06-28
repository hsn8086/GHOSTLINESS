from __future__ import annotations

from dataclasses import dataclass, field

from ghostliness.blocks import block_for_item_id
from ghostliness.world import BlockState

HOTBAR_SIZE = 9
CREATIVE_HOTBAR_SLOT_OFFSET = 36
MAX_STACK_SIZE = 64

AIR_ITEM_ID = 0
STONE_ITEM_ID = 1
GRASS_BLOCK_ITEM_ID = 54
DIRT_ITEM_ID = 55

ITEM_NAMES_BY_ID: dict[int, str] = {
    AIR_ITEM_ID: "minecraft:air",
    STONE_ITEM_ID: "minecraft:stone",
    GRASS_BLOCK_ITEM_ID: "minecraft:grass_block",
    DIRT_ITEM_ID: "minecraft:dirt",
}

DEFAULT_TEST_HOTBAR: tuple[ItemStack, ...]


@dataclass(frozen=True, slots=True)
class ItemStack:
    item_id: int = AIR_ITEM_ID
    count: int = 0
    components_supported: bool = True
    component_patch_bytes: bytes = b""

    @classmethod
    def empty(cls) -> ItemStack:
        return cls()

    @property
    def is_empty(self) -> bool:
        return self.count <= 0 or self.item_id == AIR_ITEM_ID

    @property
    def item_name(self) -> str:
        return ITEM_NAMES_BY_ID.get(self.item_id, f"unknown:{self.item_id}")

    def can_stack_with(self, other: ItemStack) -> bool:
        return (
            not self.is_empty
            and not other.is_empty
            and self.item_id == other.item_id
            and self.components_supported == other.components_supported
            and self.component_patch_bytes == other.component_patch_bytes
        )

    def with_count(self, count: int) -> ItemStack:
        if count <= 0:
            return ItemStack.empty()
        return ItemStack(
            item_id=self.item_id,
            count=count,
            components_supported=self.components_supported,
            component_patch_bytes=self.component_patch_bytes,
        )


DEFAULT_TEST_HOTBAR = (
    ItemStack(item_id=STONE_ITEM_ID, count=64),
    ItemStack(item_id=DIRT_ITEM_ID, count=64),
    ItemStack(item_id=GRASS_BLOCK_ITEM_ID, count=64),
)


@dataclass(slots=True)
class PlayerInventory:
    selected_slot: int = 0
    hotbar: list[ItemStack] = field(
        default_factory=lambda: [ItemStack.empty() for _ in range(HOTBAR_SIZE)]
    )

    def set_selected_slot(self, slot: int) -> bool:
        if not 0 <= slot < HOTBAR_SIZE:
            return False
        self.selected_slot = slot
        return True

    def set_hotbar_slot(self, slot: int, stack: ItemStack) -> bool:
        if not 0 <= slot < HOTBAR_SIZE:
            return False
        self.hotbar[slot] = stack
        return True

    def selected_stack(self) -> ItemStack:
        return self.hotbar[self.selected_slot]

    def held_stack(self, hand: int) -> ItemStack:
        if hand == 0:
            return self.selected_stack()
        return ItemStack.empty()

    def remove_from_selected(self, count: int) -> ItemStack:
        if count <= 0:
            return ItemStack.empty()
        stack = self.selected_stack()
        if stack.is_empty:
            return ItemStack.empty()
        removed_count = min(count, stack.count)
        self.hotbar[self.selected_slot] = stack.with_count(stack.count - removed_count)
        return stack.with_count(removed_count)

    def can_add_stack(self, stack: ItemStack) -> bool:
        if stack.is_empty:
            return True
        remaining = stack.count
        for slot_stack in self.hotbar:
            if slot_stack.can_stack_with(stack) and slot_stack.count < MAX_STACK_SIZE:
                remaining -= min(MAX_STACK_SIZE - slot_stack.count, remaining)
                if remaining <= 0:
                    return True
        for slot_stack in self.hotbar:
            if slot_stack.is_empty:
                remaining -= min(MAX_STACK_SIZE, remaining)
                if remaining <= 0:
                    return True
        return False

    def add_stack(self, stack: ItemStack) -> bool:
        if not self.can_add_stack(stack):
            return False
        remaining = stack.count
        for slot, slot_stack in enumerate(self.hotbar):
            if not slot_stack.can_stack_with(stack) or slot_stack.count >= MAX_STACK_SIZE:
                continue
            moved = min(MAX_STACK_SIZE - slot_stack.count, remaining)
            self.hotbar[slot] = slot_stack.with_count(slot_stack.count + moved)
            remaining -= moved
            if remaining <= 0:
                return True
        for slot, slot_stack in enumerate(self.hotbar):
            if not slot_stack.is_empty:
                continue
            moved = min(MAX_STACK_SIZE, remaining)
            self.hotbar[slot] = stack.with_count(moved)
            remaining -= moved
            if remaining <= 0:
                return True
        return True

    def load_default_test_hotbar(self) -> None:
        self.selected_slot = 0
        for slot, stack in enumerate(DEFAULT_TEST_HOTBAR):
            self.hotbar[slot] = stack


def hotbar_index_from_creative_slot(slot_num: int) -> int | None:
    hotbar_index = slot_num - CREATIVE_HOTBAR_SLOT_OFFSET
    if 0 <= hotbar_index < HOTBAR_SIZE:
        return hotbar_index
    return None


def block_for_item_stack(stack: ItemStack) -> BlockState | None:
    if stack.is_empty or not stack.components_supported:
        return None
    return block_for_item_id(stack.item_id)
