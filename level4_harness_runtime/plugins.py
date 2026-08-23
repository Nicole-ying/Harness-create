"""Capability plugins mounted beside the Harness core.

This is intentionally smaller than DeepSeek Harness/Cordis, but demonstrates the
same architectural lesson: the Agent loop should not know the implementation
details of MCP, Skills, Memory, or tracing.
"""

from __future__ import annotations

import json
import re
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp import Client, StdioServerParameters, stdio_client

from runtime import ContextSection, ToolSpec
from skill_store import catalog_text, discover_skills, load_skill


class TracePlugin:
    name = "trace"

    async def setup(self, ctx) -> None:
        def on_turn_start(payload: dict[str, Any]) -> None:
            print(f"\n[turn/start] {payload['user_text']}")

        def on_pre_step(payload: dict[str, Any]) -> None:
            print(
                f"[agent/pre-step] step={payload['step']} "
                f"messages={len(payload['messages'])} tools={len(payload['tools'])}"
            )

        def on_pre_tool(payload: dict[str, Any]) -> None:
            print(f"[tools/pre-execute] {payload['name']} {payload['arguments']}")

        def on_post_tool(payload: dict[str, Any]) -> None:
            preview = str(payload['result']).replace("\n", " ")[:180]
            print(f"[tools/post-execute] {payload['name']} -> {preview}")

        def on_turn_end(payload: dict[str, Any]) -> None:
            print(f"[turn/end] status={payload['status']}")

        ctx.on_event("turn/start", on_turn_start)
        ctx.on_event("agent/pre-step", on_pre_step)
        ctx.on_event("tools/pre-execute", on_pre_tool)
        ctx.on_event("tools/post-execute", on_post_tool)
        ctx.on_event("turn/end", on_turn_end)

    async def teardown(self) -> None:
        return None


class MCPToolsPlugin:
    """Discover MCP tools at mount time and register them into the Harness."""

    name = "mcp-tools"

    def __init__(self, server_file: Path) -> None:
        self.server_file = server_file
        self._stack: AsyncExitStack | None = None
        self.client: Client | None = None

    async def setup(self, ctx) -> None:
        self._stack = AsyncExitStack()
        server = StdioServerParameters(
            command=sys.executable,
            args=[str(self.server_file)],
        )
        self.client = await self._stack.enter_async_context(Client(stdio_client(server)))
        listed = await self.client.list_tools()

        for mcp_tool in listed.tools:
            tool_name = mcp_tool.name

            async def execute(arguments: dict[str, Any], *, name: str = tool_name) -> str:
                assert self.client is not None
                result = await self.client.call_tool(name, arguments)
                if result.structured_content is not None:
                    text = json.dumps(result.structured_content, ensure_ascii=False)
                else:
                    chunks: list[str] = []
                    for item in result.content:
                        value = getattr(item, "text", None)
                        chunks.append(value if value is not None else str(item))
                    text = "\n".join(chunks)
                if result.is_error:
                    return json.dumps(
                        {"mcp_tool_error": True, "result": text},
                        ensure_ascii=False,
                    )
                return text

            ctx.register_tool(
                ToolSpec(
                    name=mcp_tool.name,
                    description=mcp_tool.description or "MCP tool",
                    parameters=mcp_tool.input_schema,
                    executor=execute,
                )
            )

    async def teardown(self) -> None:
        if self._stack is not None:
            await self._stack.aclose()
            self._stack = None
            self.client = None


class SkillPlugin:
    """Expose Skill metadata as context and full Skill loading as a Tool."""

    name = "skills"

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir
        self.skills = []
        self.by_name = {}

    async def setup(self, ctx) -> None:
        self.skills = discover_skills(self.skills_dir)
        self.by_name = {skill.name: skill for skill in self.skills}

        ctx.register_context(
            ContextSection(
                name="Skill Catalog",
                priority=30,
                provider=lambda session: catalog_text(self.skills),
            )
        )

        async def load_skill_tool(arguments: dict[str, Any]) -> str:
            name = str(arguments.get("skill_name", ""))
            if name not in self.by_name:
                raise ValueError(
                    f"Unknown skill {name!r}; choose from {sorted(self.by_name)}"
                )
            skill = self.by_name[name]
            return (
                f"# Activated Skill: {skill.name}\n\n"
                f"Description: {skill.description}\n\n"
                f"{load_skill(skill)}"
            )

        ctx.register_tool(
            ToolSpec(
                name="load_skill",
                description=(
                    "Load the full instructions for one Skill from the visible Skill Catalog. "
                    "Use this only after selecting a relevant Skill by its metadata."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "enum": sorted(self.by_name),
                            "description": "Exact Skill name from the catalog",
                        }
                    },
                    "required": ["skill_name"],
                    "additionalProperties": False,
                },
                executor=load_skill_tool,
            )
        )

    async def teardown(self) -> None:
        return None


class MemoryPlugin:
    """Inject a tiny retrieval result from persistent episodic memory."""

    name = "episodic-memory"

    def __init__(self, memory_file: Path, top_k: int = 2) -> None:
        self.memory_file = memory_file
        self.top_k = top_k
        self.episodes: list[dict[str, Any]] = []

    async def setup(self, ctx) -> None:
        self.episodes = []
        for line in self.memory_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                self.episodes.append(json.loads(line))

        def memory_section(session) -> str:
            query = " ".join(
                [session.last_user_text(), session.recent_tool_text(limit=3)]
            ).lower()
            query_terms = set(re.findall(r"[a-zA-Z0-9_-]+", query))

            scored: list[tuple[int, dict[str, Any]]] = []
            for episode in self.episodes:
                haystack = " ".join(
                    [
                        str(episode.get("task_family", "")),
                        " ".join(episode.get("tags", [])),
                        str(episode.get("summary", "")),
                        str(episode.get("lesson", "")),
                    ]
                ).lower()
                score = sum(1 for term in query_terms if term and term in haystack)
                scored.append((score, episode))

            selected = [
                episode
                for score, episode in sorted(scored, key=lambda x: x[0], reverse=True)
                if score > 0
            ][: self.top_k]

            if not selected:
                return "No relevant historical episodes retrieved."

            lines = [
                "Historical episodes are references, NOT facts about the current run."
            ]
            for episode in selected:
                lines.append(
                    "- "
                    + json.dumps(
                        {
                            "id": episode.get("id"),
                            "summary": episode.get("summary"),
                            "outcome": episode.get("outcome"),
                            "lesson": episode.get("lesson"),
                            "provenance": episode.get("provenance"),
                        },
                        ensure_ascii=False,
                    )
                )
            return "\n".join(lines)

        ctx.register_context(
            ContextSection(
                name="Relevant Episodic Memory",
                priority=40,
                provider=memory_section,
            )
        )

    async def teardown(self) -> None:
        return None
