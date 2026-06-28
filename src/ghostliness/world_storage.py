from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from loguru import logger

from ghostliness.world import Chunk, ChunkPosition


class WorldStorage(Protocol):
    def load_chunk(self, position: ChunkPosition) -> Chunk | None:
        """Load a chunk from storage, or return None when it has not been persisted."""

    def save_chunk(self, chunk: Chunk) -> None:
        """Persist a chunk."""

    def chunk_exists(self, position: ChunkPosition) -> bool:
        """Return whether the chunk has a persisted representation."""

    def close(self) -> None:
        """Release storage resources."""


class GhostlinessWorldStorage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.chunks_path = path / "chunks"

    def load_chunk(self, position: ChunkPosition) -> Chunk | None:
        chunk_path = self._chunk_path(position)
        if not chunk_path.exists():
            return None
        try:
            data = json.loads(chunk_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("failed to read chunk path={} error={}", chunk_path, exc)
            return None
        if not isinstance(data, dict):
            logger.warning("invalid chunk document path={} reason=not_object", chunk_path)
            return None
        try:
            return Chunk.from_json(data)
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning(
                "invalid chunk document path={} format_version={} error={}",
                chunk_path,
                data.get("format_version", 0),
                exc,
            )
            return None

    def save_chunk(self, chunk: Chunk) -> None:
        self.chunks_path.mkdir(parents=True, exist_ok=True)
        chunk_path = self._chunk_path(chunk.position)
        temporary_path = chunk_path.with_suffix(".json.tmp")
        temporary_path.write_text(
            json.dumps(chunk.to_json(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary_path.replace(chunk_path)

    def chunk_exists(self, position: ChunkPosition) -> bool:
        return self._chunk_path(position).is_file()

    def close(self) -> None:
        return None

    def _chunk_path(self, position: ChunkPosition) -> Path:
        return self.chunks_path / f"{position.x}.{position.z}.json"


class AnvilWorldStorage:
    def __init__(self, path: Path) -> None:
        self.path = path
        raise NotImplementedError(
            "Anvil .mca world storage is not implemented yet; use storage = \"ghostliness\""
        )

    def load_chunk(self, position: ChunkPosition) -> Chunk | None:
        _ = position
        return None

    def save_chunk(self, chunk: Chunk) -> None:
        _ = chunk

    def chunk_exists(self, position: ChunkPosition) -> bool:
        _ = position
        return False

    def close(self) -> None:
        return None


def create_world_storage(kind: str, path: Path) -> WorldStorage:
    match kind:
        case "ghostliness":
            return GhostlinessWorldStorage(path)
        case "anvil":
            return AnvilWorldStorage(path)
        case _:
            raise ValueError(f"unsupported world storage backend: {kind}")
