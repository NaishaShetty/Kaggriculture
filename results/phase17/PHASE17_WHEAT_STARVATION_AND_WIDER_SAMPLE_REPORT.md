# Phase 17: WHEAT-Starvation Check and Wider-Sample Promotion Decision

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py` — confirmed via `git status --short` below). No code in `agents/phase15/` was modified this phase (Section 1-2 explain why). No submission is created.

## Executive Summary

**[OBSERVED] The $50,000-80,000+ bar is clearly NOT cleared, and the true gap is larger than Phase 16's headline number suggested.** On a widened, 15-seed sample (this project's existing development + validation + held-out buckets, `scripts/phase3_2_configs.py::SEED_SETS` — not invented new seeds), mean isolated final money is **$43,734.93** (median $44,375, range $31,861-$53,541, only **2 of 15 seeds** clear $50,000). This is **$5,938.82 lower** than Phase 16's published 4-seed mean of $49,673.75 — the "$326.25 short, almost there" framing from Phase 16 turns out to have been an artifact of a favorable small sample, not a slight underestimate of a true mean that was actually higher. Reported plainly, not softened: **the earlier 4 development seeds happened to be an above-average draw**, and the wider sample reveals the real shortfall to the bar is closer to Phase 15's original scale than Phase 16's.

**[OBSERVED] The WHEAT cross-crop-starvation issue Phase 16 flagged (16.3% mid-game tile idle fraction) is no longer present in the current code — no fix was needed or built.** Re-running Phase 16's exact diagnostic on the agent as Phase 16 left it (wheat-reserve fix applied, sell-timing disabled) shows WHEAT's mid-game (day 15-20) tile idle fraction at **0.0%**, down from the 16.3% Phase 16 measured on the pre-fix agent. This phase's own distance-based trace (Section 1) independently corroborates there is nothing left to fix: WHEAT's surviving mid-game footprint is now only 0-2 tiles per seed (down from 5-11 in Phase 16's measurement), and every one of those tiles was fully serviced (idle fraction 0.0 in all 4 seeds checked, all 6 days of the window). Per this phase's own explicit instruction, this is reported as a genuine negative result and the phase pivoted straight to the wider-sample question instead of forcing a fix onto a problem that had already resolved itself as a side effect of Phase 16's other changes.

**Promotion decision: DO NOT PROMOTE.** Mean isolated final money ($43,734.93) is far short of even the bar's own floor. Head-to-head performance remains excellent (15/15 wins vs. both Submission C and Submission E, +79% mean margin — even stronger than Phase 15/16's smaller-sample figures), so this remains a genuinely strong candidate relative to the live champions — it simply is not yet strong enough relative to this project's own $50-80k target, or to real top opponents ($63,798-$104,569).

## 1. Confirming (or Refuting) the WHEAT-Starvation Mechanism

Per the brief's explicit instruction to trace the actual mechanism rather than assume Phase 16's hypothesis: `scripts/phase17/confirm_mechanism.py` measured, at each day 15-20 across the 4 development seeds, the mean manhattan distance from home of WHEAT vs. STRAWBERRY/MELON tiles, alongside each crop's per-day idle fraction — a direct test of the "WHEAT tiles are geometrically farther, so the pure-nearest-distance greedy matcher services them last" hypothesis, without needing a full turn-by-turn interactive trace.

**[OBSERVED] Result: WHEAT's idle fraction is 0.0 in every single measurement** (4 seeds × 6 days = 24 day-seed cells, all `0.0`). WHEAT tiles are indeed farther from home on average (6.0-6.5 manhattan distance vs. STRAWBERRY's 5.1-5.3), consistent with the geometric-placement mechanism Section 2 below explains — but **the surviving WHEAT footprint by this window is only 0-2 tiles per seed**, small enough that the existing worker pool services all of it without difficulty. The distance-based hypothesis is directionally correct (WHEAT does land farther from home due to the crop-fraction assignment order, explained below) but **it is not currently costing anything measurable**, because so few WHEAT tiles survive into the mid-game window that the distance penalty never actually causes a missed day.

**[VERIFIED, re-running Phase 16's own methodology unchanged] Re-running `scripts/phase16/diagnose.py` on the current code (no changes made) confirms this directly**: mid-game (day 15-20) WHEAT tile idle fraction is **0.0%**, down from Phase 16's own measured 16.3%. The number of WHEAT tiles present in that window also dropped (0-2 tiles per seed now, vs. 5-11 in Phase 16's run).

**[INFERRED] Why the mid-game WHEAT footprint shrank between Phase 16's measurement and now**: Phase 16's diagnostic was run on the agent BEFORE its own sell-timing-disable change (that diagnostic predates Section 6 of the Phase 16 report, which was the phase's last code change). With sell-timing now off and the wheat-reserve fix in place, the agent's cash trajectory and crop-tile churn differ enough that fewer WHEAT tiles are being freshly (re)planted into the mid-game window in the first place — there's simply less WHEAT there to starve. This is a side effect of Phase 16's own later fix, not something this phase engineered on purpose, and it is reported as such rather than claimed as an intentional achievement of this phase.

## 2. The Underlying Geometric Mechanism (for the record, even though it's not currently costing anything)

For completeness, since the brief asked for the actual mechanism, not just a yes/no: `agents/phase15/execution.py::bounded_multi_crop_tile_pool_assignment` assigns newly-vacant tiles to crops by iterating `crop_fractions` **in descending fraction order**, consuming the distance-sorted vacant-tile list front-to-back — the highest-fraction crop claims the nearest available tiles first, and lower-fraction crops (WHEAT, at 20-30% by mid-game) are assigned whatever is left, which is systematically farther from home. This is a real, confirmed mechanism (Section 1's distance data corroborates it directly) — but it is not a priority-TIER issue (WATER sits at the same priority tier, 1, for every crop; `agents/phase2_3/common.py::_needs_water`/`_needs_harvest_crop` don't discriminate by crop identity) and not currently worth a surgical fix given Section 1's finding that it isn't costing anything measurable at the current, small, surviving WHEAT footprint. **No fix was built this phase** — building one would be optimizing a metric (WHEAT idle fraction) that no longer has any headroom left to improve, and would risk destabilizing the crop-tile assignment logic Phase 15/16 already validated for no measurable benefit. If a future phase changes the crop-fraction schedule to keep a larger WHEAT footprint alive into the mid-game, this mechanism should be revisited then, not now.

## 3. Widened Seed Sample (Step 4)

Per the brief's instruction to reuse this project's existing seed-bucket convention rather than inventing new seeds: `scripts/phase3_2_configs.py::SEED_SETS` (used by every phase since Phase 3.2) provides **development** (700000-700003, n=4 — what Phase 15/16 used), **validation** (701000-701004, n=5), and **held_out** (702000-702005, n=6 — explicitly documented as "final evaluation, used exactly once," which is precisely this phase's purpose). All three buckets combined: **n=15**, exceeding the brief's "at least 12" floor.

Script: `scripts/phase17/wide_validate.py`. Full data: `results/phase17/phase17_wide_validation_results.json`.

### Isolated final money (vs. "pass"), n=15

| Statistic | Value |
|---|---|
| Mean | **$43,734.93** |
| Median | $44,375.00 |
| Min | $31,861.00 |
| Max | $53,541.00 |
| Std. dev. | $5,904.45 |
| Seeds clearing $50,000 | **2 / 15** |

**Bar cleared? NO — mean falls $6,265.07 below even the bar's own $50,000 floor**, not the "$326.25 short" figure Phase 16 published on 4 seeds. [OBSERVED]

### Head-to-head vs. Submission C, n=15

| | Ours | Theirs |
|---|---|---|
| Mean | $38,079.80 | $21,271.47 |
| Median | $38,673.00 | $21,665.00 |
| Min | $29,200.00 | $16,354.00 |
| Max | $44,099.00 | $24,071.00 |

**Win rate: 15/15 (100%).** Mean margin: **+79.0%**.

### Head-to-head vs. Submission E, n=15

Byte-identical to the Submission C results above in every seed — the F-005 liquidity guard never fired differently in any of these 15 games (same finding as Phase 15/16).

**Win rate: 15/15 (100%).** Mean margin: **+79.0%**.

### vs. Real Opponents (Phase 6)

| Opponent | Final money | vs. our $43,734.93 mean |
|---|---|---|
| moushun_chen | $63,798 | below |
| lai_eu_wen | $104,569 | below |
| achille_gohin | $76,076 | below |
| zach_locke | $83,904 | below |

Below all 4 real opponents' final banks, same conclusion as Phase 15/16 but on much firmer statistical ground now (n=15 vs. n=4).

## 4. Was Phase 16's "$49,673.75, So Close" an Underestimate, or Was It Luck?

**[OBSERVED] It was luck, not an underestimate.** The brief's own framing asked whether the wider sample would show $49,673.75 was "a slight underestimate of the true mean" — it is the opposite. The 4 development seeds Phase 15/16 both used happen to sit in the upper half of the wider distribution: 2 of those exact 4 seeds (700001: $53,541, 700003: $50,483) are 2 of only 2 seeds in the ENTIRE 15-seed sample that clear $50,000. The other 11 seeds in the wider sample — including the 5 validation and 6 held-out seeds never previously tested — pull the true mean down to $43,734.93. This is exactly the risk small-sample validation always carries, and exactly why this project's own seed-bucket discipline (development for iteration, held-out for final evaluation, used once) exists — this phase is the first time that discipline was actually exercised for this agent, and it caught a real, materially different answer.

## 5. Diminishing Returns, or One More Iteration Likely to Close It?

**[HYPOTHESIS, stated honestly as a judgment call, not a measured fact]**: the trend across Phase 15 → Phase 16 (headline numbers $45,126.25 → $49,673.75 on the SAME 4 seeds) looked like steady, iteration-by-iteration convergence on the bar. This phase's wider sample reveals that apparent convergence was partly a mirage — the true population mean ($43,734.93) is closer to Phase 15's original number than to Phase 16's. **This does not mean Phase 16's fixes didn't work** (the wheat-reserve fix and cutting sell-timing are still real, validated, directionally-correct improvements — Phase 16 §4-5's before/after comparisons on wider 8-seed samples support that) — it means the specific 4-seed validation set was not a reliable proxy for the true mean, and every phase's promotion-adjacent number reported on just 4 seeds should be read with that in mind going forward.

Given this, the honest read is **diminishing returns are not yet clearly established, but confidence that "one more targeted fix closes it" should be lower than Phase 16's own framing implied**. The gap to the bar's floor is now measured at ~$6,265 (14.3% of the floor) on a much firmer 15-seed basis, roughly back to Phase 15's original scale of shortfall, not the near-miss Phase 16 reported. A future phase pursuing this further should validate on this same widened (or larger) seed sample from the start, not on 4 development seeds alone — the smaller sample's apparent "almost there" signal was real for those 4 seeds, but was never a reliable estimate of the true mean.

## 6. Regression Check

`git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5 agents/phase3_8 agents/phase2_3/common.py agents/phase2_4/common.py agents/phase15`: only `agents/phase3_8/adapters/competitive_v3_agent.py` (Phase 12's prior, unrelated F-005 wiring, unchanged by this phase) shows as modified; `agents/phase15/` shows as present but **not modified by this phase** (no code changes were made — Sections 1-2 found nothing to fix). Existing regression suite (`scripts/phase12_regression_tests.py`, representative of the full suite): 21/21 passing, unchanged from every prior phase.

## Changed Files

New, all additive; nothing pre-existing modified, nothing in `agents/phase15/` touched this phase:
- `scripts/phase17/confirm_mechanism.py`
- `scripts/phase17/wide_validate.py`
- `results/phase17/phase17_wide_validation_results.json`
- `results/phase17/PHASE17_WHEAT_STARVATION_AND_WIDER_SAMPLE_REPORT.md` (this file)

No frozen file was touched. `main.py` still builds Submission C/E. No `.tar.gz` is created or staged.
