# Phase 3.8: Submission C Implementation

## What Changed From Submission B

**One new layer, one new file set, zero modifications to any existing file.**

- `agents/phase3_8/animal_response.py` (new): a bounded, piecewise animal-target override, triggered by the exact same, unmodified detector Submission B already uses (`agents.phase3_5.opponent_scaling_detector.check`). Thresholds derived directly from Phase 3.7's validated real-data finding: opponent animal count ≥8 → raise target from B's baseline (COW:2/SHEEP:2=4) to (COW:3/SHEEP:2=5); ≥12 → raise to (COW:3/SHEEP:3=6). Below 8, the response is a no-op — B's existing baseline passes through unchanged.
- `agents/phase3_8/adapters/competitive_v3_agent.py` (new): wraps Planner v1 + Variant D + Submission B's existing scaling response (all frozen, imported unchanged) with the new animal-response layer applied strictly afterward, touching only the `animals` config key.
- **The hands target is never touched anywhere in this implementation** — it is set exactly once, by Submission B's own frozen `agents.phase3_5.response_policy.competitive_scaling_response`, and passed through unmodified by every subsequent layer.

## The Moushun Chen Investigation (Required by the Brief)

Direct tile-grid inspection of the real replay (episode 104768097) explains why Submission B's response set an animal target of 4 but the opponent's real game only ever showed 2 actual animals on our farm: **with 1 land quadrant (the standard, expected state — Planner v1 essentially never buys land independently) and Planner v1's own ~20-22 tile MELON commitment, the single 25-tile quadrant was already full** (`PLANT:20, WEED:2, PASTURE:2, empty:1` in the inspected snapshot) — there was no free tile space to build more than the 2 PASTURE structures Planner v1 had already committed on day 0.

**This is not a code defect and not a new mechanic** — it is the already-documented finite-tile-space mechanic. **The fix applied**: Submission C's animal-target increases are kept deliberately small (+1 to +2 over B's baseline) to stay within the realistic 1-2 tile headroom actually observed, rather than requesting a large jump that would silently fail to materialize the same way Submission B's fixed target of 4 sometimes did. No land, crop, or tactical-layer logic was touched.

## Validation Performed

1. **Regression suite**: 106/106 pre-existing tests pass, unchanged. 11/11 new Phase 3.8 tests pass (`scripts/phase3_8_regression_tests.py`), covering piecewise threshold correctness, never-downgrade discipline, hands-isolation, inertness when the detector is inactive, byte-identical reproduction of B against non-scaling archetypes, and a real-data replay validation confirming the response correctly escalates against the actual moushun chen trajectory.
2. **Frozen-control integrity**: Planner v1 file hashes unchanged, re-verified after implementation.
3. **Sanity checks**: C is byte-identical to B against `conservative`, `passive`, and `expansion_oriented` (Variant D triggers, scaling response doesn't) — confirms the new layer adds zero footprint when its own trigger condition isn't met.
4. **Real-data replay validation**: the response logic was run directly against moushun chen's actual observed animal-count trajectory (not a live re-simulation — a Category B, replay-based counterfactual per this project's evidence-classification discipline) and correctly escalates from B's baseline (4) to the moderate tier (5) at day 8 and the high tier (6) at day 20, tracking the opponent's real, growing animal count.
5. **Non-regression sweep**: see `phase3_8_VALIDATION.md` for the full B-vs-C battery across all existing archetypes, development and held-out seeds.

## Known Limitation, Stated Honestly

Because of the tile-space constraint above, Submission C's *achieved* animal count is likely still capped below its *target* in most real games (the target rising to 5-6 does not guarantee the tactical layer can build enough new structures to reach it) — this candidate's practical benefit is therefore expected to be **modest, not transformative**, and could not be measured via a live win-rate/margin experiment because no synthetic archetype could be built (without going bankrupt) that reaches the 8+ animal threshold needed to trigger the escalation at all — the same tooling ceiling Phase 3.6 already documented for hands-scaling archetypes. The promotion decision below is made honestly on this basis: correctness and non-regression are demonstrated; a live measured improvement is not, and is not overclaimed as one.
