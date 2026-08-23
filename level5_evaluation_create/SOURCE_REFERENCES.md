# Source References

Level 5 的设计不是凭空造概念，主要基于以下公开材料和本用户自己的 CREATE supplementary repository。

## 1. DeepSeek Harness

Repository:

```text
deepseek-ai/deepseek-harness
```

Primary file:

```text
docs/architecture.md
```

Level 5 继承的关键思想：

```text
append-only session events
turn / step distinction
model-visible context should be logged/reconstructable
tool execution is a runtime concern
runtime extension points
```

Level 5 没有复制 Cordis，也没有声称与 DeepSeek Harness API 兼容。

## 2. Agent Skills specification

Repository:

```text
agentskills/agentskills
```

Primary file:

```text
docs/specification.mdx
```

Relevant concepts:

```text
SKILL.md
name + description metadata
progressive disclosure
on-demand instructions/resources
```

这些概念在 Level 3/4 被实现，Level 5 负责评它们是否被正确选择和使用。

## 3. Anthropic Skills examples

Repository:

```text
anthropics/skills
```

Example:

```text
skills/mcp-builder/SKILL.md
```

Relevant lesson:

> Skill 应该描述程序性方法、检查和验证，而不只是一个长 Prompt。

## 4. CREATE supplementary repository

Repository:

```text
Nicole-ying/CREATE-Reward-Editing-Agent
```

### `README.md`

明确说明仓库是 reviewer-facing supplement，并包含实验设置、ablation、per-seed/per-round results、component evidence、reward lineage cases 等。

### `03_full_results/per_round_results_schema.csv`

当前定义字段：

```text
environment
condition
lineage_index
round
reward_version
search_fitness
best_so_far_fitness
solved
native_eval_episodes
episode_length_mean
termination_summary
selected_for_test
test_fitness
run_id
notes
```

Level 5 用这组字段作为未来 Agent trajectory ↔ PPO outcome 的 join contract。

### `03_full_results/bipedalwalker_results.csv`

当前包含 seed-level：

```text
initial_fitness
first_version_ge_300
best_fitness
test_fitness
```

其中部分 `test_fitness` 仍为 `TBD`；Adapter 保留 missing，不推断。

### `03_full_results/lunarlander_aggregate_results.csv`

当前包含 condition-level ablation：

```text
condition
budget
best_fitness_mean
best_fitness_std
solved
```

### `07_component_evidence/README.md`

定义未来 component evidence 表应包含：

```text
activation_rate
magnitude_share
dominance_rank
diagnostic_note
```

并明确要求 missing entries 使用 `NA`，不能推断。

## 5. Teaching fixture disclaimer

`level5_evaluation_create/fixtures/` 中的 97.2%、14/20、5%、2%/41% 等数字只用于演示 evaluator 行为。

它们被显式标记为 synthetic teaching cases，不应引用为 CREATE 论文实验结果。
