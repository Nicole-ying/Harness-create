"""Ordinary Python data functions used behind the MCP server.

These functions do not know anything about MCP. This separation is deliberate:
Level 2 should make it obvious that MCP standardizes access to capabilities; it
does not replace the underlying business/data code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "mock_data"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Data file does not exist: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_training_feedback(iteration: int) -> dict[str, Any]:
    """Read the compact PPO training feedback for one reward iteration."""
    path = DATA_DIR / f"iter_{iteration:02d}_training_feedback.json"
    return _read_json(path)


def read_component_stats(iteration: int) -> dict[str, Any]:
    """Read reward-component statistics for one reward iteration."""
    path = DATA_DIR / f"iter_{iteration:02d}_component_stats.json"
    return _read_json(path)
