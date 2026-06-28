import json

import pytest

from ghostliness.world import CHUNK_FORMAT_VERSION, BlockPosition, BlockState, Chunk, ChunkPosition
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
    chunk_path = storage.chunks_path / "2.-3.json"
    data = json.loads(chunk_path.read_text(encoding="utf-8"))

    assert storage.chunk_exists(position)
    assert data["format_version"] == CHUNK_FORMAT_VERSION
    assert loaded is not None
    assert loaded.position == position
    assert loaded.generated_by == "test"
    assert loaded.get_block(block_position) == block_state


def test_ghostliness_storage_loads_legacy_unversioned_chunk(tmp_path):
    storage = GhostlinessWorldStorage(tmp_path / "world")
    storage.chunks_path.mkdir(parents=True)
    chunk_path = storage.chunks_path / "0.0.json"
    chunk_path.write_text(
        json.dumps(
            {
                "position": {"x": 0, "z": 0},
                "generated_by": "legacy",
                "blocks": [
                    {
                        "position": {"x": 1, "y": 64, "z": 1},
                        "state": {"name": "minecraft:stone", "properties": {}},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    loaded = storage.load_chunk(ChunkPosition(0, 0))

    assert loaded is not None
    assert loaded.generated_by == "legacy"
    assert loaded.get_block(BlockPosition(1, 64, 1)) == BlockState("minecraft:stone")


def test_ghostliness_storage_rejects_unknown_future_chunk_format(tmp_path):
    storage = GhostlinessWorldStorage(tmp_path / "world")
    storage.chunks_path.mkdir(parents=True)
    chunk_path = storage.chunks_path / "0.0.json"
    chunk_path.write_text(
        json.dumps(
            {
                "format_version": CHUNK_FORMAT_VERSION + 1,
                "position": {"x": 0, "z": 0},
                "generated_by": "future",
                "blocks": [],
            }
        ),
        encoding="utf-8",
    )

    assert storage.load_chunk(ChunkPosition(0, 0)) is None


def test_ghostliness_storage_returns_none_for_bad_chunk_documents(tmp_path):
    storage = GhostlinessWorldStorage(tmp_path / "world")
    storage.chunks_path.mkdir(parents=True)

    (storage.chunks_path / "0.0.json").write_text("[]", encoding="utf-8")
    assert storage.load_chunk(ChunkPosition(0, 0)) is None

    (storage.chunks_path / "0.0.json").write_text("{", encoding="utf-8")
    assert storage.load_chunk(ChunkPosition(0, 0)) is None

    (storage.chunks_path / "0.0.json").write_text(
        json.dumps({"format_version": CHUNK_FORMAT_VERSION, "blocks": []}),
        encoding="utf-8",
    )
    assert storage.load_chunk(ChunkPosition(0, 0)) is None


def test_ghostliness_storage_returns_none_for_missing_chunk(tmp_path):
    storage = GhostlinessWorldStorage(tmp_path / "world")

    assert storage.load_chunk(ChunkPosition(0, 0)) is None
    assert storage.chunk_exists(ChunkPosition(0, 0)) is False


def test_anvil_storage_backend_fails_fast(tmp_path):
    with pytest.raises(NotImplementedError, match="Anvil"):
        create_world_storage("anvil", tmp_path / "world")
