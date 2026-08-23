"""Plain Python experiment-data backend.

The functions here know nothing about LLMs, Skills, Memory, Context, or MCP.
They are deliberately boring business/data functions.
"""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "mock_data"


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def read_training_feedback(iteration: int) -> dict:
    return _read_json(DATA_DIR / f"iter_{iteration:02d}_training_feedback.json")


def read_component_stats(iteration: int) -> dict:
    return _read_json(DATA_DIR / f"iter_{iteration:02d}_component_stats.json")
