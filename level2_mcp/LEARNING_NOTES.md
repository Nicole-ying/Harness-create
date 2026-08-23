# Level 2 学习笔记：MCP 要真正理解的 12 件事

## 1. MCP 不是模型

MCP 是协议与能力接入层。模型仍然通过自己的 API 完成推理。

```text
LLM != MCP Client != MCP Server
```

## 2. Host / Client / Server 三个角色

### Host

用户真正使用的 LLM Application / Agent Runtime。

例如本教程的 `step3_mcp_agent.py`。

### MCP Client

运行在 Host 内，负责和某一个 MCP Server 通信。

### MCP Server

暴露 Tools / Resources / Prompts 等标准能力，本身不直接和 LLM 对话。

---

## 3. Level 1 的 Tool 没消失

Level 1：

```text
Tool = Python function + schema + runtime dispatcher
```

Level 2：

```text
Tool 的真实能力仍然是 Python function
MCP 负责把能力标准化暴露给外部 Host
```

所以 MCP 不是“新的 Tool”，而是 Tool 接入协议。

---

## 4. Tool Discovery 很关键

Level 1 的 `TOOL_SCHEMAS` 是手工写在 Agent 代码里的。

Level 2：

```python
listed = await client.list_tools()
```

Host 可以运行时发现 Server 当前提供什么能力。

这就是：

```text
hard-coded tools
        ↓
dynamic discovery
```

---

## 5. Tool Schema 从哪里来？

`MCPServer` 的 `@mcp.tool()` 可以根据：

```text
function name
function docstring
type hints
default values
```

生成 MCP Tool 的 JSON Schema。

例如：

```python
@mcp.tool()
def get_training_feedback(iteration: int) -> dict:
    """Read PPO feedback."""
```

Client discovery 后看到：

```text
name = get_training_feedback
description = Read PPO feedback.
input_schema = {... iteration: integer ...}
```

---

## 6. 为什么 MCP Tool 还要转成 LLM Tool Schema？

因为 MCP 和模型厂商 API 是两套接口。

MCP Tool：

```text
name
description
input_schema
```

OpenAI-compatible Function Tool：

```json
{
  "type": "function",
  "function": {
    "name": "...",
    "description": "...",
    "parameters": {}
  }
}
```

所以 `mcp_adapter.py` 属于 Host 侧 Provider Adapter。

非常重要：

> MCP Server 不应该为了某一个具体模型厂商改自己的协议接口。

---

## 7. LLM 根本不知道 MCP Server 的地址

模型看到的只是：

```text
Tool name
description
parameters
```

真正知道：

```text
Server 在哪里
怎么连接
stdio 还是 HTTP
怎么认证
```

的是 Host / MCP Client。

---

## 8. `tools/list` 和 `tools/call`

基础 MCP Tool 使用可以先抽象成两类协议行为：

```text
tools/list
```

发现能力。

```text
tools/call
```

执行能力。

你的 Agent 并不是直接 import Server 里的业务函数后执行，而是让 MCP Client 发出标准调用请求。

---

## 9. `stdio` 到底是什么？

stdio = standard input / standard output。

Client 启动 MCP Server 子进程：

```text
Host process
    │
    ├── stdin  -> server
    └── stdout <- server
```

MCP 协议数据在这两条管道上交换。

因此一个重要工程规则是：

> stdio MCP Server 不应该随便把普通日志打印到协议 stdout。

真正生产代码应使用规范 logging / stderr，避免污染协议流。

---

## 10. 为什么代码开始出现 `async/await`？

MCP Client 调用本质上涉及 IO：

```text
进程通信
HTTP
远程服务
```

等待 IO 时不应该阻塞整个应用，因此 Python SDK 大量使用 async context manager 与 `await`。

你先记：

```python
async with Client(...) as client:
    result = await client.call_tool(...)
```

含义就是：

```text
异步建立/管理连接生命周期
等待远程/外部 Tool 返回结果
```

Level 2 不要求你现在把 asyncio 源码学透。

---

## 11. MCP Tool Result 不只是字符串

你会看到：

```text
result.content
result.structured_content
result.is_error
```

可以粗略理解：

```text
content
= 面向模型/文本消费的内容块

structured_content
= 结构化结果，程序更容易可靠处理

is_error
= Tool 是否以错误结果结束
```

如果 Tool 返回结构化 Python 数据，MCP SDK 可以生成相应 structured output。

---

## 12. MCP 和 Harness 的关系

现在的 `step3_mcp_agent.py` 已经开始承担一点 Harness 职责：

```text
连接 Server
发现 Tools
把 schema 给 LLM
解析 tool_call
路由到 MCP Client
把 result 放回 messages
限制 Agent rounds
错误处理
```

但它还只是手写的小 Runtime。

以后 DeepSeek Harness 会把这些能力系统化：

```text
MCP lifecycle
Tool routing
Context
Session
Skill
Sandbox
Observability
Agent Loop
```

所以学习顺序一定要保持：

```text
Level 1 本地 Tool Calling
      ↓
Level 2 MCP
      ↓
Level 3 Skill / Memory / Context
      ↓
Level 4 Harness
```

---

# 自己必须做的 5 个实验

1. 给 `mcp_server.py` 增加：

```python
@mcp.tool()
def get_available_iterations() -> list[int]:
    ...
```

然后不要修改 Agent Tool Schema，观察 `list_tools()` 是否自动发现。

2. 把 `iteration` 从 `int` 改成 `str`，重新打印 `tool.input_schema`，观察 Schema 如何变化。

3. 调用一个不存在的 iteration，例如 99，观察 `result.is_error` 和返回内容。

4. 在 `step3_mcp_agent.py` 中删除 `get_component_stats` Tool 后，观察模型诊断证据如何变化。

5. 临时在 `mcp_adapter.py` 不把某个 MCP Tool 传给 LLM，思考：Server 有能力为什么模型还是用不了？

答案：能力是否存在、Host 是否发现、Host 是否暴露给模型，是三层不同问题。

---

# Level 2 过关自测

不看代码回答：

```text
为什么 MCP Server 不直接调用 LLM？
为什么 MCP 和 Function Calling 可以同时存在？
为什么要 tools/list？
为什么 MCP Tool 还需要转成模型 Tool Schema？
stdio 连接时是谁启动 Server？
真正执行函数的是谁？
LLM 是否知道 MCP Server 地址？
MCP Tool Result 如何回到 LLM？
```

这些能讲清楚，再进入 Level 3。
