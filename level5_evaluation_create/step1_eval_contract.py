"""Step 1: inspect deterministic evaluation contracts. No API required."""

from pathlib import Path

from contracts import load_cases


HERE = Path(__file__).resolve().parent


def main() -> None:
    cases = load_cases(HERE / "fixtures" / "cases.jsonl")
    print("========== EVAL CASES ==========")
    for case in cases:
        print(f"\n[{case.case_id}]")
        print("request:", case.user_request)
        print("required_tools:", case.required_tools)
        print("expected_skill:", case.expected_skill)
        print("required_evidence_terms:", case.required_evidence_terms)
        print("forbidden_claims:", case.forbidden_claims)
        print("notes:", case.notes)

    print(
        "\nKey idea: an eval case is not just a prompt. It also contains observable success criteria."
    )


if __name__ == "__main__":
    main()
