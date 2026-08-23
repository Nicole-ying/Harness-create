"""Level 4D: inspect/replay the append-only session log without calling an LLM."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SESSION_FILE = HERE / "runs" / "full_harness_session.jsonl"


def main() -> None:
    if not SESSION_FILE.exists():
        raise SystemExit(
            "Run step3_full_harness.py first so runs/full_harness_session.jsonl exists."
        )

    events = [
        json.loads(line)
        for line in SESSION_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    print("========== EVENT TIMELINE ==========")
    for event in events:
        print(f"{event['seq']:>3}  {event['type']}")

    contexts = [e for e in events if e["type"] == "model/context"]
    print("\nmodel/context snapshots:", len(contexts))
    if contexts:
        latest = contexts[-1]["data"]
        print("\n========== LAST MODEL-VISIBLE MESSAGES ==========")
        for index, message in enumerate(latest["messages"]):
            print(f"[{index}] role={message.get('role')}")
            content = message.get("content")
            if content:
                print(str(content)[:1200])
            if message.get("tool_calls"):
                print("tool_calls:", message["tool_calls"])
            print()

        print("Visible tool names:")
        for tool in latest["tools"]:
            print("-", tool["function"]["name"])

    print(
        "\nThe snapshot is recorded after agent/pre-step hooks, so it represents "
        "the actual messages and Tool schemas sent to the model provider."
    )


if __name__ == "__main__":
    main()
