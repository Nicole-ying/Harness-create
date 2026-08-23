# Level 3 面试题：Skill / Memory / Context

下面的问题按“基础概念 → 工程设计 → CREATE 延伸”排列。

## 1. 什么是 Agent Skill？

参考回答：

> Skill 是一个可命名、可发现、按需加载的程序性能力单元，通常包含什么时候使用、需要检查什么证据、执行步骤、验证方式和边界条件。它最终会以 instruction/context 的形式影响模型，但系统层面强调 routing、progressive disclosure、复用和版本管理。

## 2. Skill 和普通 Prompt 有什么区别？

> Prompt 是一次请求或常驻角色约束；Skill 更像独立的可复用 SOP，可通过 metadata 被发现和路由，只在相关任务时加载完整说明。两者底层都可能以文本进入上下文，但组织和生命周期不同。

## 3. Skill 和 Tool 有什么区别？

> Tool 是可以实际执行的 action/capability，例如 `get_training_feedback`；Skill 是处理某类问题的方法，例如“先检查哪些证据、怎么判断 proxy leakage、如何验证 intervention”。Skill 可以指导 Agent 使用 Tool，但自己不等于 Tool。

## 4. 一个最小 Agent Skill 长什么样？

```text
skill-name/
└── SKILL.md
```

至少包含：

```yaml
---
name: skill-name
description: what it does and when to use it
---
```

## 5. 为什么 `description` 很重要？

> 因为 Router 在 progressive disclosure 阶段通常只看到 name + description。description 同时承担能力摘要和触发条件提示，写得过于宽泛或相似会降低 routing 精度。

## 6. Progressive Disclosure 是什么？

> 系统启动时只加载 Skill metadata；确定相关 Skill 后才加载完整 SKILL.md；references/scripts 继续按需读取。目的是降低无关上下文、token 成本和 instruction interference。

## 7. 为什么不能把全部 Skill 都塞进 Prompt？

> Skill 数量增长后会占用大量 context window，引入无关指令冲突，增加成本和选择难度。更好的方式是先检索/路由 top-k，再加载少量完整 Skill。

## 8. Skill Router 的输入输出是什么？

输入通常是：

```text
current task/evidence
+
Skill catalog metadata
```

输出通常是：

```text
selected skill name(s)
+
routing reason / confidence
```

Host 应校验返回 Skill 是否存在。

## 9. Router 输出为什么要白名单校验？

> LLM 可能产生不存在的 skill name、非法路径或格式错误。模型输出只是 untrusted control proposal，Runtime 必须校验后才能加载能力。

## 10. Skill Router 一定需要向量数据库吗？

> 不一定。小规模 catalog 可以直接 metadata + LLM routing。规模增大后再考虑关键词、BM25、embedding、hybrid retrieval、reranker 和 LLM final routing。

## 11. 什么是 Working Memory？

> 当前 Agent run 的可变状态，例如 user request、已收集 evidence、selected skill、当前 plan/notes。生命周期通常和当前 run/session 紧密相关。

## 12. 什么是 Episodic Memory？

> 过去具体交互/尝试/结果的记录，例如某任务某次 diagnosis、intervention 和真实 outcome。它是历史经验事实，不是抽象规则。

## 13. Working Memory 和 Episodic Memory 区别？

> Working Memory 描述“现在这次 run 正在发生什么”；Episodic Memory 描述“过去某次具体发生了什么”。前者高频变化，后者用于历史检索和经验参考。

## 14. Skill 和 Episodic Memory 区别？

> Episode 是 concrete history；Skill 是从一个或多个经验中抽象、验证后的 reusable procedure。不能把一条历史日志直接当作 Skill。

## 15. Memory 和 Context 的区别？

> Memory 是可供检索的存储/状态来源；Context 是这一轮模型实际看到的输入。Context Builder 从 Memory、Skill、Tool Result、conversation 等来源中选择和组织内容。

## 16. Context Engineering 是什么？

> 管理模型当前上下文的选择、压缩、排序、引用、token 预算和生命周期，使模型在有限 context window 中看到最相关、可信和足够的信息。

## 17. Context Builder 一般做什么？

典型职责：

```text
select relevant memory
select/insert skill
include current tool observations
summarize history
remove stale context
respect token budget
reserve output budget
preserve provenance
```

## 18. 为什么本教程不把全部历史 episode 放进 Context？

> 大量无关历史会消耗 token 并造成干扰。Memory 应被检索，Context 应被构造，而不是简单 dump 全库。

## 19. 为什么 Context 需要 token budget？

> 模型有有限 context window，而且输入、reasoning、输出共享预算。Agent 的 tool results、RAG、memory、skill 和历史对话都会增长，因此必须规划输入并预留生成空间。

## 20. 为什么本教程用 character budget，不直接叫 token budget？

