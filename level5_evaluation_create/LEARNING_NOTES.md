# Level 5 Learning Notes

## 1. Eval 的核心不是“打分”，而是定义成功

在写 evaluator 之前，先写：

```text
这个任务什么情况下算成功？
哪些行为必须发生？
哪些行为绝对不能发生？
最终外部结果是什么？
```

否则你只是事后找指标解释结果。

---

## 2. Process metrics vs Outcome metrics

### Process metrics

```text
Tool 是否正确调用
Skill 是否正确选择
Context 是否合理
是否发生 error/retry
```

### Outcome metrics

```text
任务是否真正完成
PPO 是否改善
用户是否得到正确结果
```

Process 好不代表 Outcome 一定好，但 Process metrics 对 debug 非常重要。

---

## 3. 为什么 Agent Eval 特别依赖 Trace

普通 LLM 应用经常只看：

```text
input → output
```

Agent 则有：

```text
input
→ model
→ tool
→ observation
→ model
→ skill
→ context
→ model
→ output
```

如果不保存 trajectory，就不知道中间哪里出错。

---

## 4. Gold answer 不一定够

很多 Agent 任务没有唯一文字答案。

例如 reward diagnosis：

```text
“先查 component stats 再决定是否 gating”
```

可能有很多语言表达。

所以比 exact string 更有意义的是：

```text
required evidence
required tools
acceptable skills
forbidden claims
final domain outcome
```

---

## 5. Evaluation contract 应尽量在运行前定义

如果看完模型回答才决定：

```text
“这次我觉得它这样也算对”
```

评测会不断漂移。

更好的流程：

```text
case definition
↓
freeze rubric
↓
run systems
↓
evaluate blindly
```

---

## 6. 为什么 Level 5 不直接上 LLM Judge

因为 Level 0-4 刚学完 Runtime，最重要的是先学会：

```text
从结构化事件得到结构化指标
```

如果一开始所有指标都问 LLM Judge，你会再次把系统行为隐藏进黑箱。

---

## 7. 一个 Agent 的失败可能来自不同层

```text
Model failure
Tool schema failure
Tool execution failure
MCP transport failure
Skill routing failure
Memory retrieval failure
Context packing failure
Harness stopping failure
Domain action failure
```

Eval 要帮助定位哪一层，而不只是输出一个总分。

---

## 8. 为什么要记录 model/context

因为最终回答失败时你要知道：

```text
模型到底看到了什么？
```

如果只保存 Tool Result，不保存真正组装后的请求，你无法判断：

```text
信息存在但没注入？
还是已经注入但模型没用？
```

---

## 9. Context cost 不是越低越好

极端压缩：

```text
token 很低
但重要 evidence 被删
```

也会失败。

真正优化目标更像：

```text
在 task success 不下降的前提下
降低 token / latency / cost
```

---

## 10. Skill Eval 的三个问题

```text
有没有触发？
触发的是不是正确 Skill？
触发后有没有改善真实 outcome？
```

分别对应：

```text
activation
routing
utility
```

---

## 11. Memory Eval 的三个问题

```text
Retrieve 对不对？
模型有没有正确使用？
历史信息有没有污染当前事实？
```

所以 Memory eval 不只是 Recall@K。

---

## 12. Harness Eval 的价值

Harness 提供统一的：

```text
Session
Tool Registry
Context
Events
Termination
```

因此不同业务 Agent 可以使用相同 evaluation instrumentation。

这也是 Agent Platform / Agent Infra 岗位关注的系统性问题。

---

## 13. CREATE 为什么是非常好的 Agent Eval 案例

因为它有真实外部环境：

```text
PPO training
```

LLM 不能靠“自我评价”决定自己是不是成功。

最终会有客观反馈：

```text
fitness
solved
regression
```

这比普通聊天 Agent 更容易研究真正的 closed-loop learning。

---

## 14. Experience 不能在 outcome 之前生成成功标签

顺序应该是：

```text
Agent trajectory
→ reward edit
→ validation
→ PPO outcome
→ label experience
→ Skill evolution
```

不是：

```text
Agent: 我很有信心
→ success experience
```

---

## 15. Level 0-5 的整体心智模型

```text
Level 0
LLM 可以回答

Level 1
LLM 可以决定调用函数

Level 2
外部能力可以通过 MCP 标准接入

Level 3
Agent 有 Skill / Memory / Context

Level 4
这些能力被 Harness 统一调度

Level 5
我们能够测量、比较、验证整个 Agent 系统
```

真正的 Agent Application Engineering，不只是“会调用一个 Agent Framework”，而是理解这六层之间的责任边界。
