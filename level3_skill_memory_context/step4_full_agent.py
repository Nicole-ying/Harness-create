"""Level 3D: full teaching integration.

Pipeline:
User -> LLM evidence collector -> MCP tools -> Working Memory
     -> Skill catalog (metadata only) -> LLM Skill Router
     -> load ONE SKILL.md -> relevant Episodic Memory
     -> Context Builder -> final LLM diagnosis

This is still explicit application code, not a reusable Harness. Level 4 will
extract these responsibilities into Runtime/Harness components.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import Client, StdioServerParameters, stdio_client

from context_builder import build_context, context_report
from llm_client import LLMClient, load_llm_config
from mcp_adapter import mcp_result_to_text, mcp_tool_to_openai
from memory import EpisodicMemory, WorkingMemory
from skill_loader import catalog_text, discover_skills, load_skill


HERE = Path(__file__).resolve().parent
SERVER_FILE = HERE / "mcp_server.py"
MAX_TOOL_ROUNDS = 6

EVIDENCE_SYSTEM = """你是强化学习实验 Evidence Collector。
你不能直接读取本地文件。必须通过提供的工具获取实验事实。
先读取 training feedback；如果不足以描述 reward 结构，再读取 component stats。
你这一阶段只负责收集证据，不做最终 reward 修改。证据足够时停止调用工具并简短说明收集完成。
"""

ROUTER_SYSTEM = """你是 Reward-Design Skill Router。
从提供的 Skill Catalog 中选择一个最匹配当前证据的 Skill。
Catalog 只包含 name + description，这是故意的；不要假装读过未加载的 SKILL.md。
只返回 JSON：{"skill_name":"...","reason":"..."}。
"""

FINAL_SYSTEM = """你是强化学习奖励设计诊断 Agent。
Host 已经为你构造了当前 Context，其中包含当前证据、一个已激活 Skill、相关 Episodic Memory 和 Working Memory notes。
请严格区分：观察事实、诊断假设、Skill 提供的方法、历史 episode 的参考价值。
不要把历史 episode 当成当前实验事实，也不要把 Skill 当成已经验证成功的结论。
最终用中文输出：1) 观察事实 2) 诊断假设 3) Skill 为什么适用/哪里仍不确定 4) 下一步应检查的证据 5) 抽象修改方向。不要编造具体实验提升数字。
"""


def assistant_message_with_tool_calls(message: Any) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": message.content,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in (message.tool_calls or [])
        ],
    }


async def collect_evidence(
    *,
    llm: LLMClient,
    mcp_client: Client,
    llm_tools: list[dict[str, Any]],
    working: WorkingMemory,
) -> None:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": EVIDENCE_SYSTEM},
        {"role": "user", "content": working.user_request},
    ]

    for round_index in range(1, MAX_TOOL_ROUNDS + 1):
        response = llm.completion(
            messages,
            tools=llm_tools,
            tool_choice="auto",
        )
        message = response.choices[0].message

        print(f"\n========== EVIDENCE ROUND {round_index} ==========")
        if not message.tool_calls:
            print(message.content)
            return

        messages.append(assistant_message_with_tool_calls(message))

        for call in message.tool_calls:
            try:
                arguments = json.loads(call.function.arguments)
                result = await mcp_client.call_tool(call.function.name, arguments)
                text = mcp_result_to_text(result)
                if result.is_error:
                    text = json.dumps(
                        {"mcp_tool_error": True, "result": text},
                        ensure_ascii=False,
                    )
            except Exception as exc:
                text = json.dumps(
                    {"mcp_client_error": f"{type(exc).__name__}: {exc}"},
                    ensure_ascii=False,
                )

            print(f"[MCP] {call.function.name} -> {text}")
            working.add_evidence(f"{call.function.name}: {text}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": text,
                }
            )

    raise RuntimeError("Evidence collector exceeded MAX_TOOL_ROUNDS")


def select_skill(
    *,
    llm: LLMClient,
    working: WorkingMemory,
    recent_episodes: list[dict[str, Any]],
) -> tuple[str, str]:
    skills = discover_skills()
    allowed_names = {s.name for s in skills}

    user_prompt = f"""Current evidence:
{json.dumps(working.evidence, ensure_ascii=False, indent=2)}

Relevant episodic memory (history, not current facts):
{json.dumps(recent_episodes, ensure_ascii=False, indent=2)}

Skill Catalog (metadata only):
{catalog_text(skills)}
"""

    response = llm.completion(
        [
            {"role": "system", "content": ROUTER_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    decision = json.loads(response.choices[0].message.content or "{}")
    name = str(decision.get("skill_name", ""))
    reason = str(decision.get("reason", ""))

    if name not in allowed_names:
        raise ValueError(f"Unknown Skill selected by router: {name!r}")
    return name, reason


async def main() -> None:
    llm = LLMClient(load_llm_config())
    working = WorkingMemory(
        user_request="请分析 BipedalWalker reward iteration 1 为什么训练失败，并给出下一步抽象修改方向。"
    )
    episodic = EpisodicMemory()
    recent_episodes = episodic.recent(task="BipedalWalker", limit=1)

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_FILE)],
    )

    async with Client(stdio_client(server)) as mcp_client:
        listed = await mcp_client.list_tools()
        llm_tools = [mcp_tool_to_openai(tool) for tool in listed.tools]

        print("========== MCP TOOLS ==========")
        for tool in listed.tools:
            print(f"- {tool.name}: {tool.description}")

        await collect_evidence(
            llm=llm,
            mcp_client=mcp_client,
            llm_tools=llm_tools,
            working=working,
        )

    if not working.evidence:
        raise RuntimeError("No evidence was collected; cannot route a Skill safely.")

    skill_name, routing_reason = select_skill(
        llm=llm,
        working=working,
        recent_episodes=recent_episodes,
    )
    working.selected_skill = skill_name
    working.notes.append(f"Skill router reason: {routing_reason}")

    # Progressive disclosure happens HERE: only now is the full body loaded.
    skill = load_skill(skill_name)

    context = build_context(
        working=working,
        episodes=recent_episodes,
        skill=skill,
    )

    print("\n========== SELECTED SKILL ==========")
    print(skill_name)
    print("reason:", routing_reason)

    print("\n========== CONTEXT REPORT ==========")
    print(context_report(context))

    final_response = llm.completion(
        [
            {"role": "system", "content": FINAL_SYSTEM},
            {"role": "user", "content": context},
        ],
        temperature=0.2,
    )

    print("\n========== FINAL DIAGNOSIS ==========")
    print(final_response.choices[0].message.content)

    print("\nMemory note: this demo does NOT automatically persist the final answer as a new episode.")


if __name__ == "__main__":
    asyncio.run(main())
