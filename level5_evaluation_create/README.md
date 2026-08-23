# Level 5 — Evaluation + CREATE Integration

Level 4 已经有了一个可以运行的教学型 Harness：

```text
LLM + Agent Loop + MCP + Skill + Memory + Context + Session Log
```

但“能运行”不等于“有效”。Level 5 解决最后一个问题：

> **如何证明 Agent 的行为是正确、可追踪、可比较的，并把 Harness 的评测结果与真实 CREATE 强化学习训练结果连接起来？**

这一层把评测拆成三个层次：

```text
A. Runtime / System Metrics
   - 是否正常结束
   - step 数
   - tool call 数
   - tool error 数
   - context 大小

B. Agent Behavior Metrics
   - 必要 Tool 是否调用
   - Skill 是否选对
   - 回答是否覆盖关键 evidence
   - 是否出现禁止/无依据 claim

C. CREATE Outcome Metrics
   - search fitness / best-so-far fitness
   - solved
   - reward version / round
   - test fitness
   - 组件 activation_rate / magnitude_share（有真实表时）
```

最重要的一句话：

> **Agent Eval 评“Agent 怎么做”；CREATE Outcome Eval 评“这次 reward edit 训练后到底有没有变好”。两者不能混成一个指标。**

---

## 1. 为什么 Level 5 必须存在

如果只展示一次漂亮回答：

```text
Agent: 我认为是 proxy leakage，建议 validity gating。
```

你无法知道：

- 它是不是碰巧猜对；
- 是否真的读取了实验数据；
- 是否加载了正确 Skill；
- 有没有编造数字；
- 换一个 seed 是否还能工作；
- 加 Skill 后是否真的优于不加 Skill；
- 最终 PPO 是否真的改善。

因此完整链路应该是：

```text
Eval Cases
   ↓
Run Agent Variants
   ↓
Session JSONL
   ↓
Deterministic Evaluator
   ↓
Agent Metrics
   ↓
JOIN
   ↓
CREATE Training Outcomes
   ↓
Ablation / Report
```

---

## 2. 本目录结构

```text
level5_evaluation_create/
├── contracts.py               # EvalCase / evaluation contracts
├── session_eval.py            # 直接从 Level 4 Session JSONL 计算确定性指标
├── benchmark.py               # 批量评测 case × variant
├── report.py                  # 生成 Markdown/CSV 风格报告
├── create_adapter.py          # 读取真实 CREATE supplement/local clone
├── run_live_benchmark.py      # 可选：真实 LLM + Level 4 Harness
│
├── fixtures/
│   ├── cases.jsonl            # 教学 eval cases
│   └── sessions/              # 不需要 API 的固定 session traces
│
├── step1_eval_contract.py     # 先学“什么叫可评测任务”
├── step2_evaluate_session.py  # 评一个 Session Log
├── step3_ablation_fixture.py  # 比较 baseline vs full
├── step4_create_adapter.py    # 接真实 CREATE 仓库
├── step5_generate_report.py   # 汇总报告
│
├── EVALUATION_GUIDE.md
├── CREATE_INTEGRATION.md
├── INTERVIEW_QUESTIONS.md
├── SOURCE_REFERENCES.md
└── requirements.txt
```

---

## 3. 第一步：完全不需要 API

```bash
cd level5_evaluation_create
python step1_eval_contract.py
python step2_evaluate_session.py
python step3_ablation_fixture.py
python step5_generate_report.py
```

这些步骤只读取固定的 `cases.jsonl` 和 Session JSONL。

### Eval Case 不是 Prompt

一个 Eval Case 是“任务 + 可验证成功条件”：

```json
{
  "case_id": "bw_proxy_leakage",
  "user_request": "分析 BipedalWalker reward failure",
  "required_tools": ["get_training_feedback", "get_component_stats"],
  "expected_skill": "gate-proxy-by-validity",
  "required_evidence_terms": ["97.2%", "early falls"],
  "forbidden_claims": ["improved by 50%"]
}
```

这比“看看回答是否像样”更工程化。

---

## 4. Session-based evaluation

Level 4 已经把 durable facts 记录为：

```text
turn/start
user/message
model/context
assistant/message
tool/call
tool/result
turn/end
```

