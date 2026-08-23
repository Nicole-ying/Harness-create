"""Level 1B: make one real LLM Tool Call, execute it, then return the result.

This step FORCES one tool call so you can observe the protocol clearly.
It is not yet a general Agent Loop.
"""

from __future__ import annotations

import json

from llm_client import ToolCallingLLMClient, assistant_tool_message, load_llm_config
from tools import TOOL_SCHEMAS, execute_tool


SYSTEM_PROMPT = """你是一名强化学习实验分析助手。
在给出诊断前先读取训练反馈。不要假装自己能直接读取文件；需要数据时必须通过工具获得。
工具结果返回后，再根据证据给出简短诊断，并区分观察事实和假设。
"""


def main() -> None:
    config = load_llm_config()
    client = ToolCallingLLMClient(config)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "请分析 BipedalWalker 的 reward iteration 1 为什么训练失败。",
        },
    ]

    # Step A: send a tool schema to the model.
    # We intentionally force a tool call in this teaching step.
    first_response = client.completion(
        messages=messages,
        tools=[TOOL_SCHEMAS[0]],
        tool_choice="required",
    )

    first_choice = first_response.choices[0]
    message = first_choice.message

    print("========== FIRST MODEL RESPONSE ==========")
    print("finish_reason:", first_choice.finish_reason)
    print("content:", message.content)
    print("tool_calls:", message.tool_calls)

    if not message.tool_calls:
        raise RuntimeError("Expected a tool call, but the model returned none.")

    # IMPORTANT: preserve the assistant message that requested the tool.
    messages.append(assistant_tool_message(message))

    for call in message.tool_calls:
        print("\n========== MODEL REQUESTED A TOOL ==========")
        print("tool_call_id:", call.id)
        print("tool name:   ", call.function.name)
        print("raw arguments:", call.function.arguments)

        try:
            arguments = json.loads(call.function.arguments)
            tool_result = execute_tool(call.function.name, arguments)
        except Exception as exc:
            # Tool arguments come from the model, so failures are returned as data.
            tool_result = json.dumps(
                {"error": f"{type(exc).__name__}: {exc}"},
                ensure_ascii=False,
            )

        print("\n========== PYTHON EXECUTED THE TOOL ==========")
        print(tool_result)

        # The tool_call_id connects this result to the exact call requested above.
        messages.append(
            {
                "role": "tool",
                "tool_call_id": call.id,
                "content": tool_result,
            }
        )

    # Step B: send the tool result back to the model for a final answer.
    second_response = client.completion(messages=messages)
    second_choice = second_response.choices[0]

    print("\n========== SECOND MODEL RESPONSE ==========")
    print("finish_reason:", second_choice.finish_reason)
    print(second_choice.message.content)


if __name__ == "__main__":
    main()
