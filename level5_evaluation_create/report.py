"""Small Markdown report generator for Level 5 metrics."""

from __future__ import annotations

from pathlib import Path

from contracts import SessionMetrics
from benchmark import aggregate_by_variant


def render_markdown(results: list[SessionMetrics]) -> str:
    summary = aggregate_by_variant(results)
    lines = [
        "# Level 5 Evaluation Report",
        "",
        "This report separates Agent behavior metrics from real RL outcome metrics.",
        "Fixture results below are teaching traces, not CREATE paper results.",
        "",
        "## Variant summary",
        "",
        "| Variant | Cases | Contract pass | Tool recall | Skill match | Evidence coverage | Avg steps | Avg tool calls | Avg max context chars |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for variant, row in summary.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    variant,
                    str(int(row["cases"])),
                    f"{row['contract_pass_rate']:.2f}",
                    f"{row['required_tool_recall']:.2f}",
                    f"{row['skill_match_rate']:.2f}",
                    f"{row['evidence_coverage']:.2f}",
                    f"{row['avg_steps']:.2f}",
                    f"{row['avg_tool_calls']:.2f}",
                    f"{row['avg_max_context_chars']:.0f}",
                ]
            )
            + " |"
        )

    lines += ["", "## Per-session details", ""]
    for r in results:
        lines.append(
            f"- `{r.case_id}` / `{r.variant}`: pass={r.passed_contract}, "
            f"tools={r.required_tool_recall:.2f}, skill={r.skill_match}, "
            f"evidence={r.evidence_coverage:.2f}, steps={r.step_count}."
        )

    lines += [
        "",
        "## Important interpretation rule",
        "",
        "A high Agent contract score does **not** prove the reward edit improves PPO. "
        "The real CREATE outcome must be joined separately using run/lineage/round/reward-version identifiers.",
        "",
    ]
    return "\n".join(lines)


def write_report(results: list[SessionMetrics], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(results), encoding="utf-8")
