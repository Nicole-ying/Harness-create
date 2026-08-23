---
name: calibrate-rare-risk-penalty
description: Diagnose reward designs with rare but very large penalties that destabilize learning or dominate return variance. Use when negative events are infrequent yet high magnitude, training is unstable, or the policy becomes excessively conservative because risk penalties are poorly calibrated.
metadata:
  author: Harness-create
  version: "0.1-teaching"
---

# Calibrate Rare Risk Penalties

## Goal

Keep an important risk signal while preventing rare high-magnitude penalties from overwhelming the rest of the learning objective.

## Evidence checklist

Inspect:

1. event frequency;
2. penalty magnitude when active;
3. contribution to return variance;
4. whether the policy avoids useful states too aggressively;
5. native task performance before and after the penalty becomes influential.

## Diagnostic test

A calibration problem is plausible when an event is rare, its individual penalty is very large, and learning becomes unstable or excessively conservative without corresponding improvement in the true task objective.

## Intervention pattern

Prefer bounded scaling, smoother risk shaping, or magnitude calibration before removing the safety signal.

## Validation

Check:

- native score / success;
- risk-event frequency;
- return variance;
- whether useful exploration remains possible.

## Rollback / contraindications

Do not weaken a penalty simply because it is large. If the risk event is safety-critical and the existing penalty is necessary for constraint satisfaction, preserve the constraint and investigate other optimization issues first.
