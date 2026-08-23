"""Step 2: evaluate one append-only Session JSONL. No API required."""

from pathlib import Path

from contracts import find_case, load_cases
from session_eval import evaluate_session, load_events


HERE = Path(__file__).resolve().parent


def main() -> None:
    cases = load_cases(HERE / "fixtures" / "cases.jsonl")
    case = find_case(cases, "bw_proxy_leakage")
    session_file = HERE / "fixtures" / "sessions" / "bw_proxy_leakage__full.jsonl"

    metrics = evaluate_session(
        case,
        load_events(session_file),
        variant="full",
    )

    print("========== SESSION METRICS ==========")
    print(metrics.model_dump_json(indent=2))
    print(
        "\nObserve that the evaluator never asks an LLM whether the answer looks good; "
        "it checks durable events against the contract."
    )


if __name__ == "__main__":
    main()
