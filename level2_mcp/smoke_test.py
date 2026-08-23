"""No-LLM smoke test for Level 2.

Run this before configuring any API key. It verifies that the MCP server exposes
both read-only tools and that an MCP client can call them in-process.
"""

from __future__ import annotations

import asyncio

from mcp import Client

from mcp_server import mcp


async def main() -> None:
    async with Client(mcp) as client:
        listed = await client.list_tools()
        names = {tool.name for tool in listed.tools}

        expected = {"get_training_feedback", "get_component_stats"}
        assert expected.issubset(names), (expected, names)

        result = await client.call_tool(
            "get_training_feedback",
            {"iteration": 1},
        )
        assert not result.is_error
        assert result.structured_content is not None
        assert result.structured_content["iteration"] == 1

    print("Level 2 MCP smoke test passed.")


if __name__ == "__main__":
    asyncio.run(main())
