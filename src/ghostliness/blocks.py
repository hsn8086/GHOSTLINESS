from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BlockState:
    name: str = "minecraft:air"
    properties: tuple[tuple[str, str], ...] = ()

    def to_json(self) -> dict[str, object]:
        return {"name": self.name, "properties": dict(self.properties)}

    @classmethod
    def from_json(cls, data: dict[str, object]) -> BlockState:
        properties = data.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        return cls(
            name=str(data.get("name", "minecraft:air")),
            properties=tuple(sorted((str(key), str(value)) for key, value in properties.items())),
        )


@dataclass(frozen=True, slots=True)
class BlockDefinition:
    state: BlockState
    protocol_id: int
    item_id: int | None = None
    solid: bool = True
    replaceable: bool = False
    placement_support: bool = True
    hardness: float = 0.0


class BlockRegistry:
    def __init__(self, definitions: Iterable[BlockDefinition]) -> None:
        self._by_state: dict[BlockState, BlockDefinition] = {}
        self._by_name: dict[str, BlockDefinition] = {}
        self._by_protocol_id: dict[int, BlockDefinition] = {}
        self._by_item_id: dict[int, BlockDefinition] = {}
        for definition in definitions:
            self.register(definition)

    def register(self, definition: BlockDefinition) -> None:
        if definition.state in self._by_state:
            raise ValueError(f"duplicate block state: {definition.state}")
        if definition.state.name in self._by_name:
            raise ValueError(f"duplicate block name: {definition.state.name}")
        if definition.protocol_id in self._by_protocol_id:
            raise ValueError(f"duplicate block protocol id: {definition.protocol_id}")
        if definition.item_id is not None and definition.item_id in self._by_item_id:
            raise ValueError(f"duplicate block item id: {definition.item_id}")

        self._by_state[definition.state] = definition
        self._by_name[definition.state.name] = definition
        self._by_protocol_id[definition.protocol_id] = definition
        if definition.item_id is not None:
            self._by_item_id[definition.item_id] = definition

    def get(self, name: str) -> BlockDefinition | None:
        return self._by_name.get(name)

    def get_by_state(self, state: BlockState) -> BlockDefinition | None:
        return self._by_state.get(state)

    def get_by_protocol_id(self, protocol_id: int) -> BlockDefinition | None:
        return self._by_protocol_id.get(protocol_id)

    def get_by_item_id(self, item_id: int) -> BlockDefinition | None:
        return self._by_item_id.get(item_id)


AIR = BlockState()
STONE = BlockState("minecraft:stone")
DIRT = BlockState("minecraft:dirt")
GRASS_BLOCK = BlockState("minecraft:grass_block")

BLOCKS = BlockRegistry(
    (
        BlockDefinition(
            AIR,
            protocol_id=0,
            item_id=0,
            solid=False,
            replaceable=True,
            placement_support=False,
            hardness=0.0,
        ),
        BlockDefinition(
            STONE,
            protocol_id=1,
            item_id=1,
            solid=True,
            replaceable=False,
            placement_support=True,
            hardness=1.5,
        ),
        BlockDefinition(
            GRASS_BLOCK,
            protocol_id=9,
            item_id=54,
            solid=True,
            replaceable=False,
            placement_support=True,
            hardness=0.6,
        ),
        BlockDefinition(
            DIRT,
            protocol_id=10,
            item_id=55,
            solid=True,
            replaceable=False,
            placement_support=True,
            hardness=0.5,
        ),
    )
)


def get_block(name: str) -> BlockDefinition | None:
    return BLOCKS.get(name)


def block_state_to_protocol_id(state: BlockState) -> int:
    definition = BLOCKS.get_by_state(state)
    if definition is None:
        return 0
    return definition.protocol_id


def is_air(state: BlockState) -> bool:
    return state == AIR


def is_solid(state: BlockState) -> bool:
    definition = BLOCKS.get_by_state(state)
    return definition is not None and definition.solid


def is_known(state: BlockState) -> bool:
    return BLOCKS.get_by_state(state) is not None


def can_replace(state: BlockState) -> bool:
    if is_air(state):
        return True
    definition = BLOCKS.get_by_state(state)
    return definition is not None and definition.replaceable


def can_place_against(state: BlockState) -> bool:
    definition = BLOCKS.get_by_state(state)
    return definition is not None and definition.placement_support


def hardness(state: BlockState) -> float:
    definition = BLOCKS.get_by_state(state)
    if definition is None:
        return 0.0
    return definition.hardness


def block_for_item_id(item_id: int) -> BlockState | None:
    definition = BLOCKS.get_by_item_id(item_id)
    if definition is None or definition.state == AIR:
        return None
    return definition.state


def item_id_for_block_state(state: BlockState) -> int | None:
    definition = BLOCKS.get_by_state(state)
    if definition is None or definition.state == AIR:
        return None
    return definition.item_id
