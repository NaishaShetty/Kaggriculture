# Phase 19: Ladder Recalibration — Closes the Money Gap, Breaks the Win Rate

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py` — confirmed via `git status --short` below). Per this phase's standing exception, `agents/phase15/`'s own files were modified directly (macro_controller.py recalibrated, execution.py wired to a new endgame module, agents/phase15/endgame.py added). **The already-shipped `kaggriculture_phase18_submission_F.tar.gz` package is completely unaffected by this phase** — it is a frozen artifact built at a point in time; this phase's changes live only in the repo's `agents/phase15/` going forward, as an unshipped iteration.

## Executive Summary

**[OBSERVED] Recalibrating to fresh top-ladder data dramatically closes the isolated-money gap — but at a serious, disqualifying cost to head-to-head win rate.** On the same 15-seed wide sample Phase 17 used:

- **Isolated final money: mean $57,659.47** (median $57,797, range $46,697-$67,435, **13 of 15 seeds clear $50,000**) — up from Phase 17's $43,734.93, and **clearing the $50,000-80,000+ bar for the first time in this agent's history.**
- **Head-to-head win rate against Submission C and Submission E: 8/15 (53.3%)** — down from Phase 17's **15/15 (100%)**. Mean margin is still positive (ours $28,937.20 vs. theirs $22,853.87, +26.6%), but variance exploded (std. dev. $19,514 vs. Phase 17's $4,301) and several individual seeds show severe losses (as low as $5,298 and $6,080 for our side against Submission C/E's $19,000-26,000 range).

**Root cause of the win-rate regression, confirmed by direct trace (Section 5), not assumed**: the recalibrated agent's larger, more concentrated commitment (3 land / 11 hands / 62 crop tiles, no cash-safety mechanism of any kind) is economically excellent in isolation but measurably more fragile to a live competing opponent's market activity — several head-to-head seeds show the SAME chronic, repeated cash-to-zero pattern documented elsewhere in this project as the F-005 death-spiral class, recurring 3-4 separate times across a single 30-day game, something isolation testing (vs. "pass") structurally cannot expose.

**Decision: DO NOT replace Submission F's shipped package.** Per this phase's explicit constraint, a new package requires head-to-head win rate to be "maintained or improved" — it clearly was not (100% → 53.3%), and that metric is specifically what justified F's promotion in the first place (docs/LEADERBOARD_DIAGNOSTIC.md §1). The already-shipped `kaggriculture_phase18_submission_F.tar.gz` remains the deployed Submission F, completely unaffected by this phase. This phase's recalibrated code stays in the repo as a documented, evaluated iteration — not reverted, per this project's standing practice of keeping a phase's work visible even when its promotion doesn't go through — but is explicitly NOT what Kaggle is currently running.

## 1. Why the Old Targets Were Outdated

Phase 15's macro-controller was calibrated against Phase 6's local sample (4 opponents, max final money $104,569, land capping at 4 quadrants, assumed STRAWBERRY-dominant portfolios). Fresh replay data pulled directly from Kaggle's live API for 4 current top-ladder episodes (`results/phase19/fresh_ladder/*.json`) shows a materially different picture.

## 2. Fresh-Data Findings

Extracted via `scripts/phase19/extract_fresh_ladder.py`, reusing `agents/phase6/replay_forensics.py::extract_episode_timelines` unchanged (run once per team name per episode, so BOTH sides of each match are captured). 4 episodes, 2 distinct strong players (Dmitry Larko, appearing in all 4 as either side; Milan Leonard, in 1), plus 3 weaker opponents Larko faced (Knight of Favonius, Saravanan Jaichandaran, Atakan Aldemir — all show low hands/land/animals and modest final money, useful as a contrast, not part of the recalibration target).

| | Larko (×4, avg) | Milan Leonard | Old target (Phase 15) |
|---|---|---|---|
| Land quadrants (final) | 3 | 3 | 4 |
| Hands (settle ~day 10+) | 11 (range 11-12) | 10-11 | 13 |
| Crop footprint (day 15-20) | 58-61 tiles | 62-63 tiles | ~50 tiles |
| Crop mix (day 15-20) | WHEAT 23-25 / STRAW 33-38 (~40/60) | same | STRAWBERRY-dominant (~70-80%) |
| Crop mix (day 25) | WHEAT 39 / CARROT 4-6 / STRAW 13-18 (WHEAT now dominant, ~65%) | same | still assumed STRAWBERRY-dominant |
| Animals (steady, day 15+) | 14-17 (varied COW/SHEEP split: 9/8, 9/5, 5/10) | 12 (6/6) | fixed 13 |
| Endgame (day 29) | 0 crop tiles (full liquidation) | 0 crop tiles (full liquidation) | not modeled at all |
| Final money | $166,062-$183,147 | $116,536 | $50-80k target F was judged against |

**[VERIFIED] All 4 episodes, both strong players, agree closely on every axis** — this is a corroborated pattern, not a single-episode artifact. **[OBSERVED] The day-0-through-10 opening is also consistent across all 5 trajectories**: MELON-heavy start (day 0: ~35% WHEAT / 65% MELON of ~18-19 tiles — the OPPOSITE of Phase 15's assumed WHEAT-heavy start), STRAWBERRY introduced ~day 5, MELON fully dropped by day 10, land 1→2→3 and hands ~5→11 by day 10 (a single large jump, not a gradual ramp).

**[INFERRED] Why WHEAT overtakes STRAWBERRY by day 25**: most likely a time-horizon effect, not a profitability reversal. WHEAT's `first_yield_day=2` lets it keep cycling productively right up to the season's end; a STRAWBERRY freshly planted this late (`first_yield_day=10`) would not mature before day 29. This is stated as an inference, not confirmed by reading the real players' own decision logic (inaccessible — only public board state was read, per this project's standing observability discipline).

**Optional strengthening (Step 1, not required)**: not pursued further this phase — 2 independent strong players across 4 corroborating episodes (all landing on nearly identical numbers) was judged sufficient corroboration for the scale of recalibration undertaken, consistent with the brief's framing of this as optional.

## 3. What Was Recalibrated

`agents/phase15/macro_controller.py`, direct edits (old Phase 15 docstring/constants kept as historical record, marked superseded):

| Parameter | Old (Phase 15) | New (Phase 19) |
|---|---|---|
| `TARGET_LAND_QUADRANTS` | 4 | **3** |
| `TARGET_HANDS` | 13 | **11** |
| Animal target | fixed 13 | **range: `ANIMALS_BASE_TARGET=14` (ramp default) / `TARGET_ANIMALS_TOTAL=17` (opponent-ratchet ceiling)** |
| `CROP_TILE_TARGET_CEILING` | 50 | **62** |
| Crop-tile ramp rungs | reach ceiling by day 24 | reach ceiling by day 15 (matches fresh data's day-15 jump to 58-63 tiles) |
| Crop fraction schedule | WHEAT-heavy start → STRAWBERRY-dominant by day 20, stays that way | **MELON-heavy start (65%) → STRAWBERRY dominant day 10-24 (~60%) → WHEAT-dominant from day 25 (~65%)** |
| Land/hands ramp timing | reach targets by day 18 | **reach targets by day 10-15** (matches the fresh data's faster real convergence) |

**[OBSERVED, honestly disclosed, not glossed over] The day-25 WHEAT-dominant fraction target does NOT fully materialize in practice.** `bounded_multi_crop_tile_pool_assignment`'s STICKY-assignment rule (a Phase 15 fix, kept unchanged this phase — it is what stopped the original catastrophic decay-and-replant bug) means an already-growing STRAWBERRY tile keeps its assignment until it is harvested and the tile naturally clears. Since STRAWBERRY is "ongoing," it never naturally clears on its own — so there are very few vacant tiles for the day-25 schedule shift to actually reassign to WHEAT. In practice (confirmed by a full day-by-day trace, Section 6), the agent stays STRAWBERRY-heavy through day 27, not WHEAT-dominant as the fresh data shows. This is a real, disclosed limitation of this phase's implementation, not a silent gap — building an active STRAWBERRY→WHEAT rotation mechanic (explicitly DIG-ing mature STRAWBERRY tiles before day 25 to free them for WHEAT replanting) would be needed to fully match the observed pattern, and was judged out of this phase's scope given the endgame-liquidation mechanic (Section 4) already recovers the season-end shape that matters most (0 tiles by day 29) regardless of which crop was standing beforehand.

## 4. The Endgame-Liquidation Mechanic

New module: `agents/phase15/endgame.py`. Neither Phase 15 nor 16 modeled a season-end wind-down at all — both let the crop-fraction schedule keep planting right up to day 29.

**[INFERRED, sampling limitation disclosed] The exact wind-down start day is not directly observable**: the source replays are only sampled at days {0, 5, 10, 15, 20, 25, 29} — day 25 is still full (58-62 tiles), day 29 is empty (0-2 tiles), but nothing in between was captured. `LIQUIDATION_START_DAY = 26` (stop planting) and `DIG_ONGOING_CROPS_DAY = 28` (explicitly clear any still-standing "ongoing" crop, since STRAWBERRY never auto-clears — confirmed directly from `vendor_kaggriculture/kaggriculture.py`'s own `DIG` and `HARVEST` action-handling code) are reasonable estimates inside that window, tagged as inferred rather than read off a day-26/27/28 snapshot that doesn't exist in the sampled data.

**Mechanism**: from day 26, `BUY_SEED` and new `PLANT` tasks are suppressed entirely (existing non-ongoing crops like WHEAT/MELON still finish their current cycle and auto-clear per the engine's own logic). From day 28, any tile still holding a live "ongoing" crop (checked via `CROPS[crop]["ongoing"]`, not hardcoded to STRAWBERRY specifically) is explicitly DIG'd. Animals, hands, and land are untouched — the fresh data shows animal counts held steady through day 29 in both real games, so only the crop side winds down.

**[VERIFIED, by direct trace] The mechanic works as intended**: a representative isolated run (seed 700000) shows crop tiles at 58 (day 27) → 1 (day 28) → 0 (day 29) — a clean, complete wind-down matching the observed real-data shape closely.

## 5. Diagnostic: Does the Larger 62-Tile Footprint Reintroduce a Scheduling Problem?

Reused `scripts/phase16/diagnose.py`'s exact methodology (tile idle fraction, per-crop breakdown, animal fed fraction, action-efficiency) on the recalibrated agent, same 4 development seeds:

| Day range | Overall tile idle fraction | Animal fed fraction |
|---|---|---|
| Early ramp (day 5-10) | 10.9% | 51.3% |
| Mid-game (day 15-20) | 2.0% | 89.4% |
| Late-game (day 25-29) | 9.2% (all STRAWBERRY -- the endgame DIG window) | 58.5% |
| Overall action idle fraction | **15.1%** (vs. Phase 16's 20.8-23.2%) | — |

**[OBSERVED] No new scheduling problem at the larger scale — if anything, overall action efficiency IMPROVED** (84.9% productive action rate vs. Phase 16's ~77-79%), plausibly because the smaller land footprint (3 quadrants, not 4) means less travel distance per worker even though the crop-tile count is higher. The late-game idle-fraction bump is expected and intentional — it reflects the endgame mechanic actively clearing tiles, not neglect. **[OBSERVED, disclosed] Animal fed fraction dipped somewhat in the early-ramp and late-game windows** (51-59%, vs. Phase 16's 75-90% in comparable windows) — plausibly because workers are pulled toward the now-larger crop footprint and, in the late game, toward DIG-clearing tasks, at some cost to animal feeding. This did not prevent the large isolated-money improvement (Section 6), so it was not pursued further this phase.

## 6. Wide-Sample Validation (15 Seeds, Phase 17's Own Methodology)

Reused `scripts/phase17/wide_validate.py` unchanged, same `scripts/phase3_2_configs.py::SEED_SETS` (development + validation + held-out, n=15).

### Isolated final money

| Statistic | Phase 17 (old targets) | Phase 19 (recalibrated) |
|---|---|---|
| Mean | $43,734.93 | **$57,659.47** |
| Median | $44,375.00 | $57,797.00 |
| Min | $31,861.00 | $46,697.00 |
| Max | $53,541.00 | $67,435.00 |
| Std. dev. | $5,904.45 | $6,401.64 |
| Seeds clearing $50,000 | 2/15 | **13/15** |

**Bar cleared? YES — mean $57,659.47 is clearly inside the $50,000-80,000+ range**, not a marginal or rounded-up result. [OBSERVED]

### Head-to-head vs. Submission C (byte-identical to vs. Submission E in every seed, same as every prior phase — the F-005 guard never fires differently)

| Statistic | Phase 17 (old targets) | Phase 19 (recalibrated) |
|---|---|---|
| Ours: mean | $38,079.80 | $28,937.20 |
| Ours: median | $38,673.00 | $27,332.00 |
| Ours: min | $29,200.00 | **$5,298.00** |
| Ours: max | $44,099.00 | $59,497.00 |
| Ours: std. dev. | $4,301.32 | **$19,514.49** |
| Theirs: mean | $21,271.47 | $22,853.87 |
| **Win rate** | **15/15 (100%)** | **8/15 (53.3%)** |

**Win rate regressed sharply, and this is reported as the serious finding it is, not softened.** Mean margin is still nominally positive, but a coin-flip win rate against opponents this project itself calls "safe bug-fix submissions with ~0 measured economic improvement" is not the profile that justified promoting Submission F in the first place.

## 7. Diagnosing the Win-Rate Regression (Not Assumed — Traced Directly)

A representative losing head-to-head seed (702005, vs. Submission C: ours $6,080, theirs $24,624) was traced day-by-day. **[VERIFIED, by direct replay trace]**: cash repeatedly collapses to exactly $0 across THREE separate stretches of the same 30-day game (days 8-10, days 15-20, days 17-25 with brief partial recoveries in between), each accompanied by hands dropping to 0 and animals dying off, then a slow, partial recovery, before crashing again. This is the same chronic cash-crisis mechanism this project has documented before as the "F-005 death spiral" class (Phase 3.7/12) — except recurring multiple times in a single game here, not once.

**[INFERRED] Why this doesn't show up in isolation**: against `"pass"` (Section 6's isolated figures), there is no competing seller pushing WHEAT/STRAWBERRY prices down, so the same aggressive, no-safety-net commitment (11 hands, 62 tiles, zero cash reserve discipline) reliably converts into high final money. Against a REAL competing opponent who is also producing and selling into the same market, price competition appears to intermittently starve this agent's cash flow much more severely — a risk that isolated-vs-"pass" testing structurally cannot expose, and precisely the kind of gap Phase 17's own "small-sample luck" lesson warned this project to take seriously (there, the risk was seed-sampling; here it is testing-methodology blind spot). **This agent has no cash-safety mechanism analogous to Submission C/E's F-005 liquidity guard** — Phase 15-18 never built one, and this phase's larger, more concentrated recalibration makes that gap materially more costly.

## 8. Decision

**DO NOT promote a new package. Submission F's shipped `kaggriculture_phase18_submission_F.tar.gz` is unaffected and remains exactly as built in Phase 18.**

Per this phase's explicit constraint, a new package is warranted only if the wide sample shows a clear improvement AND head-to-head win rate is maintained or improved. The isolated-money side clearly qualifies (43,735 → 57,659, clearing the bar for the first time); the head-to-head side clearly does not (100% → 53.3%, a serious regression in the exact metric that justified F's original promotion). Per the brief's own standard, this is reported honestly rather than promoted on the strength of the money number alone.

**This phase's recalibrated code remains in the repo** (`agents/phase15/macro_controller.py`, `agents/phase15/execution.py`, new `agents/phase15/endgame.py`) as a documented, fully-evaluated iteration, per this project's standing practice of keeping a phase's work visible even when promotion doesn't follow (e.g. Phase 16 kept its fixes without a new package at that time). **It is explicitly NOT what is currently deployed as Submission F on Kaggle** — that remains the Phase 18 package, byte-for-byte.

**Recommended next step (not undertaken this phase)**: before reconsidering promotion, a follow-up phase should add a cash-safety mechanism to `agents/phase15/` (an F-005-style liquidity guard, adapted to this agent's larger scale) specifically targeted at closing the head-to-head fragility Section 7 diagnosed, then re-run this same wide-sample, both-isolated-and-head-to-head validation before any new package is built. Simply reverting to Phase 17's smaller targets would recover the win rate but throw away this phase's genuine, large isolated-money gain — the more promising path is fixing the specific fragility, not abandoning the recalibration.

## Changed Files

Modified (Phase 15's own, non-frozen agent — the standing exception for this phase):
- `agents/phase15/macro_controller.py` (recalibrated targets, ramps, crop schedule; old Phase 15 constants/docstring kept as marked historical record)
- `agents/phase15/execution.py` (wired to the new endgame module: PLANT/BUY_SEED suppressed and ongoing crops DIG'd once liquidating)

New, additive:
- `agents/phase15/endgame.py`
- `scripts/phase19/extract_fresh_ladder.py`
- `results/phase19/fresh_ladder/*.json` (the 4 raw replay files, moved from the loose `results/phase19_fresh_ladder/` staging location into this phase's own results structure)
- `results/phase19/fresh_ladder_extracted/*.json` (per-episode, per-player extracted timelines)
- `results/phase19/phase19_wide_validation_results.json` (this phase's own 15-seed validation run, using `scripts/phase17/wide_validate.py` unchanged)
- `results/phase19/PHASE19_LADDER_RECALIBRATION_REPORT.md` (this file)

No frozen file was touched. `main.py` still builds Submission C/E. `kaggriculture_phase18_submission_F.tar.gz` (Submission F, already shipped) is completely unaffected by this phase's repo changes. No new `.tar.gz` is created or staged this phase.
