"""Adapter between MCP Tool definitions/results and an OpenAI-compatible LLM API.

Important idea: MCP and LLM Function Calling are different interfaces.
- MCP client receives Tool objects from the MCP server.
- The LLM API expects its own `tools=[...]` schema format.
- This adapter converts between them.
"""

from __future__ import annotations

import json
from typing import Any


def mcp_tool_to_openai(tool: Any) -> dict[str, Any]:
    """Convert one discovered MCP Tool into OpenAI-compatible function schema."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        },
    }


def mcp_result_to_text(result: Any) -> str:
    """Serialize an MCP CallToolResult into text that can be returned to the LLM."""
    if result.structured_content is not None:
        return json.dumps(result.structured_content, ensure_ascii=False)

    text_parts: list[str] = []
    for block in result.content:
        text = getattr(block, "text", None)
        if text is not None:
            text_parts.append(text)

    if text_parts:
        return "\n".join(text_parts)

    return json.dumps(
        {"is_error": bool(result.is_error), "content": str(result.content)},
        ensure_ascii=False,
    )
