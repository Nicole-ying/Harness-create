"""Level 1C: the first general Agent Loop.

The model can choose between two tools or stop and answer.
The runtime repeats:

model -> tool call? -> execute -> append observation -> model -> ... -> final answer

This is still a tiny local agent. There is no MCP, Skill, Memory, RAG, or Harness yet.
"""

from __future__ import annotations

import json

from llm_client import ToolCallingLLMClient, assistant_tool_message, load_llm_config
from tools import TOOL_SCHEMAS, execute_tool


SYSTEM_PROMPT = """你是一名强化学习奖励函数诊断 Agent。

规则：
1. 用户不会把实验数据直接写进 prompt；需要证据时使用工具读取。
2. 不要虚构工具没有返回的数据。
3. 先建立事实，再形成诊断。
4. 如果 training feedback 只能说明“训练失败”，但不足以判断 reward 结构原因，继续读取 component stats。
5. 当证据足够时停止调用工具，直接给出最终回答。

最终回答用中文，包含：观察、诊断假设、证据、下一步建议。
"""

MAX_AGENT_ROUNDS = 6


def main() -> None:
    config = load_llm_config()
    client = ToolCallingLLMClient(config)

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "请分析 BipedalWalker reward iteration 1 为什么训练失败。",
        },
    ]

    for round_index in range(1, MAX_AGENT_ROUNDS + 1):
        response = client.completion(
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        choice = response.choices[0]
        message = choice.message

        print(f"\n========== AGENT ROUND {round_index} ==========")
        print("finish_reason:", choice.finish_reason)

        # If there is no tool call, the model has decided it has enough evidence.
        if not message.tool_calls:
            print("\n========== FINAL ANSWER ==========")
            print(message.content)
            return

        # Preserve the assistant's requested tool calls in conversation history.
        messages.append(assistant_tool_message(message))

        for call in message.tool_calls:
            print("\n[MODEL DECISION]")
            print("tool_call_id:", call.id)
            print("tool name:   ", call.function.name)
            print("arguments:   ", call.function.arguments)

            try:
                arguments = json.loads(call.function.arguments)
                result = execute_tool(call.function.name, arguments)
            except Exception as exc:
                result = json.dumps(
                    {"error": f"{type(exc).__name__}: {exc}"},
                    ensure_ascii=False,
                )

            print("\n[TOOL OBSERVATION]")
            print(result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )

    raise RuntimeError(
        f"Agent exceeded {MAX_AGENT_ROUNDS} rounds without producing a final answer."
    )


if __name__ == "__main__":
    main()
