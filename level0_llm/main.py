"""Level 0 exercise: one prompt in, one answer out.

Goal:
1. Read a small experiment case with ordinary Python.
2. Manually place that information into the user prompt.
3. Send exactly one LLM request.
4. Print the returned text.

Important: this is NOT an agent yet. The model cannot read files, choose tools, call
functions, remember previous runs, or use MCP/Skills. Those capabilities are introduced
in later levels.
"""

from __future__ import annotations

import json
from pathlib import Path

from llm_client import SimpleLLMClient, load_llm_config


HERE = Path(__file__).resolve().parent


SYSTEM_PROMPT = """You are a reinforcement-learning experiment analysis assistant.
Only use the experiment information explicitly included in the user message.
Do not pretend that you can inspect files, run code, call tools, or see hidden context.

Please answer in Chinese and use this structure:
1. 观察到的现象
2. 最可能的问题
3. 你的依据
4. 下一步建议检查什么

At Level 0, do not claim certainty. Distinguish observations from hypotheses.
"""


def load_case() -> dict:
    """Ordinary Python reads the JSON file BEFORE the LLM request."""
    path = HERE / "example_case.json"
    return json.loads(path.read_text(encoding="utf-8"))


def build_user_prompt(case: dict) -> str:
    """Turn selected experiment data into plain text for the LLM.

    Notice what is happening here: *our Python program* decides what the model sees.
    The model itself does not know that example_case.json exists.
    """

    components = case["reward_components"]
    forward = components["forward_velocity_reward"]
    upright = components["upright_penalty"]
    vertical = components["vertical_oscillation_penalty"]

    return f"""请分析下面这次 PPO 奖励函数训练为什么可能失败。

任务: {case['task']}
iteration: {case['iteration']}
mean_eval_reward: {case['mean_eval_reward']}
mean_episode_length: {case['mean_episode_length']}
early_falls: {case['early_falls']}

奖励组件统计:
- forward_velocity_reward: magnitude_share={forward['magnitude_share']:.1%}, active_rate={forward['active_rate']:.1%}
- upright_penalty: magnitude_share={upright['magnitude_share']:.1%}
- vertical_oscillation_penalty: active_rate={vertical['active_rate']:.1%}

请只根据这些信息分析。你现在不能读取其他训练文件，因此如果证据不足，请明确告诉我下一步还需要检查什么。
"""


def main() -> None:
    config = load_llm_config()
    client = SimpleLLMClient(config)

    case = load_case()
    user_prompt = build_user_prompt(case)

    print(f"Provider: {config.provider}")
    print(f"Model:    {config.model}")
    print("\n========== USER PROMPT ==========")
    print(user_prompt)

    answer = client.chat(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    print("\n========== LLM RESPONSE ==========")
    print(answer)


if __name__ == "__main__":
    main()
