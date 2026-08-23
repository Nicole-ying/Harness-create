"""Level 4B: mount a Skill plugin without changing the Agent loop.

A scripted fake model first requests load_skill, then returns a final answer.
No API key is needed.  Focus on registration -> execution -> disposal.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from plugins import SkillPlugin, TracePlugin
from runtime import AgentHarness


HERE = Path(__file__).resolve().parent
SKILLS_DIR = HERE / "skills"


class ScriptedLLM:
    def __init__(self) -> None:
        self.calls = 0

    def completion(self, *, messages, tools=None, tool_choice=None):
        self.calls += 1
        if self.calls == 1:
            call = SimpleNamespace(
                id="call_skill_1",
                function=SimpleNamespace(
                    name="load_skill",
                    arguments='{"skill_name":"gate-proxy-by-validity"}',
                ),
            )
            message = SimpleNamespace(content=None, tool_calls=[call])
            return SimpleNamespace(
                choices=[SimpleNamespace(message=message, finish_reason="tool_calls")]
            )

        message = SimpleNamespace(
            content=(
                "The Skill was loaded through a plugin-contributed Tool. "
                "The Harness core did not contain reward-design logic."
            ),
            tool_calls=None,
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message, finish_reason="stop")]
        )


async def main() -> None:
    harness = AgentHarness(
        llm=ScriptedLLM(),
        base_prompt="You are a teaching Agent. Use relevant Skills when useful.",
        max_steps=4,
    )

    print("Before plugins:")
    print("  tools:", harness.tools.names())
    print("  context sections:", harness.context.names())

    await harness.mount(SkillPlugin(SKILLS_DIR))
    await harness.mount(TracePlugin())

    print("\nAfter mounting plugins:")
    print("  plugins:", harness.plugins.names())
    print("  tools:", harness.tools.names())
    print("  context sections:", harness.context.names())

    answer = await harness.run_turn(
        "A dominant proxy may remain rewarding in failure states. Choose a method."
    )
    print("\n========== ANSWER ==========")
    print(answer)

    await harness.close()

    print("\nAfter plugin teardown:")
    print("  tools:", harness.tools.names())
    print("  context sections:", harness.context.names())


if __name__ == "__main__":
    asyncio.run(main())
