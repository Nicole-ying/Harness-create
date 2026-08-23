"""Level 1 LLM client.

Compared with Level 0, this client returns the FULL ChatCompletion response instead of
immediately extracting message.content. Tool Calling needs access to:

- choices[0].finish_reason
- choices[0].message.tool_calls
- each tool call's id / function.name / function.arguments

The client still does NOT execute tools. It only talks to the model API.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


@dataclass
class LLMConfig:
    provider: str
    api_key: str
    base_url: str
    model: str


def load_llm_config() -> LLMConfig:
    load_dotenv()
    provider = os.getenv("PROVIDER", "deepseek").strip().lower()

    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            raise RuntimeError("Missing DEEPSEEK_API_KEY. Copy .env.example to .env and fill it in.")
        return LLMConfig(
            provider="deepseek",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        )

    if provider == "openai_compatible":
        api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY", "")
        base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "")
        model = os.getenv("OPENAI_COMPATIBLE_MODEL", "")
        if not api_key or not base_url or not model:
            raise RuntimeError(
                "OPENAI_COMPATIBLE_API_KEY, OPENAI_COMPATIBLE_BASE_URL, and "
                "OPENAI_COMPATIBLE_MODEL are all required."
            )
        return LLMConfig(provider, api_key, base_url, model)

    raise ValueError(f"Unsupported PROVIDER: {provider}")


class ToolCallingLLMClient:
    """Small wrapper around chat.completions.create()."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url)

    def completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        temperature: float = 0.2,
    ):
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if tools is not None:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice

        return self.client.chat.completions.create(**kwargs)


def assistant_tool_message(message) -> dict[str, Any]:
    """Convert one SDK assistant message into a plain dict that can be replayed.

    The important part is preserving tool_call.id. Later tool-result messages must use
    the same id so the model knows which requested call the result belongs to.
    """

    result: dict[str, Any] = {
        "role": "assistant",
        "content": message.content,
    }
    if message.tool_calls:
        result["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in message.tool_calls
        ]
    return result
