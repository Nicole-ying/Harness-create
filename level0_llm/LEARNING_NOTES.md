# Level 0 学习笔记

## 这一层到底学什么

Level 0 只有一件事：理解“Python 程序如何向 LLM API 发起一次请求，并拿回一次文本回答”。

当前调用链：

```text
example_case.json
      │
      │ 普通 Python 读取
      ▼
build_user_prompt()
      │
      ▼
messages = [system, user]
      │
      ▼
OpenAI-compatible HTTP API
      │
      ▼
LLM
      │
      ▼
message.content
```

这里还没有 Agent。

## 请你特别观察 5 个对象

1. `api_key`：证明你有权调用模型服务。不要提交到 Git。
2. `base_url`：请求发到哪个模型平台。
3. `model`：平台上实际调用哪个模型。
4. `messages`：本次模型真正看到的上下文。
5. `response.choices[0].message.content`：模型返回的文本。

## 为什么 example_case.json 不算 Tool

程序在调用模型之前就主动读取了 JSON，然后把内容拼进 prompt。决定“读取什么”的是 Python 程序员，不是模型。

因此：

```text
Level 0: Python 决定读取文件 → LLM 只能看结果
Level 1: LLM 决定是否需要读取文件 → Runtime 执行 Tool
```

这是 Level 0 和 Level 1 最重要的分界线。

## 运行前你应该能回答

- `SimpleLLMClient` 为什么需要 `base_url`？
- DeepSeek 和其他 OpenAI-compatible API 为什么可以共用 `OpenAI` SDK？
- 如果不把某个指标写入 `user_prompt`，模型能不能知道它？为什么？
- `system_prompt` 和 `user_prompt` 分别承担什么作用？
- 为什么 `.env` 不能提交到 Git？

## 自己动手改 3 次

第一次：删掉 `early_falls`，比较模型诊断是否变化。

第二次：把 `vertical_oscillation_penalty` 也删掉，观察模型是否仍然会提这个组件。

第三次：把 system prompt 中的“只使用显式信息”删掉，观察模型是否更容易补充未经输入支持的推测。

这三个实验的目的不是研究 Prompt Engineering，而是让你真正理解：**模型的行为高度依赖本次请求里实际提供的上下文。**

## Level 0 过关标准

你不看代码也能口头解释：

```text
Python → API Client → messages → HTTP request → model → response
```

并且你能独立改成另一个 OpenAI-compatible 模型平台，只需要替换 `api_key`、`base_url` 和 `model`。

达到这个程度后，再进入 Level 1：Tool Calling。
