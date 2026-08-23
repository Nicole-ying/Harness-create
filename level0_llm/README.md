# Level 0 — 先学会一次最普通的 LLM API 调用

这一层**故意不做 Agent**。

你只学习一条最基本的调用链：

```text
Python 程序
   ↓
读取本地示例数据
   ↓
拼成 system prompt + user prompt
   ↓
调用 LLM API
   ↓
拿到 message.content
   ↓
打印答案
```

教学案例来自你现有 CREATE / BipedalWalker 奖励函数实验：给模型一组 PPO 训练统计，让模型做一次 reward diagnosis。

> 关键点：`example_case.json` 是 **Python 程序主动读取** 的，不是 LLM 自己读取的。因此这里还没有 Tool Calling，也还不是 Agent。

## 1. 文件结构

```text
level0_llm/
├── main.py             # 入口：读取案例、构造 prompt、调用模型
├── llm_client.py       # 最小 LLM Client，支持 DeepSeek / OpenAI-compatible API
├── example_case.json   # 一个精简的 BipedalWalker 训练失败案例
├── .env.example        # API 配置模板，不包含真实 key
├── requirements.txt
└── LEARNING_NOTES.md   # 这一层必须真正理解的概念
```

## 2. 安装

进入目录：

```bash
cd level0_llm
python -m venv .venv
```

Linux / macOS：

```bash
source .venv/bin/activate
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

然后安装：

```bash
pip install -r requirements.txt
```

## 3. 配置 DeepSeek API

复制配置模板：

Linux / macOS：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

打开 `.env`：

```env
PROVIDER=deepseek
DEEPSEEK_API_KEY=你的真实key
DEEPSEEK_MODEL=deepseek-chat
```

**不要把真实 API key 提交到 GitHub。** 根目录 `.gitignore` 会忽略 `.env`。

## 4. 运行

```bash
python main.py
```

你会先看到程序打印给模型的 `USER PROMPT`，然后看到模型返回的 `LLM RESPONSE`。

先不要追求诊断是否完美。Level 0 的目标只是看懂：

```text
api_key + base_url + model + messages
                ↓
             API 请求
                ↓
        assistant message.content
```

## 5. 其他支持 GPT 的第三方 API

如果你的平台提供 **OpenAI-compatible API**，通常不需要重写 Client，只需要改 `.env`：

```env
PROVIDER=openai_compatible
OPENAI_COMPATIBLE_API_KEY=你的key
OPENAI_COMPATIBLE_BASE_URL=https://平台给你的/v1地址
OPENAI_COMPATIBLE_MODEL=平台要求的模型名
```

你之后把平台文档里的 `base_url`、模型名和调用示例发给我，我们再检查它是否真的兼容，不要直接猜。

## 6. 这一层禁止出现什么

为了学清楚边界，Level 0 暂时不加入：

```text
Tool Calling
Agent Loop
MCP
Skill
Memory
RAG
Harness
```

这些会在后面的 Level 逐层加入。

## 7. 过关标准

读完并运行后，你应该能不用背代码解释下面 5 件事：

1. `api_key`、`base_url`、`model` 分别是什么。
2. `system` 和 `user` message 分别是什么。
3. 为什么模型不知道 `example_case.json` 的存在。
4. 为什么现在还不能称为 Agent。
5. 换一个 OpenAI-compatible 平台时，为什么通常只需要换 endpoint/key/model。

然后做 `LEARNING_NOTES.md` 里的三个小实验。

下一层 Level 1 我们只增加一个变化：**让 LLM 自己决定是否调用 `read_training_feedback()`。**
