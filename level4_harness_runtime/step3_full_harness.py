"""Level 4C: full teaching Harness with real LLM + MCP + Skill + Memory.

The core AgentHarness stays unchanged while plugins contribute:
- MCP tools
- Skill catalog + load_skill tool
- episodic-memory context
- lifecycle tracing
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from llm_client import LLMClient, load_llm_config
from plugins import MCPToolsPlugin, MemoryPlugin, SkillPlugin, TracePlugin
from runtime import AgentHarness


HERE = Path(__file__).resolve().parent
BASE_PROMPT = """你是强化学习奖励函数诊断 Agent。

工作原则：
1. 当前实验事实必须优先通过可用 Tool 获取，不要猜测本地文件内容。
2. 如果 Skill Catalog 中存在明显相关的方法，先调用 load_skill 加载完整 Skill，再使用其 procedure。
3. Historical episodic memory 只能作为参考，不得当成当前实验事实。
4. 区分 observation、diagnosis、intervention hypothesis、validation plan。
5. 不编造训练提升数字。

当证据充分时停止调用 Tool，并用中文给出：
- 观察事实
- 诊断假设
- 采用/不采用哪个 Skill 及原因
- 下一步验证证据
- 抽象修改方向
"""


async def main() -> None:
    llm = LLMClient(load_llm_config())
    session_file = HERE / "runs" / "full_harness_session.jsonl"
    if session_file.exists():
        session_file.unlink()

    async with AgentHarness(
        llm=llm,
        base_prompt=BASE_PROMPT,
        max_steps=8,
        session_path=session_file,
    ) as harness:
        # The Harness core does not import MCP/Skill/Memory implementations.
        await harness.mount(TracePlugin())
        await harness.mount(MCPToolsPlugin(HERE / "mcp_server.py"))
        await harness.mount(SkillPlugin(HERE / "skills"))
        await harness.mount(MemoryPlugin(HERE / "memory" / "episodes.jsonl", top_k=2))

        print("========== MOUNTED CAPABILITIES ==========")
        print("plugins:", harness.plugins.names())
        print("tools:", harness.tools.names())
        print("context sections:", harness.context.names())

        answer = await harness.run_turn(
            "请诊断 BipedalWalker reward iteration 1 为什么训练失败，并给出下一步奖励设计方向。"
        )

        print("\n========== FINAL ANSWER ==========")
        print(answer)

        print("\n========== SESSION ==========")
        print("events:", len(harness.session.events))
        print("model/context snapshots:", len(harness.session.model_context_snapshots()))
        print("saved to:", session_file)


if __name__ == "__main__":
    asyncio.run(main())
