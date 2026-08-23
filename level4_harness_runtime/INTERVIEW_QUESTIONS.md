# Level 4 Interview Questions — Harness / Agent Runtime

下面问题按“必须会 → 深挖”排列。回答时优先结合本目录代码，而不是只背定义。

## A. Harness 基础

### 1. 什么是 Agent Harness？
参考回答：Harness 是驱动 Agent 实际运行的 Runtime 层，负责 turn/step、model request、Tool execution、Session、Context、插件生命周期、限制、错误边界和观测等。模型负责决策，Harness 负责让决策在一个可控系统里运行。

### 2. Harness 和普通 Agent Loop 有什么区别？
最小 Agent Loop 只是：

```text
model -> tool? -> execute -> model
```

Harness 在此基础上还管理 Session、Context、Registry、Plugin lifecycle、Trace、Termination、Error boundary 等运行职责。

### 3. Harness 和 Agent Framework 有什么区别？
边界不是绝对的。Framework 更偏开发抽象（graph/node/state/tool），Harness 更偏一个 Agent 实例真正怎么被驱动、记录、扩展和约束。二者可以重叠。

### 4. Harness 和 MCP 是什么关系？
MCP 是外部能力接入协议；Harness 可以持有 MCP Client，把 MCP Tools 注册进 Tool Registry。MCP 不是 Agent lifecycle 本身。

### 5. Harness 和 Skill 是什么关系？
Skill 是程序性方法；Harness 决定 Skill metadata 怎么进入 Context、完整 Skill 怎么被加载、结果如何进入后续 step。

---

## B. Turn / Step

### 6. Turn 和 Step 分别是什么？
Turn 是一次用户请求直到最终回答；Step 是一次模型请求以及该响应触发的一组 Tool calls。一个 Turn 可以包含多个 Step。

### 7. 为什么 Tool Call 后通常会进入下一个 Step？
因为 Tool result 是新的 Observation，需要再次送给模型，由模型决定继续调用工具还是生成最终答案。

### 8. 为什么要限制 max_steps？
防止模型无限循环、重复调用、错误重试不终止，并控制成本和时延。

### 9. 生产里除了 max_steps 还能有什么 termination policy？
max tool calls、token/cost budget、wall-clock timeout、retry budget、user cancellation、goal reached、human stop。

---

## C. Session

### 10. 为什么 Session 不只是 messages 数组？
messages 只是 provider 的模型输入格式。Session 还应保存 turn/start、tool/call、model/context、finish_reason、turn/end、error 等 runtime facts，以支持 replay/debug/telemetry。

### 11. `derive_messages()` 是什么思想？
从 durable session events 投影出当前 provider 需要的 chat history，而不是把 messages 当作唯一真相来源。

### 12. 什么叫 “model-visible means logged”？
所有真正送进模型请求的动态信息都应该能在日志中重建或检查，否则事后无法知道模型为何做出某个决策。

### 13. 为什么本教程记录 `model/context`？
因为 Skill、Memory、Tool schemas 可能每个 step 都变化；保存 snapshot 能复盘某一步模型实际看到的 messages 和 Tools。

### 14. 为什么 `agent/pre-step` 之后才记录 snapshot？
因为 hook 可能重写 messages/tools。要记录的是最终真正发给 provider 的内容，而不是 hook 之前的旧版本。

---

## D. Registry / Capability

### 15. Tool Registry 解决什么问题？
把 Agent Loop 与具体 Tool Provider 解耦。Loop 只按 name 执行，工具可以来自 MCP、本地 Python、HTTP API 或其他插件。

### 16. 为什么不要在 Agent Loop 里写大量 `if tool_name == ...`？
它会让 Runtime 和业务能力强耦合，新增/替换工具必须改核心 loop，也难以测试、隔离和卸载。

### 17. Context Registry 解决什么问题？
把 system/context 的多个来源统一注册、排序和组装，例如 Skill Catalog、Memory、Policy、Workspace 信息，而不是把所有内容硬编码进一个长 Prompt。

### 18. Capability Seam 怎么理解？
Consumer 只依赖一个稳定接口/registry，具体 Provider 可替换。比如 Agent Loop -> ToolRegistry -> MCPToolsPlugin。

### 19. Tool Registry 和 Plugin Manager 有什么区别？
Tool Registry 管“有哪些模型可调用动作”；Plugin Manager 管“一个能力包的完整生命周期”，插件可以同时注册 Tool、Context、Events 和外部资源。

---

## E. Plugin

### 20. 为什么 Plugin 不等于 Tool？
Tool 只是一个动作；Plugin 可以贡献多个 Tool、Context Provider、Event Handler、连接池、后台资源以及 setup/teardown。

### 21. 为什么插件需要 teardown？
需要关闭 MCP 子进程/连接、DB pool、后台任务，并撤销注册，避免资源泄漏和状态污染。

### 22. 什么是 reversible registration？
插件注册 Tool/Context/Event 时保留 disposer；卸载时逆序撤销这些 effects，让 Runtime 恢复到挂载前状态。

### 23. 插件 setup 进行到一半失败怎么办？
已经产生的 effects 也必须撤销，并释放已经创建的资源。本教程 `PluginManager.mount()` 对 setup exception 做清理。

