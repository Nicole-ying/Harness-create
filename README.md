# Harness-create

A step-by-step learning repository for AI Agent application engineering.

The repository starts from the smallest possible LLM application and gradually adds one capability at a time:

```text
Level 0  LLM API
Level 1  Tool Calling + Agent Loop
Level 2  MCP
Level 3  Skill + Memory + Context
Level 4  Harness / Agent Runtime
Level 5  Evaluation + CREATE integration
```

Completed:
- [`level0_llm/`](./level0_llm/) — one normal LLM request, request/response basics.
- [`level1_tool_agent/`](./level1_tool_agent/) — ordinary Python tools → Function Calling → first general Agent Loop.
- [`level2_mcp/`](./level2_mcp/) — MCPServer → MCP Client → stdio transport → runtime tool discovery → LLM Agent through MCP.
- [`level3_skill_memory_context/`](./level3_skill_memory_context/) — Agent Skill discovery/progressive disclosure → Skill routing → Working/Episodic Memory → explicit Context Builder → full MCP + Skill + Memory integration.

Current lesson:
- [`level4_harness_runtime/`](./level4_harness_runtime/) — extract Agent Loop, Session, Tool/Context Registries, lifecycle events and plugin management into a reusable teaching Harness; mount MCP, Skill, Memory and Trace as capabilities instead of hard-coding them into the business loop.

The teaching case is based on reward-function diagnosis from an existing CREATE reinforcement-learning experiment, so every later layer can be added to one continuous real problem instead of unrelated demos.

Learning principle: each level introduces only one new capability, and every new layer must answer one question — **what problem from the previous version does this layer solve?**
