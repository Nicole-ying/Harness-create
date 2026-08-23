"""Translate MCP tool definitions/results for an OpenAI-compatible LLM API."""

from __future__ import annotations

import json
from typing import Any


def mcp_tool_to_openai(tool: Any) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        },
    }


def mcp_result_to_text(result: Any) -> str:
    if getattr(result, "structured_content", None) is not None:
        return json.dumps(result.structured_content, ensure_ascii=False)

    parts: list[str] = []
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts)
