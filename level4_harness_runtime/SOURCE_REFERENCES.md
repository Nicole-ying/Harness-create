# Source References

Level 4 is a teaching implementation. The architecture notes were informed by the following public sources; the code in this directory is intentionally much smaller and is **not** a source-compatible reimplementation.

## DeepSeek Harness

- Repository: `https://github.com/deepseek-ai/deepseek-harness`
- Architecture: `https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md`
- Agent loop package: `https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/core/agent-loop`
- Session subsystem: `https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/session.md`

Key public concepts used as learning references:

```text
Cordis plugin composition
replaceable model/tool/session/agent-loop capabilities
turn vs step
session events
agent/* and tools/* extension events
model-visible means logged
capability seams
```

## Agent Skills

- Specification repository: `https://github.com/agentskills/agentskills`
- Specification: `https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx`
- Anthropic Skills examples: `https://github.com/anthropics/skills`
- MCP Builder Skill: `https://github.com/anthropics/skills/blob/main/skills/mcp-builder/SKILL.md`

Concepts used:

```text
SKILL.md
YAML frontmatter
name + description metadata
progressive disclosure
full instructions loaded only after activation
```

## MCP

- Protocol: `https://github.com/modelcontextprotocol/modelcontextprotocol`
- Python SDK: `https://github.com/modelcontextprotocol/python-sdk`

Level 4 carries forward the Level 2 teaching approach: MCP is a capability provider attached to the Host/Runtime; the LLM itself still sees provider-specific Tool schemas and produces Tool Calls.
