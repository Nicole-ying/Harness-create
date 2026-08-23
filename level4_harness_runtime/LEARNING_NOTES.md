# Level 4 Learning Notes — Harness / Agent Runtime

## 1. Harness 到底是什么？

在本教程里，Harness 是负责**驱动 Agent 运行**的 Runtime 层：

```text
输入进来以后：
谁管理 turn？
谁发起每一次 model request？
谁组装 context？
谁暴露 tools？
谁执行 tool？
谁限制最大步数？
谁记录 session？
谁处理 plugin lifecycle？
谁提供 trace / policy extension points？
```

这些问题都不应该由 reward-design 业务代码反复解决。

因此：

```text
Agent = model + capabilities + runtime behavior
Harness = runtime behavior 的主要承载层
```

---

## 2. Harness ≠ LLM

LLM 做：

```text
根据当前 messages + tool schemas 产生 assistant response
```

Harness 做：

```text
准备 messages
准备 tool schemas
调用 LLM
解析 tool_calls
执行 tool
把 tool result 放回 session
决定是否进入下一 step
```

LLM 不会自己启动 Python 函数，也不会自己保持真正的 process lifecycle。

---

## 3. Harness ≠ Tool Calling

Tool Calling 是模型接口能力：

```text
model -> {name, arguments}
```

Harness 是：

```text
收到 {name, arguments}
 ↓
校验
 ↓
route 到 ToolRegistry
 ↓
执行 provider
 ↓
记录 result
 ↓
再请求 model
```

Tool Calling 是协议的一环；Harness 管完整运行链。

---

## 4. Harness ≠ MCP

MCP 解决：

```text
外部能力如何标准发现/调用
```

Harness 解决：

```text
什么时候让 model 看到这些能力、何时执行、如何记录、失败后怎么办
```

因此本教程里：

```text
MCPToolsPlugin -> ToolRegistry -> Harness
```

而不是：

```text
Harness = MCP
```

---

## 5. Harness ≠ Skill

Skill 是方法/SOP。

Harness 决定：

```text
Skill catalog 什么时候进入 context
load_skill 以什么 Tool 暴露
Skill result 怎么回到 model history
```

Skill 本身不负责 Agent lifecycle。

---

## 6. Turn vs Step

一定要会说。

### Turn

一次用户请求从开始到最终结束：

```text
User: 帮我分析 reward 失败原因
          ↓
可能调用 3 次 Tool
          ↓
最终回答
```

这整个过程是一个 Turn。

### Step

一次 Model Request 以及由这一响应触发的 Tool Calls。

例：

```text
Step 1
model -> get_training_feedback

Step 2
model -> get_component_stats

Step 3
model -> load_skill

Step 4
model -> final answer
```

一个 Turn 可以包含多个 Step。

---

## 7. 为什么 Session 不应该只是 messages=[]？

`messages` 只是模型 API 的输入表示。

Runtime 还需要记录：

```text
turn/start
model/context
tool/call
finish_reason
turn/end
error
```

这些不是所有内容都适合直接变成 Chat Message，但对于 debug / replay / telemetry 很重要。

因此：

```text
Session Event Log
      ↓ projection
derive_messages()
      ↓
LLM messages
```

比“到处 append(messages)”更容易追踪。

---

## 8. model/context 为什么要单独记录？

因为动态 Agent 每一步看到的东西可能变化：

```text
Step 1:
Skill catalog
No tool results

Step 2:
Skill catalog
training feedback
memory retrieval changed

Step 3:
Skill catalog
training feedback
component stats
loaded Skill
```

如果只保存最终 messages，很难回答：

> 模型在作出某个 Tool Call 的那一刻到底看到了什么？

因此本教程在 `agent/pre-step` hook 完成之后，保存准确的：

```text
messages
Tool schemas
```

再发给 provider。

---

## 9. Tool Registry 的作用

Agent Loop 不应该写：

```python
if name == "get_training_feedback":
    ...
elif name == "load_skill":
    ...
```

而应该：

```python
await tool_registry.execute(name, arguments)
```

具体 tool 来自：

```text
MCP plugin
Skill plugin
Local tool plugin
HTTP API plugin
```

这样 Runtime 不依赖具体业务工具。

---

## 10. Context Registry 的作用

System Prompt 不是一块永远不变的长字符串。

可以由多个 Provider 动态贡献：

```text
Base instructions
+ Skill Catalog
+ Relevant Memory
+ Safety Policy
+ Current Time
+ Workspace Info
```

ContextRegistry 统一控制组装顺序。

以后你做 Context Engineering，重点不是“Prompt 写得长”，而是：

