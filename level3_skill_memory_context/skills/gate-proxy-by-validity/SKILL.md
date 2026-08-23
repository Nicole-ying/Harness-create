---
name: gate-proxy-by-validity
description: Diagnose and repair reward designs where a dominant positive proxy remains collectible in invalid or failure states. Use when component statistics show one proxy dominates reward magnitude while task success remains poor, early failures remain high, or the proxy may reward behavior outside valid task states.
metadata:
  author: Harness-create
  version: "0.1-teaching"
---

# Gate Proxy by Validity

## Goal

Determine whether a useful proxy reward is misaligned because the agent can still collect it when the task state is invalid, unsafe, or already failing.

## Evidence checklist

Before proposing a change, inspect:

1. task-native evaluation score or success metric;
2. frequency of failure / early termination;
3. reward-component magnitude share and active rate;
4. whether the dominant positive proxy stays active in failure states;
5. checkpoint trend if available, to distinguish early learning from late exploitation.

Do not infer item 4 from component share alone. If failure-state evidence is unavailable, state that the diagnosis is provisional and request that evidence.

## Diagnostic test

A proxy-validity mismatch is supported when:

- the proxy contributes a large fraction of total reward;
- native task performance is still poor;
- failure states can still receive the proxy, or the proxy remains active after the state no longer represents valid progress.

## Intervention pattern

Preserve the useful proxy, but couple it to a validity condition rather than deleting it immediately.

Abstract pattern:

```text
useful_proxy * validity_weight
```

Prefer smooth validity weighting when a hard gate would create discontinuities or remove useful learning signal too early.

## Validation

After the intervention, check whether:

- early failures decrease;
- native score / success improves;
- the proxy still provides learning signal in valid states;
- no new reward loophole dominates.

## Rollback / contraindications

Do not use this Skill merely because one component has a high share. A dominant component can be legitimate. Roll back or revise the intervention if valid exploration collapses or the proxy becomes nearly inactive everywhere.