### 24. 为什么 DeepSeek Harness 里“Everything is a Plugin”值得关注？
它体现了把 model adapter、tool registry、session、agent loop 等能力作为可组合/可替换模块，而不是依赖一个不可扩展的超级核心类。回答时要说明你参考的是其公开架构思想，不要声称本项目等价实现。

---

## F. Events / Observability

### 25. Event Hook 有什么价值？
允许 tracing、permissions、metrics、context compression、policy 等横切能力接入运行生命周期，而不修改 Agent Loop。

### 26. `agent/pre-step` 可以做什么？
检查/改写模型输入、Context 压缩、动态权限或模型路由。生产系统需要更严格的 typed contract 和安全边界。

### 27. `tools/pre-execute` 可以做什么？
参数校验、权限检查、human approval、rate limit、审计、sandbox policy。

### 28. `tools/post-execute` 可以做什么？
记录 latency/success、格式规范化、敏感信息过滤、结果截断、trace。

### 29. Trace 和普通 print 有什么区别？
print 只是展示；真正 observability 通常需要结构化 event、request/tool IDs、latency、token/cost、error taxonomy 和可查询存储。本教程 TracePlugin 只是入门。

---

## G. Error / Safety

### 30. Tool arguments 为什么不能直接信任？
它们由模型生成，可能不是合法 JSON、字段错误、越权或包含危险参数。Runtime 需要校验和 policy。

### 31. Tool 执行失败应该直接让进程崩溃吗？
通常不应。可以把受控 error observation 返回模型，并根据 error type 决定 retry/fallback/stop；但安全或基础设施错误也可能需要立即终止。

### 32. 为什么 Level 4 MCP Tools 仍然保持 read-only？
写操作会引入权限、审批、幂等性、rollback、sandbox、审计等问题，适合在理解 Runtime 后再加入。

### 33. 如果以后加入 `execute_shell`，Harness 还需要什么？
Sandbox、allowlist、cwd/root policy、timeout、resource limits、approval、audit、output limits、secret handling。

---

## H. Context / Memory / Skill 深挖

### 34. Memory 为什么通过 Context Provider 接入？
Memory store 本身不是模型输入。需要 retrieval 后选择相关内容，再由 Context Registry 组装进当前 model-visible context。

### 35. Skill 为什么用 `load_skill` Tool 而不是启动时全部塞 Prompt？
为了 progressive disclosure，减少 token 和干扰，只在相关时加载完整程序性知识。

### 36. 3000 个 Skill 怎么办？
不能把全部 metadata/正文无脑塞入上下文。需要分层 catalog、embedding/keyword retrieval、task/pathology routing、top-k、权限和 eval。

### 37. Skill load 后如何知道模型真的遵循了 Skill？
需要 trajectory/evaluation：检查 tool/action sequence、diagnostic tests、最终 output，以及任务 outcome，不能只看模型说“我使用了 Skill”。

---

## I. 项目设计题

### 38. 如果把 MCP Server 换成 REST API，需要改 AgentHarness 吗？
理想情况下不用。写一个 HTTPToolsPlugin，把 API schemas/actions 注册成 ToolSpec 即可。

### 39. 如果把 DeepSeek 换成 Claude 原生 API，需要改什么？
主要改 LLM adapter/provider schema 转换；Runtime 的 Session/Tool Registry/Plugin lifecycle 不应该与特定 provider 强绑定。

### 40. 怎么给这个 Harness 加权限系统？
可以在 `tools/pre-execute` 注册 PermissionPlugin：根据 tool annotations、user/session role、argument risk 判断 allow/deny/require approval，并把 decision 写入 session/audit log。

### 41. 怎么加 Context Compression？
在每个 step 组装后根据 token budget 对历史 tool results、memory、conversation 做 summarization/truncation；最好记录压缩前后 provenance，并用 eval 验证信息损失。

### 42. 怎么加 Multi-Agent？
不要先简单递归创建 LLM。需要定义 sub-agent interface、session/parent-child关系、budget、message passing、result contract、cancellation 和 trace。

### 43. 怎么让 Harness 可恢复？
持久化 session events、运行状态和外部 job IDs；重启后从 durable boundary 重建 messages/context，并保证 Tool side effects 的幂等性或可识别性。

---

## J. 30 秒回答模板

### “你理解的 Agent Harness 是什么？”

> 我把 Harness 理解为 Agent 的运行时层。LLM 只负责在当前上下文里产生文本或 Tool Call，而 Harness 负责 turn/step 生命周期、上下文和 Tool schema 组装、工具路由执行、Session 事件记录、错误与终止策略，以及 Plugin/Policy/Trace 等扩展点。我在项目里把 MCP、Skill 和 Episodic Memory 都做成 Plugin，通过 Tool/Context Registry 接入同一个 Agent Loop，因此新增能力不用继续修改业务主循环。同时记录每一步实际的 model-visible messages 和 Tool schemas，用于 replay 和调试。

### “你的 Level 4 和 DeepSeek Harness 是什么关系？”

> 我没有复刻 DeepSeek Harness，也没有实现 Cordis。我阅读它公开的 architecture 文档后，抽取了 plugin composition、session log、tool/system-prompt registry、turn/step 和 runtime events 这些概念，用 Python 做了一个教学型小 Harness，目的是理解这些抽象为什么存在，再回去读真实源码。
