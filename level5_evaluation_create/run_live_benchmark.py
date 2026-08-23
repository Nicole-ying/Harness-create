"""Optional live benchmark using Level 4 AgentHarness + a real LLM provider.

This script intentionally reuses the Level 4 Runtime instead of copying it.
It runs the same user task under several capability variants, writes session
traces, and evaluates them with the same deterministic Level 5 evaluator.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from contracts import find_case, load_cases
from session_eval import evaluate_session, load_events


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
LEVEL4 = REPO_ROOT / "level4_harness_runtime"
sys.path.insert(0, str(LEVEL4))

from llm_client import LLMClient, load_llm_config  # noqa: E402
from plugins import MCPToolsPlugin, MemoryPlugin, SkillPlugin, TracePlugin  # noqa: E402
from runtime import AgentHarness  # noqa: E402


BASE_PROMPT = """你是强化学习奖励函数诊断 Agent。
当前实验事实必须通过可用 Tool 获取，不要猜本地文件内容。
如果 Skill Catalog 存在明显相关方法，可以调用 load_skill。
历史 memory 只能作为参考，不得当作当前 run 的事实。
区分 observation、diagnosis、intervention hypothesis 和 validation plan。
不要编造训练提升数字。
"""


async def run_variant(variant: str, user_request: str) -> Path:
    llm = LLMClient(load_llm_config())
    output = HERE / "runs" / "live" / f"bw_proxy_leakage__{variant}.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    async with AgentHarness(
        llm=llm,
        base_prompt=BASE_PROMPT,
        max_steps=8,
        session_path=output,
    ) as harness:
        # Every live variant gets external evidence tools.
        await harness.mount(MCPToolsPlugin(LEVEL4 / "mcp_server.py"))

        if variant in {"skills", "full"}:
            await harness.mount(SkillPlugin(LEVEL4 / "skills"))

        if variant == "full":
            await harness.mount(
                MemoryPlugin(LEVEL4 / "memory" / "episodes.jsonl", top_k=2)
            )
            await harness.mount(TracePlugin())

        await harness.run_turn(user_request)

    return output


async def main() -> None:
    cases = load_cases(HERE / "fixtures" / "cases.jsonl")
    case = find_case(cases, "bw_proxy_leakage")

    for variant in ["tools_only", "skills", "full"]:
        print(f"\n========== LIVE VARIANT: {variant} ==========")
        session_file = await run_variant(variant, case.user_request)
        metrics = evaluate_session(
            case,
            load_events(session_file),
            variant=variant,
        )
        print(metrics.model_dump_json(indent=2))

    print(
        "\nRun each variant multiple times/seeds before drawing conclusions. "
        "A single live run is a smoke test, not an ablation result."
    )


if __name__ == "__main__":
    asyncio.run(main())
