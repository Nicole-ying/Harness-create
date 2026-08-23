"""Join Agent trajectory metadata with real/supplemented CREATE per-round outcomes."""

from __future__ import annotations

from typing import Any


JOIN_FIELDS = (
    "run_id",
    "environment",
    "lineage_index",
    "round",
    "reward_version",
)


def make_join_key(record: dict[str, Any]) -> tuple[str, ...]:
    missing = [field for field in JOIN_FIELDS if record.get(field) in {None, "", "TBD"}]
    if missing:
        raise ValueError(f"Cannot build provenance key; missing fields: {missing}")
    return tuple(str(record[field]) for field in JOIN_FIELDS)


def join_agent_and_outcomes(
    agent_records: list[dict[str, Any]],
    outcome_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    outcome_index = {make_join_key(row): row for row in outcome_records}
    joined: list[dict[str, Any]] = []

    for agent in agent_records:
        key = make_join_key(agent)
        outcome = outcome_index.get(key)
        joined.append(
            {
                "join_key": key,
                "agent": agent,
                "outcome": outcome,
                "has_verified_outcome": outcome is not None,
            }
        )

    return joined


def experience_gate(joined_record: dict[str, Any]) -> str:
    """Conservative gate before a trajectory can become long-term experience."""
    if not joined_record.get("has_verified_outcome"):
        return "incomplete"

    agent = joined_record["agent"]
    outcome = joined_record["outcome"] or {}

    if not agent.get("reward_code_validated", False):
        return "rejected_unvalidated_reward"

    fitness = outcome.get("search_fitness")
    if fitness in {None, "", "TBD"}:
        return "inconclusive_missing_fitness"

    return "eligible_for_experience_labeling"
