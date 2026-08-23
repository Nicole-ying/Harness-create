"""Read-only MCP server used by the MCPToolsPlugin."""

from __future__ import annotations

from mcp.server import MCPServer

from backend import read_component_stats, read_training_feedback


mcp = MCPServer("CREATE Reward Analysis")


@mcp.tool()
def get_training_feedback(iteration: int):
    """Read PPO evaluation feedback for one reward iteration."""
    return read_training_feedback(iteration)


@mcp.tool()
def get_component_stats(iteration: int):
    """Read reward-component statistics for one reward iteration."""
    return read_component_stats(iteration)


if __name__ == "__main__":
    mcp.run()
