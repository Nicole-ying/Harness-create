# Level 3 — Skill + Memory + Context

Level 2 已经解决：Agent 如何通过 MCP 连接外部能力。

```text
LLM -> tool_call -> Host -> MCP Client -> MCP Server -> backend
```

Level 3 解决的是另一类问题：

> Agent 已经“有手”了，但它怎么知道某类问题应该按什么方法处理？过去发生过什么？这一次到底应该把哪些信息给模型看？

因此这一层只加入三个概念：

```text
Skill   = 可复用的方法 / SOP / 程序性知识
Memory  = 历史发生过什么 + 当前运行状态
Context = 这一次真正送进模型窗口的信息
```

最终教学结构：

```text
User
 ↓
Evidence Collector
 ↓ tool_call
MCP
 ↓
experiment evidence
 ↓
Working Memory
 ↓
Skill Catalog (name + description only)
 ↓
Skill Router
 ↓
load ONE SKILL.md
 ↓
Relevant Episodic Memory
 ↓
Context Builder
 ↓
Final LLM diagnosis
```

最重要的一句话：

> **Skill、Memory、Context 不是三个同义词。Skill 是“怎么做”，Memory 是“发生过什么/当前状态是什么”，Context 是 Host 最终选择让模型现在看到什么。**

---

## 0. 本教程参考的 Agent Skill 结构

公开 Agent Skills 规范中，一个 Skill 最少是：

```text
skill-name/
└── SKILL.md
```

`SKILL.md` 使用 YAML frontmatter：

```markdown
---
name: gate-proxy-by-validity
description: ...what it does and when to use it...
---

# Instructions
...
```

本教程故意只实现一个很小的 `skill_loader.py`，让你直接看见：

```text
Skill Discovery
!=
Skill Loading
```

也就是 progressive disclosure：

```text
启动/路由阶段：只加载 name + description
                   ↓
                选择 Skill
                   ↓
执行阶段：才读取完整 SKILL.md body
```

这样不会把所有 Skill 全部塞进上下文。

---

## 1. 文件结构

```text
level3_skill_memory_context/
├── skill_loader.py
├── memory.py
├── context_builder.py
│
├── skills/
│   ├── gate-proxy-by-validity/
│   │   └── SKILL.md
│   ├── densify-sparse-outcome/
│   │   └── SKILL.md
│   └── calibrate-rare-risk-penalty/
│       └── SKILL.md
│
├── memory/
│   └── episodes.jsonl
│
├── backend.py
├── mcp_server.py
├── mcp_adapter.py
├── llm_client.py
├── mock_data/
│
├── smoke_test.py
├── step1_skill_catalog.py
├── step2_skill_router.py
├── step3_memory_context.py
├── step4_full_agent.py
│
├── .env.example
├── requirements.txt
├── LEARNING_NOTES.md
└── INTERVIEW_QUESTIONS.md
```

其中 `memory/episodes.jsonl` 明确标注为 **synthetic teaching memory**，只是帮助理解 Memory 结构，不是声称来自真实 CREATE 实验结果。

---

# Step 0 — 安装并先跑 smoke test

```bash
cd level3_skill_memory_context
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

先不要配置 API Key，直接：

```bash
python smoke_test.py
```

如果看到：

```text
Level 3 Skill + Memory + Context smoke test passed.
```

说明：

```text
Skill parsing
Memory loading
Context building
mock experiment data
```

这些纯 Python 层已经正常。

---

# Step 1 — `step1_skill_catalog.py`

运行：

```bash
python step1_skill_catalog.py
```

它先调用：

```python
skills = discover_skills()
```

此时只读取每个 Skill 的：

```text
name
description
path
```

输出类似：

```text
- gate-proxy-by-validity: Diagnose and repair reward designs where...
- densify-sparse-outcome: Diagnose reward designs where...
- calibrate-rare-risk-penalty: Diagnose reward designs with...
```

注意：**这一步还没有把三个 SKILL.md 正文全部送给模型。**

然后教学代码手动选择：

```python
selected = "gate-proxy-by-validity"
```

才执行：

```python
skill = load_skill(selected)
```

这时完整 body 才真正进入内存。

## 为什么这很重要？

如果你有 100 个 Skill，每个 2000 tokens：

```text
全部提前塞 Prompt = 非常浪费上下文
```

更合理的是：

```text
100 个 metadata 摘要
        ↓
选择 1~2 个
        ↓
