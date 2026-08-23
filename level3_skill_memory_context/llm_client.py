"""Small OpenAI-compatible client reused by Level 3.

Level 3 still does not introduce a Harness. The Host code explicitly owns
LLM calls, Skill routing, Memory loading, Context building, and MCP access.
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
            raise RuntimeError("Missing DEEPSEEK_API_KEY in .env")
        return LLMConfig(
            provider="deepseek",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        )

    if provider == "openai_compatible":
        api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY", "")
        base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "")
        model = os.getenv("OPENAI_COMPATIBLE_MODEL", "")
        if not api_key or not base_url or not model:
            raise RuntimeError("Missing OpenAI-compatible API settings in .env")
        return LLMConfig(provider, api_key, base_url, model)

    raise ValueError(f"Unsupported PROVIDER: {provider}")


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url)

    def completion(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.2,
    ):
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools is not None:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
        if response_format is not None:
            kwargs["response_format"] = response_format
        return self.client.chat.completions.create(**kwargs)
