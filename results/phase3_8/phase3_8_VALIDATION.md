# Phase 3.8 Validation Record

## A. Full Regression Suite

**119/119 passing** (106 pre-existing across Phase 2.6 → Phase 3.5, unchanged, + 13 new Phase 3.8 tests). One pre-existing test (`scripts/phase3_5_submission_tests.py`) had a hardcoded assertion checking that `main.py` builds `make_competitive_v2_agent` specifically — this went stale the moment `main.py` was promoted to build Submission C's agent instead, exactly as it would have gone stale when B replaced A. Fixed to be promotion-agnostic (checks that main.py builds *some* `make_competitive_vN_agent` constructor, without hardcoding which phase); a new, C-specific test (`test_main_py_builds_v3_agent`) was added to `scripts/phase3_8_regression_tests.py` to assert the *current* state precisely.

## B. Existing Scaling Benchmark (Phase 3.5-3.7's own archetypes)

B vs C run on `heavy_scaler`, `scaler_5`, `scaler_7`, `scaler_10` (development seeds 950001-950002 + held-out seeds 960001-960002): **0 regressions in 16 comparisons.** One case (`heavy_scaler`, seed 950001) showed C outperforming B: **B=$42,230 vs C=$43,006 (+$776)**, with the animal-response layer confirmed firing (`animal_response_activations=1`).

## C. Animal-Heavy Scenarios

Direct synthetic archetypes at 8+ animals could not be built without bankruptcy (same tooling ceiling documented in Phase 3.6/3.7 — every attempted configuration at 8-13 animals with viable hands/land staging still drained cash faster than production could sustain it). In place of a live synthetic test, the response logic was validated via **real-data replay** against the actual moushun chen trajectory (Submission B, episode 104768097): correctly escalates from B's baseline (4 total animals) to the moderate tier (5) at day 8 (opponent reaches 9 animals) and the high tier (6) at day 20 (opponent reaches 14 animals) — see `scripts/phase3_8_regression_tests.py::test_c_matches_moushun_chen_replay_escalation`.

## D. Existing Non-Scaling Archetypes

`passive`, `production_heavy`, `market_selling`, `expansion_oriented`, `animal_oriented`, `conservative`, `aggressive_investment` — **28 comparisons, 0 regressions, 0 unnecessary activations** (`animal_response_activations=0` in every case). C is byte-identical to B whenever its own trigger condition isn't met.

## E. Held-Out Seeds

Seeds 960001-960002 were not used to choose any threshold or design decision (thresholds were derived purely from Phase 3.7's real-data animal-count separation, before any of this session's testing) — included directly in the sweep above (Sections B/D), confirming the non-regression result generalizes beyond the development seeds.

## Summary Table

| Check | Result |
|---|---|
| Pre-existing regression tests | 106/106 (1 assertion updated for the new promotion, documented above) |
| New Phase 3.8 tests | 13/13 |
| Planner v1 control reproduction | 30/30 exact |
| Frozen file hashes | Unchanged |
| B vs C regressions (44 comparisons, 11 archetypes, dev+held-out seeds) | **0** |
| B vs C measured improvements | **1** (heavy_scaler seed 950001, +$776) |
| Unnecessary (false-positive) activations | **0** |
| Submission B still independently runnable | Confirmed |