加载完整 instructions
```

这就是 Skill progressive disclosure。

---

# Step 2 — `step2_skill_router.py`

现在才让 LLM 做 Skill Routing。

先配置：

```powershell
Copy-Item .env.example .env
```

DeepSeek 示例：

```env
PROVIDER=deepseek
DEEPSEEK_API_KEY=你的真实key
DEEPSEEK_MODEL=你账号实际支持的model id
```

运行：

```bash
python step2_skill_router.py
```

Router 只看到：

```text
Current evidence
+
Skill A name + description
Skill B name + description
Skill C name + description
```

然后用结构化 JSON 返回：

```json
{
  "skill_name": "gate-proxy-by-validity",
  "reason": "..."
}
```

Host 做两个动作：

```text
1. 校验 skill_name 必须在 catalog 白名单里
2. 只加载选中的完整 SKILL.md
```

所以：

```text
LLM 负责选择
Host 负责验证 + 加载
```

不要让模型自己随便拼文件路径。

---

# Step 3 — `step3_memory_context.py`

这一小节不需要 LLM。

运行：

```bash
python step3_memory_context.py
```

你会看到三个不同对象。

## 3.1 Working Memory

例如：

```python
working = WorkingMemory(
    user_request="分析当前 BipedalWalker reward"
)

working.evidence.append(...)
working.selected_skill = "gate-proxy-by-validity"
working.notes.append(...)
```

它表示：

> **当前这一次运行正在发生什么。**

典型生命周期：

```text
一次 Agent run 开始
↓
Working Memory 创建
↓
不断写 evidence / selected skill / notes
↓
run 结束
```

它不等于长期记忆。

## 3.2 Episodic Memory

`episodes.jsonl` 记录具体过去事件：

```text
某任务
某次 diagnosis
某次 intervention
某次 outcome
```

它回答：

> **以前发生过什么？**

例如：

```text
过去 BipedalWalker 某次尝试了 upright shaping，early falls 仍然存在
```

这是一个 episode，不是 Skill。

## 3.3 Skill

Skill 则是抽象方法：

```text
如果 dominant proxy 在 invalid state 仍可领取
→ 检查 validity mismatch
→ 考虑 validity gating
→ 验证 native metric / early failure / proxy availability
```

它回答：

> **遇到这种模式通常应该按什么步骤诊断和处理？**

所以：

```text
Episode = concrete history
Skill   = reusable procedure
```

---

# 4. Context 到底是什么？

这是这一层最容易混淆的概念。

你可能拥有：

```text
100 个 Skills
1000 条 historical episodes
10 个 tool results
完整 environment source code
过去 50 轮对话
```

这些都可以存在系统里。

但模型这一轮真正看到的可能只有：

```text
Current request
Current evidence
Selected Skill
1 relevant episode
A few working-memory notes
```

这个集合才叫当前 **Context**。

因此：

```text
Memory != Context
```

Memory 是一个数据源。

Context 是 Host 从多个数据源里筛选、组织、裁剪之后，真正发给模型的输入。

本教程的 `context_builder.py` 明确没有放进去：

```text
所有 Skill bodies
所有历史 episodes
模型没有请求的原始文件
```

这是最简单的 Context Engineering。

### 为什么这里只用 character budget？

为了不在 Level 3 又引入 tokenizer 依赖。

```python
max_chars=12000
```

只是教学裁剪。

生产系统应使用：

```text
真实模型 tokenizer
+
context window limit
+
reserved output/reasoning budget
```

进行 token 预算。

---

# Step 4 — `step4_full_agent.py`

这是 Level 3 最终整合。

运行：

```bash
python step4_full_agent.py
```

完整调用链：

```text
① User
   ↓
② LLM Evidence Collector
   ↓ Tool Calling
③ Host / Agent Loop
   ↓
④ MCP Client
   ↓
⑤ MCP Server
   ↓
⑥ experiment evidence
   ↓
⑦ Working Memory
   ↓
⑧ Skill Catalog metadata
   ↓
⑨ LLM Skill Router
   ↓
⑩ Host validates selected name
   ↓
⑪ load ONE full SKILL.md
   ↓
⑫ select relevant Episodic Memory
   ↓
⑬ Context Builder
   ↓
