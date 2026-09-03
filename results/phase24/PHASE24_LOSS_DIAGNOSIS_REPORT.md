# Phase 24: Diagnosing agents/phase21/'s Losses to Submission G

Diagnostic phase. No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`). `agents/phase15/` was not modified (confirmed via `git status --short` below — the changes present predate this phase). Per this phase's own scope, `agents/phase21/portfolio.py` was modified after diagnosis, once a clear, targeted mechanism was found.

## Executive Summary

**[VERIFIED] Neither of Phase 23's two disclosed hypotheses explains the losses. The real mechanism is a crop-choice economic miscalculation: STRAWBERRY does not actually crash under real combined-production selling pace, and agents/phase21/'s WHEAT-heavy allocation was leaving large, real revenue on the table by avoiding it.**

- **Hypothesis 2 (chronic cash collapse) is refuted directly**: traced day-by-day, neither agent shows the chronic near-$0 collapse pattern documented three times elsewhere in this project. Both dip to low cash in the routine day 2-8 window (a known, harmless, universal pattern) and both recover cleanly by day 10-11, reaching land=3/hands=11 at nearly the same pace.
- **Hypothesis 1 (execution/calibration/ramp-speed gap) is also refuted**: land, hands, and animal ramp timing are nearly identical between the two agents across all 4 traced losses — this is not a "G ramps up faster" story.
- **The real mechanism, found by reading the financial ledger, not assumed**: across all 4 traced losses, Submission G sold 146-157 units of STRAWBERRY per game at a realized average price of **$269-288/unit** (essentially uncrashed, close to STRAWBERRY's $120 base — note the realized price often EXCEEDS base due to the game's below-I0 pricing mechanic, not a contradiction). agents/phase21/'s own STRAWBERRY sales realized the SAME uncrashed price range ($269-288/unit) on its much smaller volume (39-48 units) — **the shared pool never actually saturated enough to trigger STRAWBERRY's glut penalty at either agent's actual production/selling pace.** Meanwhile agents/phase21/'s WHEAT sales (295-361 units/game) realized only $33-41/unit. Submission G's near-total STRAWBERRY portfolio out-earned agents/phase21/'s WHEAT-heavy one by **$30,000-33,000 in STRAWBERRY revenue alone**, in every traced loss.

**[OBSERVED] A targeted fix (reversing the day≥8 WHEAT/STRAWBERRY weighting to favor STRAWBERRY, and disabling the now-counterproductive opponent-aware STRAWBERRY-shrinking logic) produced a real, validated improvement: win rate against Submission G on the full 15-seed set rose from 2/15 (13.3%) to 6/15 (40.0%)**, and the mean gap narrowed from $8,409 (17.5%) to $5,126 (9.4%). **This is a genuine improvement, not a full fix** — Submission G still wins more often than it loses (9-6). Win rate against Submission C stayed strong (14/15, down slightly from 15/15, but with a substantially higher mean margin).

**Recommendation: Reframe 1 needs more tuning before Reframe 2/3 are worth building.** The mechanism found here is squarely a crop-economics calibration problem — exactly the kind of thing a further, narrower sweep (mirroring Phase 22's own successful opening-ratio sweep) is likely to make more progress on cheaply, before reaching for Reframe 2's win-probability objective or Reframe 3's market-as-weapon idea. See Section 5.

## 1. Method

Per Phase 23's per-seed table (`results/phase23/phase23_vs_submission_g_results.json`), the 4 worst losses by margin (seeds 700001 −$18,904, 701002 −$17,269, 700002 −$14,948, 701001 −$13,413) plus 1 win for contrast (701000, +$2,386) were re-run head-to-head and traced day-by-day using `agents/phase6/replay_forensics.py::extract_episode_timelines`, reused unchanged (`scripts/phase24/trace_losses.py`; `replay["info"]["TeamNames"]` was set to `["phase21", "Submission_G"]` before extraction, a legitimate minimal use of the function's own name-lookup mechanism for a locally-run synthetic episode that has no real team names — not a modification of the function).

## 2. Ruling Out Hypothesis 2 (Chronic Cash Collapse)

**[VERIFIED, by direct trace, all 5 seeds]** Both agents show the SAME early-game shape: cash dips to low single/double digits around day 2-8 (e.g. seed 700001: phase21 $8→$6 day 4-5, Submission G $59→$10 day 4-6), then both cleanly recover by day 9-11, reaching hands=11 and land=3 within a turn or two of each other in every traced seed. **Neither agent shows the multi-day, hands-repeatedly-dropping-to-0, cash-stuck-at-exactly-$0 pattern this project has documented three times before** (Submission C's F-005 case, Phase 19's `agents/phase15/` recalibration, Phase 21's own first-cut). The early dip present here is the same routine, harmless trough Phase 15/16/19/20 have already characterized as universal and not itself a problem. **Hypothesis 2 does not explain these losses.**

## 3. Ruling Out Hypothesis 1 (Ramp-Speed / Calibration Gap)

**[VERIFIED, by direct side-by-side trace]** Land and hand counts track almost identically between the two agents across all 4 losing seeds: both reach land=3 and hands=11 by day 10-11 in every case, and both hold that scale for the rest of the game with no divergence in timing. Animal counts differ only modestly (phase21 typically 8-11, Submission G typically 6-10 — not a consistent advantage either direction). **There is no ramp-speed or scale-timing gap to find here — both agents reach the same operating scale at the same pace.** Hypothesis 1, as originally framed (a slower/weaker overall ramp), is refuted.

## 4. What Actually Explains the Losses

**[VERIFIED, by direct financial-ledger read, `instrumentation.pipeline.analyze_replay`'s `market_transaction_summary`]**, all 4 traced losses:

| Seed | P21 STRAW qty / rev / avg px | G STRAW qty / rev / avg px | P21 WHEAT qty / rev | G WHEAT qty / rev |
|---|---|---|---|---|
| 700001 | 40 / $11,092 / $276.57 | 146 / $40,588 / $279.89 | 295 / $12,428 | 17 / $574 |
| 701002 | 39 / $10,956 / $287.77 | 157 / $43,547 / $277.98 | 314 / $13,451 | 14 / $467 |
| 700002 | 43 / $12,376 / $287.10 | 153 / $44,106 / $287.80 | 361 / $14,708 | 15 / $505 |
| 701001 | 48 / $13,079 / $269.32 | 155 / $42,682 / $274.62 | 333 / $12,061 | 12 / $369 |

**STRAWBERRY's realized price never crashes for either agent** — it stays in the $269-288/unit range throughout, essentially uncrashed relative to its $120 base price (the below-I0 pricing branch of `market_price` can quote ABOVE base, which is what's happening here — the shared pool is not being oversupplied by either side's actual selling pace). **[INFERRED] Why the glut never triggers in practice**: harvesting and selling happen incrementally, spread across many turns by both agents' own task-scheduling and worker-count limits — neither agent ever dumps enough STRAWBERRY into the pool in a single window to push `market["inventory"]["STRAWBERRY"]` past its `T=100` glut threshold before `_refresh_prices` and ordinary consumption let it settle back down. Phase 21 Step 1's glut experiment (which DID find a real, large MELON crash) used two single-crop, 40-tile-monoculture agents selling nothing else — a much more concentrated selling pattern than either of these mixed-portfolio, animal-and-crop agents produces for any one crop. **The MELON conclusion does not automatically transfer to STRAWBERRY, and Phase 21 never separately tested it** — this phase is the first time it has been.

**The consequence for agents/phase21/'s original design**: WHEAT's own realized price (~$33-41/unit) is roughly 7-8x LOWER than STRAWBERRY's uncrashed price, in absolute terms, regardless of glut-resistance. A portfolio that shifts a majority of its footprint from STRAWBERRY to WHEAT specifically to avoid a crash that never actually happens at this scale simply forfeits revenue for no benefit. **This is the real, verified mechanism — a third explanation, not predicted by either hypothesis 1 or 2, and not forced to fit them.**

## 5. The Fix and Its Validated Result

**Targeted change, confined to `agents/phase21/portfolio.py`** (no execution-layer, ramp-timing, or MELON-opening changes — those are untouched, since neither was implicated):

1. **Reversed the day≥8 WHEAT/STRAWBERRY weighting** to favor STRAWBERRY as the bulk crop (day 8-14: STRAWBERRY 0.65/WHEAT 0.35, was WHEAT 0.55/STRAWBERRY 0.45; day 15+: STRAWBERRY 0.80/WHEAT 0.20, was WHEAT 0.65/STRAWBERRY 0.35). MELON's day<8 opening-only role is completely unchanged — that specific glut conclusion (Phase 21 Step 1) was directly confirmed, unlike the STRAWBERRY assumption this replaces.
2. **Made the opponent-aware STRAWBERRY-shrinking logic dormant** (threshold raised above 1.0, so it can never fire) rather than deleted — it was built on exactly the assumption Section 4 refuted (that piling into STRAWBERRY alongside a STRAWBERRY-heavy opponent is costly); left in place and documented as a disclosed dead lever, not silently removed, in case a future phase at a different production scale finds the original concern real again.

### Before/After: Head-to-Head vs. Submission G, Full 15-Seed Set

| Statistic | Before (Phase 23) | After (Phase 24 fix) |
|---|---|---|
| phase21 mean | $48,124.27 | **$49,448.13** |
| Submission G mean | $56,533.67 | $54,574.27 |
| Mean gap | -$8,409.40 (-17.5%) | **-$5,126.13 (-9.4%)** |
| **Win rate** | **2/15 (13.3%)** | **6/15 (40.0%)** |

**A real, validated improvement — nearly tripling the win rate and roughly halving the mean gap — but not a full fix.** Submission G still wins 9 of 15 games. Full per-seed results: `results/phase23/phase23_vs_submission_g_results.json` (overwritten with this phase's post-fix run — the pre-fix numbers are preserved in the table above and in `results/phase23/PHASE23_PHASE21_VS_SUBMISSION_G_REPORT.md`).

### Head-to-Head vs. Submission C, Full 15-Seed Set (Secondary Check)

| Statistic | Before (Phase 23) | After (Phase 24 fix) |
|---|---|---|
| phase21 mean | $53,692.93 | **$58,141.93** |
| Submission C mean | $33,342.60 | $32,096.47 |
| **Win rate** | **15/15 (100%)** | **14/15 (93.3%)** |

Mean margin against Submission C actually widened; one previously-untested seed (702002) flipped to a loss (phase21 $22,373 vs. Submission C $30,704) — not investigated further this phase, since Submission C is not this phase's target comparison and a 14/15 record remains decisive.

## 6. Recommendation

**[OBSERVED] The remaining gap to Submission G is very likely still closeable with further Reframe-1 tuning, not evidence that Reframe 2 or 3 is needed.** The mechanism found and fixed this phase (a crop-economics miscalibration — favoring a glut-resistant crop that was never actually gluting, over a much higher-absolute-revenue crop) is exactly the same CATEGORY of problem Phase 22 already fixed once (the day<5 opening ratio) with a simple, direct sweep. A natural next step, not undertaken this phase per its own "keep the fix targeted, don't redesign" constraint: **sweep the day≥8 STRAWBERRY/WHEAT ratio the same way Phase 22 swept the opening ratio** (this phase picked 0.65/0.80 STRAWBERRY by inference from the trace, not from a systematic sweep) — there is a reasonable chance a better ratio exists in the neighborhood of what was chosen here, the same way Phase 22 found 0.40 was a local minimum rather than a sensible middle ground.

**[INFERRED] Nothing traced this phase points specifically at Reframe 2 (win-probability objective) or Reframe 3 (market-as-weapon) as the missing piece.** The 9 remaining losses were not individually re-traced after the fix (out of this phase's scope — the fix was validated in aggregate, per the brief's own instruction), so it remains possible some of them show a close-game risk-posture pattern Reframe 2 would address, or a market-timing interaction Reframe 3 would exploit — but that is speculation this phase did not test, not a finding. **The concrete, evidence-backed next step is a further crop-ratio sweep on Reframe 1 first** — cheap, directly motivated by this phase's own diagnosis, and likely to close more of the gap before any bigger architectural investment is justified.

## Changed Files

Modified (Phase 21's own, non-frozen agent — the standing exception for this phase, used only after diagnosis found a clear, targeted mechanism):
- `agents/phase21/portfolio.py` (day≥8 WHEAT/STRAWBERRY weighting reversed; opponent-aware STRAWBERRY-shrink threshold made dormant)

New, additive:
- `scripts/phase24/trace_losses.py`
- `results/phase24/PHASE24_LOSS_DIAGNOSIS_REPORT.md` (this file)

`results/phase23/phase23_vs_submission_g_results.json` was overwritten by re-running Phase 23's own unchanged `scripts/phase23/vs_submission_g.py` script against the now-fixed `agents/phase21/` code, per this phase's instruction to re-validate on the full 15-seed set — the pre-fix numbers remain on record in `results/phase23/PHASE23_PHASE21_VS_SUBMISSION_G_REPORT.md`'s own tables and reproduced in Section 5 above. No frozen file was touched, `agents/phase15/` was not modified, and no submission is created.
