"""Minimal Agent Skills loader with progressive disclosure."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SkillMeta:
    name: str
    description: str
    path: Path


def _parse_skill(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Missing YAML frontmatter: {path}")
    _, frontmatter, body = text.split("---", 2)
    meta = yaml.safe_load(frontmatter) or {}
    return meta, body.strip()


def discover_skills(root: Path) -> list[SkillMeta]:
    skills: list[SkillMeta] = []
    for path in sorted(root.glob("*/SKILL.md")):
        meta, _ = _parse_skill(path)
        name = str(meta.get("name", "")).strip()
        description = str(meta.get("description", "")).strip()
        if not name or not description:
            raise ValueError(f"Skill needs name + description: {path}")
        if path.parent.name != name:
            raise ValueError(f"Skill directory must match name: {path}")
        skills.append(SkillMeta(name=name, description=description, path=path))
    return skills


def load_skill(meta: SkillMeta) -> str:
    _, body = _parse_skill(meta.path)
    return body


def catalog_text(skills: list[SkillMeta]) -> str:
    lines = [
        "Available Skills (metadata only; full instructions are NOT loaded yet):"
    ]
    for skill in skills:
        lines.append(f"- {skill.name}: {skill.description}")
    lines.append(
        "When a Skill is clearly relevant, call load_skill(skill_name) before using its procedure."
    )
    return "\n".join(lines)
