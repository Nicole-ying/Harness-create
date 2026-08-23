"""Swappable capability registries for the teaching Harness."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from .session import SessionLog


ToolExecutor = Callable[[dict[str, Any]], Awaitable[str] | str]
ContextProvider = Callable[[SessionLog], Awaitable[str] | str]


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    executor: ToolExecutor

    def as_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> Callable[[], None]:
        if spec.name in self._tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        self._tools[spec.name] = spec

        def dispose() -> None:
            self._tools.pop(spec.name, None)

        return dispose

    def schemas(self) -> list[dict[str, Any]]:
        return [spec.as_openai_tool() for spec in self._tools.values()]

    def names(self) -> list[str]:
        return list(self._tools)

    async def execute(self, name: str, arguments: dict[str, Any]) -> str:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        result = self._tools[name].executor(arguments)
        if inspect.isawaitable(result):
            result = await result
        return str(result)


@dataclass
class ContextSection:
    name: str
    provider: ContextProvider
    priority: int = 100


class ContextRegistry:
    def __init__(self, base_prompt: str) -> None:
        self.base_prompt = base_prompt.strip()
        self._sections: dict[str, ContextSection] = {}

    def register(self, section: ContextSection) -> Callable[[], None]:
        if section.name in self._sections:
            raise ValueError(f"Context section already registered: {section.name}")
        self._sections[section.name] = section

        def dispose() -> None:
            self._sections.pop(section.name, None)

        return dispose

    async def build(self, session: SessionLog) -> str:
        parts = [self.base_prompt]
        for section in sorted(self._sections.values(), key=lambda x: x.priority):
            value = section.provider(session)
            if inspect.isawaitable(value):
                value = await value
            text = str(value).strip()
            if text:
                parts.append(f"## {section.name}\n{text}")
        return "\n\n".join(parts)

    def names(self) -> list[str]:
        return list(self._sections)
