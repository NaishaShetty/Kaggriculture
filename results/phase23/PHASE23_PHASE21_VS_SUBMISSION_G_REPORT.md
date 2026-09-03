# Phase 23: agents/phase21/ vs. Submission G — The Real Comparison

Validation-only phase. No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`). Neither `agents/phase15/` nor `agents/phase21/` was modified — this phase only runs them against each other. New code: `scripts/phase23/vs_submission_g.py`.

## Executive Summary

**[VERIFIED] agents/phase21/ loses decisively to Submission G (agents/phase15/, Phase 20's liquidity-guard-enabled configuration, exactly as shipped) on the full 15-seed set: a 2-13 record (13.3% win rate), with Submission G ahead on both mean and median final money.** This directly contradicts the impression Phase 21/22's own validation could have left — a 15/15 win rate against a synthetic benchmark did not translate into competitiveness against this project's actual strongest shipped work. This is exactly the finding this phase exists to surface, reported without softening.

**[VERIFIED] agents/phase21/ beats Submission C decisively: 15-0 (100% win rate)**, mean $53,692.93 vs. Submission C's $33,342.60 — consistent with every prior phase's finding that Submission C is comparatively weak.

**The honest read: agents/phase21/ sits BETWEEN Submission C and Submission G, closer to G than to C in absolute terms, but clearly behind G where it actually matters (win/loss).** The synthetic realistic-opponent benchmark Phase 21/22 validated against (`scripts/phase21/realistic_opponent.py`) has zero shared-market discipline or cash-safety mechanism of its own — a real, if real-data-grounded, opponent, but not a demanding one. It was never a fair proxy for whether agents/phase21/ could beat something with G's actual competitive logic (Phase 19's real-ladder-calibrated targets AND Phase 20's liquidity guard) already built in.

**Recommendation: do NOT package or promote agents/phase21/ at this time.** Do NOT proceed straight to building Reframe 2/3 on the assumption that Reframe 1 alone is already competitive, either — the gap to G is real and needs to be understood, not built around. See Section 4.

## 1. Confirming Call Signatures Before Wiring (Step 1)

Read directly, not assumed:
- `agents/phase15/adapters/macro_agent.py::make_macro_agent(sell_timing_enabled=False, trace_path=None)` — defaults exactly match Submission G's shipped configuration (Phase 16 disabled sell-timing after finding it a net negative; Phase 20's liquidity guard is unconditional inside `agents/phase15/execution.py`, not a constructor flag, so it is always active regardless of arguments).
- `agents/phase21/adapters/portfolio_agent.py::make_portfolio_agent()` — no arguments; wraps `agents/phase21/portfolio.py`'s Phase-22-tuned targets with `agents/phase3/opponent_observation.py`'s telemetry, matching the exact configuration Phase 22's own wide validation used.

Both were called with their bare defaults — i.e., exactly what is actually shipped as Submission G, and exactly what Phase 22 validated.

## 2. agents/phase21/ vs. Submission G — Full 15-Seed Distribution

Same seed set every phase since 17 has used (`scripts/phase3_2_configs.py::SEED_SETS`: development n=4 + validation n=5 + held-out n=6 = 15).

| Seed | agents/phase21/ | Submission G | Winner |
|---|---|---|---|
| 700000 | $57,392 | $52,600 | **phase21** |
| 700001 | $38,990 | $57,894 | Submission G |
| 700002 | $39,030 | $53,978 | Submission G |
| 700003 | $48,165 | $58,005 | Submission G |
| 701000 | $63,695 | $61,309 | **phase21** |
| 701001 | $49,279 | $62,692 | Submission G |
| 701002 | $23,968 | $41,237 | Submission G |
| 701003 | $53,226 | $57,967 | Submission G |
| 701004 | $40,764 | $47,365 | Submission G |
| 702000 | $49,592 | $61,904 | Submission G |
| 702001 | $58,291 | $59,245 | Submission G |
| 702002 | $52,932 | $63,666 | Submission G |
| 702003 | $48,458 | $55,306 | Submission G |
| 702004 | $55,373 | $59,471 | Submission G |
| 702005 | $42,709 | $55,366 | Submission G |

| Statistic | agents/phase21/ | Submission G |
|---|---|---|
| Mean | $48,124.27 | **$56,533.67** |
| Median | $49,279.00 | **$57,967.00** |
| Min | $23,968.00 | $41,237.00 |
| Max | $63,695.00 | $63,666.00 |
| Std. dev. | $9,892.83 | $6,008.43 |

**Record: 2 wins, 13 losses, 0 ties. Win rate: 2/15 (13.3%).** [VERIFIED] Submission G wins on mean (+$8,409.40, +17.5%), on median (+$8,688), and is more CONSISTENT (lower std. dev., $6,008 vs. $9,893) — agents/phase21/'s two wins (seeds 700000, 701000) are its own highest scores, not cases where G collapsed; G simply out-produces it in 13 of 15 games. This is not a close or ambiguous result.

## 3. agents/phase21/ vs. Submission C — Secondary Data Point

Same 15 seeds, `make_competitive_v3_agent(trace_path=None, liquidity_guard_enabled=False)` — matching every prior phase's "Submission C" convention.

| Statistic | agents/phase21/ | Submission C |
|---|---|---|
| Mean | **$53,692.93** | $33,342.60 |
| Median | **$54,535.00** | $33,725.00 |
| Min | $43,865.00 | $27,334.00 |
| Max | $64,536.00 | $37,073.00 |
| Std. dev. | $6,692.20 | $3,001.86 |

**Record: 15 wins, 0 losses, 0 ties. Win rate: 15/15 (100%).** [VERIFIED] Not a single close game — agents/phase21/'s minimum ($43,865) exceeds Submission C's maximum ($37,073) in every comparison.

## 4. What This Means, and What Should Happen Next

**[OBSERVED] agents/phase21/ is a genuine improvement over Submission C, but not yet competitive with Submission G — the strongest thing this project has actually shipped.** The synthetic realistic-opponent benchmark's 15/15 result (Phase 22) measured something real (shared-market durability beats a real-data-grounded but competitively-naive opponent) but did not measure the thing that actually matters for this project's next decision: is Reframe 1 alone enough to beat the best of what's already live? **The answer, directly tested, is no.**

**[INFERRED, not further diagnosed this phase — validation-only scope] Two concrete, disclosed-but-untested hypotheses for the gap, both grounded in what's actually different between the two agents:**
1. **Execution/calibration maturity**: Submission G's targets (land 3, hands 11, animal range 12-17, the exact crop-fraction transition timing) went through four full iteration phases against real data (15, 16, 19, 20) — including a liquidity guard purpose-built and tuned against G's own specific collapse patterns (Phase 20). agents/phase21/'s portfolio controller has had exactly one tuning pass (Phase 22, the opening-ratio sweep) on top of a first-cut design (Phase 21). The gap may be substantially execution polish, not a limitation of the shared-market reframe itself.
2. **G's own cash-safety guard is a per-turn, re-armable mechanism purpose-tuned against traced collapse patterns (Phase 20 §2-3); agents/phase21/'s cash-safety throttle (Section 1 of the Phase 21 report) was a quick, unvalidated addition built only to stop its OWN realistic-opponent benchmark from collapsing in isolation — it has never been stress-tested against a real, strong, competitively-aware opponent the way Phase 20's guard was.** The 13 losses here may concentrate in exactly the kind of chronic-cash-collapse pattern this project has now documented three times (Submission C's F-005 case, Phase 19's original agents/phase15/ recalibration, and Phase 21's own first-cut) — this phase did not trace individual losing seeds to confirm or refute that, since doing so is diagnostic work outside this phase's validation-only scope.

**Recommendation: do NOT package or promote agents/phase21/.** It is not yet competitive with the actual best shipped submission, and shipping it would be a real regression risk against Submission G's own live rating.

**Recommendation: do NOT proceed straight to Reframe 2/3 on the assumption Reframe 1 alone is "done."** Building more architecture on top of an agent that currently loses to this project's own G would compound an unaddressed gap rather than close it. **A more useful next step, per this project's own standing discipline (diagnose before you build), would be a focused phase tracing agents/phase21/'s losses against Submission G directly** — the same "confirm the mechanism before assuming" approach every phase since 10 has used — to determine whether the gap is closeable with further tuning of Reframe 1's own execution (cheap, before touching Reframe 2/3) or whether it genuinely requires Reframe 2/3's additional ideas (win-probability objective, market-as-weapon) to close. This phase deliberately stops at reporting the gap, not diagnosing it, per its own explicit validation-only scope.

## Changed Files

New, all additive; nothing pre-existing modified:
- `scripts/phase23/vs_submission_g.py`
- `results/phase23/phase23_vs_submission_g_results.json`
- `results/phase23/PHASE23_PHASE21_VS_SUBMISSION_G_REPORT.md` (this file)

No frozen file was touched. `agents/phase15/` and `agents/phase21/` were both used exactly as they already exist — neither was modified. No submission is created.
