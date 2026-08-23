# Level 1 学习笔记

这份笔记只抓最容易混淆的对象。

## 一、一次 Tool Calling 到底发生了什么

```text
1. Python 把 messages + tools schema 发给 LLM
2. LLM 不执行函数，只返回 tool_calls
3. Python 读取 tool_calls[0].function.name
4. Python 解析 tool_calls[0].function.arguments
5. Python 验证参数并调用真实函数
6. Python 把结果作为 role=tool 消息放回 messages
7. Python 再次请求 LLM
8. LLM 根据 Observation 决定继续调用工具或最终回答
```

要始终区分三类对象：

```text
Tool Function   真正执行代码
Tool Schema     给模型看的能力说明
Tool Call       模型本轮提出的调用请求
```

## 二、最重要的 Response 路径

普通回答：

```python
response.choices[0].message.content
```

Tool Calling：

```python
response.choices[0].message.tool_calls
```

第一个调用：

```python
call = response.choices[0].message.tool_calls[0]
```

然后：

```python
call.id
call.function.name
call.function.arguments
```

其中 `arguments` 通常是一段 JSON 字符串：

```python
'{"iteration":1}'
```

所以需要：

```python
arguments = json.loads(call.function.arguments)
```

## 三、为什么 arguments 不能直接信任

LLM 输出不是程序真理。它可能：

- 输出非法 JSON；
- 漏参数；
- 多出 schema 中没有的参数；
- 请求不存在的 tool；
- 给 iteration 传字符串或负数。

所以 Runtime 至少要做：

```text
JSON parse
→ tool whitelist
→ parameter validation
→ execute
→ error handling
```

不要对模型生成内容使用 `eval()`。

## 四、`finish_reason` 和 Agent 控制流

常见情况：

```text
finish_reason = stop
→ 模型正常给出最终回答

finish_reason = tool_calls
→ 模型请求调用工具

finish_reason = length
→ 输出被长度限制截断
```

实际 Agent Loop 不应只依赖文本内容猜测状态，而应读取结构化字段，例如 `message.tool_calls` 和 `finish_reason`。

## 五、为什么 Tool Result 要写回 messages

Tool Calling 是一个多轮协议：

```text
user
 ↓
assistant: 请调用 tool A，id=123
 ↓
runtime: 执行 A
 ↓
tool: id=123 的结果
 ↓
assistant: 根据结果继续
```

如果不把这些历史传回去，下一次 LLM 请求就不知道工具为什么被调用、结果属于哪个请求。

## 六、Agent Loop 和 Workflow 的区别先怎么理解

Level 1 暂时这样记：

```text
Workflow：程序预先决定步骤
Agent：模型在运行中决定下一步是否调用什么 Tool
```

现实工程中两者经常混合：外层 Workflow 约束流程，某个节点内部允许 Agent 自主决策。

## 七、为什么要设置 MAX_AGENT_ROUNDS

如果没有最大轮次，模型可能：

```text
call tool A
→ call tool B
→ call tool A
→ call tool B
→ ...
```

导致无限循环、费用增加和服务阻塞。

因此哪怕是最小 Agent，也应该有：

```python
MAX_AGENT_ROUNDS = 6
```

生产系统还会进一步加入 timeout、token budget、cost budget、重复调用检测等策略。

## 八、三个必须亲手做的实验

### 实验 1：把 `tool_choice="auto"` 改成 `"none"`

观察模型无法读取任何训练数据时怎么回答。

### 实验 2：删除 `read_component_stats` 的 schema

注意：真实函数还在 `tools.py`，但模型不知道它存在，因此不会调用它。

这个实验用于理解：

> Function 存在 ≠ Model 知道 Function 存在。

### 实验 3：把 Tool Schema 的 description 写得非常模糊

例如把：

```text
读取 reward components 的 magnitude_share 和 active_rate
```

改成：

```text
读取一些数据
```

观察 Tool 选择是否变差。

这个实验用于理解：

> Tool description 也是 Agent Context 的一部分，会直接影响 routing。

## 九、Level 1 的一句话总结

```text
LLM 负责“决定动作”，Runtime 负责“安全执行动作”，Tool Result 作为 Observation 再反馈给 LLM。
```

如果这句话你能结合代码逐行解释，Level 1 的核心就已经掌握。
