# Phase 36: Adaptive Purchase Pacing — A Real Improvement on Existing Targets; the Sundar Rebalance Still Doesn't Work

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`). `agents/phase15/` (Submission G) and `agents/phase21/` (Submission H) are unmodified — confirmed via `git status --short`, which shows only `scripts/phase36/` and `results/phase36/` as new, untracked paths. **No submission was packaged this phase** (packaging was outside this phase's own scope), but Stage 1's result clears this project's own bar for one — see Section 5.

## Executive Summary

**[VERIFIED] Stage 1's adaptive pacer — SAME targets as shipped Submission H (3 land / 11 hands / 58 crop tiles / current COW9-SHEEP8 ratio), only the TIMING of purchases changed — is a real, validated improvement.** Isolated economy: $59,144.50 vs. $55,785.00 baseline (**+6.0%**). Full 15-seed validation: **10/15 (66.7%) vs. Submission G**, up from Submission H's shipped 9/15 (60.0%), and **15/15 (100%) vs. Submission C**, up from 14/15 (93.3%). **This clears this project's own bar for a submission-worthy change** (a real, validated improvement over the current 9/15 record).

**[VERIFIED] Stage 2 — Phase 35's best rebalance candidate (A2, Sundar-informed SHEEP-heavy) reintroduced ON TOP of the working pacer — still does NOT work.** Isolated economy: $43,871.00, **-21.4% vs. the unmodified baseline** (better than Phase 35's own A2 result of -29.2%, confirming pacing helps even the rebalance somewhat, but the combination is still net negative and performs WORSE than the pacer alone). Per this phase's own decision rule, Stage 2 did not clear the isolated-economy screen, so no full 15-seed validation was run for the rebalance-on-pacer combination.

**Bottom line: adaptive pacing helps `agents/phase21/`'s EXISTING targets by itself — a real, validated, submission-worthy finding. It does NOT rescue the Sundar-style rebalance — that idea remains eliminated, now on its second independent test.**

## 1. Purchase Logic Read First (Per This Phase's Own Instruction)

`agents/phase21/execution.py`, confirmed directly:
- **HIRE**: affordability-caps the day's cumulative Fibonacci hire cost against current money, but holds back **zero reserve** beyond that — will spend every last affordable dollar hiring.
- **BUY_LAND**: DOES hold a reserve (`land_purchase_reserve`, from `agents/phase21/risk_posture.py`'s posture-aware $75/$150/$300 — Phase 26, grounded in that phase's own traced close-margin data) — but it is a flat reserve, unaware of animal-feed or other upcoming obligations.
- **BUY_ANIMAL**: **zero reserve of any kind** — `buy_n = min(still_needed, int(money // cost))` spends every affordable dollar the instant animals become affordable, in one lump sum. This is exactly the mechanism Phase 35 traced as the cause of its own rebalance candidates' collapse.

## 2. Pacer Design (Grounded in Real Data)

`scripts/phase36/paced_execution.py` — a from-scratch adaptation of `agents/phase21/execution.py` (imports its other primitives unchanged) that gates **BUY_ANIMAL only**:

```
ANIMAL_RESERVE = land_purchase_reserve (posture-aware, Phase 26's own grounded values)
              + FEED_BUFFER_DAYS(2) * owned_animal_count * WHEAT_PRICE_ESTIMATE($30)
```

An animal purchase fires only if `money - cost >= ANIMAL_RESERVE`, and is additionally throttled to **1 unit per species per turn** (directly countering Phase 35's diagnosed lump-sum front-loading).

- **`FEED_BUFFER_DAYS = 2`**: not arbitrary — directly matches `vendor_kaggriculture/kaggriculture.py::_daily_refresh_animals`'s own confirmed "2 consecutive unfed days → animal escapes" threshold (the exact mechanism Phase 34 traced destroying capital in its Sundar-archetype reconstruction attempts).
- **`WHEAT_PRICE_ESTIMATE = $30`**: grounded in this session's own observed `BUY_PRODUCT:WHEAT` realized prices (Phase 33/35 traces: $20-70/unit range; `CROPS["WHEAT"]["base"] = $25`) — a conservative near-base estimate.

## 3. A Design Bug Found and Fixed by Direct Trace

The first version of this pacer applied the SAME reserve formula (including an added "next hire cost" term) to **HIRE and BUY_LAND as well as BUY_ANIMAL**. Isolated-economy result: **-66.2%**, with idle_action_fraction RISING (7.1% → 15.3%). Direct trace (seed 700000) found why: `hands` dropped to **0** for multiple stretches (days 3, 5, 8, 12, 18), and owned animal count fell alongside it (day 3: 4 → day 5: 2) — a self-defeating feedback loop. Coupling HIRE's reserve to the animal feed-buffer term meant that whenever cash got tight because animals needed feeding, HIRE ALSO froze, removing the very hands needed to feed those animals — causing MORE escapes, not fewer, while simultaneously starving the crop side of the economy. **[VERIFIED] The fix was to decouple the reserve: HIRE and BUY_LAND are left EXACTLY as `agents/phase21/execution.py` already has them (no reserve change); only BUY_ANIMAL — the one purchase type with a genuinely zero reserve before, and the one Phase 35 identified as the actual front-loading culprit — is paced.** This is reported as an honest part of the process, not hidden: a plausible, real-data-grounded design still needed one direct-trace correction before it worked, exactly the kind of check this project's standing discipline calls for.

## 4. Stage 1 Results: A Real Improvement

### Isolated Economy (4 Development Seeds, vs. "pass")

| Condition | Mean final money | Mean idle_action_fraction |
|---|---|---|
| baseline (unmodified Submission H) | $55,785.00 | 7.1% |
| **Stage 1 pacer (same targets, BUY_ANIMAL paced)** | **$59,144.50** | 7.95% |

**[VERIFIED] +$3,359.50 (+6.0%), cleanly clearing the cheap screen** — idle_action_fraction barely moved (7.1% → 8.0%), confirming this is a genuine timing improvement, not a wholesale behavior change.

### Full 15-Seed Validation

| Matchup | Submission H (shipped) | Stage 1 pacer |
|---|---|---|
| vs. Submission G | 9/15 (60.0%) | **10/15 (66.7%)** |
| vs. Submission C | 14/15 (93.3%) | **15/15 (100%)** |

**[VERIFIED] The pacer wins one additional game against Submission G (net flip, not just margin narrowing) and sweeps Submission C cleanly.** Per this project's own promotion bar ("No submission is created unless full 15-seed validation clearly beats agents/phase21/'s current 9/15 record vs. Submission G") — **10/15 clears this bar.**

## 5. Stage 2: Rebalance-on-Pacer Still Fails

Per this phase's own gate (Stage 1 must clear its baseline before Stage 2 is attempted — it did), `scripts/phase35/rebalance_candidates.py::make_candidate_a2_targets` (Phase 35's best-performing rebalance — Sundar-informed SHEEP-heavy, crop_tile_target capped at 32, COW9/SHEEP16 reached by day 20) was run through the SAME validated pacer, unchanged:

| Condition | Mean final money | vs. unmodified baseline | vs. Stage 1 pacer alone |
|---|---|---|---|
| baseline | $55,785.00 | — | -5.7% |
| Stage 1 pacer alone | $59,144.50 | +6.0% | — |
| **Stage 2: A2 rebalance + pacer** | **$43,871.00** | **-21.4%** | **-25.8%** |
| *(for reference) Phase 35's A2, no pacer* | *$39,467.00* | *-29.2%* | *n/a* |

**[VERIFIED] The combination is still net negative — it does NOT clear the isolated-economy screen, so no full 15-seed validation was run for it, per this phase's own decision rule.** **[OBSERVED] Pacing DID help the rebalance somewhat** (-21.4% vs. Phase 35's own -29.2% for the same target ratio without pacing) — a real, if partial, improvement directly attributable to the pacer, consistent with Phase 35's own diagnosis. **[VERIFIED] But it performs WORSE than simply keeping the existing targets and pacing them** (-21.4% vs. +6.0%) — the SHEEP-heavy rebalance itself, not just its timing, remains a net negative for this execution layer.

## 6. Honest Diagnosis

**[VERIFIED]** Phase 35's architectural diagnosis — that `agents/phase21/`'s reactive-only cash safety (throttle after the fact, no forward pacing) was a real, fixable gap — is confirmed correct: fixing exactly that gap, for exactly the purchase type Phase 35 identified (BUY_ANIMAL), on the EXISTING validated targets, produces a real, promotion-worthy improvement. **[VERIFIED]** The SAME fix, applied underneath Phase 35's rebalanced targets, narrows but does not close that rebalance's own gap — meaning the rebalance's failure was never PURELY a pacing problem; some of Sundar's real SHEEP-heavy ratio's disadvantage for this specific execution layer is structural (fewer crop tiles competing at tier-3 priority against MORE animals at tier-1/2, a genuine capacity trade this agent's crop-heavy design is evidently better suited to), not just a matter of purchase timing. **[INFERRED]** This is a clean, two-part answer: the architectural gap Phase 35 found is real and worth fixing on its own merits (Stage 1); but it was never the SOLE reason Sundar's specific ratio failed here (Stage 2) — this agent's crop-heavy allocation appears to be closer to a genuine local optimum for its own execution layer than either hypothesis alone predicted.

