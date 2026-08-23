"""Level 3A: Skill discovery and progressive disclosure without an LLM.

First print only metadata for every Skill. Then explicitly load ONE full Skill.
The point is to see that discovery != activation/loading.
"""

from skill_loader import catalog_text, discover_skills, load_skill


def main() -> None:
    skills = discover_skills()

    print("========== SKILL CATALOG: METADATA ONLY ==========")
    print(catalog_text(skills))

    selected = "gate-proxy-by-validity"
    print("\n========== ACTIVATE ONE SKILL ==========")
    print("selected:", selected)

    skill = load_skill(selected)
    print("\n========== FULL SKILL BODY NOW LOADED ==========")
    print(skill.instructions)


if __name__ == "__main__":
    main()
