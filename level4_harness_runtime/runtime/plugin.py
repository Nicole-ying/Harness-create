"""Minimal plugin lifecycle with reversible registrations.

The purpose is educational: the Harness core exposes seams, while plugins add
capabilities beside it. Unmounting a plugin reverses the registrations it
created instead of patching the Agent loop.
"""

from __future__ import annotations

import inspect
from typing import Any, Protocol

from .events import EventBus
from .registries import ContextRegistry, ContextSection, ToolRegistry, ToolSpec
from .session import SessionLog


class Plugin(Protocol):
    name: str

    async def setup(self, ctx: "PluginContext") -> None: ...

    async def teardown(self) -> None: ...


class PluginContext:
    def __init__(
        self,
        *,
        tools: ToolRegistry,
        context: ContextRegistry,
        events: EventBus,
        session: SessionLog,
    ) -> None:
        self.tools = tools
        self.context = context
        self.events = events
        self.session = session
        self._disposers: list[Any] = []

    def register_tool(self, spec: ToolSpec) -> None:
        self._disposers.append(self.tools.register(spec))

    def register_context(self, section: ContextSection) -> None:
        self._disposers.append(self.context.register(section))

    def on_event(self, event_name: str, handler: Any) -> None:
        self._disposers.append(self.events.on(event_name, handler))

    async def dispose(self) -> None:
        for disposer in reversed(self._disposers):
            value = disposer()
            if inspect.isawaitable(value):
                await value
        self._disposers.clear()


class PluginManager:
    def __init__(
        self,
        *,
        tools: ToolRegistry,
        context: ContextRegistry,
        events: EventBus,
        session: SessionLog,
    ) -> None:
        self._shared = dict(tools=tools, context=context, events=events, session=session)
        self._mounted: list[tuple[Plugin, PluginContext]] = []

    async def mount(self, plugin: Plugin) -> None:
        if any(existing.name == plugin.name for existing, _ in self._mounted):
            raise ValueError(f"Plugin already mounted: {plugin.name}")

        ctx = PluginContext(**self._shared)
        try:
            await plugin.setup(ctx)
        except Exception:
            # A half-mounted plugin must not leak tools/context/event handlers.
            await ctx.dispose()
            teardown = getattr(plugin, "teardown", None)
            if teardown is not None:
                value = teardown()
                if inspect.isawaitable(value):
                    await value
            raise

        self._mounted.append((plugin, ctx))

    async def close(self) -> None:
        for plugin, ctx in reversed(self._mounted):
            await ctx.dispose()
            teardown = getattr(plugin, "teardown", None)
            if teardown is not None:
                value = teardown()
                if inspect.isawaitable(value):
                    await value
        self._mounted.clear()

    def names(self) -> list[str]:
        return [plugin.name for plugin, _ in self._mounted]
