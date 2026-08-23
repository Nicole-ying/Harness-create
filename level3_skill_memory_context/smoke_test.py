"""No-LLM smoke test for Skill + Memory + Context plumbing."""

import json

from backend import read_component_stats, read_training_feedback
from context_builder import build_context
from memory import EpisodicMemory, WorkingMemory
from skill_loader import discover_skills, load_skill


def main() -> None:
    skills = discover_skills()
    names = {skill.name for skill in skills}
    expected = {
        "gate-proxy-by-validity",
        "densify-sparse-outcome",
        "calibrate-rare-risk-penalty",
    }
    assert expected.issubset(names), (expected, names)

    training = read_training_feedback(1)
    components = read_component_stats(1)
    assert training["iteration"] == 1
    assert components["iteration"] == 1

    working = WorkingMemory(user_request="smoke test")
    working.add_evidence(json.dumps(training, ensure_ascii=False))
    working.selected_skill = "gate-proxy-by-validity"

    episodes = EpisodicMemory().recent(task="BipedalWalker", limit=1)
    assert len(episodes) == 1

    skill = load_skill(working.selected_skill)
    context = build_context(working=working, episodes=episodes, skill=skill)
    assert "Selected procedural Skill" in context
    assert "gate-proxy-by-validity" in context
    assert "synthetic teaching memory" in context

    print("Level 3 Skill + Memory + Context smoke test passed.")


if __name__ == "__main__":
    main()
