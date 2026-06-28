from ghostliness.items import (
    AIR_ITEM_ID,
    DEFAULT_TEST_HOTBAR,
    DIRT_ITEM_ID,
    GRASS_BLOCK_ITEM_ID,
    STONE_ITEM_ID,
    ItemStack,
    PlayerInventory,
    block_for_item_stack,
    hotbar_index_from_creative_slot,
)
from ghostliness.world import DIRT, GRASS_BLOCK, STONE


def test_hotbar_index_from_creative_slot_maps_inventory_hotbar():
    assert hotbar_index_from_creative_slot(35) is None
    assert hotbar_index_from_creative_slot(36) == 0
    assert hotbar_index_from_creative_slot(44) == 8
    assert hotbar_index_from_creative_slot(45) is None


def test_player_inventory_tracks_selected_hotbar_stack():
    inventory = PlayerInventory()
    assert inventory.set_hotbar_slot(2, ItemStack(item_id=DIRT_ITEM_ID, count=64)) is True
    assert inventory.set_selected_slot(2) is True

    assert inventory.selected_stack().item_id == DIRT_ITEM_ID
    assert inventory.held_stack(0).item_id == DIRT_ITEM_ID
    assert inventory.held_stack(1).is_empty


def test_player_inventory_rejects_invalid_hotbar_slots():
    inventory = PlayerInventory()

    assert inventory.set_selected_slot(-1) is False
    assert inventory.set_selected_slot(9) is False
    assert inventory.set_hotbar_slot(9, ItemStack(item_id=DIRT_ITEM_ID, count=1)) is False
    assert inventory.selected_slot == 0


def test_player_inventory_loads_default_test_hotbar():
    inventory = PlayerInventory()
    inventory.set_selected_slot(4)

    inventory.load_default_test_hotbar()

    assert inventory.selected_slot == 0
    assert inventory.hotbar[:3] == list(DEFAULT_TEST_HOTBAR)


def test_player_inventory_removes_from_selected_slot():
    inventory = PlayerInventory()
    inventory.set_hotbar_slot(0, ItemStack(item_id=DIRT_ITEM_ID, count=5))

    removed = inventory.remove_from_selected(2)

    assert removed == ItemStack(item_id=DIRT_ITEM_ID, count=2)
    assert inventory.selected_stack() == ItemStack(item_id=DIRT_ITEM_ID, count=3)


def test_player_inventory_clears_selected_slot_when_removing_entire_stack():
    inventory = PlayerInventory()
    inventory.set_hotbar_slot(0, ItemStack(item_id=DIRT_ITEM_ID, count=5))

    removed = inventory.remove_from_selected(64)

    assert removed == ItemStack(item_id=DIRT_ITEM_ID, count=5)
    assert inventory.selected_stack().is_empty


def test_player_inventory_adds_stack_by_merging_then_empty_slot():
    inventory = PlayerInventory()
    inventory.set_hotbar_slot(0, ItemStack(item_id=DIRT_ITEM_ID, count=63))

    assert inventory.add_stack(ItemStack(item_id=DIRT_ITEM_ID, count=3)) is True

    assert inventory.hotbar[0] == ItemStack(item_id=DIRT_ITEM_ID, count=64)
    assert inventory.hotbar[1] == ItemStack(item_id=DIRT_ITEM_ID, count=2)


def test_player_inventory_rejects_stack_when_hotbar_is_full():
    inventory = PlayerInventory()
    for slot in range(9):
        inventory.set_hotbar_slot(slot, ItemStack(item_id=DIRT_ITEM_ID, count=64))

    assert inventory.can_add_stack(ItemStack(item_id=STONE_ITEM_ID, count=1)) is False
    assert inventory.add_stack(ItemStack(item_id=STONE_ITEM_ID, count=1)) is False
    assert all(stack == ItemStack(item_id=DIRT_ITEM_ID, count=64) for stack in inventory.hotbar)


def test_block_for_item_stack_maps_supported_placeable_items():
    assert block_for_item_stack(ItemStack(item_id=STONE_ITEM_ID, count=1)) == STONE
    assert block_for_item_stack(ItemStack(item_id=GRASS_BLOCK_ITEM_ID, count=1)) == GRASS_BLOCK
    assert block_for_item_stack(ItemStack(item_id=DIRT_ITEM_ID, count=1)) == DIRT


def test_block_for_item_stack_rejects_empty_air_and_unsupported_components():
    assert block_for_item_stack(ItemStack.empty()) is None
    assert block_for_item_stack(ItemStack(item_id=AIR_ITEM_ID, count=64)) is None
    assert (
        block_for_item_stack(
            ItemStack(item_id=DIRT_ITEM_ID, count=1, components_supported=False)
        )
        is None
    )
