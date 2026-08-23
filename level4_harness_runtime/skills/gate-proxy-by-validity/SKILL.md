---
name: gate-proxy-by-validity
description: Diagnose reward proxy leakage when a dominant positive proxy may remain rewarding in invalid, failure, or task-incomplete states. Use when component statistics show one proxy dominating reward while behavior still fails.
---

# Gate Proxy by Validity

## Trigger
Use this Skill when a positive proxy dominates reward magnitude but task performance remains poor, especially when failure states may still collect that proxy.

## Evidence checklist
1. Inspect component magnitude share and active rate.
2. Inspect failure or early-termination behavior.
3. Verify whether the proxy remains positive in invalid states. Do not infer this only from global magnitude share.
4. Compare checkpoint trends if available.

## Diagnostic test
Ask: **Can the agent obtain substantial proxy reward while violating the state conditions under which that proxy is supposed to represent progress?**

If the answer is not yet supported by evidence, request more evidence instead of declaring proxy leakage.

## Abstract intervention
Condition the proxy on a smooth validity signal or reduce its influence outside valid states. Preserve useful learning signal in genuinely valid states.

## Validation
After intervention, check whether invalid-state proxy collection and early failures decrease without destroying useful progress signal. Validate with actual training outcomes.

## Rollback / contraindication
Do not apply this Skill merely because one component is large. A dominant component can be legitimate if it remains causally aligned with task success.
