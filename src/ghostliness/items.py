from __future__ import annotations

from dataclasses import dataclass, field

from ghostliness.blocks import block_for_item_id
from ghostliness.world import BlockState

HOTBAR_SIZE = 9
CREATIVE_HOTBAR_SLOT_OFFSET = 36

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
