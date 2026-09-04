# Phase 34: Sundar Archetype Reconstruction (Inconclusive by Construction) and CARROT Rotation (Confirmed Negative)

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`). `agents/phase15/` (Submission G) and `agents/phase21/` (Submission H) are unmodified — confirmed via `git status --short`, which shows only `scripts/phase34/` and `results/phase34/` as new, untracked paths (the previously-downloaded raw replays were moved from `results/phase34_live_H/` and `results/phase34_gold/` into `results/phase34/raw_replays/`, not copied). No submission is created.

## Executive Summary

**Part A — the synthetic Sundar archetype could not be built into a viable stand-in, even after three rounds of principled adjustment, so the loss-reproduction question is genuinely UNTESTABLE by this method, not answered either way.** Every reconstruction attempt (a raw real-data rung table, then a smoothed version keeping animal-structure counts within serviceable hand capacity, then a version delaying animal purchases by 2 days) went to **$0 final money in ISOLATION** (vs. `"pass"`, no competitive pressure at all) — nowhere near the real Sundar's $97,246. Direct trace found a genuine, confirmed mechanism (`vendor_kaggriculture/kaggriculture.py::_daily_refresh_animals`: an animal escapes, destroying the capital spent on it, after 2 consecutive unfed days) that a too-aggressive target ramp triggers, but slowing the ramp did not fix the deeper problem: Sundar's real, confirmed opening (100% MELON, `first_yield_day=10` — no possible crop revenue before day 10) has no plausible revenue source before day 6 at the very earliest (SHEEP wool), yet the real Sundar's own bank grew steadily from day 0 ($5 → $307 by day 4) while every reconstruction attempt here died at exactly $0 and stayed there. **This is reported honestly as a failed reconstruction, not a confirmed vulnerability or non-vulnerability of Submission H** — Part A's steps 4-5 (diagnose mechanism, test a counter) were not pursued, since step 3's own prerequisite sanity check was never cleared.

**Part B — CARROT as a late-game market-rotation crop is confirmed as a real pattern in both gold-tier replays, but does NOT help in the realistic test that actually matches the scenario (25 days of real prior WHEAT/STRAWBERRY selling pressure against a real opponent, not a fresh market).** Mean final money dropped from $49,593 (baseline) to $47,588 (CARROT rotation) — **-4.0%** — and the win rate against Submission G on the same 4 seeds dropped from 2/4 to 1/4. Per this phase's own decision rule, this is a negative result, reported honestly; no further validation was pursued.

**No submission is created for either part. Submission H remains the current best, unchanged.**

---

## PART A: The Sundar Archetype

### 1. Confirmed Real Trajectory (Directly From the Raw Replay)

`scripts/phase34/extract_trajectories.py`, reusing `agents/phase6/replay_forensics.py::extract_episode_timelines` unchanged, on `results/phase34/raw_replays/105208327_worstloss.json` (full day-by-day dump: `results/phase34/phase34_trajectory_sundar_worstloss.json`):

| Day | Sundar hands | Sundar land | Sundar crops | Sundar animals | Sundar bank |
|---|---|---|---|---|---|
| 0 | 2 | 1 | MELON 8 | COW2/SHEEP2 | $5 |
| 9 | 3 | 2 | MELON 14 | COW1/SHEEP6 | $1,563 |
| 11 | 7 | 3 | STRAW1/MELON19 | COW1/SHEEP14 | $1,742 |
| 12 | 10 | 3 | STRAW1/MELON19 | GOOSE3/COW2/SHEEP19 | $1,894 |
| 15 | 10 | **4** (bought) | STRAW8/MELON19 | GOOSE5/COW2/SHEEP19 | $2,447 |
| 20 | — | 4 | STRAW7/MELON6 | GOOSE3/COW2/SHEEP19 | $35,162 |
| 29 | 5 | 4 | STRAW6 (no liquidation) | GOOSE3/COW2/SHEEP19 | **$97,246** |

**[VERIFIED, directly from the raw replay, not the prompt's summary]** All four claimed features are real: the 4th land quadrant (bought day 15), heavy SHEEP (19, sustained from day 13 onward), sustained MELON (19 tiles through day 18, still 6 on day 20 — not abandoned by day 10), and light GOOSE (3-5). **[VERIFIED, an additional detail the prompt didn't mention]** Sundar never fully liquidates — 6 STRAWBERRY tiles remain on day 29, unlike every other real trajectory this project has built an opponent from. `shettynaisha`'s (our) own real losing trajectory in the same episode is also confirmed: ends at $30,699, STRAWBERRY-heavy (up to 52 tiles) with light WHEAT/MELON — consistent with Submission H's own shipped design.

### 2. Reconstruction Attempts

`scripts/phase34/sundar_archetype.py`, built the same way Phase 21's `realistic_opponent.py` built its Larko-derived benchmark (day-indexed rung table fed through `agents/phase21/execution.py::make_execution_agent`, imported unmodified) — reused as a PATTERN, not copied code.

| Attempt | Change | Isolated result (seed 700000, vs. "pass") |
|---|---|---|
| 1 | Raw real-data rungs (hands 2→10 at day 12, SHEEP 2→19 at day 12) | **$0** |
| 2 | Smoothed ramp (finer intermediate rungs, animal-structure count kept ≤ hand count, matching Larko's own ratio) | **$0** |
| 3 | Attempt 2 + animal purchases delayed 2 days (more early cash cushion) | **$30** (still effectively bankrupt) |

**[VERIFIED, by direct trace] Attempt 1's collapse has a confirmed, real mechanism**: `vendor_kaggriculture/kaggriculture.py::_daily_refresh_animals` — "Animal escapes; structure remains" after 2 consecutive unfed days. The raw rungs scheduled far more PASTURE `BUILD`s than the (small, early-game) hand count could service, starving `FEED` and causing owned animals to escape — a genuine, confirmed capital-destruction cascade, not a false economy. **[VERIFIED] Slowing the ramp (Attempt 2) did not fix the underlying problem** — the collapse persisted even in the first 9 days, before the heavy SHEEP ramp had even begun, meaning animal escape was not the sole or even primary cause once the ramp was fixed.

**[OBSERVED] The deeper problem: Sundar's confirmed 100% MELON opening (`CROPS["MELON"]["first_yield_day"] = 10`, confirmed by direct read of `vendor_kaggriculture/kaggriculture.py`) has NO possible crop revenue before day 10, and no possible animal-product revenue before day 6 (SHEEP wool, the earliest of the three) — yet the REAL Sundar's own bank grew steadily and without a single day at exactly $0 from day 0 ($5) through day 9 ($1,563).** Every reconstruction attempt here, targeting the SAME real hand/animal/crop counts through this project's standard generic execution layer, instead hit exactly $0 within the first 8-9 days and could not recover (a hire-cost poverty trap: at $0, even the cheapest hire, $1, is unaffordable). **[INFERRED]** This strongly suggests the real Sundar's actual code has either a revenue source this project's agent design doesn't model (a plausible candidate: selling collected `FERTILIZER` as a passive, animal-driven income stream — the dormant reference implementation in `agents/phase2_3/common.py` defaults `fertilizer_sell_surplus=True`, a mechanism this project has built but never enabled in `agents/phase21/`) or a materially different cash-sequencing discipline (e.g., a reserve gate on animal/land purchases, not just on hiring) than a fixed day-indexed target table can express.

### 3. Steps 4-5: Not Pursued (Correctly, Per the Prerequisite Gate)

Per this phase's own Step 3 instruction ("confirm the synthetic agent is a reasonable stand-in — should reach final money in a plausible range relative to the real game"), no reconstruction attempt cleared this gate. **Running a head-to-head against a bankrupt synthetic opponent would not be informative** (any non-degenerate agent "beats" $0 trivially, telling us nothing about whether Submission H specifically struggles against Sundar's real archetype) — so Steps 4 (diagnose the loss mechanism) and 5 (test a counter) were not pursued. This is reported as an honest, incomplete result: **whether `agents/phase21/` actually loses to a synthetic Sundar archetype remains unanswered** — this reconstruction technique, successful for Larko's smoother, WHEAT-forward economy in Phase 21, does not transfer to Sundar's front-loaded, all-MELON, heavy-animal archetype.

---

## PART B: CARROT as a Late-Game Market-Rotation Crop

### 4. Confirmed Real Pattern (Directly From Both Gold-Tier Replays)

`scripts/phase34/extract_trajectories.py` on `results/phase34/raw_replays/105373474.json` and `105341441.json` (Crop Dusta, viewed as self via `extract_episode_timelines(..., our_name="Crop Dusta")`):

| Episode | CARROT surge start | Peak CARROT tiles | Peak day | Fully liquidated by |
|---|---|---|---|---|
| 105373474 (vs. Jesse Bullard) | day 21 (17 tiles) | **49** | day 25-26 | day 29 (2 tiles) |
| 105341441 (vs. Knight of Favonius) | day 26 (6 tiles) | **6** | day 26 | day 29 (0 tiles) |

**[VERIFIED] Both episodes confirm a real, late-game CARROT rotation**, though at very different scales (49 tiles vs. 6) — the prompt's "14-48 tiles starting ~day 25" summary is directionally right but the actual range is wider (6-49) and the start day varies (21 vs. 26).

**Market price check (Step 6, the part the prompt didn't cover in detail):**

| Episode | STRAWBERRY price, day 15 → day 21 | WHEAT price, day 15 → day 21 |
|---|---|---|
| 105373474 | $192 → **$1** (a real, severe crash) | $35 → $36 (flat) |
| 105341441 | $237 → $223 (essentially flat — NO crash) | $39 → $41 (flat) |

**[VERIFIED] Only ONE of the two episodes shows the expected STRAWBERRY price depression** — 105373474's crash is real and severe (a ~99% price collapse), directly coincident with its large CARROT rotation. **105341441 shows NO STRAWBERRY depression at all, yet still rotates a (much smaller) CARROT allocation.** **[INFERRED]** This means glut-driven price depression is not the sole trigger — endgame tile availability (STRAWBERRY's own planting cutoff, `agents/phase21/liquidation.py::planting_cutoff_day("STRAWBERRY") = 19`, freeing tiles regardless of price as those tiles' own remaining-yield window closes) plausibly matters independently, and CARROT's combination of a late cutoff (`planting_cutoff_day("CARROT") = 27`, COMPUTED directly, matching WHEAT's) and a higher base price ($35 vs. WHEAT's $25) makes it a strictly better "quick filler" for those naturally-vacating endgame tiles regardless of whether STRAWBERRY specifically crashed.

### 5. The Realistic Test

`scripts/phase34/carrot_rotation.py`: both conditions run `agents/phase21/portfolio.py::portfolio_targets` UNCHANGED for days 0-24 (identical real prior WHEAT/STRAWBERRY selling pressure against `agents/phase15/`'s Submission G, `make_macro_agent`, as shipped, on the same 4 development seeds) — condition (b) then redirects all newly-vacant tile allocation to 100% CARROT from day 25 through `planting_cutoff_day("CARROT")` (day 27, computed, not assumed); condition (a) is the unmodified baseline.

| Condition | Win rate vs. Submission G | Mean final money |
|---|---|---|
| (a) baseline (unmodified Submission H) | 2/4 | $49,593.00 |
| (b) CARROT rotation, day 25-27 | **1/4** | **$47,587.50** |

**[VERIFIED] CARROT rotation is a net negative in the realistic test — -4.0% mean money, and a worse win rate (1/4 vs. 2/4) on the same 4 seeds.** This directly contradicts what Phase 33's fresh-market test alone could have predicted either way (Phase 33 never tested this specific late-rotation scenario) — the realistic, 25-days-of-real-selling-pressure test this phase built is a materially different and more informative check, and it comes back negative.

### 6. Step 8: No Further Validation

Per this phase's own decision rule ("If rotation shows a real, positive effect ... implement it ... validate on the full 15-seed set"), the realistic test is decisively negative, not positive, so **no full 15-seed validation was run and no submission is created for this part.**

## Verdict

- **Sundar archetype**: reconstruction failed its own prerequisite isolation sanity check on every attempt (3 rounds) — the loss-reproduction question is **untestable by this method**, not confirmed or refuted. [VERIFIED for the reconstruction failure; INFERRED for the likely cause — a revenue mechanism this project's agent design doesn't currently model]
- **CARROT rotation**: the real pattern is confirmed in both gold-tier replays [VERIFIED], but the realistic 25-days-prior-selling test shows it is a net negative for `agents/phase21/` (-4.0% mean money, worse win rate vs. Submission G) [VERIFIED].
- **Neither is worth shipping.** No submission is created for either part.

## Changed Files

New, additive only:
- `scripts/phase34/extract_trajectories.py`
- `scripts/phase34/sundar_archetype.py`
- `scripts/phase34/sundar_headtohead.py`
- `scripts/phase34/carrot_rotation.py`
- `results/phase34/phase34_trajectory_sundar_worstloss.json`
- `results/phase34/phase34_trajectory_gold_105373474.json`
- `results/phase34/phase34_trajectory_gold_105341441.json`
- `results/phase34/phase34_sundar_headtohead_results.json`
- `results/phase34/phase34_carrot_rotation_results.json`
- `results/phase34/raw_replays/` (moved, not copied, from the pre-existing `results/phase34_live_H/` and `results/phase34_gold/`)
- `results/phase34/PHASE34_ARCHETYPE_AND_ROTATION_REPORT.md` (this file)

No frozen file, `agents/phase21/`, or `agents/phase15/` was touched. No submission is created — Submission H (Phase 29) remains the current best.
