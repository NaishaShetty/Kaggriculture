# Phase 27: Per-Tile, Per-Crop Liquidation Timing

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`). `agents/phase15/` (Submission G) was not modified (confirmed via `git status --short` below — the changes present predate this phase). `agents/phase21/risk_posture.py` was left untouched, per this phase's constraint. No submission is created.

## Executive Summary

**[VERIFIED] Replacing the fixed global liquidation-day thresholds with per-crop, per-tile timing recovered the win Phase 26's fix broke, kept the win it created, and produced two additional flips — a real, substantial improvement.** On the full 15-seed set, win rate against Submission G rose from **6/15 (40.0%) to 9/15 (60.0%)**, and the mean margin narrowed from -$5,126.13 (-9.4%, Phase 24/25 baseline) / -$4,147.00 (-7.6%, Phase 26) to just **-$1,216.67 (-2.2%)**.

**[VERIFIED] Both of this phase's direct questions are answered yes**: seed 700003 (broken by Phase 26's fixed one-day delay) is recovered to a clear win (+$3,129, better than its original Phase 24/25 margin of +$190), and seed 700002 (created by Phase 26's fix) is kept as a win (+$1,666). Beyond just those two, two more seeds flipped from loss to win under the new logic: seed 702002 (Phase 26: -$944 → now +$1,507) and seed 702004 (Phase 26: -$4,544 → now +$15, effectively a coin-flip tie that landed as a win). One seed (702003) improved from a -$4,196/-$1,682 loss to a **-$71 near-tie** — still technically a loss but no longer meaningfully distinguishable from a win.

**Recommendation: this closes most of the remaining gap on liquidation timing specifically, and the mechanism is now validated as real and largely correct.** The gap that remains (6 losses, mostly moderate — one still resembling the original non-timing-related loss, 701002) looks like it needs a different mechanism, not further liquidation-timing refinement — see Section 5.

## 1. Per-Crop Cutoff-Day Arithmetic

Read directly from `vendor_kaggriculture/kaggriculture.py`'s `CROPS` dict and its `_apply_unit_action`/`_daily_refresh_plants` functions (not assumed):

**The governing constraint, confirmed by direct code read**: `_apply_unit_action`'s `HARVEST` branch (line ~453) blocks any harvest until `day - tile["planted_day"] >= crop_data["first_yield_day"]` — **and this check applies identically to BOTH ongoing and non-ongoing crops** (the `if crop_data["ongoing"]:` branch inside it only gates a warning print, not the `return` itself). This means, for ANY crop, a tile planted on `planted_day` needs `planted_day + first_yield_day <= 29` for even a single harvest to be possible before the season ends. **The last day it is worth planting a new seed of any crop is therefore `29 - first_yield_day`, uniformly.**

| Crop | `first_yield_day` | Cutoff day (`29 - first_yield_day`) |
|---|---|---|
| WHEAT | 2 | **27** |
| CARROT | 2 | **27** |
| TOMATO | 8 | **21** |
| MELON | 10 | **19** |
| STRAWBERRY | 10 | **19** |

(MELON's cutoff is moot in practice — `agents/phase21/portfolio.py`'s crop schedule already retires MELON entirely by day 8, the opening-only window Phase 21/24 already validated; TOMATO and CARROT are never used by this controller's crop schedule at all. The two cutoffs that actually matter for `agents/phase21/`'s day≥8 WHEAT/STRAWBERRY portfolio are **STRAWBERRY: 19** and **WHEAT: 27**.)

**For STANDING ongoing-crop tiles (STRAWBERRY/TOMATO only — non-ongoing crops auto-clear themselves on harvest, per `_apply_unit_action`'s own `farm["tiles"][fy][fx] = None` once `not crop_data["ongoing"]`)**: `_daily_refresh_plants` (line ~786-802) schedules each yield at `planted_day + first_yield_day + k*interval` for `k = 0 .. max_yield-1`. A given tile has real production left exactly when at least one of those `max_yield` scheduled days is still `> current_day` and `<= 29` — a per-tile computation depending on that specific tile's own `planted_day`, not a single day number for the whole farm.

## 2. Implementation

**New module: `agents/phase21/liquidation.py`** — `planting_cutoff_day(crop)` (the table above, one line of arithmetic) and `tile_has_future_yield(planted_day, crop, current_day)` (the per-tile scheduled-yield check, directly implementing the `_daily_refresh_plants` formula).

**`agents/phase21/execution.py`** (the task-scheduling loop):
- **PLANT gate**: `elif tt is None and seeds.get(c, 0) > 0 and day <= planting_cutoff_day(c):` — replaces the old blanket `is_liquidating(day)`-style suppression with a per-crop check, so WHEAT can keep being planted through day 27 while STRAWBERRY correctly stops at day 19.
- **DIG-ongoing gate**: `elif (... CROPS[c]["ongoing"] and not tile_has_future_yield(tt.get("planted_day", day), c, day)):` — replaces the old blanket `digging_ongoing` day-threshold flag with a per-tile check using that specific tile's own `planted_day`, so a tile with real production left keeps growing regardless of what day it is, and a tile that's truly done gets cleared as soon as it's actually done (not on some shared calendar date).
- **BUY_SEED** was also gated by `day <= planting_cutoff_day(crop)` (a small consistency fix — no point buying seed for a crop that can no longer be planted).

**`agents/phase21/portfolio.py`**: removed the old global `LIQUIDATION_START_DAY`/`DIG_ONGOING_CROPS_DAY` constants and the `crop_tile_target = 0` / `digging_ongoing = True` overrides they drove (now handled entirely inside `execution.py`'s per-crop/per-tile gates). One necessary mechanical addition: past STRAWBERRY's own cutoff (day 19), the crop-fraction schedule now returns `{"WHEAT": 1.0}` instead of continuing to nominally allocate 80% of new vacant-tile slots to STRAWBERRY (which the PLANT gate would just block anyway) — this redirects those slots to WHEAT, which can still use them through day 27. **This is a mechanical consequence of the per-crop cutoff fix, not a re-tuning of the Phase 22/24/25-validated 0.65/0.80 ratios themselves**, which still govern every day up to the cutoff unchanged, per this phase's explicit constraint.

## 3. Final-Day Sanity Check (Step 4)

**[VERIFIED]** The per-tile `tile_has_future_yield` check and the HARVEST branch's own priority (checked before DIG in the same task loop, unchanged from Phase 21's original priority order) together guarantee day 29's own maturing tiles are harvested and sold normally — a tile scheduled to yield exactly on day 29 satisfies `tile_has_future_yield(..., current_day=28) == True` (yield day 29 is `> 28` and `<= 29`), so it is NOT dug on day 28, and on day 29 itself `_needs_harvest_crop` fires first (tier 0, ahead of any DIG task) exactly as it always has. No change was needed here beyond what the per-tile logic already produces correctly.

## 4. Direct Trace Confirmation (the 6 Named Seeds)

Re-traced exactly the seeds Phase 26 examined, same technique (`agents/phase6/replay_forensics.py::extract_episode_timelines`, reused unchanged):

| Seed | Phase 24/25 (original) | Phase 26 (fixed +1 day) | **Phase 27 (per-tile)** |
|---|---|---|---|
| 700002 | -$3,277 (loss) | **+$290 (win)** | **+$1,666 (win, kept)** |
| 702003 | -$4,196 (loss) | -$1,682 (loss, narrowed) | **-$71 (loss, near-tie)** |
| 702002 | -$4,915 (loss) | -$944 (loss, narrowed) | **+$1,507 (win, flipped)** |
| 702004 | -$5,280 (loss) | -$4,544 (loss, ~unchanged) | **+$15 (win, flipped)** |
| 701002 | -$8,867 (loss) | -$8,860 (loss, unchanged) | **-$4,857 (loss, narrowed)** |
| 700003 | **+$190 (win)** | -$1,726 (loss, BROKEN by Phase 26) | **+$3,129 (win, recovered)** |

**Both of this phase's direct questions are answered by this table**: **seed 700003 recovered** (from Phase 26's -$1,726 loss back to a +$3,129 win, even better than its original +$190), **without losing seed 700002** (still a win, and by a wider margin: +$1,666 vs. Phase 26's +$290). Beyond those two named seeds, the per-tile approach improved further on every other seed in this set — 702002 and 702004 both flipped to wins, 702003 came within $71 of a win, and even 701002 (the one seed Phase 25 already flagged as dominated by a non-timing factor) narrowed meaningfully (-$8,867 → -$4,857).

## 5. Full 15-Seed Validation

Same methodology as every phase since 23 (`scripts/phase23/vs_submission_g.py`, unchanged).

### vs. Submission G

| Statistic | Phase 24/25 | Phase 26 | **Phase 27** |
|---|---|---|---|
| phase21 mean | $49,448.13 | $50,400.87 | **$53,406.00** |
| Submission G mean | $54,574.27 | $54,547.87 | $54,622.67 |
| Mean gap | -$5,126.13 (-9.4%) | -$4,147.00 (-7.6%) | **-$1,216.67 (-2.2%)** |
| **Win rate** | **6/15 (40.0%)** | **6/15 (40.0%)** | **9/15 (60.0%)** |

**Win rate crossed 50% for the first time** in this project's ongoing series of validations against Submission G. Full per-seed data: `results/phase23/phase23_vs_submission_g_results.json` (this phase's run).

### vs. Submission C (Secondary Check)

| Statistic | Phase 26 | **Phase 27** |
|---|---|---|
| phase21 mean | $60,706.67 | **$63,478.20** |
| Submission C mean | $32,230.87 | $32,331.27 |
| **Win rate** | **14/15 (93.3%)** | **14/15 (93.3%)** — same seed (702002 in this matchup) still the sole loss |

Mean margin against Submission C improved further; no regression.

## 6. Honest Assessment

**[VERIFIED] This closes meaningfully more of the gap than Phase 26's fixed-day version did.** Phase 26's fixed one-day delay was a genuinely correct diagnosis applied with the wrong tool (a single global day number can't adapt to each game's own harvest-cycle phase); this phase's per-crop/per-tile version is the natural fix for exactly that limitation, and the result confirms it: win rate 40.0% → 60.0%, mean gap -9.4% → -2.2%.

**[OBSERVED] The remaining 6 losses no longer look dominated by liquidation timing.** Seed 701002 (still the worst of the traced set at -$4,857, though improved from -$8,867) was already flagged by Phase 25 as losing under every crop ratio tested there, independent of the timing question — consistent with a different, still-unaddressed factor. The other losses (700000, 700001, 701001... — full list in `results/phase23/phase23_vs_submission_g_results.json`) were not individually re-traced this phase (out of scope — this phase's job was the liquidation mechanism specifically), so no new claim is made about what drives them.

**[HYPOTHESIS, not tested this phase]** With the two most recently-diagnosed mechanisms (Phase 24's crop economics, this phase's liquidation timing) both now fixed and validated, the character of whatever's left is unclear from this phase's own evidence alone — it could be more of the same category (a further scheduling/timing refinement not yet found), or it could genuinely need Reframe 2/3's ideas (win-probability posture, market-as-weapon) after all, now that the more mechanical gaps have been closed. A fresh diagnostic trace of the CURRENT remaining losses (not the ones this phase and Phase 26 already fixed) would be the natural next step, mirroring the same "diagnose before you build" discipline every phase since 24 has used.

## Changed Files

Modified (Phase 21's own, non-frozen agent — the standing exception for this phase):
- `agents/phase21/execution.py` (PLANT/DIG/BUY_SEED gates now use per-crop `planting_cutoff_day` and per-tile `tile_has_future_yield` instead of the blanket `is_liquidating`/`digging_ongoing` flags)
- `agents/phase21/portfolio.py` (removed `LIQUIDATION_START_DAY`/`DIG_ONGOING_CROPS_DAY` and their overrides; added a post-STRAWBERRY-cutoff crop-fraction redirect to WHEAT — a mechanical consequence of the fix, not a re-tuning of the validated ratios)

New, additive:
- `agents/phase21/liquidation.py`
- `results/phase27/PHASE27_PER_TILE_LIQUIDATION_REPORT.md` (this file)

`agents/phase21/risk_posture.py` was left completely untouched, per this phase's constraint. `results/phase23/phase23_vs_submission_g_results.json` was overwritten by re-running Phase 23's own unchanged validation script against this phase's updated code — the pre-Phase-27 numbers are preserved in this report's own tables. No frozen file was touched, `agents/phase15/` was not modified, and no submission is created.
