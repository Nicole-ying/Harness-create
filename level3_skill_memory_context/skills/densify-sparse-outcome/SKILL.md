---
name: densify-sparse-outcome
description: Diagnose reward designs where the task objective is too sparse or delayed for learning. Use when success information arrives rarely or only at episode end, learning makes little progress, and a causal precursor can provide denser feedback without replacing the true task objective.
metadata:
  author: Harness-create
  version: "0.1-teaching"
---

# Densify Sparse Outcome with a Causal Precursor

## Goal

Provide denser learning signal when the true outcome is valid but too sparse or delayed to guide early policy improvement.

## Evidence checklist

Inspect:

1. how often the native success/outcome signal occurs;
2. whether training is flat because successful trajectories are rarely observed;
3. candidate precursor signals that causally precede the desired outcome;
4. whether the precursor can be optimized without actually improving the native task.

## Diagnostic test

This pattern is appropriate when the native objective is trustworthy but too sparse, and a precursor is both measurable and meaningfully related to progress toward that objective.

## Intervention pattern

Keep the native task objective. Add a bounded or weighted causal precursor as shaping signal rather than replacing the objective.

## Validation

Check both:

- whether learning starts earlier / more consistently;
- whether improvement transfers to the native task metric instead of only increasing the precursor.

## Rollback / contraindications

Do not densify using a convenient correlation that can be exploited independently of task success. If precursor reward increases while native success does not, treat that as a new proxy-misalignment problem.
