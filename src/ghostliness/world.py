from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
class BlockState:
    name: str = "minecraft:air"
    properties: tuple[tuple[str, str], ...] = ()

    def to_json(self) -> dict[str, object]:
        return {"name": self.name, "properties": dict(self.properties)}

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> BlockState:
        properties = data.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        return cls(
            name=str(data.get("name", "minecraft:air")),
            properties=tuple(sorted((str(key), str(value)) for key, value in properties.items())),
        )


AIR = BlockState()


@dataclass(frozen=True, slots=True)
class ChunkPosition:
    x: int
    z: int

    def to_json(self) -> dict[str, int]:
        return {"x": self.x, "z": self.z}

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ChunkPosition:
        return cls(x=int(data["x"]), z=int(data["z"]))


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

    def status_description(self) -> dict[str, str]:
        return {"text": f"{self.generator} world"}

    def generate_chunk(self, position: ChunkPosition) -> Chunk:
        return Chunk(position=position, generated_by=self.generator)
