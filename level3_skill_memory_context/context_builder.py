"""Explicit Context Builder for Level 3.

Context is what the model sees NOW. It is assembled from selected pieces of
Working Memory, Episodic Memory, evidence, and one activated Skill.

This file uses a character budget only to make trimming visible without adding
a provider-specific tokenizer dependency. Production systems should budget in
model tokens with the actual tokenizer/context limits.
"""

from __future__ import annotations

import json
from typing import Any

from memory import WorkingMemory
from skill_loader import SkillDefinition


DEFAULT_MAX_CHARS = 12000


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 20)] + "\n...[truncated]"


def build_context(
    *,
    working: WorkingMemory,
    episodes: list[dict[str, Any]],
    skill: SkillDefinition,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """Build only the context needed for the final diagnosis.

    Deliberately NOT included:
    - every Skill body in the library;
    - every past episode;
    - raw files the Agent never requested.
    """

    sections = [
        "# Current user request\n" + working.user_request,
        "# Current evidence\n" + ("\n\n".join(working.evidence) or "No evidence collected yet."),
        "# Selected procedural Skill\n"
        + f"Skill: {skill.metadata.name}\n\n{skill.instructions}",
        "# Relevant episodic memory\n"
        + (json.dumps(episodes, ensure_ascii=False, indent=2) if episodes else "No relevant prior episodes."),
        "# Working-memory notes\n" + ("\n".join(working.notes) or "No additional notes."),
    ]

    text = "\n\n".join(sections)
    return _clip(text, max_chars)


def context_report(context: str) -> str:
    return (
        f"Context characters: {len(context)}\n"
        "Note: this lesson uses characters only. Production code should measure model tokens."
    )
