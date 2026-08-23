"""Adapter for a local clone of Nicole-ying/CREATE-Reward-Editing-Agent.

This module reads only files that currently exist in the supplement repository.
It never replaces TBD/NA with guessed values.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MISSING_MARKERS = {"", "TBD", "NA", "N/A", "None", "null"}


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return None if value in MISSING_MARKERS else value


def _read_csv(path: Path) -> list[dict[str, str | None]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [
            {key: _clean(value) for key, value in row.items()}
            for row in csv.DictReader(f)
        ]


@dataclass
class CREATERepositorySnapshot:
    root: Path
    bipedalwalker_results: list[dict[str, str | None]]
    lunarlander_aggregate_results: list[dict[str, str | None]]
    per_round_results: list[dict[str, str | None]]
    component_evidence_csvs: dict[str, list[dict[str, str | None]]]

    def missing_report(self) -> dict[str, Any]:
        per_round_missing = sum(
            1
            for row in self.per_round_results
            if any(value is None for value in row.values())
        )
        component_rows = sum(len(rows) for rows in self.component_evidence_csvs.values())
        return {
            "per_round_rows": len(self.per_round_results),
            "per_round_rows_with_missing": per_round_missing,
            "component_evidence_csv_files": len(self.component_evidence_csvs),
            "component_evidence_rows": component_rows,
        }


def load_create_repository(root: Path) -> CREATERepositorySnapshot:
    root = root.resolve()
    if not (root / "README.md").exists():
        raise FileNotFoundError(f"Not a CREATE repository root: {root}")

    results_dir = root / "03_full_results"
    evidence_dir = root / "07_component_evidence"

    component_tables: dict[str, list[dict[str, str | None]]] = {}
    if evidence_dir.exists():
        for path in sorted(evidence_dir.rglob("*.csv")):
            component_tables[str(path.relative_to(root))] = _read_csv(path)

    return CREATERepositorySnapshot(
        root=root,
        bipedalwalker_results=_read_csv(results_dir / "bipedalwalker_results.csv"),
        lunarlander_aggregate_results=_read_csv(
            results_dir / "lunarlander_aggregate_results.csv"
        ),
        per_round_results=_read_csv(results_dir / "per_round_results_schema.csv"),
        component_evidence_csvs=component_tables,
    )


def numeric(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def extract_bipedal_seed_outcomes(
    snapshot: CREATERepositorySnapshot,
) -> list[dict[str, Any]]:
    """Return only seed rows; aggregate mean/std rows are excluded."""
    outcomes: list[dict[str, Any]] = []
    for row in snapshot.bipedalwalker_results:
        seed = row.get("seed")
        if seed in {None, "mean", "std"}:
            continue
        outcomes.append(
            {
                "environment": "BipedalWalker-v3",
                "seed": int(seed),
                "initial_fitness": numeric(row.get("initial_fitness")),
                "first_version_ge_300": row.get("first_version_ge_300"),
                "best_fitness": numeric(row.get("best_fitness")),
                "test_fitness": numeric(row.get("test_fitness")),
                "source": "03_full_results/bipedalwalker_results.csv",
            }
        )
    return outcomes


def extract_lunarlander_ablation_outcomes(
    snapshot: CREATERepositorySnapshot,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in snapshot.lunarlander_aggregate_results:
        rows.append(
            {
                "environment": "LunarLander-v3",
                "condition": row.get("condition"),
                "budget": numeric(row.get("budget")),
                "best_fitness_mean": numeric(row.get("best_fitness_mean")),
                "best_fitness_std": numeric(row.get("best_fitness_std")),
                "solved": row.get("solved"),
                "source": "03_full_results/lunarlander_aggregate_results.csv",
            }
        )
    return rows
