# Level 1 面试题：Tool Calling + Agent Loop

下面这些问题对应 AI 应用工程师最基础的一层 Agent 能力。

## 1. Tool Calling 和普通函数调用有什么区别？

普通函数调用由程序员在代码里决定：

```python
read_training_feedback(1)
```

Tool Calling 中，程序先把函数能力以 schema 告诉 LLM，由 LLM 产生“调用哪个工具、参数是什么”的结构化请求，再由 Runtime 真正执行函数。

## 2. LLM 会不会真的执行 Python 函数？

不会。LLM 只生成 `tool_calls`。执行函数的是宿主程序 / Agent Runtime。

## 3. Tool Schema 是什么？

是给模型看的能力描述，一般包括：

```text
name
description
parameters(JSON Schema)
```

它告诉模型“有哪些能力、什么时候用、输入参数长什么样”。

## 4. Tool Schema 和真实 Python Function 是同一个东西吗？

不是。

```text
Schema = 描述
Function = 执行实现
```

Schema 存在并不意味着函数一定实现；函数存在也不意味着模型知道它存在。

## 5. `tool_choice="auto"` 是什么意思？

让模型自己决定：直接回答，还是调用一个或多个工具。

## 6. `tool_choice="required"` 呢？

要求模型至少产生一个 Tool Call。教学或强制检索场景可能使用。

## 7. `tool_choice="none"` 呢？

禁止 Tool Calling，只允许模型直接回答。

## 8. Tool Call 在 response 的哪里？

典型路径：

```python
response.choices[0].message.tool_calls
```

## 9. 一个 Tool Call 里最重要的字段有哪些？

```python
call.id
call.function.name
call.function.arguments
```

## 10. 为什么 `function.arguments` 经常需要 `json.loads()`？

因为 API 返回的 arguments 通常是 JSON 字符串，例如：

```python
'{"iteration":1}'
```

要转成 Python dict 才方便验证和执行。

## 11. 模型生成的 Tool 参数可靠吗？

不能完全信任。可能非法 JSON、漏参数、多参数、类型错误或 hallucinate 工具名，所以 Runtime 必须验证。

## 12. 为什么不要 `eval(model_output)`？

模型输出是不可信输入。直接 `eval()` 可能执行任意代码，存在严重安全风险。

## 13. `finish_reason="tool_calls"` 表示什么？

表示这一轮模型没有自然结束，而是选择请求工具执行。

## 14. `tool_call_id` 有什么作用？

把某个 Tool Result 和模型之前发出的具体 Tool Call 对应起来。并行或多工具调用时尤其重要。

## 15. Tool Result 为什么是 `role="tool"`？

因为它不是用户说的话，也不是 assistant 自己生成的结论，而是外部执行环境返回的 Observation。

## 16. 为什么必须把 assistant 的 tool-call message 也保留在 messages？

下一次调用模型时，需要完整看到：模型请求了哪个 Tool、call id 是什么、随后收到了什么结果。否则对话状态会断裂。

## 17. 一个最小 Agent Loop 怎么写？

核心逻辑：

```python
while True:
    response = llm(messages, tools)
    if response.message.tool_calls:
        execute_tools()
        append_tool_results()
    else:
        return response.message.content
```

## 18. 为什么这就可以叫最小 Agent？

因为模型开始根据当前状态自主选择下一步 Action（Tool Call），执行环境返回 Observation，模型再继续决策，而不是只做一次静态 Prompt → Response。

## 19. 为什么 Agent Loop 需要最大轮次？

防止模型重复调用、无限循环、成本失控或服务长时间阻塞。

## 20. Tool Calling 和 MCP 是什么关系？

Tool Calling 解决“模型如何表达要调用某个工具”。

MCP 进一步解决“外部工具和资源如何通过标准协议接入 Agent Runtime”。

所以 Level 1 仍是本地 Tool，Level 2 才把它们放到 MCP Server 后面。

## 21. Tool description 为什么重要？

模型通常根据 tool name、description 和参数 schema 判断什么时候调用哪个工具。描述含糊会导致 routing 质量下降。

## 22. 如果一个 Agent 有 100 个工具，会有什么问题？

工具 schema 会占上下文，模型选择难度增加，可能出现 routing 错误。后续可以通过 tool retrieval、分层 router、Skill/Harness 动态暴露工具等方式控制。

## 23. Tool 调用失败怎么办？

不要直接让 Agent 崩溃。通常把错误包装成结构化 Tool Result 返回模型，让模型决定重试、换工具或终止；同时 Runtime 应限制重试次数。

## 24. Agent 和固定 Workflow 的区别？

固定 Workflow 的步骤主要由程序预定义；Agent 的部分步骤由模型运行时动态决策。生产系统常常是“Workflow 外壳 + Agent 节点”的混合结构。

## 25. 你这个 Level 1 项目做了什么？

建议面试时回答：

> 我从一次普通 LLM 调用逐步实现了 Tool Calling。先把 PPO 训练反馈和 reward component statistics 封装成本地 Python Tool，再用 JSON Schema 暴露给模型；Runtime 解析 `tool_calls`、验证参数、执行白名单函数，并通过 `tool_call_id` 把结果作为 tool message 写回上下文，最终形成一个可连续调用多个工具、直到输出诊断结果的最小 Agent Loop。这个版本故意没有引入 LangChain 或 MCP，目的是先把 Agent Runtime 的基本协议和控制流彻底理解。
