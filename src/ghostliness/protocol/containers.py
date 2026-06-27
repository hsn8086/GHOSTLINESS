from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass, field
from typing import Any

from ghostliness.protocol.registry import PacketType


@dataclass(slots=True)
class PacketContainer:
    packet_type: PacketType
    fields: MutableMapping[str, Any] = field(default_factory=dict)
    raw_payload: bytes = b""
    cancelled: bool = False

    def get(self, name: str, default: Any = None) -> Any:
        return self.fields.get(name, default)

    def set(self, name: str, value: Any) -> None:
        self.fields[name] = value

    @property
    def name(self) -> str:
        return self.packet_type.name