⑭ Final LLM diagnosis
```

这个流程最值得反复画。

---

# 5. 为什么 Skill 不做成 MCP Tool？

它们解决的问题不同。

### Tool

```text
read_training_feedback(iteration=1)
```

表示：

> 执行一个动作 / 获取外部信息。

### Skill

```text
gate-proxy-by-validity
```

表示：

> 面对一类问题，应采用怎样的诊断流程、证据 checklist、intervention pattern、validation / rollback。

所以：

```text
Tool = capability / action
Skill = procedure / know-how
```

Skill 里面可以要求使用某些 Tool，但 Skill 自己不等于 Tool。

---

# 6. Skill 和 Prompt 有什么区别？

最简单的 System Prompt：

```text
你是 reward diagnosis agent，请认真分析。
```

这是通用行为约束。

Skill：

```text
什么时候触发
看哪些证据
如何诊断
抽象 intervention
如何验证
何时 rollback
```

更像一个按需加载的 SOP。

当然从底层看，Skill 最终也会进入模型上下文，所以它仍以文本 instruction 影响模型。

关键差异在 **组织、路由、按需加载和可复用生命周期**，而不是“Skill 是某种神秘的新模型能力”。

---

# 7. Skill 和 Memory 有什么区别？

一句话：

```text
Memory: 上次发生了什么
Skill: 以后遇到类似问题可以怎么做
```

例如：

```text
Episode:
BipedalWalker iter-X 增大某 upright shaping 后 early falls 仍存在
```

这是历史事实。

经过多个任务/实验验证后，可能抽象成：

```text
Skill:
不要仅根据单次失败盲目增大惩罚；先检查 dominant proxy 是否绕过 validity condition
```

这才是可迁移程序性知识。

所以你的 CREATE 第四章真正有价值的地方之一，就是：

```text
Experience / episode
       ↓ abstraction + validation
Reusable Reward-Design Skill
```

而不是把所有历史日志直接叫 Skill。

---

# 8. 为什么 Skill Router 只看 metadata？

因为 Skill library 可能很大。

公开 Agent Skills 规范也强调 progressive disclosure：启动时只需要很小的 metadata，激活时才加载完整 instructions，references/scripts 再按需读取。

因此我们的教学实现是：

```text
Catalog:
name + description
        ↓
Router
        ↓
Selected name
        ↓
Full SKILL.md
```

不是：

```text
把所有 SKILL.md 拼成一个 50k prompt
```

---

# 9. Skill Router 一定要向量数据库吗？

不一定。

这个教程 Skill 只有 3 个，所以直接把 metadata catalog 给 LLM 选择即可。

随着数量变大，可以逐渐变成：

```text
metadata filtering
keyword/BM25
embedding retrieval
hybrid retrieval
reranker
LLM final routing
```

但不要为了“用了向量库”而提前复杂化。

先理解 routing 的目标：

> 从大量能力中找到少量当前最相关能力。

---

# 10. Level 3 的安全/工程边界

本教程仍然保持：

```text
MCP tools read-only
Skills are instructions, not trusted executable code
Router output is validated against whitelist
Episodic memory is labelled with provenance
Final output is NOT auto-saved as truth
```

为什么不自动把 final diagnosis 写入长期 Memory？

因为模型刚说出的内容：

```text
不等于 validated experience
```

真正的 CREATE 自进化逻辑应该是：

```text
Agent proposal
↓
PPO / environment outcome
↓
validation
↓
再决定是否写 Experience / revise Skill
```

这会在后面的 CREATE integration / Evaluation 层继续展开。

---

# 11. Level 3 过关标准

你应该能够不看代码解释以下关系：

```text
Tool
Skill
Working Memory
Episodic Memory
Context
Skill Catalog
Skill Router
Progressive Disclosure
Context Builder
```

并能画出：

```text
External Evidence --MCP--> Working Memory
                              |
Skill Library --metadata--> Router
                              |
                     selected Skill
                              |
Episodic Memory --------------+
                              ↓
                       Context Builder
                              ↓
                             LLM
```

你还应该能回答：

```text
为什么 Skill 不是 Tool？
为什么 Memory 不是 Context？
为什么不把所有 Skill 都塞 Prompt？
为什么不能把一次 Agent 输出直接当长期经验？
为什么 Skill Router 的输出必须校验？
```

做到这里，Level 3 就过关。

下一层 Level 4 才把目前散落在：

```text
MCP lifecycle
Agent Loop
Skill discovery/loading
Skill routing
Memory
Context Builder
retry / round limits
trace
```

这些显式应用代码抽出来，形成真正的 **Harness / Agent Runtime**。
