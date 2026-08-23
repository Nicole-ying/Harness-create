"""Minimal Agent Skill discovery/loading for Level 3.

The format follows the public Agent Skills convention:
- one directory per skill
- required SKILL.md
- YAML frontmatter with name + description
- Markdown instructions in the body

This lesson intentionally implements a tiny loader instead of depending on a
full Agent Skills runtime, so the progressive-disclosure mechanism stays visible.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


HERE = Path(__file__).resolve().parent
DEFAULT_SKILLS_DIR = HERE / "skills"


@dataclass(frozen=True)
class SkillMetadata:
    name: str
    description: str
    path: Path


@dataclass(frozen=True)
class SkillDefinition:
    metadata: SkillMetadata
    instructions: str


def _split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")

    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("SKILL.md frontmatter is not closed with ---")

    frontmatter_text = text[4:end]
    body = text[end + 5 :].strip()
    metadata = yaml.safe_load(frontmatter_text) or {}
    return metadata, body


def read_skill_metadata(skill_file: Path) -> SkillMetadata:
    metadata, _ = _split_frontmatter(skill_file.read_text(encoding="utf-8"))
    name = str(metadata.get("name", "")).strip()
    description = str(metadata.get("description", "")).strip()

    if not name or not description:
        raise ValueError(f"{skill_file}: name and description are required")
    if name != skill_file.parent.name:
        raise ValueError(
            f"{skill_file}: skill name '{name}' must match directory '{skill_file.parent.name}'"
        )

    return SkillMetadata(name=name, description=description, path=skill_file)


def discover_skills(skills_dir: Path = DEFAULT_SKILLS_DIR) -> list[SkillMetadata]:
    skills = [read_skill_metadata(path) for path in sorted(skills_dir.glob("*/SKILL.md"))]
    if not skills:
        raise RuntimeError(f"No skills found under {skills_dir}")
    return skills


def load_skill(name: str, skills_dir: Path = DEFAULT_SKILLS_DIR) -> SkillDefinition:
    skill_file = skills_dir / name / "SKILL.md"
    if not skill_file.exists():
        raise KeyError(f"Unknown skill: {name}")

    raw = skill_file.read_text(encoding="utf-8")
    metadata_dict, body = _split_frontmatter(raw)
    metadata = read_skill_metadata(skill_file)
    if metadata_dict.get("name") != name:
        raise ValueError("Skill name mismatch")
    return SkillDefinition(metadata=metadata, instructions=body)


def catalog_text(skills: list[SkillMetadata]) -> str:
    """Only metadata goes into discovery context; bodies stay unloaded."""
    return "\n".join(f"- {s.name}: {s.description}" for s in skills)
