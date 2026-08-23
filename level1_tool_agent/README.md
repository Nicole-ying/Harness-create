# Level 1 — Tool Calling + 第一个 Agent Loop

Level 0 里，LLM 只能看我们提前塞进 Prompt 的数据。

Level 1 只增加一个核心能力：**让模型自己决定是否需要调用工具，并由 Python Runtime 真正执行工具。**

这一步是从“普通 LLM Application”跨到“Agent”的关键。

---

## 1. Level 0 和 Level 1 的区别

Level 0：

```text
Python 决定读什么
    ↓
读取 JSON
    ↓
拼进 Prompt
    ↓
LLM 回答
```

Level 1：

```text
用户只提出任务
    ↓
LLM 判断缺少什么信息
    ↓
LLM 产生 tool_call
    ↓
Python Runtime 执行真实函数
    ↓
tool result 回到 messages
    ↓
LLM 继续判断
```

最重要的一句话：

> **LLM 不会真正执行 Python 函数。LLM 只是生成“我想调用哪个 Tool、参数是什么”；真正执行 Tool 的永远是我们的程序。**

---

## 2. 文件结构

```text
level1_tool_agent/
├── step1_manual_tool.py       # 1A：先证明 Tool 本质只是普通 Python 函数
├── step2_single_tool_call.py  # 1B：第一次真实 Function Calling
├── step3_agent_loop.py        # 1C：第一个 while/for Agent Loop
├── tools.py                   # Tool 函数 + Tool Schema + 白名单执行器
├── llm_client.py              # 返回完整 response，不能只拿 content
├── mock_data/
│   ├── iter_01_training_feedback.json
│   └── iter_01_component_stats.json
├── .env.example
├── requirements.txt
├── LEARNING_NOTES.md
└── INTERVIEW_QUESTIONS.md
```

教学数据只是从 Level 0 的紧凑案例拆成两个文件，方便观察“模型逐步读取证据”的过程，不代表完整 CREATE 原始日志。

---

## 3. 安装和配置

```bash
cd level1_tool_agent
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

DeepSeek：

```env
PROVIDER=deepseek
DEEPSEEK_API_KEY=你的真实key
DEEPSEEK_MODEL=你的账号实际可用模型名
```

如果是 OpenAI-compatible 第三方平台：

```env
PROVIDER=openai_compatible
OPENAI_COMPATIBLE_API_KEY=你的key
OPENAI_COMPATIBLE_BASE_URL=平台给你的base_url
OPENAI_COMPATIBLE_MODEL=平台给你的model id
```

不要提交真实 `.env`。

---

# 4. Step 1A：Tool 其实只是普通函数

运行：

```bash
python step1_manual_tool.py
```

你会看到 Python 直接调用：

```python
result = read_training_feedback(iteration=1)
```

这里还不是 Tool Calling，因为决定调用函数的人是程序员。

本质仍然只是：

```text
Python
  ↓
read_training_feedback(1)
  ↓
读 JSON
  ↓
return dict
```

所以“Tool”这个词不要神化。**真实执行能力最终仍然是普通代码。**

---

# 5. Tool Schema 是什么？

`tools.py` 里同时存在两种完全不同的东西。

第一种是真函数：

```python
def read_training_feedback(iteration: int):
    ...
```

它真的能执行。

第二种是 Tool Schema：

```python
{
    "type": "function",
    "function": {
        "name": "read_training_feedback",
        "description": "读取某一轮 PPO 的训练反馈",
        "parameters": {
            "type": "object",
            "properties": {
                "iteration": {"type": "integer"}
            },
            "required": ["iteration"]
        }
    }
}
```

Schema 本身不会读文件。

它只是告诉模型：

```text
你有一个能力
名字：read_training_feedback
作用：读取训练反馈
输入参数：iteration，整数
```

因此：

```text
Python Function = 真正的能力
Tool Schema     = 给 LLM 看的能力说明书
```

---

# 6. Step 1B：第一次真实 Tool Call

运行：

```bash
python step2_single_tool_call.py
```

这一版为了看清协议，故意使用：

```python
tool_choice="required"
```

强制模型先调用一个工具。

第一次 LLM 请求大概是：

```python
response = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=[...],
    tool_choice="required"
)
```

模型如果决定调用工具，不会直接返回最终答案，而会返回类似：

```text
response
└── choices[0]
    ├── finish_reason = "tool_calls"
    └── message
        ├── content = None
        └── tool_calls
            └── [0]
                ├── id
                ├── type = "function"
                └── function
                    ├── name = "read_training_feedback"
                    └── arguments = "{\"iteration\":1}"
