"""No-API smoke test for Level 5 evaluation plumbing."""

from pathlib import Path

from benchmark import evaluate_fixture_directory


HERE = Path(__file__).resolve().parent


def main() -> None:
    results = evaluate_fixture_directory(
        cases_file=HERE / "fixtures" / "cases.jsonl",
        sessions_dir=HERE / "fixtures" / "sessions",
    )
    assert len(results) == 6, f"expected 6 fixture traces, got {len(results)}"

    by_key = {(r.case_id, r.variant): r for r in results}
    for case_id in ["bw_proxy_leakage", "bw_sparse_outcome", "bw_rare_risk"]:
        assert by_key[(case_id, "full")].passed_contract is True
        assert by_key[(case_id, "baseline")].passed_contract is False

    print("Level 5 evaluation smoke test passed.")


if __name__ == "__main__":
    main()
