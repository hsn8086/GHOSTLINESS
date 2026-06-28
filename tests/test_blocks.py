from ghostliness.blocks import (
    AIR,
    BLOCKS,
    DIRT,
    GRASS_BLOCK,
    STONE,
    block_for_item_id,
    block_state_to_protocol_id,
    can_place_against,
    can_replace,
    get_block,
    hardness,
    is_air,
    is_known,
    is_solid,
)
from ghostliness.world import BlockState


def test_block_registry_resolves_supported_blocks_by_name_state_and_protocol_id():
    assert get_block("minecraft:air") is not None
    assert get_block("minecraft:stone") is not None
    assert get_block("minecraft:grass_block") is not None
    assert get_block("minecraft:dirt") is not None

    assert BLOCKS.get_by_state(AIR) == get_block("minecraft:air")
    assert BLOCKS.get_by_state(STONE) == get_block("minecraft:stone")
    assert BLOCKS.get_by_protocol_id(9) == get_block("minecraft:grass_block")
    assert BLOCKS.get_by_protocol_id(10) == get_block("minecraft:dirt")


def test_block_registry_preserves_26_2_protocol_ids():
    assert block_state_to_protocol_id(AIR) == 0
    assert block_state_to_protocol_id(STONE) == 1
    assert block_state_to_protocol_id(GRASS_BLOCK) == 9
    assert block_state_to_protocol_id(DIRT) == 10
    assert block_state_to_protocol_id(BlockState("ghostliness:missing")) == 0


def test_block_registry_maps_current_item_ids_to_blocks():
    assert block_for_item_id(0) is None
    assert block_for_item_id(1) == STONE
    assert block_for_item_id(54) == GRASS_BLOCK
    assert block_for_item_id(55) == DIRT
    assert block_for_item_id(9999) is None


def test_block_rule_helpers_describe_known_blocks():
    assert is_air(AIR) is True
    assert is_solid(AIR) is False
    assert can_replace(AIR) is True
    assert can_place_against(AIR) is False
    assert hardness(AIR) == 0.0

    for state in (STONE, GRASS_BLOCK, DIRT):
        assert is_air(state) is False
        assert is_known(state) is True
        assert is_solid(state) is True
        assert can_replace(state) is False
        assert can_place_against(state) is True
        assert hardness(state) > 0.0


def test_block_rule_helpers_reject_unknown_blocks_conservatively():
    missing = BlockState("ghostliness:missing")

    assert is_air(missing) is False
    assert is_known(missing) is False
    assert is_solid(missing) is False
    assert can_replace(missing) is False
    assert can_place_against(missing) is False
    assert hardness(missing) == 0.0
