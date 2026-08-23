"""Level 2 MCP server: expose CREATE reward-analysis data as MCP Tools.

Current MCP Python SDK v2 uses MCPServer (older tutorials may still show FastMCP).
The default transport of mcp.run() is stdio, which is ideal for learning/local hosts.
"""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from backend import read_component_stats, read_training_feedback


mcp = MCPServer(
    "CREATE Reward Analysis",
    version="0.1.0",
    instructions=(
        "Read-only tools for inspecting PPO reward-design experiments. "
        "Use training feedback first, then component statistics when deeper reward evidence is needed."
    ),
)


@mcp.tool()
def get_training_feedback(iteration: int) -> dict[str, Any]:
    """Read PPO evaluation feedback for one reward iteration."""
    return read_training_feedback(iteration)


@mcp.tool()
def get_component_stats(iteration: int) -> dict[str, Any]:
    """Read reward-component magnitude/activity statistics for one reward iteration."""
    return read_component_stats(iteration)


if __name__ == "__main__":
    # stdio is the default transport. A host/client launches this process and
    # exchanges MCP messages over stdin/stdout.
    mcp.run()