因此 Level 5 不需要猜 Agent 做过什么，可以直接从 JSONL 计算：

```text
completed
step_count
tool_call_count
tool_error_count
required_tool_recall
loaded_skill
skill_match
evidence_coverage
forbidden_claim_count
context_char_count
```

这也是为什么 Level 4 的 append-only log 很重要。

---

## 5. Fixture Ablation

`fixtures/sessions/` 放了同一教学 case 的两种固定 trace：

```text
baseline
full
```

baseline 故意少调用组件证据、没有加载 Skill；full 则完整执行 MCP evidence + Skill。

运行：

```bash
python step3_ablation_fixture.py
```

你应该看到 full 在：

```text
required_tool_recall
skill_match
evidence_coverage
```

上优于 baseline。

注意：这些是 **teaching fixtures**，不是论文实验结果。

---

## 6. 接真实 CREATE 仓库

这一层直接适配你的公开 supplement 仓库：

```text
Nicole-ying/CREATE-Reward-Editing-Agent
```

当前该仓库明确是 reviewer-facing supplement，而不是通用软件包；其中：

```text
03_full_results/
07_component_evidence/
08_reward_lineage_cases/
```

正好分别对应：

```text
训练 outcome
组件 evidence
reward lineage / diagnosis case
```

先把两个仓库放在同一级：

```text
workspace/
├── Harness-create/
└── CREATE-Reward-Editing-Agent/
```

然后：

```bash
python step4_create_adapter.py ../CREATE-Reward-Editing-Agent
```

Adapter 会：

1. 读取 `03_full_results/bipedalwalker_results.csv`；
2. 读取 `03_full_results/lunarlander_aggregate_results.csv`；
3. 检查 `03_full_results/per_round_results_schema.csv`；
4. 扫描 `07_component_evidence/` 下未来出现的 CSV evidence 表；
5. 把 `TBD` 保留为 missing，而不是编造数值。

### 这点非常重要

当前 CREATE supplement 本身明确说明一部分 per-round / component evidence 仍需从 raw experiment logs 填充，因此 Level 5 **不会自动把 TBD 猜成数字**。

---

## 7. 真正的 CREATE × Harness 闭环应该怎么接

最终不是：

```text
Agent 回答很好看 → success
```

而是：

```text
Harness Agent
  ↓
collect evidence
  ↓
select/load Skill
  ↓
propose reward edit
  ↓
CREATE validator
  ↓
PPO training
  ↓
real outcome
  ↓
Evaluation record
```

建议最终每一轮保存两类记录：

### Agent trace

```text
session_id
selected skill
tool calls
context snapshot
final diagnosis
proposed intervention
```

### RL outcome

```text
environment
seed / lineage
round
reward_version
search_fitness
best_so_far_fitness
solved
test_fitness
```

然后通过：

```text
run_id + lineage + round + reward_version
```

进行 join。

---

## 8. Live benchmark（可选，需要 API）

`run_live_benchmark.py` 会复用 Level 4 的 `AgentHarness`，运行同一个 case 的不同 capability 配置：

```text
tools_only
skills
a full harness
```

真实结果写入：

```text
runs/live/*.jsonl
```

然后仍然交给同一个 `session_eval.py` 评。

也就是说：

> evaluator 不关心 session 是 fixture、DeepSeek 还是其他 OpenAI-compatible provider 生成的，只认统一 Session Event Log。

---

## 9. Level 5 过关标准

你应该能独立回答：

1. 为什么 demo success 不等于 Agent evaluation？
2. offline eval 和 online/domain outcome 有什么区别？
3. 为什么先做 deterministic eval，再考虑 LLM-as-a-Judge？
4. 如何从 session trace 计算 Tool success？
5. Skill routing accuracy 怎么定义？
6. Context cost 怎么量？
7. 为什么 Agent answer score 不能替代 PPO outcome？
8. Ablation 为什么必须固定 case / seed / budget？
9. 如何避免 data leakage？
10. 如何把 CREATE 的 round outcome 与 Agent trajectory join？

做到这里，Level 0 → 5 就形成完整工程链：

```text
LLM API
 ↓
Tool Calling
 ↓
MCP
 ↓
Skill / Memory / Context
 ↓
Harness / Runtime
 ↓
Evaluation / Ablation / Real CREATE Outcome
```
