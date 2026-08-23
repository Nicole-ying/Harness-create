"""Level 3B: let the LLM select a Skill from metadata, then load only that Skill.

The router sees:
- current evidence;
- Skill name + description catalog.

It does NOT see every SKILL.md body. Only after selection does the Host load the
full instructions. This demonstrates progressive disclosure.
"""

from __future__ import annotations

import json

from backend import read_component_stats, read_training_feedback
from llm_client import LLMClient, load_llm_config
from skill_loader import catalog_text, discover_skills, load_skill


ROUTER_SYSTEM = """你是 Reward-Design Skill Router。
你的任务不是直接修改奖励函数，而是从给定 Skill Catalog 中选择最匹配当前证据的一项。
只能选择 catalog 中存在的 skill name。如果证据不足，也必须选择最需要进一步验证的一项并在 reason 中说明不确定性。
只返回 JSON：{"skill_name": "...", "reason": "..."}。
"""


def main() -> None:
    llm = LLMClient(load_llm_config())

    evidence = {
        "training_feedback": read_training_feedback(1),
        "component_stats": read_component_stats(1),
    }
    skills = discover_skills()
    allowed_names = {skill.name for skill in skills}

    user_prompt = f"""Current evidence:
{json.dumps(evidence, ensure_ascii=False, indent=2)}

Available Skill Catalog (metadata only):
{catalog_text(skills)}

Select exactly one Skill.
"""

    response = llm.completion(
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )

    raw = response.choices[0].message.content or "{}"
    decision = json.loads(raw)
    selected = str(decision.get("skill_name", ""))

    if selected not in allowed_names:
        raise ValueError(f"Router selected unknown Skill: {selected!r}")

    print("========== ROUTER DECISION ==========")
    print(json.dumps(decision, ensure_ascii=False, indent=2))

    print("\n========== NOW LOAD ONLY THE SELECTED SKILL ==========")
    skill = load_skill(selected)
    print(skill.instructions)


if __name__ == "__main__":
    main()
