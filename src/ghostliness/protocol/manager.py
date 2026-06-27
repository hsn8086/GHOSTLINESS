from __future__ import annotations

import inspect
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import IntEnum

from ghostliness.protocol.containers import PacketContainer
from ghostliness.protocol.registry import PacketDirection, PacketState


class ListenerPriority(IntEnum):
    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


PacketListener = Callable[[PacketContainer], Awaitable[None] | None]


@dataclass(frozen=True, slots=True)
class PacketListenerHandle:
    state: PacketState | None
    direction: PacketDirection | None
    packet_name: str | None
    listener: PacketListener
    priority: ListenerPriority


class ProtocolManager:
    def __init__(self) -> None:
        self._listeners: dict[
            tuple[PacketState | None, PacketDirection | None, str | None],
            list[PacketListenerHandle],
        ] = defaultdict(list)

    def add_packet_listener(
        self,
        listener: PacketListener,
        *,
        state: PacketState | None = None,
        direction: PacketDirection | None = None,
        packet_name: str | None = None,
        priority: ListenerPriority = ListenerPriority.NORMAL,
    ) -> PacketListenerHandle:
        handle = PacketListenerHandle(
            state=state,
            direction=direction,
            packet_name=packet_name,
            listener=listener,
            priority=priority,
        )
        key = (state, direction, packet_name)
        self._listeners[key].append(handle)
        self._listeners[key].sort(key=lambda item: item.priority, reverse=True)
        return handle

    def remove_packet_listener(self, handle: PacketListenerHandle) -> None:
        key = (handle.state, handle.direction, handle.packet_name)
        listeners = self._listeners.get(key)
        if not listeners:
            return
        if handle in listeners:
            listeners.remove(handle)

    async def notify(self, packet: PacketContainer, direction: PacketDirection) -> PacketContainer:
        keys = (
            (packet.packet_type.state, direction, packet.packet_type.name),
            (packet.packet_type.state, direction, None),
            (None, direction, packet.packet_type.name),
            (None, direction, None),
        )
        seen: set[PacketListenerHandle] = set()
        handles: list[PacketListenerHandle] = []
        for key in keys:
            for handle in self._listeners.get(key, ()):
                if handle not in seen:
                    handles.append(handle)
                    seen.add(handle)
        handles.sort(key=lambda item: item.priority, reverse=True)
        for handle in handles:
            result = handle.listener(packet)
            if inspect.isawaitable(result):
                await result
            if packet.cancelled:
                break
        return packet
