"""Level 4A: observe the Harness lifecycle without any real API or Tool.

This step proves that Harness is more than a while-loop: it owns the turn/step
lifecycle, session log, context assembly, round limit, and plugin lifecycle.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from plugins import TracePlugin
from runtime import AgentHarness


class FakeLLM:
    def completion(self, *, messages, tools=None, tool_choice=None):
        message = SimpleNamespace(
            content="FakeLLM: I received one Harness-managed turn.",
            tool_calls=None,
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message, finish_reason="stop")]
        )


BASE_PROMPT = """You are a teaching Agent. Answer briefly.
The Harness, not the model, owns lifecycle and external capabilities.
"""


async def main() -> None:
    trace_path = Path(__file__).resolve().parent / "runs" / "step1_session.jsonl"
    if trace_path.exists():
        trace_path.unlink()

    async with AgentHarness(
        llm=FakeLLM(),
        base_prompt=BASE_PROMPT,
        max_steps=3,
        session_path=trace_path,
    ) as harness:
        await harness.mount(TracePlugin())
        answer = await harness.run_turn("Explain what the Harness controls in this turn.")

        print("\n========== ANSWER ==========")
        print(answer)

        print("\n========== APPEND-ONLY SESSION EVENTS ==========")
        for event in harness.session.events:
            print(event["seq"], event["type"])

        print("\nmodel/context snapshots:", len(harness.session.model_context_snapshots()))
        print("session file:", trace_path)


if __name__ == "__main__":
    asyncio.run(main())
