# Level 4 Architecture

## 1. 一张图

```text
                         ┌───────────────────────┐
                         │      AgentHarness     │
                         │                       │
User ───────────────────>│  run_turn()           │
                         │    ├─ SessionLog      │
                         │    ├─ ContextRegistry │
                         │    ├─ ToolRegistry    │
                         │    ├─ EventBus        │
                         │    └─ PluginManager   │
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
             MCPToolsPlugin     SkillPlugin      MemoryPlugin
                    │                │                │
              MCP Client       Skill Catalog     Episodic store
                    │           load_skill Tool    context section
                    ▼
               MCP Server
                    │
                    ▼
                 Backend
```

## 2. Runtime Core 不知道业务能力

`runtime/harness.py` 只依赖：

```text
EventBus
SessionLog
ToolRegistry
ContextRegistry
PluginManager
LLM adapter interface
```

它不知道：

```text
BipedalWalker
MCP
Skill
Episodic Memory
CREATE reward design
```

这是 Level 4 最重要的架构变化。

## 3. Capability 注册流程

以 SkillPlugin 为例：

```text
PluginManager.mount(skill_plugin)
        ↓
PluginContext
        ↓
register_context(Skill Catalog)
register_tool(load_skill)
        ↓
AgentHarness 下一 step 自动看到这些能力
```

Agent Loop 本身没有任何 `if skill:`。

## 4. Reversible Effects

每一次：

```python
ctx.register_tool(...)
ctx.register_context(...)
ctx.on_event(...)
```

都会得到一个 disposer，由 PluginContext 保存。

卸载时：

```text
reverse(disposers)
        ↓
remove event handlers
remove context sections
remove tools
        ↓
plugin.teardown()
```

这不是完整 Cordis effect system，但用很小代码展示了“能力挂载应该有生命周期”的思想。

## 5. Turn / Step 生命周期

```text
turn/start
  user/message

  step 1
    build context
    record model/context
    agent/pre-step
    LLM request
    agent/post-step
    assistant/message
    tool/call
    tools/pre-execute
    tool/result
    tools/post-execute

  step 2
    ...

turn/end
```

一个 Tool Call 之后通常还需要另一个 model request，因此一个 turn 可以包含多个 step。

## 6. Session Event Log

Session 不只是：

```python
messages = []
```

本教程记录更多 runtime facts：

```text
turn/start
user/message
model/context
assistant/message
tool/call
tool/result
turn/end
```

`derive_messages()` 只是从 event log 中投影出 Chat Completion 需要的 message history。

所以：

```text
Session Log > messages list
```

## 7. Model-visible means logged

每一步调用模型前，Harness 记录：

```text
model/context
  system_prompt
  tool schemas
```

这样运行结束后可以检查模型到底看到了哪些 Skill metadata、Memory context 和 Tools。

这是对 DeepSeek Harness 公开架构中“Model-visible means logged”原则的教学化实现，不代表其内部实现细节完全相同。

## 8. MCP 是 Plugin，而不是 Agent Loop 的一部分

`MCPToolsPlugin` 在 mount 时：

```text
start/connect MCP Server
 ↓
tools/list
 ↓
for each MCP Tool
 ↓
register ToolSpec into ToolRegistry
```

运行时：

```text
LLM tool_call
 ↓
Harness ToolRegistry
 ↓
MCP plugin executor
 ↓
MCP Client.call_tool
 ↓
MCP Server
```

因此把 MCP 换成本地 Python、HTTP API 或数据库 Provider，不需要重写 Agent loop。

## 9. Skill 也是 Plugin

SkillPlugin 同时贡献：

```text
Context Provider:
Skill Catalog (metadata only)

Tool:
load_skill(skill_name)
```

这实现：

```text
Discover metadata
 ↓
Select relevant Skill
 ↓
Load full SKILL.md
```

即 progressive disclosure。

## 10. Memory 是 Context Provider

MemoryPlugin 不直接控制 Agent Loop。

它只实现：

```text
current session
 ↓
retrieve historical episode
 ↓
render short context section
```

ContextRegistry 在每个 step 统一组装。

## 11. EventBus 是扩展点

TracePlugin 没有修改 Harness：

```python
ctx.on_event("agent/pre-step", ...)
ctx.on_event("tools/post-execute", ...)
```

同一机制以后可以支持：

```text
permissions
approval
metrics
retry
policy
context compression
```

## 12. 和 DeepSeek Harness 的对应关系（概念级）

本教程不是一比一复刻，但可以这样建立阅读映射：

| 本教程 | DeepSeek Harness 公开架构中的相近职责 |
|---|---|
| `SessionLog` | `core/session` |
| `ContextRegistry` | `core/system-prompt` + context assembly |
| `ToolRegistry` | `core/tools` |
| `AgentHarness.run_turn` | `core/agent-loop` driver |
| `EventBus` | `agent/*`, `tools/*` extension events |
| `PluginManager` | Cordis plugin composition/effects 的极简教学版 |
| `MCPToolsPlugin` | MCP capability plugin/provider |
| `SkillPlugin` | Skill registry/filesystem/model-facing loading capability |

真正阅读 DeepSeek Harness 时，必须以其官方 `docs/architecture.md` 和源码为准。
