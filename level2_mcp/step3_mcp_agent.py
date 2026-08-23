"""Level 2C: an LLM Agent whose Tools come from an MCP server.

Flow:
MCP server -> tools/list -> adapter -> LLM tool schemas -> model tool_call
-> MCP client tools/call -> tool result -> LLM -> final answer

The LLM does NOT speak MCP directly. The host/runtime owns the MCP client.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import Client, StdioServerParameters, stdio_client

from llm_client import ToolCallingLLMClient, load_llm_config
from mcp_adapter import mcp_result_to_text, mcp_tool_to_openai


HERE = Path(__file__).resolve().parent
SERVER_FILE = HERE / "mcp_server.py"
MAX_AGENT_ROUNDS = 6

SYSTEM_PROMPT = """你是一名强化学习奖励函数诊断 Agent。

你不能直接访问实验文件。所有外部实验数据都必须通过可用工具获取。
先读取训练反馈；如果仅凭训练反馈不足以解释 reward 结构问题，再读取组件统计。
不要虚构工具没有返回的数据。证据足够时停止调用工具并给出最终回答。

最终回答包含：
1. 观察事实
2. 诊断假设
3. 支持证据
4. 下一步建议
"""


def assistant_message_with_tool_calls(message: Any) -> dict[str, Any]:
    """Preserve the assistant tool-call message in conversation history."""
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


async def main() -> None:
    llm_config = load_llm_config()
    llm = ToolCallingLLMClient(llm_config)

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_FILE)],
    )

    async with Client(stdio_client(server)) as mcp_client:
        # 1. Discover tools from the MCP server at runtime.
        listed = await mcp_client.list_tools()
        llm_tools = [mcp_tool_to_openai(tool) for tool in listed.tools]

        print("========== MCP TOOLS DISCOVERED ==========")
        for tool in listed.tools:
            print(f"- {tool.name}: {tool.description}")

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "请分析 BipedalWalker reward iteration 1 为什么训练失败。",
            },
        ]

        for round_index in range(1, MAX_AGENT_ROUNDS + 1):
            # 2. LLM sees schemas converted from MCP tools.
            response = llm.completion(
                messages=messages,
                tools=llm_tools,
                tool_choice="auto",
            )
            choice = response.choices[0]
            message = choice.message

            print(f"\n========== AGENT ROUND {round_index} ==========")
            print("finish_reason:", choice.finish_reason)

            # 3. No tool call means the model decided to answer.
            if not message.tool_calls:
                print("\n========== FINAL ANSWER ==========")
                print(message.content)
                return

            messages.append(assistant_message_with_tool_calls(message))

            # 4. Host/runtime routes each model request through MCP.
            for call in message.tool_calls:
                print("\n[LLM TOOL CALL]")
                print("name:", call.function.name)
                print("arguments:", call.function.arguments)

                try:
                    arguments = json.loads(call.function.arguments)
                    result = await mcp_client.call_tool(
                        call.function.name,
                        arguments,
                    )
                    tool_text = mcp_result_to_text(result)
                    if result.is_error:
                        tool_text = json.dumps(
                            {"mcp_tool_error": True, "result": tool_text},
                            ensure_ascii=False,
                        )
                except Exception as exc:
                    tool_text = json.dumps(
                        {"mcp_client_error": f"{type(exc).__name__}: {exc}"},
                        ensure_ascii=False,
                    )

                print("\n[MCP TOOL RESULT]")
                print(tool_text)

                # 5. Return the observation to the LLM using the original tool_call_id.
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": tool_text,
                    }
                )

    raise RuntimeError(
        f"Agent exceeded {MAX_AGENT_ROUNDS} rounds without a final answer."
    )


if __name__ == "__main__":
    asyncio.run(main())
