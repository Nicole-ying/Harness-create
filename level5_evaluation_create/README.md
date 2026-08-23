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
   - activation_rate / magnitude_share（有真实 component 表时）
```

最重要的一句话：

> **Agent Eval 评“Agent 怎么做”；CREATE Outcome Eval 评“这次 reward edit 训练后到底有没有变好”。两者不能混成一个指标。**

---

## 1. 为什么 Level 5 必须存在

如果只展示一次漂亮回答：

```text
Agent: 我认为是 proxy leakage，建议 validity gating。
```

你无法知道它是不是碰巧猜对、有没有真的读取实验数据、是否加载了正确 Skill、有没有编造数字、换 seed 后是否稳定，也无法知道最终 PPO 是否真的改善。

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

## 2. 文件结构

```text
level5_evaluation_create/
├── contracts.py               # EvalCase / SessionMetrics
├── session_eval.py            # 直接从 Level 4 Session JSONL 算确定性指标
├── benchmark.py               # case × variant 批量评测
├── report.py                  # Markdown report
├── create_adapter.py          # 读取真实 CREATE supplement/local clone
├── outcome_join.py            # Agent trajectory ↔ PPO outcome provenance join
├── run_live_benchmark.py      # 可选：真实 LLM + Level 4 Harness
│
├── fixtures/
│   ├── cases.jsonl
│   ├── sessions/
│   ├── agent_records.jsonl
│   └── create_round_outcomes.csv
│
├── smoke_test.py
├── step1_eval_contract.py
├── step2_evaluate_session.py
├── step3_ablation_fixture.py
├── step4_create_adapter.py
├── step5_generate_report.py
├── step6_join_agent_create.py
│
├── EVALUATION_GUIDE.md
├── CREATE_INTEGRATION.md
├── LEARNING_NOTES.md
├── INTERVIEW_QUESTIONS.md
├── SOURCE_REFERENCES.md
└── tests/test_level5.py
```

---

## 3. 安装与第一轮运行：完全不需要 API

```bash
cd level5_evaluation_create
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

先跑：

```bash
python smoke_test.py
pytest -q
```

然后严格按顺序：

```bash
python step1_eval_contract.py
python step2_evaluate_session.py
python step3_ablation_fixture.py
python step5_generate_report.py
python step6_join_agent_create.py
```

这些步骤都不需要 LLM API。

---

## 4. Eval Case 不是 Prompt

一个 Eval Case 是“任务 + 可验证成功条件”：

```json
{
  "case_id": "bw_proxy_leakage",
  "user_request": "分析 BipedalWalker reward failure",
  "required_tools": ["get_training_feedback", "get_component_stats"],
  "expected_skill": "gate-proxy-by-validity",
  "required_evidence_terms": ["97.2%", "14/20"],
  "forbidden_claims": ["improved by 50%"]
}
```

这比“看看回答是否像样”更工程化。

`fixtures/` 中所有数值都明确是 synthetic teaching data，不是 CREATE 论文实验结果。

---

## 5. Session-based evaluation

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

因此 Level 5 可以直接计算：

```text
completed
step_count
tool_call_count
tool_error_count
required_tool_recall
loaded_skills
skill_match
evidence_coverage
forbidden_claim_count
total_context_chars
max_context_chars
passed_contract
```

这也是为什么 Level 4 的 append-only Session Log 很重要。

---

## 6. Fixture Ablation

固定 trace 提供两种 variant：

```text
baseline
full
```

baseline 故意缺少部分 evidence / Skill；full 完成 required Tool + Skill 流程。

```bash
python step3_ablation_fixture.py
```

它只证明 evaluator 能区分两种轨迹，**不证明真实 LLM 或真实 CREATE 得到了提升**。

---

## 7. 接真实 CREATE 仓库

Level 5 直接适配当前公开 supplement：

```text
Nicole-ying/CREATE-Reward-Editing-Agent
```

当前仓库本身说明它是 reviewer-facing supplement，而非通用 Python package；因此这里采用 artifact adapter，而不是强行 import。

将两个仓库放在同一级：

```text
workspace/
├── Harness-create/
└── CREATE-Reward-Editing-Agent/
```

然后：

```bash
python step4_create_adapter.py ../CREATE-Reward-Editing-Agent
```

Adapter 当前会读取：

```text
03_full_results/bipedalwalker_results.csv
03_full_results/lunarlander_aggregate_results.csv
03_full_results/per_round_results_schema.csv
07_component_evidence/**/*.csv
```

`TBD` / `NA` 会转换为 missing (`None`)；绝不猜数字。

---

## 8. Agent trajectory 和真实 PPO outcome 怎么 join

Level 5 用 provenance key：

```text
run_id
+ environment
+ lineage_index
+ round
+ reward_version
```

进行连接。

```bash
python step6_join_agent_create.py
```

这个教学步骤使用 synthetic records 来演示：

```text
Agent session
      ↓
reward proposal + validation status
      ↓
JOIN
      ↓
PPO round outcome
      ↓
Experience gate
```

真实系统中，只有存在实际 PPO outcome 且 reward code 已通过 validation 的 trajectory，才应进入 Experience/Skill 后续标注流程。

---

## 9. Live benchmark（可选，需要 API）

复制：

```powershell
Copy-Item .env.example .env
```

填本地 API Key 后：

```bash
python run_live_benchmark.py
```

它复用 Level 4 的 `AgentHarness`，比较：

```text
tools_only
tools + skill
full = tools + skill + memory + trace
```

每个结果都保存到：

```text
runs/live/*.jsonl
```

然后仍由同一个 `session_eval.py` 评测。

**单次 live run 只算 smoke test。** 真正 ablation 至少需要多次运行/种子、固定 model/version、matched budget 和相同 stopping rule。

---

## 10. 真正的 CREATE × Harness 闭环

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
CREATE code validation
  ↓
PPO training
  ↓
real outcome
  ↓
join Agent trace + outcome
  ↓
Evaluation / Experience labeling / Skill evolution
```

建议每一轮保存：

```text
Agent trace:
session_path / tool calls / selected skill / proposal / model+skill versions

RL outcome:
run_id / environment / lineage / round / reward_version /
search_fitness / best_so_far_fitness / solved / test_fitness
```

---

## 11. Level 5 过关标准

你应该能独立解释：

```text
Demo success vs evaluation
offline vs online/domain outcome
deterministic eval vs LLM-as-a-Judge
Tool/Skill/Memory/Context metrics
trajectory evaluation
ablation + matched budget
paired seeds
data leakage
Agent trace ↔ PPO outcome join
为什么 LLM 自评不能成为 Experience 成功标签
```

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
