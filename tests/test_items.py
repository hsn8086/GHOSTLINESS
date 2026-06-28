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
