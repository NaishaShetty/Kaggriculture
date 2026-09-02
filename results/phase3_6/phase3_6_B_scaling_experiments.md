# Phase 3.6-B: Adaptive Scaling-Response Experiments

**Hypothesis H1**: A magnitude-aware, threat-aware scaling response will reduce F-001 losses more effectively than Submission B's fixed response, without materially degrading performance against non-scaling opponents.

**Control (B0)**: Submission B's own, unmodified `agents.phase3_5.response_policy.competitive_scaling_response` (fixed target: n_hands=5, animals={COW:2,SHEEP:2}), called through directly, never edited.

**Challengers**: 5 new candidates in `agents/phase3_6/response_policy_v2.py` (new file, frozen Phase 3.5/3.3/2.6 code untouched):
- **B1 (absolute proportional)**: target = `proportion * opponent's absolute hands/animals count` (proportion=0.6), capped at 12.
- **B2 (relative gap)**: closes a fraction (0.7) of the GAP between our ~2-hand baseline and the opponent's current level.
- **B3 (growth-rate-aware)**: same base as B1, +0.3 proportion bonus if the opponent's count is still increasing over the last 5 days.
- **B4 (budget-constrained)**: same base as B1, explicitly capped so the proposed commitment never drops projected cash below a $500 reserve (uses `obs`, read-only, to check our own cash — the frozen Phase 3.5 adapter never exposed this; a new adapter, `agents/phase3_6/adapters/adaptive_agent.py`, was built to supply it).
- **B5 (hybrid)**: B3's growth-awareness, then B4's budget cap.

All candidates share the exact same, unmodified trigger condition (`agents.phase3_5.opponent_scaling_detector.check`) — Phase 3.5/3.6-A already established detection works; this experiment is only about response magnitude.

## Test Archetypes

`agents/phase3_6/opponent_classes_scaling_ladder.py` (new, additive): `scaler_5`, `scaler_7`, `scaler_10` (labor-intensity ladder, tuned for viability — see Stage C for the documented bankruptcy ceiling), plus Phase 3.5's existing `heavy_scaler`, reused unchanged.

## Results (development seeds, n=3 per cell; validation seeds re-check, n=4, for B0 vs B2)

| Candidate | scaler_5 | scaler_7 | scaler_10 | heavy_scaler |
|---|---|---|---|---|
| **B0 (fixed, control)** | **$46,121** | **$47,857** | **$44,171** | **$40,464** |
| B1 (absolute proportional) | $27,925 | $33,199 | $35,542 | $34,945 |
| B2 (relative gap) | $33,102 | $36,721 | $38,096 | $36,944 |
| B3 (growth-rate-aware) | $27,950 | $35,380 | $36,784 | $35,953 |
| B4 (budget-constrained) | $27,844 | $32,496 | $36,261 | $36,796 |
| B5 (hybrid) | $27,950 | $35,380 | $36,784 | $35,953 |

**B0 (the existing fixed response) has the highest mean final money against every single opponent tested, with no exception.** Re-checked on 4 independent validation seeds (not used for any design decision) for the strongest challenger, B2, against `scaler_10` and `heavy_scaler`: B0 means $41,484/$42,607 vs. B2's $37,705/$36,084 — the pattern holds outside development seeds.

Win rate is uninformative here: **100% for every candidate against every archetype** — none of these synthetic opponents (including `heavy_scaler`, per Phase 3.5's own documented finding) ever actually beat the plain Planner v1 control, so this experiment measures margin/efficiency, not loss prevention. See Stage C for why a stronger, loss-inducing synthetic opponent could not be built.

## Interpretation

**H1 is REJECTED for every design tested.** The proportional/adaptive candidates do not merely fail to beat B0 — they consistently *underperform* it, including in the one case (`scaler_10`, 10 hands) where B1's calculated target (0.6×10=6) exceeds B0's fixed target of 5. More resources committed did not translate into more money. Two plausible (not yet isolated) explanations:
1. **Configuration churn**: B1-B5 re-evaluate and re-apply their target far more often than B0 (18-27 activations vs. B0's 1, over ~27 in-game days) because the opponent's own hands count fluctuates with the documented daily reset mechanic. Even with a same-day-late-hour sampling fix (applied mid-experiment, see commit history in `response_policy_v2.py`), the target is recomputed once per day rather than set-and-forget. Repeated `config.clear()/update()` cycles may carry a real cost (e.g., re-triggering tactical-layer BUILD_COOP/PASTURE or HIRE sequencing) not present in B0's one-shot commitment.
2. **Diminishing/negative marginal labor value**: beyond a certain point, additional hands/animals may not be productively utilizable within the tile/land footprint Planner v1 otherwise commits to (1 land quadrant in every one of these tests, since land is a separate lever this phase did not touch) — i.e., more workers than there is farmable capacity to use them on.

Neither explanation was isolated further this phase (would require its own dedicated experiment); both are reported as **HYPOTHESIS**, not fact.

## Decision

**REJECT H1 as stated. B0 (Submission B's existing fixed response) is retained; none of B1-B5 are promoted.** This is a genuine, evidence-backed negative result, not a failure to find code — reported honestly per the phase's own instruction.
