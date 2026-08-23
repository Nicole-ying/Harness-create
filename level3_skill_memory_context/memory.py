"""Tiny Memory layer for Level 3.

WorkingMemory = mutable state for the current run.
EpisodicMemory = prior concrete attempts/outcomes loaded from JSONL.

A Skill is intentionally NOT stored here: Skills are reusable procedural knowledge,
while episodic memory records what actually happened in prior runs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_EPISODES_FILE = HERE / "memory" / "episodes.jsonl"


@dataclass
class WorkingMemory:
    user_request: str
    evidence: list[str] = field(default_factory=list)
    selected_skill: str | None = None
    notes: list[str] = field(default_factory=list)

    def add_evidence(self, text: str) -> None:
        self.evidence.append(text)

    def snapshot(self) -> dict[str, Any]:
        return {
            "user_request": self.user_request,
            "evidence": list(self.evidence),
            "selected_skill": self.selected_skill,
            "notes": list(self.notes),
        }


class EpisodicMemory:
    def __init__(self, path: Path = DEFAULT_EPISODES_FILE):
        self.path = path

    def load_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        episodes: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                episodes.append(json.loads(line))
        return episodes

    def recent(self, *, task: str | None = None, limit: int = 2) -> list[dict[str, Any]]:
        episodes = self.load_all()
        if task:
            episodes = [e for e in episodes if str(e.get("task", "")).lower() == task.lower()]
        return episodes[-limit:]

    def append(self, episode: dict[str, Any]) -> None:
        """Persist a new episode. Not called automatically in the teaching scripts."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(episode, ensure_ascii=False) + "\n")
