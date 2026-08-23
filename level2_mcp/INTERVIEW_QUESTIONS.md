# Level 2 — MCP 面试题

下面这些题如果能结合本仓库代码回答，MCP 基础就够扎实了。

## 1. MCP 是什么？

答题关键词：

```text
标准协议
LLM application / Host
外部 Tools / Resources / Prompts
能力发现与调用
模型与外部能力解耦
```

不要只回答“让大模型调用工具”。Tool Calling 在 MCP 之前就能做到。

---

## 2. MCP 解决的核心问题是什么？

参考：

> MCP 主要解决不同 Agent/LLM Host 与外部能力之间缺少统一接入接口的问题。Server 按统一协议暴露能力，Host 内 MCP Client 可以发现并调用这些能力，减少为每个模型应用重复写私有集成代码。

---

## 3. MCP 和 Function Calling 有什么区别？

参考：

```text
Function Calling
= 模型如何表达“我要调用哪个函数、参数是什么”

MCP
= Host 如何以标准方式发现、连接、调用外部能力
```

本教程中两者同时存在。

---

## 4. LLM 会直接连接 MCP Server 吗？

不会。

```text
LLM
 ↓ tool_call
Host / Agent Runtime
 ↓
MCP Client
 ↓
MCP Server
```

模型通常只看到经过 Host 适配后的 Tool Schema。

---

## 5. Host、MCP Client、MCP Server 分别是什么？

Host：完整 AI Application / Agent Runtime。

Client：Host 内负责说 MCP 协议的一侧。

Server：标准化暴露外部能力的一侧。

---

## 6. 一个 Host 可以连接多个 MCP Server 吗？

可以。实际系统通常会为不同外部能力连接多个 Server，例如 Git、文件、数据库、实验平台等，再由 Host 聚合/路由能力。

---

## 7. MCP Server 自己需要 API Key 调 LLM 吗？

不一定，通常完全不需要。Server 的职责可能只是访问数据库、文件、GitHub、业务 API 等。是否调用 LLM 是它自己的业务实现选择，不是 MCP 的必需部分。

---

## 8. `@mcp.tool()` 做了什么？

在当前高层 Python SDK 中，它把普通 Python 函数注册成 MCP Tool，并可根据函数名、docstring、type hints 等生成 Tool metadata 与输入 JSON Schema。

---

## 9. 为什么旧教程是 `FastMCP`，你的代码是 `MCPServer`？

当前 Python SDK v2 已将高层 `FastMCP` 类重命名为 `MCPServer`。看 MCP 教程时首先要确认 SDK 大版本。

---

## 10. `list_tools()` 有什么意义？

动态能力发现。

Level 1 的 Tool Schema 是写死在 Agent 中的；Level 2 可以运行时从 MCP Server 获取当前 Tool catalog。

---

## 11. MCP Tool Definition 通常包含哪些关键内容？

基础需要掌握：

```text
name
description
input_schema
```

这些足够让 Host 理解 Tool 是什么以及参数怎么构造。

---

## 12. 为什么 MCP Tool Schema 不能直接假设就是 OpenAI Tool Schema？

因为 MCP 协议数据结构和模型厂商 API 的函数调用格式属于不同接口。Host 通常需要 Provider Adapter，把 MCP Tool Definition 转成目标模型 API 所要求的 schema。

---

## 13. `call_tool()` 返回什么？

不是简单字符串。当前 SDK 中结果可包含：

```text
content
structured_content
is_error
meta 等
```

程序应显式处理错误和结构化内容。

---

## 14. `content` 和 `structured_content` 有什么区别？

`content` 适合模型/文本内容块消费；`structured_content` 是结构化数据，更适合程序可靠解析和后续逻辑。

---

## 15. Tool 出错时为什么不应该直接崩掉整个 Agent？

