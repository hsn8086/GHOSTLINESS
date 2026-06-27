from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Position:
    x: float = 0.0
    y: float = 64.0
    z: float = 0.0
    yaw: float = 0.0
    pitch: float = 0.0


@dataclass(slots=True)
class World:
    name: str = "world"
    generator: str = "void"
    spawn: Position = field(default_factory=Position)

    def status_description(self) -> dict[str, str]:
        return {"text": f"{self.generator} world"}
