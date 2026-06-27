from __future__ import annotations

import inspect
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

EventHandler = Callable[[Any], Awaitable[None] | None]


@dataclass(slots=True)
class EventSubscription:
    event_name: str
    handler: EventHandler
    priority: int = 0


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventSubscription]] = defaultdict(list)

    def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
        priority: int = 0,
    ) -> EventSubscription:
        subscription = EventSubscription(event_name=event_name, handler=handler, priority=priority)
        self._handlers[event_name].append(subscription)
        self._handlers[event_name].sort(key=lambda item: item.priority, reverse=True)
        return subscription

    def unsubscribe(self, subscription: EventSubscription) -> None:
        handlers = self._handlers.get(subscription.event_name)
        if not handlers:
            return
        if subscription in handlers:
            handlers.remove(subscription)

    async def publish(self, event_name: str, event: Any) -> None:
        for subscription in list(self._handlers.get(event_name, ())):
            result = subscription.handler(event)
            if inspect.isawaitable(result):
                await result
