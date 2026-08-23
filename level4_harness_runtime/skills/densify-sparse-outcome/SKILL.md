---
name: densify-sparse-outcome
description: Add or refine a causal precursor signal when the true task outcome is too sparse to support learning. Use only when sparse credit assignment is the diagnosed bottleneck and a valid precursor can be identified.
---

# Densify Sparse Outcome with a Causal Precursor

## Trigger
Use when the task-success signal is rare or delayed and training cannot reliably assign credit to earlier useful behavior.

## Evidence checklist
1. Confirm that the desired outcome is actually sparse or delayed.
2. Identify candidate precursors that occur earlier than the final outcome.
3. Check whether each precursor is causally related to success rather than merely correlated with an exploitable state.

## Diagnostic test
Ask whether the policy lacks learning signal before the final outcome, and whether a precursor can provide earlier credit without becoming a new shortcut objective.

## Abstract intervention
Introduce a bounded, interpretable precursor reward while retaining the true task outcome as the final objective.

## Validation
Check both learning speed and task-native success. Verify that the precursor does not dominate reward or create an occupancy exploit.

## Rollback / contraindication
Do not densify if no trustworthy precursor exists. A dense but misaligned signal can be worse than a sparse signal.
