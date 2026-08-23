# Agent Evaluation Guide

## 1. 三层 Eval，不要混

### Layer A — Runtime correctness

回答：系统有没有正确运行？

```text
turn completed?
max_steps exceeded?
tool errors?
invalid arguments?
context unexpectedly huge?
```

这类指标通常可以 **100% deterministic**。

### Layer B — Agent behavior quality

回答：Agent 有没有按预期过程完成任务？

```text
required tool coverage
skill selection accuracy
evidence coverage
unsupported claim rate
retry count
```

能写规则就优先写规则。

### Layer C — Domain outcome

回答：Agent 的动作最终有没有让真实任务变好？

CREATE 中就是：

```text
PPO search fitness
best-so-far fitness
solved rate
test fitness
rounds-to-threshold
regression rate
```

这层最重要，也最贵。

---

## 2. 为什么先 deterministic eval

例如你知道一个 case 必须调用：

```text
get_training_feedback
get_component_stats
```

那么最好的 evaluator 是：

```python
required_tools <= observed_tool_calls
```

而不是：

```text
请另一个 LLM 判断这个 Agent 是否充分查看了证据。
```

Deterministic eval 的优点：

```text
便宜
可重复
易 debug
不会受 judge model 漂移影响
```

---

## 3. LLM-as-a-Judge 什么时候用

适合评价很难写硬规则的内容：

```text
诊断是否逻辑连贯
回答是否真正区分 observation / hypothesis
修改建议是否过度具体
解释是否覆盖关键 tradeoff
```

但要做：

```text
固定 judge model/version
固定 rubric
结构化输出
人工抽样校准
记录 judge prompt
```

不要让 LLM Judge 替代所有硬指标。

---

## 4. Tool metrics

可以从 Session Event Log 直接算：

```text
tool_call_count
unique_tools
required_tool_recall
tool_error_rate
retry_count
```

其中：

```text
required_tool_recall
= called required tools / all required tools
```

不要把“调用越多”当“越好”。

过多 Tool Call 可能意味着：

```text
routing 不确定
重复查询
错误恢复差
context 不够
```

---

## 5. Skill metrics

### Skill selection accuracy

有 gold Skill 时：

```text
correct selected Skill / cases with gold Skill
```

### Skill activation precision

如果不是每个任务都需要 Skill：

```text
correctly activated skills / all activated skills
```

### Negative transfer

尤其重要：

```text
Skill 被加载
但任务 outcome 变差
```

因此 Skill eval 最终必须结合 domain outcome。

---

## 6. Evidence grounding

最低成本版本：

```text
required evidence term coverage
forbidden claim detection
```

更强版本可以保存 evidence IDs：

```json
{
  "claim": "forward reward is dominant",
  "evidence_ids": ["tool_result_7"]
}
```

然后评：

```text
claim citation coverage
citation validity
unsupported claim rate
```

这比字符串匹配更可靠，适合作为后续升级。

---

## 7. Context metrics

Level 5 教学代码先统计：

```text
total_context_chars
max_context_chars
```

真正生产环境应该记录：

```text
prompt_tokens
completion_tokens
reasoning_tokens（provider 支持时）
cache hit tokens
latency
cost
```

为什么教学先用 chars？

因为它 provider-independent，而且 Session Log 已经保存完整 model-visible request。

---

## 8. Ablation 设计

典型 Agent ablation：

```text
A: tools_only
B: tools + skill
C: tools + skill + memory
D: full harness policies
```

必须尽量固定：

```text
same task
same initial reward
same PPO seed
same model/version
same token/tool budget
same stopping rule
```

否则你不知道 improvement 来自哪里。

---

## 9. CREATE 特别需要控制什么

CREATE 是 closed-loop：

```text
reward edit
→ PPO training
→ evidence
→ next edit
```

因此真正比较 Skill/Harness 时建议：

```text
iteration 1 initial reward fixed
paired PPO seed
same training timesteps
same evaluation episodes
same edit budget
same stopping threshold
```

Skill 应从后续 revision 开始影响流程，否则初始 reward 不一致会混淆结果。

---

## 10. Data leakage

跨任务 Skill eval 最容易犯的错误：

```text
从 held-out task 轨迹抽 Skill
然后又声称在 held-out task 上 zero-shot transfer
```

必须保证：

```text
Skill source tasks
≠ held-out target evaluation data
```

如果 target task 用于调 Skill trigger、文本或超参，它就不再是纯 held-out。

---

## 11. 报告不要只放平均值

真实实验建议至少保存：

```text
per seed
per round
mean ± std
solved count
failure cases
```

Agent 系统还可以保存：

```text
trajectory IDs
selected Skills
tool sequence
context tokens
errors
```

这样论文和工程 debug 可以共用一套 provenance。

---

## 12. 一个成熟的 Eval Stack

```text
Unit tests
  ↓
Runtime smoke tests
  ↓
Deterministic offline eval
  ↓
LLM-judge qualitative eval
  ↓
Live Agent benchmark
  ↓
Real PPO/domain outcome
  ↓
Ablation + held-out validation
```

不要一开始就跳到最后一步，也不要只停留在第一步。
