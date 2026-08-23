# CREATE Integration Contract

Level 5 不把 CREATE 当成一个虚构目录。本教程专门检查了当前公开仓库：

```text
Nicole-ying/CREATE-Reward-Editing-Agent
```

该仓库 README 明确说明它是 **reviewer-facing supplement**，目前包含实验设置、ablation、结果 schema、component evidence 说明、reward lineage cases 和 reward programs，而不是一个通用 Python package。

因此最安全的集成方式不是强行 import 它，而是定义 **artifact contract**。

---

## 1. 当前可直接读取的 outcome 数据

### `03_full_results/bipedalwalker_results.csv`

当前字段：

```text
seed
initial_fitness
first_version_ge_300
best_fitness
test_fitness
```

`create_adapter.py` 只抽取 seed 行，`mean/std` 行不会伪装成独立 seed。

如果字段是 `TBD`，返回 `None`。

### `03_full_results/lunarlander_aggregate_results.csv`

当前字段：

```text
condition
budget
best_fitness_mean
best_fitness_std
solved
```

它适合做论文级 condition/ablation 对比，不适合替代单轮 Agent trajectory。

---

## 2. per-round 连接点

当前 `03_full_results/per_round_results_schema.csv` 定义：

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

这正是未来 Harness Session 与 CREATE PPO outcome 的主要 join contract。

推荐最小 join key：

```text
run_id
+ environment
+ lineage_index
+ round
+ reward_version
```

如果 `run_id` 在 raw pipeline 中已经全局唯一，也可以作为 primary key，但保留其余 provenance 字段更利于审计。

---

## 3. Harness 侧应该额外保存什么

建议每次 reward-editing turn 保存：

```json
{
  "run_id": "...",
  "environment": "BipedalWalker-v3",
  "lineage_index": 0,
  "round": 2,
  "input_reward_version": "v1",
  "output_reward_version": "v2",
  "session_path": "...jsonl",
  "selected_skill": "gate-proxy-by-validity",
  "proposal_hash": "..."
}
```

其中真实 PPO 指标不要在 Agent 输出时填写；训练完成后，由实验 runner 回填。

---

## 4. Component evidence

CREATE supplement 的 `07_component_evidence/README.md` 当前定义了推荐字段：

```text
environment
condition
lineage_index
round
component_name
episode_sum_mean
activation_rate
magnitude_share
dominance_rank
diagnostic_note
```

并明确要求缺失值使用 `NA`，不要推断。

因此 `create_adapter.py` 会扫描：

```text
07_component_evidence/**/*.csv
```

如果现在还没有 CSV，它返回空 collection；未来真实表加入后不需要改 adapter API。

---

## 5. 正确的闭环顺序

```text
Harness Session
  ↓
Agent diagnosis
  ↓
reward proposal
  ↓
CREATE code validation
  ↓
PPO train/eval
  ↓
per-round outcome artifact
  ↓
join session + outcome
  ↓
Eval / ablation
```

错误顺序是：

```text
LLM 说“这个 edit 应该更好”
  ↓
直接写 success=True
```

这种写法会污染 Memory/Skill 学习。

---

## 6. Experience / Skill Evolution 的数据门

如果后续把 Level 5 接到 CREATE 第四章的 Experience → Skill 机制，建议只允许满足下面条件的记录进入长期经验：

```text
Agent proposal exists
AND reward code passed validation
AND PPO outcome exists
AND provenance complete
```

再根据真实 outcome 标记：

```text
successful experience
failed experience
regression
confounded / inconclusive
```

不能把没有 PPO outcome 的 Agent 自评结果直接当成 Skill 成功证据。

---

## 7. 未来 raw CREATE pipeline 接入时

`create_adapter.py` 当前读 supplement。真正接 raw experiment repo 时，建议新增：

```text
RawCREATEAdapter
```

而不是修改 evaluator。

原因：

```text
raw files / supplement files
        ↓
    Adapter Layer
        ↓
Canonical Outcome Record
        ↓
    Evaluation
```

这样 artifact layout 改变不会污染评测逻辑。
