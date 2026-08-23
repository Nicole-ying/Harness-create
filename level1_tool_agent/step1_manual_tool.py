"""Level 1A: a Tool is first just an ordinary Python function.

There is NO LLM decision in this file. Python chooses the function directly.
Run this first before learning Function Calling.
"""

from __future__ import annotations

import json

from tools import read_training_feedback


def main() -> None:
    # The programmer decides to call this function.
    result = read_training_feedback(iteration=1)

    print("========== PYTHON CALLED THE TOOL ==========")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\nQuestion for yourself:")
    print("Who decided to call read_training_feedback()? Answer: Python code, not the LLM.")


if __name__ == "__main__":
    main()
