---
name: calibrate-rare-risk-penalty
description: Diagnose and calibrate rare high-magnitude safety or risk penalties that can destabilize reward scale or dominate learning. Use when a penalty is infrequent but its magnitude may distort optimization.
---

# Calibrate Rare Risk Penalty

## Trigger
Use when a safety/risk penalty fires rarely but has very large magnitude, or when training appears unstable around rare failure events.

## Evidence checklist
1. Measure activation frequency.
2. Measure conditional magnitude when active.
3. Compare its scale with positive reward components.
4. Inspect whether the policy overreacts, freezes, or ignores the penalty.

## Diagnostic test
Determine whether the problem is under-penalization, over-penalization, or simply insufficient evidence due to rarity.

## Abstract intervention
Adjust scale, clipping, smoothing, or frequency-aware treatment while preserving the semantic meaning of the risk event.

## Validation
Track both native task performance and risk-event frequency. A safer policy that completely stops making progress may still indicate miscalibration.

## Rollback / contraindication
Do not change a rare penalty solely because it is statistically rare. Some rare events legitimately deserve large consequences.
