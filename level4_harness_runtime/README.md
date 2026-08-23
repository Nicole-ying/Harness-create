# Level 4 — Harness / Agent Runtime

Level 3 已经把能力全部凑齐了：

```text
LLM
+ Tool Calling
+ MCP
+ Skill
+ Memory
+ Context Builder
```

但 `step4_full_agent.py` 仍然是一个**业务脚本**：它自己负责 Agent Loop、MCP 生命周期、Skill 加载、Memory、Context、错误处理、轮数限制和日志。

Level 4 解决的问题是：

> **如何把这些“每个 Agent 应用都会重复出现的运行职责”抽成一个可复用 Agent Runtime / Harness，让业务能力以插件形式挂载，而不是继续把所有逻辑塞进一个 main.py？**

---

## 1. Level 3 → Level 4 的变化

Level 3：

```text
step4_full_agent.py
├── Agent Loop
├── MCP Client
├── Skill routing/loading
├── Memory
├── Context
├── error handling
└── tracing
```

Level 4：

```text
AgentHarness
├── Agent Loop
├── Session Log
├── Tool Registry
├── Context Registry
├── Event Bus
├── Plugin Manager
└── Runtime policies

Plugins
├── MCPToolsPlugin
├── SkillPlugin
├── MemoryPlugin
└── TracePlugin
```

核心原则：

> **Harness 负责“怎么运行”；Plugin 负责“增加什么能力”。**

因此 `runtime/harness.py` 根本不需要 import `mcp`、`Skill` 或 reward-design 业务代码。

---

## 2. 本教程和 DeepSeek Harness 的关系

这一层参考了 DeepSeek Harness 当前公开架构里的几个重要思想：

- model adapter、tool registry、session log、agent loop 等都是可替换能力；
- 通过事件/扩展点在不直接修改 Agent Loop 的情况下增加行为；
- Tool schema 在每一步请求前组装；
- turn 可以包含多个 step；
- session event log 是模型上下文、恢复、调试和 replay 的重要来源；
- “model-visible means logged”——给模型看的运行信息应该可追溯。

但本目录**不是 DeepSeek Harness 的 Python 重写，也没有实现 Cordis**。它只是为了教学，把同样的系统设计思想压缩成大约几百行可读 Python。

参考：
- `deepseek-ai/deepseek-harness/docs/architecture.md`
- `deepseek-ai/deepseek-harness/packages/core/agent-loop/`

---

## 3. 文件结构

```text
level4_harness_runtime/
├── runtime/
│   ├── harness.py       # 可复用 Agent Loop / turn / step
│   ├── session.py       # append-only Session Event Log
│   ├── registries.py    # Tool Registry + Context Registry
│   ├── events.py        # lifecycle extension points
│   └── plugin.py        # plugin mount / teardown / reversible registration
│
├── plugins.py           # MCP / Skill / Memory / Trace plugins
├── llm_client.py        # DeepSeek / OpenAI-compatible provider adapter
├── backend.py           # 普通实验业务函数
├── mcp_server.py        # 把实验函数暴露为 MCP Tools
├── skill_store.py       # Agent Skill discovery/loading
├── skills/              # Reward-design Skills
├── memory/              # synthetic teaching episodic memory
├── mock_data/           # teaching experiment data
│
├── smoke_test.py
├── step1_runtime_skeleton.py
├── step2_plugin_runtime.py
├── step3_full_harness.py
├── step4_replay_session.py
├── ARCHITECTURE.md
├── LEARNING_NOTES.md
└── INTERVIEW_QUESTIONS.md
```

---

# 4. 先运行：完全不需要 API

```bash
cd level4_harness_runtime
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

先跑：

```bash
python smoke_test.py
```

如果看到：

```text
Level 4 Harness smoke test passed.
```

说明至少这些基础结构工作正常：

```text
AgentHarness
PluginManager
SkillPlugin
Tool Registry
Context Registry
Session Log
plugin teardown
```

---

# 5. Step 1 — 先只看 Runtime Skeleton

```bash
python step1_runtime_skeleton.py
```

这一版使用 FakeLLM，不需要真实 API。

只观察 Harness 自动完成：

```text
turn/start
user/message
model/context
assistant/message
turn/end
```

注意：业务代码没有自己维护 `messages=[]` 的 while-loop。

它只调用：

```python
answer = await harness.run_turn(user_text)
```

Agent Loop 已经成为 Runtime 的责任。

---

# 6. Step 2 — Plugin 为什么存在

```bash
python step2_plugin_runtime.py
```

运行前：

```text
tools = []
context sections = []
```

挂载：

```python
await harness.mount(SkillPlugin(SKILLS_DIR))
```

以后：

```text
tools = [load_skill]
context sections = [Skill Catalog]
```

但 `AgentHarness.run_turn()` 一行都没改。

这就是 Plugin/Capability Seam 的意义。

更重要的是：

```python
await harness.close()
```

以后插件注册的 Tool 和 Context 都会被撤销。

所以不是“插件往全局变量里塞点东西就不管了”，而是有生命周期：

```text
mount
 ↓
