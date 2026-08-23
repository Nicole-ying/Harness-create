"""Plain Python experiment backend.  It knows nothing about MCP or Harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "mock_data"


def _load(name: str) -> dict[str, Any]:
    path = DATA_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def read_training_feedback(iteration: int) -> dict[str, Any]:
    if iteration != 1:
        raise ValueError("Teaching dataset currently contains only iteration=1")
    return _load("iter_01_training_feedback.json")


def read_component_stats(iteration: int) -> dict[str, Any]:
    if iteration != 1:
        raise ValueError("Teaching dataset currently contains only iteration=1")
    return _load("iter_01_component_stats.json")
