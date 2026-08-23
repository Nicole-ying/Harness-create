"""No-API smoke test for Level 4 runtime, plugins, session, and Skills."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from plugins import SkillPlugin
from runtime import AgentHarness
from skill_store import discover_skills


HERE = Path(__file__).resolve().parent


class FakeLLM:
    def completion(self, *, messages, tools=None, tool_choice=None):
        message = SimpleNamespace(content="ok", tool_calls=None)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message, finish_reason="stop")]
        )


async def run() -> None:
    skills = discover_skills(HERE / "skills")
    assert {s.name for s in skills} == {
        "gate-proxy-by-validity",
        "densify-sparse-outcome",
        "calibrate-rare-risk-penalty",
    }

    harness = AgentHarness(llm=FakeLLM(), base_prompt="test", max_steps=2)
    assert harness.tools.names() == []
    assert harness.context.names() == []

    await harness.mount(SkillPlugin(HERE / "skills"))
    assert "load_skill" in harness.tools.names()
    assert "Skill Catalog" in harness.context.names()

    answer = await harness.run_turn("smoke test")
    assert answer == "ok"
    assert harness.session.model_context_snapshots()
    assert any(e["type"] == "turn/end" for e in harness.session.events)

    await harness.close()
    assert "load_skill" not in harness.tools.names()
    assert "Skill Catalog" not in harness.context.names()

    print("Level 4 Harness smoke test passed.")


if __name__ == "__main__":
    asyncio.run(run())
