"""Level 3C: explicitly assemble Working Memory + Episodic Memory + Skill into Context.

No LLM call is required here. The purpose is to inspect what the model WOULD see
and, equally important, what the Host deliberately leaves out.
"""

import json

from backend import read_component_stats, read_training_feedback
from context_builder import build_context, context_report
from memory import EpisodicMemory, WorkingMemory
from skill_loader import load_skill


def main() -> None:
    working = WorkingMemory(
        user_request="请分析 BipedalWalker reward iteration 1 为什么训练失败。"
    )

    working.add_evidence(
        "training_feedback=" + json.dumps(read_training_feedback(1), ensure_ascii=False)
    )
    working.add_evidence(
        "component_stats=" + json.dumps(read_component_stats(1), ensure_ascii=False)
    )
    working.selected_skill = "gate-proxy-by-validity"
    working.notes.append(
        "Current evidence does not directly prove the proxy remains active in failure states; keep that distinction explicit."
    )

    episodes = EpisodicMemory().recent(task="BipedalWalker", limit=1)
    skill = load_skill(working.selected_skill)

    context = build_context(
        working=working,
        episodes=episodes,
        skill=skill,
    )

    print("========== WORKING MEMORY ==========")
    print(json.dumps(working.snapshot(), ensure_ascii=False, indent=2))

    print("\n========== SELECTED EPISODIC MEMORY ==========")
    print(json.dumps(episodes, ensure_ascii=False, indent=2))

    print("\n========== FINAL CONTEXT ==========")
    print(context)

    print("\n========== CONTEXT REPORT ==========")
    print(context_report(context))


if __name__ == "__main__":
    main()