```

注意：

```python
call.function.arguments
```

通常是 **JSON 字符串**，不是已经解析好的 Python dict，所以需要：

```python
arguments = json.loads(call.function.arguments)
```

---

# 7. 谁真正执行 Tool？

模型只产生：

```text
name = read_training_feedback
arguments = {"iteration": 1}
```

然后我们的 Python Runtime 才执行：

```python
tool_result = execute_tool(
    call.function.name,
    arguments
)
```

`execute_tool()` 做三件事：

```text
检查 Tool 是否在白名单
    ↓
验证参数
    ↓
调用真实 Python 函数
```

不要写：

```python
eval(model_generated_text)
```

模型生成的 Tool 参数必须当作不可信输入处理。

---

# 8. 为什么有 `tool_call_id`？

假设模型同时请求两个工具：

```text
call A → id=abc123
call B → id=xyz789
```

Runtime 执行完后，需要告诉模型每个结果对应哪个请求：

```python
{
    "role": "tool",
    "tool_call_id": "abc123",
    "content": "..."
}
```

因此 `tool_call_id` 相当于请求与结果之间的关联 ID。

---

# 9. 为什么一定要把 assistant 的 tool_call 放回 messages？

正确历史：

```text
system
user
assistant(tool_call id=abc123)
tool(tool_call_id=abc123, result=...)
assistant(final answer)
```

而不是直接：

```text
system
user
tool result
```

模型必须看到：

> “上一条 assistant 消息是我请求调用 abc123，现在这条 tool message 是 abc123 的执行结果。”

这也是为什么 `llm_client.py` 里专门有：

```python
assistant_tool_message(message)
```

用于保留 tool call 结构。

---

# 10. Step 1C：第一个 Agent Loop

运行：

```bash
python step3_agent_loop.py
```

这次不强制特定工具，而是：

```python
tool_choice="auto"
```

模型可以选择：

```text
直接回答
或
read_training_feedback
或
read_component_stats
```

核心循环只有这一件事：

```text
LLM
 ↓
有 tool_calls 吗？
 ├─ 没有 → 最终回答 → stop
 └─ 有
      ↓
   Runtime 执行 Tool
      ↓
   append tool result
      ↓
   再问 LLM
      ↓
   重复
```

伪代码：

```python
while True:
    response = llm(messages, tools)

    if response.message.tool_calls:
        execute_tools()
        append_results()
    else:
        return response.message.content
```

这就是第一个最小 Agent Loop。

---

# 11. Level 1 的 messages 会长成什么样？

Level 0：

```text
messages[0] system
messages[1] user
```

Level 1 可能变成：

```text
messages[0] system
messages[1] user
messages[2] assistant + tool_calls
messages[3] tool result
messages[4] assistant + tool_calls
messages[5] tool result
messages[6] assistant final answer
```

所以 Agent 本质上并不是一个神秘的新模型。

很多时候它只是：

> **普通 LLM + 可调用工具 + 运行时循环 + 状态/messages。**

---

# 12. `tool_choice` 三种最重要模式

```python
tool_choice="none"
```

禁止调用工具，只允许直接回答。

```python
tool_choice="auto"
```

让模型决定是回答还是调用工具。

```python
tool_choice="required"
```

要求模型至少调用一个工具。

Level 1B 用 `required` 是为了教学；Level 1C 才用 `auto` 形成真正的自主决策。

DeepSeek 当前 Chat Completions 文档也使用 `tools` + `tool_choice` 这一套兼容结构：
https://api-docs.deepseek.com/api/create-chat-completion/

---

# 13. Level 1 还没有什么？

现在仍然没有：

```text
MCP
Skill
RAG
Memory system
Context manager
Sandbox
Sub-agent
DeepSeek Harness
```

Tool 仍然是本地 Python 函数。

Level 2 才会把这些函数从 Agent 程序里拆出去，变成：

```text
Agent Runtime
    ↓
MCP Client
    ↓
MCP Server
    ↓
read_training_feedback()
```

只有走到这一步，你才会真正理解 MCP 解决了上一版什么问题。

---

# 14. Level 1 过关标准

不要只看“代码跑通”。你需要能不用看代码解释：

1. Tool 本质是什么？
2. Tool Schema 和 Python Function 有什么区别？
3. LLM 有没有真正执行 Tool？
4. `tool_calls` 在 response 的什么位置？
5. 为什么 `function.arguments` 要 `json.loads()`？
6. `finish_reason="tool_calls"` 表示什么？
7. `tool_call_id` 有什么用？
8. 为什么 Tool Result 的 role 是 `tool`？
9. 为什么必须把 assistant tool-call message 放回历史？
10. `tool_choice=none/auto/required` 分别是什么？
11. 一个最小 Agent Loop 怎么写？
12. 为什么要限制最大 Agent rounds？
13. 为什么模型生成的 Tool 参数必须验证？
14. Level 1 和 MCP 的差别是什么？

这些能讲清楚，再进入 Level 2。
