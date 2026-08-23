"""Step 6: join Agent trajectory provenance with CREATE round outcomes."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from outcome_join import experience_gate, join_agent_and_outcomes


HERE = Path(__file__).resolve().parent


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    agents = load_jsonl(HERE / "fixtures" / "agent_records.jsonl")
    outcomes = load_csv(HERE / "fixtures" / "create_round_outcomes.csv")

    joined = join_agent_and_outcomes(agents, outcomes)

    print("========== JOINED RECORDS ==========")
    for row in joined:
        print(json.dumps(row, indent=2, ensure_ascii=False))
        print("experience gate:", experience_gate(row))
        print()

    print(
        "All rows in this step are synthetic teaching records. In real CREATE, "
        "the outcome side must come from actual PPO artifacts, not from the Agent answer."
    )


if __name__ == "__main__":
    main()
