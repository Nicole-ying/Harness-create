"""Step 5: generate a reproducible Markdown report from fixture traces."""

from pathlib import Path

from benchmark import evaluate_fixture_directory
from report import write_report


HERE = Path(__file__).resolve().parent


def main() -> None:
    results = evaluate_fixture_directory(
        cases_file=HERE / "fixtures" / "cases.jsonl",
        sessions_dir=HERE / "fixtures" / "sessions",
    )
    output = HERE / "runs" / "fixture_report.md"
    write_report(results, output)
    print("report written to:", output)
    print(output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
