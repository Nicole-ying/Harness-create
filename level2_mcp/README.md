# Level 2 — MCP：把本地 Tool 变成标准化外部能力

Level 1 已经会了：

```text
LLM -> tool_call -> Python Runtime -> 本地函数 -> tool result -> LLM
```

Level 2 只做一个核心升级：**Tool 不再必须写死在 Agent 进程里，而是由独立 MCP Server 标准化暴露，Agent/Host 通过 MCP Client 发现并调用它。**

最终结构：

```text
                         Host / Agent Application
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  User -> LLM -> tool_call -> Agent Loop                 │
│                         │                               │
│                         ▼                               │
│                    MCP Client                           │
│                         │                               │
└─────────────────────────┼───────────────────────────────┘
                          │ MCP
                          │ tools/list
                          │ tools/call
                          ▼
                 ┌──────────────────┐
                 │    MCP Server    │
                 │                  │
                 │ get_training...  │
                 │ get_component... │
                 └────────┬─────────┘
                          │
                          ▼
                    backend.py
                          │
                          ▼
                    experiment data
```

最重要的一句话：

> **LLM 本身不会说 MCP。Host/Agent Runtime 里面的 MCP Client 才负责与 MCP Server 通信。LLM 仍然只是看到 Tool Schema，并输出 Tool Call。**

---

## 0. 先注意 SDK 版本

本教程使用当前 MCP Python SDK v2：

```python
from mcp.server import MCPServer
```

你在旧教程里可能看到：

```python
from mcp.server.fastmcp import FastMCP
```

那是 v1 风格。当前 v2 已将高层 server 类重命名为 `MCPServer`。

`requirements.txt` 因此固定在：

```text
mcp[cli]>=2.0.0,<3.0.0
```

---

## 1. 文件结构

```text
level2_mcp/
├── backend.py                  # 普通 Python 数据能力，不知道 MCP 的存在
├── mcp_server.py               # 用 @mcp.tool() 把能力暴露为 MCP Tools
├── step1_inprocess_client.py   # 2A：同进程 Client，先学 tools/list + tools/call
├── step2_stdio_client.py       # 2B：Server 变成独立子进程，使用 stdio transport
├── step3_mcp_agent.py          # 2C：LLM Agent 通过 MCP 调用外部 Tool
├── mcp_adapter.py              # MCP Tool Schema <-> LLM Tool Schema 的适配层
├── llm_client.py               # DeepSeek / OpenAI-compatible LLM client
├── mock_data/
├── .env.example
├── requirements.txt
├── LEARNING_NOTES.md
└── INTERVIEW_QUESTIONS.md
```

---

# 2A — 先不要碰网络：理解 MCP Server / Client

先安装：

```bash
cd level2_mcp
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

然后运行：

```bash
python step1_inprocess_client.py
```

这里：

```python
async with Client(mcp) as client:
```

Client 直接连接 Python 里的 `MCPServer` 对象，没有 stdio、端口或 HTTP。

重点观察：

```python
listed = await client.list_tools()
```

对应 MCP 的 Tool Discovery。

每个 Tool 会有：

```text
name
description
input_schema
```

然后：

```python
result = await client.call_tool(
    "get_training_feedback",
    {"iteration": 1},
)
```

你第一次从 MCP Client 正式调用 MCP Tool。

请观察：

```text
result.is_error
result.structured_content
result.content
```

### 为什么先做 in-process？

为了证明 MCP 有两个不同问题：

```text
能力定义/协议语义
```

和：

```text
通信 transport
```

不是一回事。

---

# 2B — 再把 MCP Server 拆成独立进程

运行：

```bash
python step2_stdio_client.py
```

这次 Client 不再直接拿 `mcp` 对象。

而是：

```python
server = StdioServerParameters(
    command=sys.executable,
    args=[str(SERVER_FILE)],
)

transport = stdio_client(server)

async with Client(transport) as client:
    ...
```

调用关系变成：

```text
step2_stdio_client.py
        │
        │ 启动子进程
        ▼
mcp_server.py
        │
        │ stdin/stdout
        ↕
   MCP Client
```

### `StdioServerParameters` 是 MCP Client 吗？

不是。

它只是描述：

```text
用什么命令启动 Server？
启动参数是什么？
```

真正 transport 是：

```python
stdio_client(server)
```

真正高层 MCP Client 是：

```python
Client(transport)
```

这三层要分清。

---

# 3. `mcp_server.py` 为什么这么短？

核心只有：

```python
mcp = MCPServer("CREATE Reward Analysis")

@mcp.tool()
def get_training_feedback(iteration: int):
    """Read PPO evaluation feedback for one reward iteration."""
    return read_training_feedback(iteration)
