"""Level 1 tools: ordinary Python functions + model-facing schemas.

Key idea:
- Python function: the REAL executable capability.
- Tool schema: a DESCRIPTION sent to the LLM so it can decide when/how to call it.

The LLM never executes these functions by itself. Our runtime code does that.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "mock_data"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Teaching data not found: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_training_feedback(iteration: int) -> dict[str, Any]:
    """Read score / episode-length / early-fall feedback for one iteration."""
    path = DATA_DIR / f"iter_{iteration:02d}_training_feedback.json"
    return _read_json(path)


def read_component_stats(iteration: int) -> dict[str, Any]:
    """Read per-component reward statistics for one iteration."""
    path = DATA_DIR / f"iter_{iteration:02d}_component_stats.json"
    return _read_json(path)


# These schemas are sent to the LLM. They are NOT Python functions.
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_training_feedback",
            "description": (
                "读取某一轮 PPO 的训练反馈，包括 mean_eval_reward、"
                "mean_episode_length 和 early_falls。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "iteration": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "要读取的奖励函数迭代轮次，例如 1。",
                    }
                },
                "required": ["iteration"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_component_stats",
            "description": (
                "读取某一轮 reward components 的统计信息，包括 magnitude_share "
                "和 active_rate，用于判断奖励组件是否支配、失活或可能被利用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "iteration": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "要读取的奖励函数迭代轮次，例如 1。",
                    }
                },
                "required": ["iteration"],
                "additionalProperties": False,
            },
        },
    },
]


TOOL_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "read_training_feedback": read_training_feedback,
    "read_component_stats": read_component_stats,
}


def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    """Validate a model-requested tool call, execute a whitelist function, return JSON.

    Never use eval() on model-generated text. Treat tool arguments as untrusted input.
    """

    if name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unknown tool: {name}")

    if set(arguments) != {"iteration"}:
        raise ValueError(f"Unexpected arguments for {name}: {sorted(arguments)}")

    iteration = arguments["iteration"]
    if not isinstance(iteration, int) or isinstance(iteration, bool) or iteration < 1:
        raise ValueError("iteration must be a positive integer")

    result = TOOL_FUNCTIONS[name](iteration=iteration)
    return json.dumps(result, ensure_ascii=False, indent=2)
