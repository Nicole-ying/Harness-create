"""Batch evaluation for case × variant session traces."""

from __future__ import annotations

from pathlib import Path

from contracts import SessionMetrics, find_case, load_cases
from session_eval import evaluate_session, load_events


def evaluate_fixture_directory(
    *,
    cases_file: Path,
    sessions_dir: Path,
) -> list[SessionMetrics]:
    cases = load_cases(cases_file)
    results: list[SessionMetrics] = []

    for session_file in sorted(sessions_dir.glob("*.jsonl")):
        stem = session_file.stem
        if "__" not in stem:
            continue
        case_id, variant = stem.split("__", 1)
        case = find_case(cases, case_id)
        events = load_events(session_file)
        results.append(evaluate_session(case, events, variant=variant))

    return results


def aggregate_by_variant(results: list[SessionMetrics]) -> dict[str, dict[str, float]]:
    variants = sorted({r.variant for r in results})
    summary: dict[str, dict[str, float]] = {}

    for variant in variants:
        rows = [r for r in results if r.variant == variant]
        if not rows:
            continue
        n = len(rows)
        skill_rows = [r for r in rows if r.skill_match is not None]
        summary[variant] = {
            "cases": float(n),
            "contract_pass_rate": sum(r.passed_contract for r in rows) / n,
            "completed_rate": sum(r.completed for r in rows) / n,
            "required_tool_recall": sum(r.required_tool_recall for r in rows) / n,
            "skill_match_rate": (
                sum(bool(r.skill_match) for r in skill_rows) / len(skill_rows)
                if skill_rows
                else 1.0
            ),
            "evidence_coverage": sum(r.evidence_coverage for r in rows) / n,
            "avg_steps": sum(r.step_count for r in rows) / n,
            "avg_tool_calls": sum(r.tool_call_count for r in rows) / n,
            "avg_max_context_chars": sum(r.max_context_chars for r in rows) / n,
        }

    return summary
