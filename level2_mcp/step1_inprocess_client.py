"""Level 2A: learn MCP concepts without transport complexity.

The MCP Client connects directly to the MCPServer object in the same Python process.
This lets you inspect tools/list and tools/call before learning stdio.
"""

from __future__ import annotations

import asyncio

from mcp import Client

from mcp_server import mcp


async def main() -> None:
    async with Client(mcp) as client:
        print("========== MCP CONNECTION ==========")
        print("protocol_version:", client.protocol_version)
        print("server_info:", client.server_info)

        listed = await client.list_tools()

        print("\n========== TOOLS DISCOVERED ==========")
        for tool in listed.tools:
            print("name:", tool.name)
            print("description:", tool.description)
            print("input_schema:", tool.input_schema)
            print("---")

        result = await client.call_tool(
            "get_training_feedback",
            {"iteration": 1},
        )

        print("\n========== TOOL RESULT ==========")
        print("is_error:", result.is_error)
        print("structured_content:", result.structured_content)
        print("content:", result.content)


if __name__ == "__main__":
    asyncio.run(main())
