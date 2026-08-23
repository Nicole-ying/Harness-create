"""Step 4: inspect real CREATE supplementary results from a local clone."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from create_adapter import (
    extract_bipedal_seed_outcomes,
    extract_lunarlander_ablation_outcomes,
    load_create_repository,
)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python step4_create_adapter.py ../CREATE-Reward-Editing-Agent"
        )

    root = Path(sys.argv[1])
    snapshot = load_create_repository(root)

    print("========== CREATE SNAPSHOT ==========")
    print("root:", snapshot.root)
    print("missing report:")
    print(json.dumps(snapshot.missing_report(), indent=2, ensure_ascii=False))

    print("\n========== BIPEDALWALKER SEED OUTCOMES ==========")
    print(
        json.dumps(
            extract_bipedal_seed_outcomes(snapshot),
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\n========== LUNARLANDER ABLATIONS ==========")
    print(
        json.dumps(
            extract_lunarlander_ablation_outcomes(snapshot),
            indent=2,
            ensure_ascii=False,
        )
    )

    print(
        "\nTBD/NA values are returned as null. Level 5 never invents missing experimental outcomes."
    )


if __name__ == "__main__":
    main()