register effects
 ↓
runtime use
 ↓
teardown
 ↓
reverse registrations
```

---

# 7. Step 3 — 完整 Harness

复制配置：

```powershell
Copy-Item .env.example .env
```

DeepSeek：

```env
PROVIDER=deepseek
DEEPSEEK_API_KEY=你的本地 key
DEEPSEEK_MODEL=你账号实际支持的模型 ID
```

然后：

```bash
python step3_full_harness.py
```

完整结构：

```text
User
 ↓
AgentHarness
 │
 ├── ContextRegistry
 │    ├── base system prompt
 │    ├── Skill Catalog       <- SkillPlugin
 │    └── Episodic Memory     <- MemoryPlugin
 │
 ├── ToolRegistry
 │    ├── get_training_feedback <- MCPToolsPlugin
 │    ├── get_component_stats   <- MCPToolsPlugin
 │    └── load_skill             <- SkillPlugin
 │
 ├── EventBus
 │    └── TracePlugin
 │
 ├── SessionLog
 │
 └── Agent Loop
      ↓
     LLM
      ↓ tool_call
     ToolRegistry
      ↓
     Plugin capability
```

对于 reward diagnosis，模型可能经历：

```text
Step 1
LLM -> get_training_feedback

Step 2
LLM -> get_component_stats

Step 3
LLM -> load_skill(gate-proxy-by-validity)

Step 4
LLM -> final diagnosis
```

具体顺序由模型决定，Harness 只负责安全地驱动 lifecycle。

---

# 8. Turn 和 Step

Level 4 第一次正式区分：

```text
Turn
= 用户一次完整请求直到最终回答

Step
= 一次 LLM request + 它随后触发的 Tool calls
```

所以一个 Turn 可以是：

```text
turn/start
  step 1 -> LLM -> tool
  step 2 -> LLM -> tool
  step 3 -> LLM -> final
turn/end
```

这和 DeepSeek Harness 当前公开架构对 turn/step 的区分是一致的概念方向。

---

# 9. Session Log 为什么属于 Harness

每次运行会记录：

```text
turn/start
user/message
model/context
assistant/message
tool/call
tool/result
...
turn/end
```

`model/context` 会保存这一 step 实际组装出的：

```text
system prompt
visible tool schemas
```

因此事后可以回答：

> 模型第 3 步到底看到了什么？

而不是只能看最终答案猜。

运行完整 Agent 后：

```bash
python step4_replay_session.py
```

可以不调用模型，直接检查 event timeline 和最后一次模型可见 context。

---

# 10. Event Hook 为什么属于 Harness

现在 Runtime 提供：

```text
turn/start
agent/pre-step
agent/post-step
tools/pre-execute
tools/post-execute
turn/end
```

`TracePlugin` 只是监听它们。

以后完全可以再写：

```text
PermissionPlugin
RetryPlugin
MetricsPlugin
ApprovalPlugin
ContextCompressionPlugin
SkillRouterPlugin
SafetyPolicyPlugin
```

而不去复制一份新的 Agent Loop。

这就是 Runtime extension point 的价值。

---

# 11. Harness 和 Agent Framework 有什么区别？

边界不是绝对的，但本教程这样理解：

```text
Agent Framework
更偏开发抽象：graph/node/state/tool/prompt 等

Harness / Runtime
更偏“一个 Agent 实例如何真正被驱动运行”：
turn/step
session
context assembly
tool execution
plugin lifecycle
error boundary
limits
trace/replay
permissions/sandbox（后续）
```

LangGraph 可以成为 Harness 内部的一部分；Harness 也可以不用 LangGraph。

---

# 12. Level 4 还没有做什么

为了让你学清楚，本层故意没直接做：

```text
Sandbox
human approval
remote HTTP MCP
multi-agent
sub-agent
job scheduling
retry/backoff
persistent database
distributed execution
production auth
full context compression
```

这些不是“不重要”，而是不能在你刚理解 Runtime 时一次堆完。

---

# 13. Level 4 过关标准

你应该能够不看代码解释：

```text
Harness / Runtime
Turn vs Step
Session Log
Tool Registry
Context Registry
Event Hook
Plugin Lifecycle
Capability Seam
Model-visible context
Replay / Trace
```

并且能够回答：

> 为什么 MCP、Skill、Memory 不应该全部写死在 Agent Loop？

> 为什么 Tool Registry 和 Plugin Manager 是两层概念？

> 为什么 Session 不等于 messages 数组？

> 为什么要保存 model/context snapshot？

> 为什么插件卸载时需要 reverse effects？

做到这里，你就不再只是“会用 Agent 框架”，而开始真正理解 **Agent Runtime Engineering**。

下一层 Level 5 才会做 Evaluation + CREATE integration：比较 baseline / MCP / Skill / Harness，并加入 trace metrics、task success、tool success、token/latency 等真实评测。
