"""Deterministic evaluation over Level 4 append-only Session JSONL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from contracts import EvalCase, SessionMetrics


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


def _final_answer(events: list[dict[str, Any]]) -> str:
    for event in reversed(events):
        if event.get("type") == "turn/end":
            answer = event.get("data", {}).get("answer")
            if answer is not None:
                return str(answer)
    for event in reversed(events):
        if event.get("type") == "assistant/message":
            content = event.get("data", {}).get("content")
            if content:
                return str(content)
    return ""


def _tool_calls(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [e for e in events if e.get("type") == "tool/call"]


def _tool_results(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [e for e in events if e.get("type") == "tool/result"]


def _loaded_skills(events: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for event in _tool_calls(events):
        data = event.get("data", {})
        if data.get("name") != "load_skill":
            continue
        args = data.get("arguments") or {}
        skill_name = args.get("skill_name")
        if skill_name:
            names.append(str(skill_name))
    return names


def _context_chars(events: list[dict[str, Any]]) -> tuple[int, int]:
    sizes: list[int] = []
    for event in events:
        if event.get("type") != "model/context":
            continue
        data = event.get("data", {})
        # Level 4 records exact model-visible messages + tools.
        rendered = json.dumps(
            {"messages": data.get("messages", []), "tools": data.get("tools", [])},
            ensure_ascii=False,
        )
        sizes.append(len(rendered))
    return sum(sizes), max(sizes, default=0)


def _looks_like_tool_error(content: str) -> bool:
    text = content.lower()
    markers = (
        '"error"',
        "mcp_tool_error",
        "mcp_client_error",
        "traceback",
        "unknown tool",
    )
    return any(marker in text for marker in markers)


def evaluate_session(
    case: EvalCase,
    events: list[dict[str, Any]],
    *,
    variant: str,
) -> SessionMetrics:
    final_answer = _final_answer(events)
    answer_lower = final_answer.lower()

    calls = _tool_calls(events)
    call_names = [str(e.get("data", {}).get("name", "")) for e in calls]
    called_set = set(call_names)

    if case.required_tools:
        required_hits = sum(1 for name in case.required_tools if name in called_set)
        required_tool_recall = required_hits / len(case.required_tools)
    else:
        required_tool_recall = 1.0

    loaded_skills = _loaded_skills(events)
    if case.expected_skill is None:
        skill_match: bool | None = None
    else:
        skill_match = case.expected_skill in loaded_skills

    if case.required_evidence_terms:
        evidence_hits = sum(
            1 for term in case.required_evidence_terms if term.lower() in answer_lower
        )
        evidence_coverage = evidence_hits / len(case.required_evidence_terms)
    else:
        evidence_coverage = 1.0

    forbidden_claim_count = sum(
        1 for claim in case.forbidden_claims if claim.lower() in answer_lower
    )

    tool_error_count = 0
    for event in _tool_results(events):
        content = str(event.get("data", {}).get("content", ""))
        if _looks_like_tool_error(content):
            tool_error_count += 1

    completed = any(
        e.get("type") == "turn/end"
        and e.get("data", {}).get("status") == "completed"
        for e in events
    )
    step_count = sum(1 for e in events if e.get("type") == "model/context")
    total_context_chars, max_context_chars = _context_chars(events)

    passed_contract = (
        completed
        and bool(final_answer.strip())
        and required_tool_recall == 1.0
        and (skill_match is not False)
        and evidence_coverage == 1.0
        and forbidden_claim_count == 0
        and tool_error_count == 0
    )

    return SessionMetrics(
        case_id=case.case_id,
        variant=variant,
        completed=completed,
        step_count=step_count,
        tool_call_count=len(calls),
        tool_error_count=tool_error_count,
        required_tool_recall=required_tool_recall,
        loaded_skills=loaded_skills,
        skill_match=skill_match,
        evidence_coverage=evidence_coverage,
        forbidden_claim_count=forbidden_claim_count,
        final_answer_nonempty=bool(final_answer.strip()),
        total_context_chars=total_context_chars,
        max_context_chars=max_context_chars,
        passed_contract=passed_contract,
    )
