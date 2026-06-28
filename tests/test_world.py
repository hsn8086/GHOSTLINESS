from ghostliness.world import (
    AIR,
    CHUNK_FORMAT_VERSION,
    DIRT,
    GRASS_BLOCK,
    STONE,
    BlockPosition,
    Chunk,
    ChunkPosition,
    Position,
    World,
    chunk_position_from_block,
    chunk_position_from_world,
    local_block_position,
)


def test_void_generator_returns_empty_chunk():
    world = World(generator="void")

    chunk = world.generate_chunk(ChunkPosition(0, 0))

    assert chunk.generated_by == "void"
    assert chunk.blocks == {}


def test_flat_generator_returns_layered_chunk_and_spawn_above_ground():
    world = World(generator="flat")

    chunk = world.generate_chunk(ChunkPosition(0, 0))

    assert world.spawn == Position(y=65.0)
    assert chunk.generated_by == "flat"
    assert chunk.get_block(BlockPosition(0, 0, 0)) == STONE
    assert chunk.get_block(BlockPosition(0, 60, 0)) == STONE
    assert chunk.get_block(BlockPosition(0, 61, 0)) == DIRT
    assert chunk.get_block(BlockPosition(0, 63, 0)) == DIRT
    assert chunk.get_block(BlockPosition(0, 64, 0)) == GRASS_BLOCK
    assert chunk.get_block(BlockPosition(0, 65, 0)) == AIR
    assert len(chunk.blocks) == 16 * 16 * 65


def test_flat_generator_keeps_explicit_spawn():
    spawn = Position(x=10.0, y=80.0, z=10.0)
    world = World(generator="flat", spawn=spawn)

    assert world.spawn is spawn
    assert world.spawn.y == 80.0


def test_block_position_maps_to_chunk_and_local_coordinates():
    cases = [
        (BlockPosition(0, 64, 0), ChunkPosition(0, 0), BlockPosition(0, 64, 0)),
        (BlockPosition(15, 64, 15), ChunkPosition(0, 0), BlockPosition(15, 64, 15)),
        (BlockPosition(16, 64, 16), ChunkPosition(1, 1), BlockPosition(0, 64, 0)),
        (BlockPosition(-1, 64, -1), ChunkPosition(-1, -1), BlockPosition(15, 64, 15)),
        (BlockPosition(-16, 64, -16), ChunkPosition(-1, -1), BlockPosition(0, 64, 0)),
        (BlockPosition(-17, 64, 32), ChunkPosition(-2, 2), BlockPosition(15, 64, 0)),
    ]

    for world_position, chunk_position, local_position in cases:
        assert chunk_position_from_block(world_position) == chunk_position
        assert local_block_position(world_position) == local_position


def test_chunk_json_includes_format_version_and_loads_legacy_data():
    chunk = Chunk(position=ChunkPosition(0, 0), generated_by="test")
    chunk.set_block(BlockPosition(1, 64, 1), STONE)

    data = chunk.to_json()

    assert data["format_version"] == CHUNK_FORMAT_VERSION
    legacy_data = dict(data)
    legacy_data.pop("format_version")
    loaded = Chunk.from_json(legacy_data)
    assert loaded.position == ChunkPosition(0, 0)
    assert loaded.generated_by == "test"
    assert loaded.get_block(BlockPosition(1, 64, 1)) == STONE


def test_world_coordinates_map_to_chunk_with_floor_semantics():
    cases = [
        ((0.0, 0.0), ChunkPosition(0, 0)),
        ((15.99, 15.99), ChunkPosition(0, 0)),
        ((16.0, 16.0), ChunkPosition(1, 1)),
        ((-0.1, -0.1), ChunkPosition(-1, -1)),
        ((-16.0, -16.0), ChunkPosition(-1, -1)),
        ((-16.1, 32.0), ChunkPosition(-2, 2)),
    ]

    for (x, z), chunk_position in cases:
        assert chunk_position_from_world(x, z) == chunk_position
