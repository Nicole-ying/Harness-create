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

Current lesson:
- [`level1_tool_agent/`](./level1_tool_agent/) — ordinary Python tools → Function Calling → first general Agent Loop.

The teaching case is based on reward-function diagnosis from an existing CREATE reinforcement-learning experiment, so every later layer can be added to one continuous real problem instead of unrelated demos.

Learning principle: each level introduces only one new capability, and every new layer must answer one question — **what problem from the previous version does this layer solve?**
