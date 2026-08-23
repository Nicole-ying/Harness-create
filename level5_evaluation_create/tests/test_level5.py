from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
LEVEL5 = HERE.parent
sys.path.insert(0, str(LEVEL5))

from benchmark import aggregate_by_variant, evaluate_fixture_directory
from contracts import find_case, load_cases
from outcome_join import experience_gate, join_agent_and_outcomes
from session_eval import evaluate_session, load_events


def test_full_proxy_trace_passes_contract():
    cases = load_cases(LEVEL5 / "fixtures" / "cases.jsonl")
    case = find_case(cases, "bw_proxy_leakage")
    events = load_events(
        LEVEL5 / "fixtures" / "sessions" / "bw_proxy_leakage__full.jsonl"
    )
    metrics = evaluate_session(case, events, variant="full")
    assert metrics.passed_contract is True
    assert metrics.required_tool_recall == 1.0
    assert metrics.skill_match is True
    assert metrics.evidence_coverage == 1.0


def test_baseline_proxy_trace_fails_contract():
    cases = load_cases(LEVEL5 / "fixtures" / "cases.jsonl")
    case = find_case(cases, "bw_proxy_leakage")
    events = load_events(
        LEVEL5 / "fixtures" / "sessions" / "bw_proxy_leakage__baseline.jsonl"
    )
    metrics = evaluate_session(case, events, variant="baseline")
    assert metrics.passed_contract is False
    assert metrics.required_tool_recall < 1.0
    assert metrics.skill_match is False


def test_fixture_full_variant_beats_baseline_contract_rate():
    results = evaluate_fixture_directory(
        cases_file=LEVEL5 / "fixtures" / "cases.jsonl",
        sessions_dir=LEVEL5 / "fixtures" / "sessions",
    )
    summary = aggregate_by_variant(results)
    assert summary["full"]["contract_pass_rate"] > summary["baseline"]["contract_pass_rate"]


def test_outcome_join_requires_verified_outcome():
    agent = {
        "run_id": "r1",
        "environment": "BipedalWalker-v3",
        "lineage_index": 0,
        "round": 2,
        "reward_version": "v2",
        "reward_code_validated": True,
    }
    outcome = {
        "run_id": "r1",
        "environment": "BipedalWalker-v3",
        "lineage_index": 0,
        "round": 2,
        "reward_version": "v2",
        "search_fitness": "320.0",
    }
    row = join_agent_and_outcomes([agent], [outcome])[0]
    assert row["has_verified_outcome"] is True
    assert experience_gate(row) == "eligible_for_experience_labeling"
