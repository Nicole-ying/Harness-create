"""Step 3: compare baseline vs full Harness traces. No API required."""

from pathlib import Path

from benchmark import aggregate_by_variant, evaluate_fixture_directory


HERE = Path(__file__).resolve().parent


def main() -> None:
    results = evaluate_fixture_directory(
        cases_file=HERE / "fixtures" / "cases.jsonl",
        sessions_dir=HERE / "fixtures" / "sessions",
    )
    summary = aggregate_by_variant(results)

    print("========== ABLATION SUMMARY ==========")
    for variant, row in summary.items():
        print(f"\n[{variant}]")
        for key, value in row.items():
            print(f"{key}: {value:.3f}" if isinstance(value, float) else f"{key}: {value}")

    print(
        "\nInterpretation: the fixture demonstrates the evaluation pipeline only. "
        "It is not evidence that a real model/Harness improves CREATE."
    )


if __name__ == "__main__":
    main()
