import pytest

from ghostliness.world import BlockPosition, BlockState, Chunk, ChunkPosition
from ghostliness.world_storage import (
    GhostlinessWorldStorage,
    create_world_storage,
)


def test_ghostliness_storage_saves_and_loads_chunk(tmp_path):
    storage = GhostlinessWorldStorage(tmp_path / "world")
    position = ChunkPosition(2, -3)
    block_position = BlockPosition(1, 64, 1)
    block_state = BlockState("minecraft:stone", (("variant", "smooth"),))
    chunk = Chunk(position=position, generated_by="test")
    chunk.set_block(block_position, block_state)

    storage.save_chunk(chunk)
    loaded = storage.load_chunk(position)

    assert storage.chunk_exists(position)
    assert loaded is not None
    assert loaded.position == position
    assert loaded.generated_by == "test"
    assert loaded.get_block(block_position) == block_state


def test_ghostliness_storage_returns_none_for_missing_chunk(tmp_path):
    storage = GhostlinessWorldStorage(tmp_path / "world")

    assert storage.load_chunk(ChunkPosition(0, 0)) is None
    assert storage.chunk_exists(ChunkPosition(0, 0)) is False


def test_anvil_storage_backend_fails_fast(tmp_path):
    with pytest.raises(NotImplementedError, match="Anvil"):
        create_world_storage("anvil", tmp_path / "world")
