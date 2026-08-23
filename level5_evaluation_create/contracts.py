"""Evaluation contracts for Level 5.

The evaluator is intentionally deterministic first.  An EvalCase defines what
must be observable in a session trace instead of asking another LLM whether the
answer merely 'looks good'.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    case_id: str
    user_request: str
    required_tools: list[str] = Field(default_factory=list)
    expected_skill: str | None = None
    required_evidence_terms: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)
    notes: str = ""


class SessionMetrics(BaseModel):
    case_id: str
    variant: str
    completed: bool
    step_count: int
    tool_call_count: int
    tool_error_count: int
    required_tool_recall: float
    loaded_skills: list[str]
    skill_match: bool | None
    evidence_coverage: float
    forbidden_claim_count: int
    final_answer_nonempty: bool
    total_context_chars: int
    max_context_chars: int
    passed_contract: bool


def load_cases(path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cases.append(EvalCase.model_validate(json.loads(line)))
    return cases


def find_case(cases: list[EvalCase], case_id: str) -> EvalCase:
    for case in cases:
        if case.case_id == case_id:
            return case
    raise KeyError(f"Unknown case_id={case_id!r}")
