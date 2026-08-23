# Level 5 — Agent Evaluation 面试题

## 1. 为什么 Agent Demo 能跑不等于 Agent 做得好？

因为单次成功可能是偶然。需要固定 case、可验证成功条件、多次运行和 domain outcome 才能判断系统能力。

## 2. 什么是 deterministic eval？

不用另一个 LLM 打分，而是根据可观察事实和规则直接计算，例如是否调用指定 Tool、是否出现 Tool error、是否达到 threshold。

## 3. 为什么 Tool Calling 很适合 deterministic eval？

Tool calls 已经是结构化事件，name、arguments、result 都可以直接记录和检查。

## 4. `required_tool_recall` 怎么定义？

```text
实际调用的 required tools 数 / case 要求的 required tools 总数
```

## 5. Tool 调得越多越好吗？

不是。过多调用可能说明 routing 不稳定、重复查询、错误恢复差，也会增加 latency/token/cost。

## 6. 怎么评 Skill Router？

如果 case 有 gold Skill，可以计算 Skill selection accuracy；没有单一 gold Skill 时可以用 acceptable-skill set 或 rubric。

## 7. Skill match 高就说明 Skill 有价值吗？

不说明。选对 Skill 只是过程指标，最终还必须看 task/domain outcome 和 negative transfer。

## 8. 什么是 negative transfer？

Skill 看起来相关，但加载后反而降低任务表现或导致错误干预。

## 9. Memory 怎么评？

可以评 retrieval relevance、memory utilization、contamination、stale memory rate，以及加入 Memory 后 domain outcome 是否改善。

## 10. 为什么不能把历史 Memory 当当前 run 的事实？

历史 episode 只提供 prior/reference。当前 run 的事实必须来自当前 evidence，否则会产生错误归因。

## 11. Context Engineering 怎么评？

至少记录 prompt/context token、latency、任务成功率；比较更短 context 是否保持或提高 task success。

## 12. Level 5 为什么先用字符数，不直接 Token？

字符数是 provider-independent 的教学 proxy。生产环境应使用 tokenizer/provider usage 记录真实 token。

## 13. 什么是 unsupported claim rate？

最终回答中的事实性 claim 没有对应 evidence/tool result 支撑的比例。

## 14. 为什么 LLM-as-a-Judge 不能替代所有 eval？

Judge 也会漂移、有偏差、有成本。能用结构化规则判断的内容应优先 deterministic evaluation。

## 15. LLM-as-a-Judge 适合什么？

难以用简单规则衡量的 reasoning quality、解释完整性、是否区分 observation 与 hypothesis 等。

## 16. LLM Judge 怎么提高可靠性？

固定 judge model/version、固定 rubric、结构化输出、blind comparison、人工抽样校准。

## 17. 为什么 Session Event Log 对 eval 很重要？

它让 evaluator 看到实际发生的 Tool Call、Tool Result、模型上下文和结束状态，而不是依赖最终答案自述。

## 18. 什么是 trajectory evaluation？

不是只评最终 answer，而是评完整执行轨迹：Tool 顺序、Skill activation、retries、errors、context 和 termination。

## 19. `turn` 和 `step` 的 eval 有什么区别？

一个 turn 可能包含多个 step。turn success 是任务级；step metrics 更适合分析推理/工具循环效率。

## 20. Agent 的 online eval 是什么？

在真实或近真实系统中运行 Agent，观察真实工具、用户任务或环境 outcome，而不是固定离线 trace。

## 21. CREATE 中最重要的 domain outcome 是什么？

真实 PPO 训练后的 search fitness、best-so-far fitness、solved、test fitness 等，而不是 LLM 对 reward 的自我评价。

## 22. 为什么 Agent 诊断正确不代表 reward edit 成功？

诊断到正确 failure mode 后，具体干预强度、参数尺度、训练随机性仍可能导致失败或 regression。

## 23. 怎么把 Agent trace 和 PPO outcome 连接？

使用稳定 provenance key，例如 `run_id + environment + lineage + round + reward_version`。

## 24. 为什么不能在 Agent 输出时就写 `success=True`？

success 必须由后续真实训练/验证 outcome 决定，否则会污染 Experience/Memory/Skill 学习。

## 25. Agent ablation 要控制哪些变量？

相同 task、initial reward、PPO seed、training budget、LLM model、tool budget、stopping rule、evaluation episodes。

## 26. 为什么 paired PPO seed 有价值？

能减少环境/训练随机性造成的方差，使不同 Agent capability 之间更可比较。

## 27. 什么是 matched budget？

不同方法拥有相同或可比的模型调用、reward proposal、训练次数等预算，防止“更多算力”被误认为方法更好。

## 28. 什么是 data leakage？

评测目标的数据、轨迹或结果被用于构造/调试 Skill、Prompt 或 Memory，导致 held-out 结果被污染。

## 29. 为什么报告 per-seed/per-round？

均值会掩盖 collapse、regression 和个别 lineage 的行为。per-seed/per-round 能支持机制分析和复现。

## 30. 生产 Agent 还应该记录什么？

latency、prompt/completion tokens、Tool success、retry、timeout、cost、trace ID、model version、Skill version、context version。

## 31. Eval Case 和普通 Prompt 的区别？

Prompt 只描述任务；Eval Case 还定义可验证 contract，例如 required tools、expected skill、evidence requirements 和 forbidden claims。

## 32. 为什么 evaluator 应尽量与 Agent implementation 解耦？

这样同一套 evaluator 可以比较不同 Provider、Framework、Harness 和版本，避免测量逻辑跟被测系统一起变化。

## 33. 为什么 Level 5 的 evaluator 直接吃 Session JSONL？

因为 Level 4 已经把重要 runtime facts 统一成 event log，这形成稳定 evaluation interface。

## 34. 如果一个回答很好，但 required Tool 没调用，怎么算？

根据 contract 可以判失败，因为它可能依靠先验猜测或数据泄漏。任务是否允许无 Tool 作答应在 Eval Case 中预先定义。

## 35. 如何评 Context 压缩是否有效？

比较压缩前后 task success / domain outcome，同时看 prompt tokens、latency 和 cost，不能只看 context 变短。

## 36. 如何评 MCP 本身？

Tool discovery success、Tool call success、schema correctness、latency、error quality、timeout/retry，以及模型能否完成真实任务。

## 37. Skill version 为什么要记录？

Skill 文本变化会改变 Agent 行为。没有 version/provenance，实验无法复现。

## 38. Memory version 为什么重要？

Memory 内容是模型输入的一部分。不同 memory snapshot 会成为实验 confounder。

## 39. Harness Eval 和模型 Eval 有什么区别？

模型 Eval 关注基础模型能力；Harness Eval 关注围绕模型的 Tool/Skill/Context/Memory/Runtime 组合后系统表现。

## 40. 30 秒回答：你如何评测一个 Agent 系统？

> 我会把评测分成 Runtime correctness、Agent behavior 和真实 domain outcome 三层。首先基于 Session/Trace 做 deterministic metrics，比如任务是否结束、Tool success、required-tool recall、Skill routing、context/token 和 unsupported claims；再用固定 eval set 比较不同 capability ablation。对难以规则化的 reasoning quality 可以增加经过人工校准的 LLM-as-a-Judge。最终如果 Agent 会修改外部系统，例如 CREATE 的 reward function，我不会把回答质量当成功，而会把 trajectory 与真实 PPO 训练 outcome 通过 run/round/version provenance join，做 paired-seed 和 matched-budget 的最终验证。
