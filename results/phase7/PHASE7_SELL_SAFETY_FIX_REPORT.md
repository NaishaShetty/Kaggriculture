# PHASE 7 — Sell-Safety Wiring Fix: Final Report

## 1. Executive Summary

**[VERIFIED]** The bug Phase 6 diagnosed is real, reproduces under controlled conditions, and is fixed by exactly the one-line change the diagnosis predicted. `agents/phase2_6/common.py` (Planner v1) set `sell_policy["horizon_aware"] = True` on every non-passive sell policy, believing this activated a force-liquidate-near-season-end safety net (`agents/phase2_5/common.py`'s `_sell_quantity_horizon_aware`) — but it imported its tactical layer from `agents.phase2_4.common` directly, whose own `_sell_quantity` never reads that flag. The flag was set and read by nothing.

**The fix**: change one import in `agents/phase2_6/common.py` — `from agents.phase2_4.common import make_agent as make_agent_24` → `from agents.phase2_5.common import make_agent as make_agent_24`. `agents/phase2_5/common.py`'s `make_agent` has an identical signature (forwards `**kwargs` straight to `agents.phase2_4.common.make_agent`) and only adds the `horizon_aware` deadline check on top. No other file was touched.

**Validation, in order**:
- Reproduced the freeze on unpatched code in a controlled, isolated scenario: 0 SELL orders across 720 turns, 50 units of MELON permanently stranded, final money $50.
- Applied the fix and re-ran the identical scenario: 1 SELL order fires at day 29 (the terminal liquidation deadline for threshold-mode selling), liquidating all 40 held units; shed ends empty.
- Full regression suite: every behavioral test still passes. The only failures (5, one per suite that checks it) are the expected consequence of an intentionally, explicitly authorized change — a stale "Planner v1 is byte-for-byte unchanged" hash-pin, not a functional regression.
- 32-pair archetype sweep (8 archetypes × 4 seeds), before vs. after: **byte-identical in every one of the 21 pairs that ended with zero unsold shed inventory**; in all but one of the 11 pairs that had stranded inventory before the fix, the fix converts it to cash (never decreases final money) and empties the shed; the one exception is correctly-reserved animal feed stock, which the fix correctly still refuses to force-sell.
- Cold-process test: the packaged submission runs a full 720-turn episode standalone, isolated from the repo, exactly as Kaggle would load it.

**Promotion decision: PROMOTED.** Packaged as `kaggriculture_phase7_submission_D.tar.gz` (SHA-256 below).

## 2. What Changed

One file, one import line, in `agents/phase2_6/common.py`:

```diff
-from agents.phase2_4.common import make_agent as make_agent_24
+from agents.phase2_5.common import make_agent as make_agent_24
```

(A short explanatory comment was added alongside it, pointing to this report; no logic changed beyond the import target.)

Nothing else in `agents/phase2_6/` was touched. `agents/phase2_4/common.py`, `agents/phase2_5/common.py`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, and `main.py` are all byte-for-byte unchanged (`git status --short` confirms only `agents/phase2_6/common.py` is modified among tracked files).

## 3. What Remained Frozen

Per this phase's explicit, narrow exception: only `agents/phase2_6/common.py` was modified, and only its import line. Everything else — Planner v1's own decision logic (`state.py`, `opportunities.py`, `evaluator.py`, `constraints.py`, `decisions.py`, `trace.py`), the tactical execution layer (`agents/phase2_4/common.py`), the already-existing wrapper being newly wired in (`agents/phase2_5/common.py`), and every response/detection layer built on top (Variant D, the scaling response, the animal response) — is unchanged.

## 4. Reproduction and Fix Validation (Step 3)

**Design note, disclosed rather than hidden**: an initial reproduction attempt ran the *full* Submission C stack (Planner v1's adaptive loop + Variant D + scaling response + animal response) against a synthetic MELON-heavy opponent. It did produce 0 SELL orders — but for the *wrong* reason: the adaptive planner's own reaction to that specific opponent drove our hands to 0 and cash to $0 by day 7, matching the already-documented NEW-F-005 early-collapse pattern (Phase 3.7), not the "harvest succeeds, selling freezes" mechanism Phase 6 diagnosed. Per this phase's own instruction ("if step (a) does NOT reproduce the freeze... say so rather than force a positive result"), this was reported as a non-reproduction and abandoned in favor of a cleaner design (`scripts/phase7/reproduce_experiment1.py`): call `agents.phase2_6.common`'s own `make_agent_24` symbol directly — whichever module it currently resolves to, so the same script automatically exercises exactly the code path the fix changes — with a **fixed, realistic config** (`crops={"MELON":1.0}`, `n_hands=1`, threshold selling, `threshold_frac=1.0`, `horizon_aware=True`, `plant_delay_day=18` to keep production below the existing, unrelated `overflow_safety` valve's 85-unit trigger) against a synthetic MELON-heavy opponent, isolating the one mechanism this fix targets.

**(a) Unpatched code** [OBSERVED]:

| | Value |
|---|---|
| SELL orders across all 720 turns | **0** |
| Max shed inventory reached | 50 (day 29) |
| Final shed contents | 50 units MELON |
| Final money | $50 |
| MELON price, days 12→29 | crashes from $189 to $1-16, never again reaches base ($250) |

Matches the real Lai Eu Wen episode's signature (0 sells, substantial stranded shed inventory, price permanently below threshold) at a smaller, controlled scale.

**(b) Patched code, identical scenario, identical seed** [OBSERVED]:

| | Value |
|---|---|
| SELL orders across all 720 turns | **1** (day 29, hour 1) |
| Order | `["SELL", "MELON", 40]` |
| Final shed contents | **0** (fully liquidated) |
| Final money | $55 (money before the sale: $51; the sale realized $84 gross revenue at crashed, near-floor prices, partly offset by that day's ordinary hire cost) |

**(c) Conclusion**: the freeze reproduces on unpatched code and resolves after the fix, exactly at the mechanism Phase 6 diagnosed — the day-29 `terminal_liquidation_deadline` for threshold-mode selling. The realized recovery is modest in dollar terms in this deliberately small isolated scenario (because the market is already crashed by the time the forced sale fires, by design — a late safety net cannot undo an earlier price collapse, only prevent total loss of the held inventory) — the meaningful result is **0 units stranded instead of 50**, i.e., production that would have been entirely wasted is now converted to cash.

## 5. Regression Suite (Step 4)

All 8 project regression suites plus Phase 6's pipeline tests, run against the patched code:

| Suite | Result |
|---|---|
| `scripts/phase2_6_regression_tests.py` | 18/18 passed |
| `scripts/phase3_1_regression_tests.py` | 21/21 passed |
| `scripts/phase3_2_regression_tests.py` | 13/14 passed — 1 expected failure (see below) |
| `scripts/phase3_3_regression_tests.py` | 11/12 passed — 1 expected failure |
| `scripts/phase3_4_regression_tests.py` | 13/14 passed — 1 expected failure |
| `scripts/phase3_5_regression_tests.py` | 19/20 passed — 1 expected failure |
| `scripts/phase3_5_submission_tests.py` | 7/7 passed |
| `scripts/phase3_8_regression_tests.py` | 12/13 passed — 1 expected failure |
| `scripts/phase6/phase6_regression_tests.py` | 31/31 passed |

**[VERIFIED]** All 5 failures are the exact same check in every case: `"Planner v1 remains byte-for-byte unchanged"` / `"frozen Planner v1 remains byte-for-byte unchanged"` — a hash-pin against `results/phase3_1/control_reproduction/frozen_file_hashes.txt`, which records `agents/phase2_6/common.py`'s pre-Phase-7 hash. This is the **expected and correct** consequence of this phase's explicitly authorized change — every one of those 5 files' *other* checks (behavioral, structural, non-interference) still passes. No unrelated test failed. The frozen-hash record itself (`results/phase3_1/control_reproduction/frozen_file_hashes.txt`) was deliberately **not** updated in this phase, since it was out of the explicitly authorized scope ("the fix should be entirely contained in the one import"); refreshing that record is a one-line follow-up if the project wants these suites green again without an explanatory caveat, but was not done here to avoid silently expanding scope.

## 6. Archetype Sweep (Step 5)

`scripts/phase7/sweep_archetypes.py` ran Submission C's real adapter (`make_competitive_v3_agent`, entirely unmodified) against 8 existing archetypes (passive, production_heavy, market_selling, expansion_oriented, animal_oriented, conservative, aggressive_investment, heavy_scaler) × 4 development seeds = 32 pairs, once on unpatched code and once patched. Full results: `results/phase7/sweep_before.json`, `results/phase7/sweep_after.json`.

**[VERIFIED]**: In all 21 of 32 pairs where final shed inventory was already 0 before the fix, final money is **byte-identical** after the fix — no unexplained side effect anywhere.

**[VERIFIED]**: In 10 of the remaining 11 pairs (nonzero shed before the fix), the fix converts the stranded inventory to cash: shed goes to 0, final money strictly increases (never decreases). Example: `heavy_scaler_seed800001` — before: shed=78, money=$42,032; after: shed=0, money=$47,410 (+$5,378).

**[VERIFIED, correctly-explained exception]**: 1 of 11 pairs (`expansion_oriented_seed800000`) shows 1 unit of WHEAT still unsold and money unchanged after the fix. This is **not a gap in the fix** — `agents/phase2_4/common.py`'s own SELL block reserves `n_animals_alive` units of WHEAT as animal feed stock (`wheat_reserved`) *before* computing `sellable_held`, and the horizon_aware wrapper only ever sees the already-reserve-adjusted `held` quantity. The fix correctly declines to force-sell feed reserve needed by a still-living animal, exactly as the existing (unmodified) reserve logic intends.

**[VERIFIED, mechanistically expected, disclosed]**: 4 of 32 pairs show a small **opponent**-side final-money difference (production_heavy: -$3, -$3; heavy_scaler: -$132, -$48). This is not a bug in our own logic — the market's SELL processing interleaves both players' orders against the same shared, advancing inventory within a turn (verified in Phase 4/5's market-model work); our own newly-added day-29 SELL order adds supply to the shared market on that turn, which can shift the price the opponent's own simultaneous order receives. This is a small, real, correctly-understood side effect of adding legitimate sell activity to a shared market, not a defect.

## 7. Cold-Process / Packaging Validation

- `scripts/smoke_test.py`: passes (50-step sanity episode via `kaggle_environments.make`).
- `scripts/phase3_5_submission_tests.py`: 7/7 passed, including the exec()-based, no-`__file__`, cwd-outside-repo Kaggle-loader simulation.
- Packaged via `scripts/phase7_build_submission.py` (same pattern as `scripts/phase3_8_build_submission.py`, which built Submission C): `kaggriculture_phase7_submission_D.tar.gz`, 35 files, 84.6 KB.
- Cold-process 720-turn test: extracted the package into an isolated temp directory (outside the repo), loaded `main.py` via `exec()` with `__file__` deliberately unset (matching Kaggle's own loading mechanism), and ran a full 720-turn episode against a `"pass"` opponent from that isolated directory alone. Result: `DONE` status, final money $28,898 (vs. the static opponent's unchanged $3,000) — the package runs standalone, correctly, with no dependency on anything outside its own file list.

## 8. Regression / Promotion Decision

**PROMOTED.** All three of this phase's validation gates (mechanism reproduction + fix, full regression suite, archetype sweep) pass cleanly, with every side effect either strictly beneficial (stranded inventory converted to cash) or explicitly, correctly explained (the feed-reserve exception, the interleaved-market opponent-price effect). No unexplained regression was found anywhere.

## 9. SHA-256 / Package Manifest

```
kaggriculture_phase7_submission_D.tar.gz
SHA-256: 14db20c2e34fd2a18375445848ec229f8464dcae91f0be12fd965360e2d25e7c
Size: 86,631 bytes (84.6 KB), 35 files
```

Contents (35 files): `main.py`, `results/phase3_3/detector/artifact.json`, `vendor_kaggriculture/{kaggriculture.py,kaggriculture.json}`, `economic_model/model.py`, `agents/__init__.py`, `agents/phase2_{2,3,4,5}/common.py`, `agents/phase2_6/{__init__,common,state,opportunities,evaluator,constraints,decisions,trace}.py`, `agents/phase3/{__init__,opponent_observation,feature_extractor}.py`, `agents/phase3_3/{__init__,expansion_detector,interventions}.py` + `adapters/{__init__,intervention_agent}.py`, `agents/phase3_5/{__init__,opponent_scaling_detector,response_policy}.py` + `adapters/{__init__,competitive_v2_agent}.py`, `agents/phase3_8/{__init__,animal_response}.py` + `adapters/{__init__,competitive_v3_agent}.py`.

Identical to Submission C's file list (`scripts/phase3_8_build_submission.py`) plus exactly one added file (`agents/phase2_5/common.py`, the module the fix now routes through) and the one changed file (`agents/phase2_6/common.py`).

## 10. Changed / New Files

Modified (1 file, 1 import line + comment):
- `agents/phase2_6/common.py`

New (all additive):
- `scripts/phase7/reproduce_experiment1.py`
- `scripts/phase7/sweep_archetypes.py`
- `scripts/phase7_build_submission.py`
- `results/phase7/sweep_before.json`, `results/phase7/sweep_after.json`
- `results/phase7/PHASE7_SELL_SAFETY_FIX_REPORT.md` (this file)
- `kaggriculture_phase7_submission_D.tar.gz` (repo root)

## Git

```powershell
cd C:\Kaggriculture
git status
```

```powershell
git add agents\phase2_6\common.py scripts\phase7 scripts\phase7_build_submission.py results\phase7
```

```powershell
git status
git diff --cached agents\phase2_6\common.py
```

```powershell
git commit -m "Phase 7: fix dead horizon_aware sell-safety wiring in Planner v1 (agents/phase2_6/common.py now imports make_agent from agents.phase2_5.common instead of agents.phase2_4.common) -- restores the already-designed, already-tested F16 force-liquidation safety net that was set but never read; reproduced the exact freeze Phase 6 found, confirmed the fix resolves it, full regression suite and 32-pair archetype sweep both clean; packaged as Submission D"
```

```powershell
git status
```

```powershell
git push origin main
```

**Note on the packaged artifact**: `kaggriculture_phase7_submission_D.tar.gz` is a binary build output at the repo root. Per this project's standing policy, it is not staged automatically above — stage it explicitly (`git add kaggriculture_phase7_submission_D.tar.gz`) only if you want it tracked in git; otherwise it can be uploaded to Kaggle directly without committing it.
