"""Level 0: the thinnest possible LLM client.

This file deliberately does NOT contain tools, agents, memory, MCP, skills, or a harness.
Its only job is to send messages to one chat-completion API and return text.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI


@dataclass
class LLMConfig:
    provider: str
    api_key: str
    base_url: str
    model: str


def load_llm_config() -> LLMConfig:
    """Read provider settings from environment variables.

    Supported values:
    - PROVIDER=deepseek
    - PROVIDER=openai_compatible

    Most third-party GPT API platforms expose an OpenAI-compatible endpoint, so they
    can usually reuse the same OpenAI SDK by changing base_url, api_key, and model.
    """

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
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
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
        return LLMConfig(
            provider="openai_compatible",
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

    raise ValueError(f"Unsupported PROVIDER: {provider}")


class SimpleLLMClient:
    """A tiny wrapper around one chat-completion request."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url)

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
