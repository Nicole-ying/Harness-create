# MCP wire-level mental model

你不需要手写这些 JSON，Python SDK 会处理。但面试时知道 wire 上发生什么很有帮助。

> 下面是**简化示意**，省略 SDK/协议版本附带的 `_meta`、request state 等字段。不要把它当成逐字抓包结果。

## 1. Tool discovery

Client 想知道 Server 有什么工具：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

Server 返回：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_training_feedback",
        "description": "Read PPO evaluation feedback for one reward iteration.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "iteration": {"type": "integer"}
          },
          "required": ["iteration"]
        }
      }
    ]
  }
}
```

Python 高层代码对应：

```python
listed = await client.list_tools()
```

---

## 2. Tool call

Client 调工具：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_training_feedback",
    "arguments": {
      "iteration": 1
    }
  }
}
```

Server 执行真实 Python function 后返回结果。

Python 高层代码：

```python
result = await client.call_tool(
    "get_training_feedback",
    {"iteration": 1}
)
```

---

## 3. 最容易混淆的两套 JSON

### LLM Function Calling

模型 API 返回的可能是：

```json
{
  "name": "get_training_feedback",
  "arguments": "{\"iteration\":1}"
}
```

这是：

```text
LLM -> Host
```

### MCP tools/call

Host 再把模型意图路由成 MCP 请求：

```text
Host/MCP Client -> MCP Server
```

所以一次 Agent Tool Call 实际跨了两个边界：

```text
LLM Function Calling boundary
             ↓
Host routing / adapter
             ↓
MCP protocol boundary
```

这也是为什么“会 Function Calling”不等于“会 MCP”。

---

## 4. MCP 是不是只有 Tools？

不是。MCP Server 还可以暴露 Resources 和 Prompts 等能力。本 Level 只做 Tools，因为我们要先把最重要的 Agent Tool 调用链学透。

Level 2 的重点不是背协议所有 method，而是能解释：

```text
Discovery -> Call -> Result
```

以及这些行为在 Host / Client / Server 中分别是谁负责。
