# Phase 3.6-E: Integrated Adaptive Policy

## Decision: No Integration

Per the brief's own explicit instruction ("Only after 3.6-B through 3.6-D have results should you integrate the strongest validated components... Do NOT force a promotion"), this stage's job is to assemble whatever survived Stages B-D. **Nothing did:**

- **Stage B/C (H1)**: all 5 adaptive scaling-response candidates (B1-B5) underperformed the existing fixed response (B0) in every tested scenario, confirmed on both development and validation seeds. There is no "strongest validated component" from this axis to integrate — B0 (Submission B's existing, unmodified response) remains the best tested option.
- **Stage D (H2/F-003)**: a specific mechanism was identified and precisely evidenced (`opportunistic_market_exit_timing`), but explicitly **no countermeasure was designed or tested** this phase, per the brief's own instruction not to build a detector before the mechanism is sufficiently supported. There is nothing here to integrate yet either.

## What This Means Architecturally

The conceptual architecture the brief specifies —

```
OBSERVATION → OPPONENT STATE → THREAT ASSESSMENT → RESPONSE SELECTION → FROZEN PLANNER V1 → FROZEN VARIANT D → ACTION
```

— already exists and is exactly what Submission B (`agents/phase3_5/adapters/competitive_v2_agent.py`) implements for the scaling-response layer. Phase 3.6 did not find a validated reason to change it. The new Phase 3.6 code (`agents/phase3_6/`) is retained as a tested, documented, **negative-result research artifact** — modular, switchable (via `agents/phase3_6/adapters/adaptive_agent.py`'s `candidate_name` parameter), and fully traceable (per-activation JSON trace records with trigger/evidence/opponent-state/response-magnitude/cost fields) — available for Phase 3.7 to build on or reference, but not wired into `main.py` and not replacing any frozen component.

## Frozen Components — Confirmed Untouched

- Planner v1: byte-for-byte unchanged (re-verified, Stage F).
- Variant D (`agents/phase3_3/interventions.py`): unchanged.
- Phase 3.5 Competitive Agent V2 (`agents/phase3_5/adapters/competitive_v2_agent.py`, `response_policy.py`, `opponent_scaling_detector.py`): unchanged. Submission B's actual `main.py` behavior is identical to what shipped before Phase 3.6 began.
