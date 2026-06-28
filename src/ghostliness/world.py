from __future__ import annotations

from dataclasses import dataclass, field
from math import floor
from typing import Any

from ghostliness.blocks import AIR, DIRT, GRASS_BLOCK, STONE, BlockState

CHUNK_WIDTH = 16
CHUNK_FORMAT_VERSION = 1


@dataclass(slots=True)
class Position:
    x: float = 0.0
    y: float = 64.0
    z: float = 0.0
    yaw: float = 0.0
    pitch: float = 0.0


@dataclass(frozen=True, slots=True)
class BlockPosition:
    x: int
    y: int
    z: int

    def to_json(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y, "z": self.z}

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> BlockPosition:
        return cls(x=int(data["x"]), y=int(data["y"]), z=int(data["z"]))


@dataclass(frozen=True, slots=True)
class ChunkPosition:
    x: int
    z: int

    def to_json(self) -> dict[str, int]:
        return {"x": self.x, "z": self.z}

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ChunkPosition:
        return cls(x=int(data["x"]), z=int(data["z"]))


def chunk_position_from_block(position: BlockPosition) -> ChunkPosition:
    return ChunkPosition(position.x // CHUNK_WIDTH, position.z // CHUNK_WIDTH)


def chunk_position_from_world(x: float, z: float) -> ChunkPosition:
    return ChunkPosition(floor(x) // CHUNK_WIDTH, floor(z) // CHUNK_WIDTH)


def local_block_position(position: BlockPosition) -> BlockPosition:
    return BlockPosition(position.x % CHUNK_WIDTH, position.y, position.z % CHUNK_WIDTH)


@dataclass(slots=True)
class Chunk:
    position: ChunkPosition
    generated_by: str = "void"
    blocks: dict[BlockPosition, BlockState] = field(default_factory=dict)

    def get_block(self, position: BlockPosition) -> BlockState:
        return self.blocks.get(position, AIR)

    def set_block(self, position: BlockPosition, state: BlockState) -> None:
        if state == AIR:
            self.blocks.pop(position, None)
            return
        self.blocks[position] = state

    def to_json(self) -> dict[str, object]:
        return {
            "format_version": CHUNK_FORMAT_VERSION,
            "position": self.position.to_json(),
            "generated_by": self.generated_by,
            "blocks": [
                {"position": position.to_json(), "state": state.to_json()}
                for position, state in sorted(
                    self.blocks.items(),
                    key=lambda item: (item[0].x, item[0].y, item[0].z),
                )
            ],
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Chunk:
        format_version = int(data.get("format_version", 0))
        if format_version not in {0, CHUNK_FORMAT_VERSION}:
            raise ValueError(f"unsupported chunk format version: {format_version}")
        chunk = cls(
            position=ChunkPosition.from_json(data["position"]),
            generated_by=str(data.get("generated_by", "void")),
        )
        blocks = data.get("blocks", [])
        if isinstance(blocks, list):
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                position = block.get("position")
                state = block.get("state")
                if isinstance(position, dict) and isinstance(state, dict):
                    chunk.set_block(
                        BlockPosition.from_json(position),
                        BlockState.from_json(state),
                    )
        return chunk


@dataclass(slots=True)
class World:
    name: str = "world"
    generator: str = "void"
    spawn: Position = field(default_factory=Position)

    def __post_init__(self) -> None:
        if self.generator == "flat" and self.spawn == Position():
            self.spawn.y = 65.0

    def status_description(self) -> dict[str, str]:
        return {"text": f"{self.generator} world"}

    def generate_chunk(self, position: ChunkPosition) -> Chunk:
        chunk = Chunk(position=position, generated_by=self.generator)
        if self.generator != "flat":
            return chunk

        for x in range(16):
            for z in range(16):
                for y in range(0, 61):
                    chunk.set_block(BlockPosition(x, y, z), STONE)
                for y in range(61, 64):
                    chunk.set_block(BlockPosition(x, y, z), DIRT)
                chunk.set_block(BlockPosition(x, 64, z), GRASS_BLOCK)
        return chunk
