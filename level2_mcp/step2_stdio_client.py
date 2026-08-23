"""Level 2B: connect to the same MCP server over stdio.

Now the server is a separate subprocess. The client launches mcp_server.py and
speaks MCP over the child's stdin/stdout.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters, stdio_client


HERE = Path(__file__).resolve().parent
SERVER_FILE = HERE / "mcp_server.py"


async def main() -> None:
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_FILE)],
    )

    # StdioServerParameters only describes how to launch the server.
    # stdio_client(server) creates the actual MCP transport.
    transport = stdio_client(server)

    async with Client(transport) as client:
        print("========== STDIO MCP CONNECTION ==========")
        print("protocol_version:", client.protocol_version)
        print("server_info:", client.server_info)

        listed = await client.list_tools()

        print("\n========== SERVER TOOL CATALOG ==========")
        for tool in listed.tools:
            print(f"{tool.name}: {tool.description}")
            print("schema:", tool.input_schema)

        result = await client.call_tool(
            "get_component_stats",
            {"iteration": 1},
        )

        print("\n========== MCP tools/call RESULT ==========")
        print("is_error:", result.is_error)
        print("structured_content:", result.structured_content)
        print("content:", result.content)


if __name__ == "__main__":
    asyncio.run(main())
