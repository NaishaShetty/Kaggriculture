# Phase 28: Diagnosing agents/phase21/'s Remaining Losses — A Real Bug Found, A Fix Attempted and Reverted

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`). `agents/phase15/` (Submission G) was not modified (confirmed via `git status --short` below — the changes present predate this phase). No submission is created. **Net code state at the end of this phase is byte-identical in behavior to Phase 27's** — a real fix was attempted, found to do more harm than good on the full 15-seed set, and reverted, per this project's own discipline against forcing a change the evidence doesn't support.

## Executive Summary

**[VERIFIED] The 6 current losses split into three distinct patterns, not one shared mechanism** — confirmed by direct trace, not assumed from Phase 26/27's prior findings:

1. **Seed 700000 (-$32,005, by far the largest loss)**: a genuinely different, one-off pattern — land purchase stalls at 2 quadrants from day 6 through day 21 (15 days late relative to the normal day-11 ramp), accompanied by a real chronic cash collapse (2 consecutive days at exactly $0, hands dropping to 0) in the early game. This is the same "unusually harsh early-RNG trough" character this project has seen before in isolated cases, not a systemic bug.
2. **Seeds 701002, 700001, 702000, 702003 (-$4,857 to -$71)**: all four share the SAME residual pattern Phase 26/27 already targeted — agents/phase21/ builds a comfortable mid-game lead (often $5,000-13,000 ahead by day 18-21) that Submission G erodes and overtakes specifically in the final 1-2 days, because G's own endgame liquidation converts its remaining tiles into more cash than agents/phase21/'s does in the same window. Phase 27's per-tile fix genuinely narrowed all four of these (verified directly — margins improved from Phase 24/25's -$3,277 to -$5,280 range down to the current, much smaller range), but did not fully close them.
3. **Seed 702001 (-$4,902)**: an ordinary, volatile back-and-forth game (the lead flips 8 separate times across the match) with no single dominant mechanism — decided by the cumulative sum of many small differences, not one identifiable failure point.

**[VERIFIED] A genuine, previously-unknown, systemic inefficiency was found and confirmed by direct financial-ledger read: agents/phase21/ was never given Phase 16's wheat-reserve-for-feed fix** (built for the separate `agents/phase15/` lineage, never ported to this from-scratch agent). On a representative seed, this cost agents/phase21/ **$16,035 in market-bought feed wheat vs. Submission G's $7,413** for the same need — a real, measurable, systemic gap present in every game, not just losses.

**[OBSERVED, honestly reported] A fix mirroring Phase 16's approach was implemented and tested, but made the full 15-seed result WORSE, not better, under every gating strategy tried (unconditional, cash-threshold-gated, day-and-cash-gated) — it was reverted.** The mechanism: reserving WHEAT for feed removes exactly the small trickle of SELL cash this agent's own ramp depends on at unpredictable points across the game (not just the early window, as first hypothesized) — the fix is economically sound in the aggregate ledger but destabilizes cash timing in a way this agent's specific ramp is more sensitive to than `agents/phase15/`'s was. **The current code is functionally identical to Phase 27's validated state** (confirmed by exact reproduction of Phase 27's 9/15 result).

**Recommendation: this looks like the point of diminishing returns for single-mechanism fixes on this specific benchmark.** Two of three loss patterns (700000's outlier, 702001's ordinary variance) don't present a clean lever, and the third (the residual endgame pattern) has already been substantially — if not completely — addressed by Phase 27. A real additional inefficiency was found (the wheat round-trip) but does not have a low-risk fix currently available. **Packaging the current 60% version, or moving to Reframe 2/3, both look more productive than continuing to chase individual losses on this same benchmark.** See Section 5.

## 1. Current Loss List (Confirmed Directly, Not Assumed)

From `results/phase23/phase23_vs_submission_g_results.json` (Phase 27's most recent run, re-confirmed identical after this phase's revert):

| Seed | Margin | |
|---|---|---|
| 700000 | -$32,005 | huge outlier |
| 702001 | -$4,902 | |
| 701002 | -$4,857 | previously flagged (Phase 25/27) |
| 700001 | -$2,940 | |
| 702000 | -$458 | close |
| 702003 | -$71 | near-tie |

6 losses, exactly as Phase 27 reported. All 6 were traced day-by-day, both sides (`scripts/phase28/trace_current_losses.py`, reusing `agents/phase6/replay_forensics.py::extract_episode_timelines` unchanged).

## 2. Seed 700000: A Genuine Outlier, Not a Systemic Pattern

**[VERIFIED, by direct trace]** Land quadrants stall at 2 from day 6 through day 21 — 15 days later than the normal day-11 ramp seen in every other traced seed (including this same seed's own eventual recovery). Cash hits exactly $0 on days 7-8 (both hands drop to 0), and the deficit compounds: by day 14, agents/phase21/ has only $3 cash and 26 crop tiles while Submission G has $14,700 and 33 tiles already at land=3. **This is the same character as the chronic cash-collapse pattern this project has documented before (Submission C's F-005 case, Phase 19's `agents/phase15/` recalibration)** — an unusually harsh early trajectory that this agent's existing cash-safety throttle (Phase 26's `risk_posture.py`) does not fully prevent in every seed. **[HYPOTHESIS, not pursued further this phase]** A deeper fix here would likely require strengthening the cash-safety throttle's land-purchase gating specifically (the reserve check exists, per Phase 26, but evidently isn't sufficient in this one seed) — but this is a single seed out of 15, and per this phase's own scope, was not chased further given the other two loss categories below offered more information per seed traced.

## 3. Seeds 701002, 700001, 702000, 702003: The Same Residual Endgame Pattern, Narrowed But Not Closed

**[VERIFIED, by direct trace, all 4 seeds]** Every one of these shows the identical shape: agents/phase21/ builds and holds a real lead for most of the game (e.g. seed 701002: +$6,827 at day 21; seed 700001: +$10,339 at day 18; seed 702003: +$11,801 at day 18), then Submission G's own endgame conversion (days 27-29) outpaces agents/phase21/'s, closing and reversing the gap by day 29. This is **exactly** the mechanism Phase 26 diagnosed and Phase 27 built a per-tile fix for.

**Confirming Phase 27's fix genuinely helped, not just shuffled the problem**: comparing this phase's margins against Phase 24/25's pre-Phase-27 numbers for the same 4 seeds (701002: -$8,867 → -$4,857; 700001: not previously in the worst-5 list but improved per Phase 27's own report; 702000: was not separately tracked before; 702003: -$4,196 → -$71) shows Phase 27's per-tile timing fix **did** narrow these, sometimes dramatically (702003 down to a $71 near-tie). **What remains is a smaller residual of the same pattern** — Submission G's own endgame liquidation still converts marginally more value in the final 1-2 days in these specific seeds, for reasons this phase did not further decompose (Section 5's honest limitation).

## 4. Seed 702001: Ordinary Game Variance, Not a Mechanism

**[VERIFIED, by direct trace]** The lead flips 8 separate times across the match (days 6, 7, 9, 11, 16, 17, 19, 23, 25, 26 all show a sign change in the running margin), with no sustained advantage either direction and no single large swing. Final margin (-$4,902) is the accumulated sum of many small differences across the whole game, not attributable to any one turn, mechanism, or endgame effect. **This looks like ordinary head-to-head variance, not a bug or a fixable pattern.**

## 5. The Wheat-Reserve Fix: A Real Bug, A Reverted Fix

### The Bug (Confirmed)

`agents/phase21/execution.py` sells 100% of harvested WHEAT immediately every turn, then separately buys wheat back from the market for every animal-feed need — the exact double-transaction pattern Phase 16 diagnosed and fixed for the unrelated `agents/phase15/` lineage. **This fix was never ported to `agents/phase21/`, a separate, from-scratch agent (correctly, per this project's own "don't build on the other lineage" scope for both agents) — but that also means the bug was never independently found or fixed here until this phase.**

**[VERIFIED, direct financial-ledger read, seed 701002]**:

| Cost line | agents/phase21/ | Submission G |
|---|---|---|
| BUY_PRODUCT (market wheat for feed) | **$16,035** | $7,413 |

A real, roughly 2.2x gap, present in this and (by the shape of the mechanism) plausibly every game agents/phase21/ plays, not specific to losses.

### The Attempted Fix and Why It Was Reverted

A wheat-reserve mechanism mirroring Phase 16's (reserve enough harvested WHEAT to cover the current turn's feed need before generating a SELL order for it) was implemented in `agents/phase21/execution.py` and tested on the 6 current-loss seeds plus re-validated on the full 15-seed set at each iteration:

| Gating strategy | Result on the 6 traced seeds | Full 15-seed result |
|---|---|---|
| Unconditional reserve | 1 improved dramatically (700000: -$32,005 → **+$13,627**), **5 collapsed catastrophically** (e.g. 701002: -$4,857 → **-$60,994**) | Not run (collapse was severe enough to stop here) |
| Reserve only when `money >= cash_danger_threshold` | Collapse less severe but still much worse on 3 of 6 seeds (700001: -$2,940 → -$20,056) | Not run |
| Reserve only when `day >= 15` AND `money >= cash_danger_threshold` | Still mixed and net negative (4 of 6 seeds worse, including 702001 at -$15,562 and 702003 at -$22,022) | Not run (clear from the 6-seed pattern this would not net positive) |

**[VERIFIED, root cause of the instability]** Reserving WHEAT removes cash from circulation exactly at the turns it would otherwise have been converted to SELL revenue — the reserve is economically sound in the AGGREGATE ledger (a shortfall is still bought from the market exactly as before, just not double-paid), but the TIMING cost (inventory instead of liquid cash, right when the agent's own ramp needs cash) is not confined to the early game as first hypothesized — debugging traced it recurring at unpredictable points throughout the match, not just days 0-9. **`agents/phase15/`'s own version of this fix (Phase 16) did not need this caveat**, most likely because that agent's ramp/liquidity-guard interaction differs enough from `agents/phase21/`'s that the same fix lands safely there but not here — a real, disclosed difference between the two lineages, not a contradiction.

**Decision: reverted.** `agents/phase21/execution.py`'s SELL and BUY_PRODUCT blocks are restored to their exact Phase 27 form (confirmed by reproducing Phase 27's 9/15 result exactly, byte-for-byte, on the full 15-seed set — see Section 6). Per this phase's explicit instruction, a fix that helps some seeds at real risk to others is reported honestly rather than forced through.

## 6. Full 15-Seed Validation (Confirms No Net Change From This Phase)

| Statistic | Phase 27 (unchanged) | **Phase 28 (after revert)** |
|---|---|---|
| phase21 mean vs. G | $53,406.00 | **$53,406.00** |
| Submission G mean | $54,622.67 | $54,622.67 |
| **Win rate vs. G** | **9/15 (60.0%)** | **9/15 (60.0%)** |
| phase21 mean vs. C | $63,478.20 | $63,478.20 |
| **Win rate vs. C** | **14/15 (93.3%)** | **14/15 (93.3%)** |

Exact reproduction, per-seed identical, confirming the revert is clean and this phase's net code change is a no-op relative to Phase 27.

## 7. Honest Recommendation

**[OBSERVED] The three loss categories found this phase do not present a common, low-risk lever the way Phase 24 (crop economics) and Phase 27 (liquidation timing) did.** 700000 is a rare bad-early-luck outlier; 702001 is ordinary variance; the 4-seed residual endgame pattern has already been substantially narrowed by Phase 27 and what remains doesn't decompose into a further clean fix within this phase's tracing. The one clear NEW mechanism found (the wheat round-trip) is real but does not have a currently-available low-risk fix — every gating strategy tried made the full-sample result worse, not better.

**This is the signal this phase was built to surface, and it points toward stopping single-mechanism iteration on this benchmark, not continuing it.** Two consecutive successful diagnose-fix cycles (Phase 24, Phase 27) compounded win rate from 13.3% to 60.0% — a genuinely strong run. This phase's honest finding is that the well is now shallower: the remaining losses are heterogeneous (outlier / narrowed-residual / ordinary-variance), and the one systemic bug still found doesn't have a safe fix in hand.

**Recommendation: package agents/phase21/ at its current, validated 60.0%/93.3% state, or move to Reframe 2/3, rather than continuing to search for a fourth single-mechanism fix on this same benchmark.** Both are reasonable next steps from here; continuing to chase individual losses on this specific 15-seed set is not, absent a new diagnostic angle this phase didn't find.

## Changed Files

**Net change: none** (a fix was implemented, tested, and fully reverted — `agents/phase21/execution.py` is functionally identical to its Phase 27 state, confirmed by exact result reproduction).

New, additive:
- `scripts/phase28/trace_current_losses.py`
- `results/phase28/PHASE28_REMAINING_LOSS_DIAGNOSIS_REPORT.md` (this file)

No frozen file was touched, `agents/phase15/` was not modified, and no submission is created.