Tool failure 本身可以成为 Agent 的 observation。Runtime 可以把错误结果返回给模型，由模型决定重试、换 Tool、修改参数或停止。同时 Runtime 仍应设置最大重试、超时等边界。

---

## 16. stdio transport 是什么？

Host 启动 MCP Server 子进程，通过标准输入/输出交换 MCP 协议消息。适合本地工具、桌面 Agent、IDE 等。

---

## 17. stdio Server 为什么不能随便 `print()` 到 stdout？

因为 stdout 是协议通信通道。非协议文本可能污染 wire data。日志应走规范 logging/stderr。

---

## 18. `StdioServerParameters`、`stdio_client()`、`Client()` 有什么区别？

```text
StdioServerParameters
= 如何启动子进程的配置

stdio_client(...)
= stdio transport

Client(...)
= 高层 MCP Client
```

三者不要混为一个东西。

---

## 19. 为什么 MCP Python 代码大量使用 `async/await`？

MCP 调用通常涉及进程/网络 IO，异步模型可以在等待外部 IO 时避免阻塞整个应用，并适合同时管理多个连接和工具请求。

---

## 20. stdio 和 Streamable HTTP 怎么选？

```text
stdio
= 本地子进程、桌面/IDE、本机能力

Streamable HTTP
= 远程服务、部署、共享能力
```

新项目不应优先基于旧 SSE transport 设计。

---

## 21. 为什么本教程 MCP Server 只做 read-only？

因为写文件、启动训练、Shell 等副作用 Tool 会引入权限、审批、幂等性、Sandbox、审计、超时等更复杂的 Runtime 安全问题。先把协议调用链学清楚，再引入副作用。

---

## 22. MCP 是否等于 API Gateway？

不等于。API Gateway 更关注 HTTP 服务治理、路由、认证、限流等；MCP 是面向 AI Host 的上下文与能力协议。MCP Server 底下可以再调用普通 REST API/API Gateway。

---

## 23. MCP 是否等于 Agent Framework？

不等于。MCP 不负责完整 Agent Loop、Memory、Skill、Planning、Context 管理、Stop Policy 等。它主要是标准化外部能力接入。

---

## 24. MCP 和 Harness 什么关系？

MCP 是 Harness 可能管理的一类能力接入机制。

Harness/Runtime 通常还负责：

```text
Agent Loop
MCP lifecycle
Tool routing
Context
Session
Memory
Skill
Retry/Timeout
Sandbox
Observability
```

---

## 25. 你这个项目里一次 MCP Tool Call 的完整链路是什么？

推荐按代码回答：

```text
用户请求
↓
LLM 收到 MCP tools 经 adapter 转换后的 Tool Schema
↓
LLM 生成 tool_call
↓
step3_mcp_agent.py 解析 name + arguments
↓
mcp_client.call_tool(...)
↓
MCP Server 收到 tools/call
↓
@mcp.tool() 对应函数执行
↓
backend.py 读取实验数据
↓
CallToolResult 回 MCP Client
↓
Host 转成 role=tool message
↓
再次调用 LLM
↓
继续 Tool Call 或最终回答
```

如果这一题可以完全不看代码讲出来，Level 2 基本过关。

---

# 30 秒面试版回答

面试官问“你怎么理解 MCP？”时可以回答：

> 我把 MCP 理解为 Agent Host 与外部能力之间的标准接入协议。模型的 Function Calling 解决的是模型输出哪个 Tool 和参数，而 MCP 解决的是 Host 如何动态发现和标准调用外部 Tool。我的学习项目里把 PPO 实验分析能力封装成独立 MCP Server，Host 通过 MCP Client 的 tools/list 获取 Tool Definition，再适配成模型的 Function Calling schema；模型产生 Tool Call 后，由 Host 路由为 MCP tools/call，结果再作为 Tool observation 写回消息历史。因此 LLM 本身不直接连接 MCP Server，MCP 的连接、生命周期和路由是在 Agent Runtime 一侧完成的。