```text
谁提供？
什么时候提供？
是否相关？
占多少 tokens？
有没有过期？
能否追溯？
```

---

## 11. Event Hook 是什么？

Event Hook 是 Runtime 提供的扩展点。

例如：

```text
agent/pre-step
```

以后 Context Compression Plugin 可以在这里裁剪 messages。

```text
tools/pre-execute
```

Permission Plugin 可以在这里拒绝危险操作。

```text
tools/post-execute
```

Metrics Plugin 可以记录 latency / success。

重点：

> 不需要复制或修改 Agent Loop。

---

## 12. Plugin 和 Tool 有什么区别？

一个 Tool 只是模型可调用的一个动作。

一个 Plugin 可以同时贡献很多东西：

```text
Tool
Context section
Event hooks
External connection
Background resources
Lifecycle
```

例如 `SkillPlugin`：

```text
Context: Skill Catalog
Tool: load_skill
Lifecycle: discover at setup, unregister at teardown
```

所以：

```text
Plugin > Tool
```

它们不是同一级概念。

---

## 13. Plugin 为什么需要 teardown？

因为插件可能持有真实资源：

```text
MCP subprocess
HTTP connection
DB pool
file watcher
background task
```

如果 mount 有 setup，却没有 teardown：

```text
资源泄漏
重复 tool registration
不可预测状态
测试相互污染
```

所以生命周期是 Runtime 工程的一部分。

---

## 14. 什么是 reversible registration？

本教程：

```python
ctx.register_tool(...)
```

底层会保存一个 disposer。

关闭插件时：

```text
register A
register B
register C

↓ reverse

dispose C
dispose B
dispose A
```

这是一个非常简化的 effect-unwind 思想。

DeepSeek Harness 的 Cordis plugin/effect 机制更完整；本教程只是帮助你先理解为什么“插件卸载后状态要能恢复”。

---

## 15. Capability Seam

可以粗略理解成：

```text
Consumer
   ↓
Interface / Registry
   ↓
Provider
```

例如 Tool：

```text
Agent Loop (consumer)
 ↓
ToolRegistry (interface/seam)
 ↓
MCPToolsPlugin (provider)
```

因此替换 Provider：

```text
MCP
→ Local Python
→ HTTP service
```

Consumer 不一定需要改。

---

## 16. Harness 为什么要限制 max_steps？

因为模型可能：

```text
反复调用同一个 tool
错误重试不停止
在两个工具之间循环
```

Runtime 必须有 termination policy。

最简单就是：

```python
max_steps = 8
```

生产系统还可能有：

```text
max tool calls
max cost
max wall-clock time
max retries
user cancellation
```

---

## 17. Error Boundary 为什么属于 Runtime？

Tool 参数来自模型，不可信。

可能：

```text
不是合法 JSON
字段缺失
Tool 不存在
MCP Server 报错
网络超时
```

所以 Runtime 应该把错误转成受控 Observation，而不是让整个进程随意崩溃。

本教程只做最小 error-to-tool-result，Level 5/后续可以继续加 retry、error taxonomy、metrics。

---

## 18. 为什么 Level 4 不直接用 LangGraph？

因为学习目标不是框架 API。

你需要先亲眼看到：

```text
Session
Registry
Plugin
Event
Loop
```

之后再看 LangGraph / DeepSeek Harness，你才能判断：

> 这个框架到底帮我抽象掉了什么？

而不是只会背 `StateGraph()`。

---

## 19. DeepSeek Harness 值得重点对照的概念

读官方 `docs/architecture.md` 时重点找：

```text
Cordis plugin tree
core/session
core/system-prompt
core/tools
core/agent
core/agent-loop
agent/* events
tools/* events
turn / step
model-visible means logged
capability seams
```

然后回来看本教程对应的小模块。

不要说：

> “我复刻了 DeepSeek Harness。”

更准确：

> “我参考其公开架构思想实现了一个教学型 Python Agent Runtime，用于理解 Session、Tool/Context Registry、Plugin lifecycle 和 Agent Loop 的职责边界。”

---

## 20. Level 4 面试能讲到什么程度？

最少应该能完整讲：

```text
User request
 ↓
Harness opens turn
 ↓
Context providers assemble model-visible context
 ↓
Tool registry exposes current capabilities
 ↓
LLM produces tool_calls
 ↓
Runtime routes execution
 ↓
Session logs durable events
 ↓
next step
 ↓
final answer / termination
```

然后能解释 MCP/Skill/Memory 为什么都只是挂载到 Runtime 的能力，而不是 Agent Loop 自己的业务 if/else。