```

MCP SDK 会根据：

```text
函数名
Docstring
Python type hints
```

生成 Tool 的：

```text
name
description
input JSON Schema
```

所以 Level 1 里我们手写的 Tool Schema，在 MCP Server 这一侧可以由 SDK 自动生成。

但注意：

```python
read_training_feedback()
```

仍然只是普通业务函数。

MCP 没有替代业务代码，只是提供了标准化访问层。

---

# 4. 用 MCP Inspector 看 Server

安装了 `mcp[cli]` 后，可以在 `level2_mcp` 目录运行：

```bash
mcp dev mcp_server.py
```

Inspector 会像真正的 Host 一样连接 Server，你可以观察：

```text
server information
Tools
input schema
tool call
result
```

这一步非常推荐，因为它让你直观看到：**MCP Server 可以脱离我们自己的 Agent 独立存在。**

---

# 2C — 最关键：把 MCP 接回 LLM Agent

先配置：

```powershell
Copy-Item .env.example .env
```

DeepSeek：

```env
PROVIDER=deepseek
DEEPSEEK_API_KEY=你的真实key
DEEPSEEK_MODEL=你账号实际支持的模型ID
```

然后：

```bash
python step3_mcp_agent.py
```

完整流程：

```text
1. Host 启动 MCP Server

2. MCP Client
   -> tools/list

3. Server 返回 MCP Tool definitions

4. mcp_adapter.py
   MCP Tool
      ↓
   OpenAI-compatible Tool Schema

5. Host 把 Tool Schema 给 LLM

6. LLM 返回：
   tool_call(name, arguments)

7. Host 不再执行本地 execute_tool()
   而是：
   await mcp_client.call_tool(name, arguments)

8. MCP Server 执行真实 Python backend

9. MCP Tool Result 回 Host

10. Host 把结果放进 role=tool message

11. LLM 继续推理 / 再调用 Tool / 最终回答
```

这就是 Level 1 到 Level 2 真正发生的变化。

---

# 5. MCP 和 Function Calling 到底什么关系？

Level 1：

```text
LLM Function Calling
       ↓
本地 Python Tool Registry
       ↓
Python Function
```

Level 2：

```text
LLM Function Calling
       ↓
Host / Agent Runtime
       ↓
MCP Client
       ↓
MCP Protocol
       ↓
MCP Server
       ↓
Python Function / API / DB / Service
```

因此：

> **Function Calling 解决“模型如何表达我要调用什么”。**

> **MCP 解决“外部能力如何以统一协议被 Host 发现和调用”。**

它们不是竞争关系，可以同时存在。

---

# 6. `mcp_adapter.py` 为什么存在？

MCP Server 返回的 Tool Definition 是 MCP 数据结构：

```text
Tool
├── name
├── description
└── input_schema
```

而 OpenAI-compatible Chat Completion 需要：

```python
{
    "type": "function",
    "function": {
        "name": ...,
        "description": ...,
        "parameters": ...,
    },
}
```

所以 Host 需要一个 adapter：

```text
MCP Tool Definition
        ↓
provider-specific LLM Tool Schema
```

以后如果换 Claude 原生 Messages API，MCP Server 可以完全不动，只换 Provider Adapter。

这就是标准化的重要价值之一。

---

# 7. Transport：stdio / Streamable HTTP

当前教程只真正实现 `stdio`。

### stdio

```text
Host 启动本地子进程
stdin/stdout 传 MCP 消息
```

适合：

```text
本地工具
桌面 Agent
IDE / coding agent
教学
```

### Streamable HTTP

```text
Host
 ↓ HTTP
远程 MCP Server
```

适合：

```text
远程服务
团队共享能力
生产部署
```

旧教程还可能出现 `SSE` transport。当前 MCP SDK 已将 SSE 视为被 Streamable HTTP 取代的旧方案，新项目不要优先从 SSE 开始。

Level 2 先把 stdio 搞懂；以后做工程化时再加 Streamable HTTP、认证、超时和权限。

---

# 8. 一个非常重要的安全边界

本教程 MCP Server 全部是 **read-only**：

```text
get_training_feedback
get_component_stats
```

暂时没有：

```text
launch_training
modify_reward_file
delete_run
execute_shell
```

原因是：一旦模型可以触发有副作用的 Tool，就必须考虑：

```text
权限
参数校验
审批
Sandbox
超时
重试
幂等性
审计
```

这些以后会逐渐进入 Harness / Runtime 层。

---

# 9. Level 2 过关标准

你应该可以不看代码解释：

```text
Host
MCP Client
MCP Server
Tool
Tool Discovery
Tool Call
Transport
stdio
Streamable HTTP
```

并能画出：

```text
User
 ↓
LLM
 ↓ tool_call
Host / Agent Loop
 ↓
MCP Client
 ↓
MCP Server
 ↓
Backend
```

你还应该能够独立写出：

```python
from mcp.server import MCPServer

mcp = MCPServer("demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

if __name__ == "__main__":
    mcp.run()
```

以及用 MCP Client：

```python
listed = await client.list_tools()
result = await client.call_tool("add", {"a": 1, "b": 2})
```

做到这里，才算真正学会 MCP 的基础，而不是只知道“模型可以连工具”。

下一层 Level 3 才开始解决另一个问题：

> Agent 已经“能做事”，但它怎么知道面对某类问题应该采用什么方法？

那时再加入 Skill，并逐渐区分 Skill、Memory 和 Context。