> 这是教学简化。字符数不等于 token 数，尤其中文和不同 tokenizer 下差异明显。生产系统应该用目标模型 tokenizer 和 context limit 计算真实 token budget。

## 21. 为什么不能把 Agent 的每个最终回答都自动写成长期 Memory？

> LLM 输出可能是错误假设。如果未经真实 outcome 或其他证据验证就持久化，会造成 memory contamination，并在后续检索中自我强化错误。

## 22. CREATE 里什么更适合写进 Experience？

> 应写可追溯的 task context、evidence、diagnosis、intervention、真实 PPO outcome、confounders/provenance 等，而不是只记录模型说了什么。

## 23. Experience 怎么进一步变成 Skill？

> 需要从多个/高价值 Experience 中抽象 task-agnostic pattern，再通过 held-out task 或真实 outcome 验证，才能 add/revise/deprecate Skill。Skill evolution 不应只依赖 LLM 自评。

## 24. Skill 为什么需要 contraindication / rollback？

> 因为一个程序性模式不是在所有场景都成立。明确“不应该什么时候用”和“出现什么结果应回滚”可以减少 negative transfer 和过度应用。

## 25. 你的 `gate-proxy-by-validity` Skill 为什么不能仅凭 97.2% component share 就直接下结论？

> 高占比只说明该 component 在 reward 中占主导，不证明它在 failure state 仍错误激活。还要检查 failure-state activation 等证据，因此 Skill 中明确要求 provisional diagnosis 和进一步验证。

## 26. 为什么 Skill 里要写 Evidence Checklist？

> 它把“凭感觉修改 Reward”变成“先收集特定证据再诊断”的 procedure，能约束 Agent 的工具使用和判断依据，也方便后续 evaluation。

## 27. MCP、Skill、Memory、Context 各自回答什么问题？

> MCP：外部能力怎么标准接入；Skill：某类问题怎么做；Memory：过去/现在发生过什么；Context：这一次模型看到什么。

## 28. 它们是谁组织起来的？

> Host / Agent Runtime / Harness。Level 3 里这些职责还是显式散落在应用代码中；Level 4 才把它们抽成通用 Runtime components。

## 29. 如果 Skill Library 从 3 个扩展到 3000 个，怎么改？

可以回答：

> 先做 metadata indexing 和权限/namespace filter，再用 BM25/embedding hybrid retrieval 得到候选，必要时 rerank，再让 LLM 做最终 routing；完整 body 仍只按需加载。同时要做 version、usage trace、success metrics 和 deprecation。

## 30. Skill 的评估指标可以有哪些？

例如：

```text
Skill routing accuracy
activation precision/recall
任务成功率
达到成功所需轮次
Tool-call efficiency
Token cost
negative-transfer rate
rollback rate
```

真正价值最终要落到任务 outcome，而不是“模型觉得 Skill 很好”。

## 31. Memory retrieval 可以怎么做？

小规模：task/name/filter。

大规模：

```text
metadata filter
recency
semantic retrieval
similarity + outcome weighting
reranking
provenance constraints
```

## 32. 为什么 provenance 对 Memory 很重要？

> Agent 必须区分真实实验结果、用户输入、模型推测、合成教学数据等来源。否则错误内容会在后续 context 中被当成事实。

## 33. Context 太长时你会怎么处理？

> 先保留 system/safety/current task 和最新 tool observations；检索少量相关 memory/skill；对长历史做结构化摘要；去除重复/过期内容；按 tokenizer 计算预算；必要时重新检索而不是长期携带所有原文。

## 34. Context 太短有什么问题？

> 缺少必要 evidence、历史约束或 Skill instruction，模型容易重复调用工具、忘记目标、产生不一致诊断或无法遵循流程。

## 35. 为什么 Skill Selection 可以看作一种 Retrieval？

> 因为本质是从一个能力库里根据当前任务取相关的少量程序性知识。区别只是被检索的对象不是普通知识文档，而是能力/SOP 定义。

---

# 30 秒面试回答模板

> 我把 Agent 的外部能力、程序性知识和运行状态分开设计。MCP 负责把训练反馈等外部能力标准化成可发现 Tool；Skill Library 存储可复用的 reward-design procedure，路由时只暴露 name/description，选中后再加载完整 SKILL.md；Working Memory 保存当前 run 的 evidence 和状态，Episodic Memory 保存过去真实尝试及 outcome；最后由 Context Builder 选择当前 Skill、相关 Memory 和 Tool observations 组成模型本轮上下文。这样可以避免把所有历史和能力都塞进 Prompt，也为后续 Harness 统一管理 lifecycle、trace 和 evaluation 做准备。

# 追问：为什么不直接用一个超长 Prompt？

> 因为能力库和历史会持续增长，超长 Prompt 不可扩展，也难做 provenance、更新、routing 和 evaluation。把 Tool、Skill、Memory、Context 分层后，每层都能独立管理和测量。