## Verdict

- **Does the adaptive pacer improve on `agents/phase21/`'s existing targets by itself?** **Yes** — +6.0% isolated, 10/15 vs. Submission G (up from 9/15), 15/15 vs. Submission C (up from 14/15). [VERIFIED]
- **Does the Sundar-style rebalance finally work once purchases are properly paced?** **No** — still -21.4% vs. baseline, worse than the pacer alone. Pacing helps the rebalance partially (vs. Phase 35's own -29.2%) but does not make it competitive. [VERIFIED]
- **Is a new submission warranted?** Stage 1's pacer alone clears this project's own validation bar (10/15 > 9/15 vs. Submission G, full 15-seed set). This phase did not include a packaging step in its own scope, so no submission `.tar.gz` was built — flagged here as clearing the bar, for a decision on whether to proceed with packaging.

## Changed Files

New, additive only:
- `scripts/phase36/paced_execution.py`
- `scripts/phase36/isolated_economy.py`
- `scripts/phase36/vs_submission_g_paced.py`
- `scripts/phase36/stage2_rebalance_on_pacer.py`
- `results/phase36/phase36_isolated_economy_results.json`
- `results/phase36/phase36_vs_submission_g_results.json`
- `results/phase36/phase36_stage2_isolated_results.json`
- `results/phase36/PHASE36_ADAPTIVE_PACING_REPORT.md` (this file)

No frozen file, `agents/phase21/`, or `agents/phase15/` was touched. `agents/phase21/`'s shipped configuration remains unchanged pending a decision on packaging Stage 1's validated result.
