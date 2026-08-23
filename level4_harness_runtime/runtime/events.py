"""Tiny async event bus used as Harness extension points.

DeepSeek Harness has a much richer typed event system.  This teaching version
keeps the idea small: plugins can subscribe to lifecycle events without
changing the Agent loop itself.
"""

from __future__ import annotations

import inspect
from collections import defaultdict
from collections.abc import Callable
from typing import Any


EventHandler = Callable[[dict[str, Any]], Any]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def on(self, event_name: str, handler: EventHandler) -> Callable[[], None]:
        """Register a handler and return a disposer."""
        self._handlers[event_name].append(handler)

        def dispose() -> None:
            handlers = self._handlers.get(event_name, [])
            if handler in handlers:
                handlers.remove(handler)

        return dispose

    async def emit(self, event_name: str, payload: dict[str, Any]) -> None:
        """Run listeners in registration order.

        Payload is intentionally mutable.  A teaching plugin may inspect or
        rewrite fields such as ``messages`` before the model request.
        """
        for handler in list(self._handlers.get(event_name, [])):
            result = handler(payload)
            if inspect.isawaitable(result):
                await result
