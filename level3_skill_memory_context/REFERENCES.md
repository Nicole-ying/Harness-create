# Level 3 references

The teaching implementation is intentionally small, but its Skill layout is informed by public Agent Skill conventions and real Skill examples.

## Agent Skills specification

- Repository: `agentskills/agentskills`
- Specification: `docs/specification.mdx`
- Key concepts used here:
  - one directory per Skill;
  - required `SKILL.md`;
  - YAML frontmatter with required `name` and `description`;
  - optional `scripts/`, `references/`, and `assets/`;
  - progressive disclosure: metadata first, full instructions on activation, resources as needed.

## Anthropic Skills examples

- Repository: `anthropics/skills`
- Example studied: `skills/mcp-builder/SKILL.md`
- Useful pattern:
  - clear trigger/description;
  - procedural workflow rather than vague advice;
  - references loaded on demand;
  - implementation, testing, and evaluation all included in the procedure.

## Important teaching simplification

`skill_loader.py` in this repository is **not** a complete implementation of every Agent Skills feature. It intentionally implements only enough to make discovery, routing, progressive disclosure, and loading visible before Level 4 introduces a Harness/Runtime abstraction.
