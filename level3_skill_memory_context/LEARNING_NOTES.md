# Level 3 学习笔记

这一层只记住一个大框架：

```text
Tool    = 能做什么
Skill   = 遇到某类问题怎么做
Memory  = 以前/现在发生了什么
Context = 这一轮模型实际看到什么
Harness = 谁负责把它们组织起来（Level 4）
```

## 1. Skill 的最小结构

```text
my-skill/
└── SKILL.md
```

```markdown
---
name: my-skill
description: What it does and when to use it.
---

# Instructions
...
```

当前公开 Agent Skills 规范要求 `name` 和 `description`，并建议把长资料放到 `references/`、脚本放到 `scripts/`、静态资源放到 `assets/`。

本项目暂时只用 SKILL.md，因为我们正在学最小机制。

## 2. Progressive Disclosure

不要把“发现 Skill”和“加载 Skill”混为一谈。

```text
discover_skills()
→ name + description

load_skill(name)
→ full SKILL.md body
```

为什么？

```text
Library size ↑
→ 全量 Prompt 成本 ↑
→ 无关 instruction 干扰 ↑
→ Context 更难控制
```

## 3. Skill Router 是什么

Router 输入：

```text
current task/evidence
+
Skill catalog metadata
```

输出：

```json
{
  "skill_name": "...",
  "reason": "..."
}
```

Host 必须校验：

```python
if selected not in allowed_names:
    raise ValueError(...)
```

LLM 输出永远不是天然可信的控制信号。

## 4. Tool vs Skill

Tool：

```text
get_training_feedback(iteration=1)
```

有输入，有执行，有 observation。

Skill：

```text
gate-proxy-by-validity
```

包含：

```text
trigger
Evidence checklist
diagnostic test
intervention pattern
validation
rollback / contraindications
```

Tool 负责 Action；Skill 负责 Procedure。

## 5. Skill vs Prompt

Skill 最终也会以 instruction 文本进入 Context，因此底层并不是“新型神经网络模块”。

区别主要在系统设计：

```text
Prompt
= 通常常驻或针对当前请求直接构造

Skill
= 独立、可命名、可路由、可版本化、按需加载的程序性 instruction package
```

所以面试不要回答“Skill 就是 Prompt”，也不要回答“Skill 和 Prompt 完全无关”。

更准确：

> Skill 通常以 Prompt/Context 的形式影响模型，但它在 Agent 系统中被组织成可发现、可激活、可复用的程序性能力单元。

## 6. Working Memory

当前 run 的状态：

```text
user request
collected evidence
selected skill
notes
```

它不断变化。

可以类比程序运行中的 state object。

## 7. Episodic Memory

过去具体发生过的事件：

```text
task
iteration
diagnosis
intervention
outcome
provenance
```

关键是 **concrete + historical**。

它不是抽象方法。

## 8. Skill vs Episodic Memory

```text
Episode:
“某次 BipedalWalker 调整 upright shaping 后发生了什么”

Skill:
“当 dominant proxy 可能在 invalid state 可领取时，应该如何验证和干预”
```

从 CREATE 研究角度：

```text
raw trajectory / experiment
↓
Experience record
↓ abstraction
candidate Skill
↓ held-out/outcome validation
versioned Skill
```

不要把“日志堆起来”直接叫 self-evolving Skill。

## 9. Memory vs Context

Memory 是存储。

Context 是一次模型请求的输入选择结果。

例如系统存了 1000 episodes：

```text
Episodic Memory = 1000 episodes
```

这次只取 1 条：

```text
Context = current evidence + selected Skill + 1 relevant episode
```

所以 Context Builder 是一个 selection / packing 层。

## 10. 为什么 Context Engineering 很重要

Agent 越复杂，潜在信息越多：

```text
conversation history
MCP tool results
RAG docs
memory
skills
system instructions
sub-agent results
```

不能全部无限增长。

要回答：

```text
什么必须进？
什么按需进？
什么摘要？
什么丢弃？
什么必须保留 provenance？
给输出留多少 token？
```

Level 3 只用字符裁剪演示概念。生产环境要按真实 tokenizer 做预算。

## 11. 为什么 Final Answer 不自动进入 Memory

LLM 输出只是 proposal。

在 CREATE 里更合理的是：

```text
LLM diagnosis/revision
↓
PPO training
↓
metrics + behavior evidence
↓
validation
↓
Experience
↓
可能抽象/修订 Skill
```

否则 Agent 很容易：

```text
自己说了一个错误结论
→ 写入 memory
→ 下次把错误当事实
→ 自我强化
```

这叫 memory contamination / self-reinforcing error，是 Agent 系统非常现实的问题。

## 12. 为什么我们的 Skill Router 不用向量库

只有三个 Skill 时，LLM 看 metadata catalog 最透明。

当 Skill 数量变大，再考虑：

```text
metadata filter
→ BM25 / embedding
→ top-k
→ reranker
→ LLM route
```

不要把数据库当能力本身。

## 13. Level 3 最重要的调用链

```text
MCP Tool Results
      ↓
Working Memory
      ↓
Skill metadata catalog
      ↓
Router
      ↓
Selected full SKILL.md
      +
Relevant episodic memory
      ↓
Context Builder
      ↓
LLM
```

如果这一条你能自己画出来并解释每个箭头，Level 3 核心就理解了。

## 14. 自己动手的 5 个实验

1. 把 `gate-proxy-by-validity` 的 description 改得非常模糊，观察 Router 是否更容易选错。
2. 在 Skill catalog 再加一个 description 很相似的 Skill，观察 routing ambiguity。
3. 把所有 Skill body 都拼进 router prompt，比较 Context 长度和回答差异。
4. 把 LunarLander episode 错误地塞给 BipedalWalker，观察无关 memory 是否干扰判断。
5. 把 `episodes.jsonl` 中 provenance 删除，思考为什么生产系统里来源追踪会变难。

## 15. 过关自测

不用看代码回答：

- Skill 最小目录是什么？
- `description` 为什么影响 routing？
- Skill discovery 和 loading 有什么区别？
- Tool 和 Skill 的边界？
- Working Memory 和 Episodic Memory 的边界？
- Memory 和 Context 的边界？
- 为什么不能自动把所有 LLM 输出写长期 Memory？
- Context Builder 为什么属于 Host/Runtime，而不是 LLM 本身？

全部能答，再进入 Level 4。
