import uuid

from ghostliness.items import DIRT_ITEM_ID, STONE_ITEM_ID, ItemStack
from ghostliness.server.entities import ITEM_ENTITY_LIFETIME_TICKS, ItemEntity, Vec3
from ghostliness.world import BlockPosition, Position


def _item_entity(
    *,
    entity_id: int = 1,
    x: float = 0.5,
    y: float = 66.0,
    z: float = 0.5,
    item_id: int = DIRT_ITEM_ID,
    count: int = 1,
    velocity: Vec3 | None = None,
    pickup_delay: int = 10,
) -> ItemEntity:
    return ItemEntity.create(
        entity_id=entity_id,
        entity_uuid=uuid.UUID(int=entity_id),
        position=Position(x=x, y=y, z=z),
        stack=ItemStack(item_id=item_id, count=count),
        velocity=velocity,
        pickup_delay=pickup_delay,
    )


def test_item_entity_falls_and_lands_on_solid_block():
    entity = _item_entity(y=65.2)

    for _ in range(20):
        entity.tick(lambda position: position == BlockPosition(0, 64, 0))

    assert entity.position.y >= 65.0
    assert entity.position.y < 65.01
    assert entity.on_ground is True
    assert entity.velocity.y >= 0.0


def test_item_entity_pickup_delay_counts_down():
    entity = _item_entity(pickup_delay=3)

    entity.tick(lambda _position: False)
    entity.tick(lambda _position: False)
    entity.tick(lambda _position: False)

    assert entity.pickup_delay == 0


def test_item_entity_despawns_after_lifetime():
    entity = _item_entity()
    entity.age = ITEM_ENTITY_LIFETIME_TICKS - 1

    entity.tick(lambda _position: False)

    assert entity.removed is True


def test_item_entities_merge_same_stack_when_close():
    first = _item_entity(entity_id=1, x=0.5, z=0.5, count=20)
    second = _item_entity(entity_id=2, x=0.9, z=0.5, count=30)

    assert first.merge_from(second) is True

    assert first.stack == ItemStack(item_id=DIRT_ITEM_ID, count=50)
    assert first.metadata_dirty is True
    assert second.removed is True


def test_item_entities_do_not_merge_different_items_or_over_max_stack():
    first = _item_entity(entity_id=1, count=63)
    different = _item_entity(entity_id=2, item_id=STONE_ITEM_ID, count=1)
    too_many = _item_entity(entity_id=3, count=2)

    assert first.merge_from(different) is False
    assert first.merge_from(too_many) is False
    assert first.stack == ItemStack(item_id=DIRT_ITEM_ID, count=63)


def test_item_entity_pickup_range_uses_player_position():
    entity = _item_entity(x=1.0, y=65.0, z=1.0)

    assert entity.within_pickup_range(Position(x=1.2, y=64.5, z=1.2)) is True
    assert entity.within_pickup_range(Position(x=4.0, y=64.5, z=1.2)) is False
