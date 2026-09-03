# Phase 25: Systematic Sweep of agents/phase21/'s STRAWBERRY/WHEAT Ratio

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`). `agents/phase15/` (Submission G) was not modified (confirmed via `git status --short` below — the changes present predate this phase). Per the standing exception, `agents/phase21/portfolio.py` was tested with new ratios, then reverted to Phase 24's original values after validation showed they were not actually better. No submission is created.

## Executive Summary

**[VERIFIED] The systematic sweep found no improvement over Phase 24's inferred ratios — if anything, it surfaced a small-sample-screening trap and confirms the STRAWBERRY/WHEAT ratio has plateaued as a lever.** Win rate against Submission G on the full 15-seed set remains **6/15 (40.0%)**, unchanged from Phase 24. The 4-seed screening pass's apparent "winner" (mid-game STRAWBERRY 0.70, late-game 0.70) was validated on the full 15-seed set and found to perform WORSE than Phase 24's original values (0.65 / 0.80): only 3/15 (20.0%) win rate, down from 6/15. **Phase 24's original ratios were restored** after this check — they remain the better-validated choice.

**Unlike Phase 22's sweep (which found a clear, generalizable winner — 0.50 beat a genuine local minimum at 0.40, and that improvement held up on the full 15-seed set), this sweep found every tested combination clustered in a similarly-negative margin band on the 4-seed screen, with no combination clearing even the screening pass's own bar, let alone generalizing to a full-sample improvement.** This is reported honestly as a plateau, not dressed up as progress.

**[OBSERVED] The dormant opponent-aware STRAWBERRY-shrinking logic should stay dormant.** The sweep found no monotonic pattern consistent with STRAWBERRY's glut curve re-triggering at higher allocation fractions (up to 0.95 tested) — margins moved unpredictably with fraction, not in the clean "worse past a threshold" shape a real glut effect would produce. There is no evidence in this sweep of a production scale where re-enabling that logic would help.

**Recommendation: further crop-ratio tuning on Reframe 1 is unlikely to close much more of the remaining gap to Submission G. A different mechanism — plausibly Reframe 2's win-probability objective, since the losses concentrate in close/moderate-margin games, not blowouts — is the more promising next direction.** See Section 4.

## 1. The Sweep

`scripts/phase25/ratio_sweep.py`, same 4 development seeds Phase 22 used for its own screening, measuring head-to-head performance against Submission G directly (win/loss and mean margin — a competitiveness question, not the isolated-money metric Phase 22 used for a different question).

**Sequential design** (day 8-14 and day 15+ tested somewhat independently, per the brief): Pass 1 swept day 15+ STRAWBERRY fraction `{0.70, 0.75, 0.80, 0.85, 0.90, 0.95}` holding day 8-14 fixed at Phase 24's 0.65; Pass 2 swept day 8-14 `{0.55, 0.60, 0.65, 0.70, 0.75}` holding day 15+ fixed at Pass 1's winner.

### Pass 1 (day 15+ STRAWBERRY fraction, mid fixed at 0.65)

| Late fraction | Win rate (4 seeds) | Mean margin |
|---|---|---|
| 0.70 | 1/4 | -$9,960 |
| 0.75 | 2/4 | -$10,198 |
| **0.80 (Phase 24's original)** | 1/4 | -$11,912 |
| 0.85 | 0/4 | -$12,932 |
| 0.90 | 1/4 | -$12,206 |
| 0.95 | 0/4 | -$10,654 |

### Pass 2 (day 8-14 STRAWBERRY fraction, late fixed at 0.70)

| Mid fraction | Win rate (4 seeds) | Mean margin |
|---|---|---|
| 0.55 | 1/4 | -$13,171 |
| 0.60 | 1/4 | -$10,949 |
| 0.65 | 1/4 | -$9,960 |
| **0.70 (screen's apparent winner)** | 2/4 | -$9,896 |
| 0.75 | 0/4 | -$15,646 |

**[OBSERVED] Every single tested combination across both passes shows a negative margin on this 4-seed screen — nothing came close to competitive, let alone a clear winner the way Phase 22's sweep found.** The best point (mid=0.70, late=0.70, margin -$9,896) is only marginally better than several nearby points and is dominated by one consistently-bad seed (700000), which loses by $30,000-45,000 to Submission G under every single ratio tested in this sweep, regardless of STRAWBERRY/WHEAT balance — a strong signal that seed 700000's loss is NOT primarily a crop-ratio problem.

## 2. Full 15-Seed Validation: The Screening Trap

The Pass 2 "winner" (mid=0.70, late=0.70) was implemented and validated on the full 15-seed set, exactly like Phase 23/24's methodology:

| Statistic | Phase 24 (0.65/0.80) | Phase 25 candidate (0.70/0.70) |
|---|---|---|
| phase21 mean | $49,448.13 | $47,667.87 |
| Submission G mean | $54,574.27 | $54,920.20 |
| **Win rate** | **6/15 (40.0%)** | **3/15 (20.0%)** |

**[VERIFIED] The 4-seed screen's apparent winner performs WORSE on the full sample — a real small-sample-screening trap, the same category of risk Phase 17 already documented for a different agent.** Phase 24's original 0.65/0.80 ratios were restored in `agents/phase21/portfolio.py` after this check. Re-running the full 15-seed validation after reverting confirmed the exact Phase 24 numbers reproduce deterministically (6/15 vs. Submission G, 14/15 vs. Submission C) — see `results/phase25/phase25_final_validation_results.json`.

## 3. The Dormant Opponent-Aware STRAWBERRY-Shrink Logic

**[OBSERVED] No evidence supports re-enabling it.** If STRAWBERRY's glut curve were starting to bind at high allocation fractions, Pass 1's margin should degrade monotonically as the late-game fraction rises from 0.70 toward 0.95 — it does not (margins move from -$9,960 → -$10,198 → -$11,912 → -$12,932 → -$12,206 → -$10,654, worsening then partially recovering, not a clean threshold shape). **This is consistent with noise/seed-specific effects, not a real glut re-trigger at any fraction tested up to 0.95.** The logic remains correctly dormant, as Phase 24 left it — this phase found no production scale in the tested range where turning it back on would help.

## 4. Honest Assessment: Plateau, Not Progress

**[VERIFIED]** The STRAWBERRY/WHEAT ratio, having already been corrected once (Phase 24) to fix a real, large, verified mechanism (WHEAT was earning far less than STRAWBERRY's actual uncrashed realized price), has now been swept systematically and found NOT to have a further nearby optimum worth adopting. Unlike Phase 22's opening-ratio sweep — a genuine success story where a real local minimum was found and fixed — **this sweep is a genuine negative result**: the ratio is not the remaining lever.

**[OBSERVED] Seed 700000 loses badly to Submission G under every ratio tested (margins -$30,000 to -$45,000 regardless of crop mix)** — this is the single most informative data point in the whole sweep. A loss that doesn't move no matter how the crop-fraction dial is turned is evidence the remaining gap is not primarily a crop-economics problem. **[HYPOTHESIS, not tested this phase]** Re-examining the full 15-seed loss table (`results/phase23/phase23_vs_submission_g_results.json`, this phase's re-run): the 9 remaining losses are mostly moderate-margin, not blowouts (e.g. seed 701001: $59,084 vs. $58,749, essentially a coin-flip; seed 700003: $57,721 vs. $57,531, another near-tie), while agents/phase21/'s wins tend to be by wider margins. **This pattern — close losses outnumbering close wins — is exactly the shape Reframe 2's win-probability objective was designed to address** (docs/FRESH_STRATEGY.md's own framing: money-maximizing and win-probability-maximizing coincide most of the time, but diverge specifically in close games, where a design that reasons about relative score position rather than absolute money could tip some of these near-ties). This is offered as a hypothesis for the next phase to test directly, not asserted as proven — this phase's own scope (ratio tuning) stops here.

**Recommendation: move to Reframe 2 (win-probability objective) rather than continuing to tune Reframe 1's crop ratios.** Two independent tuning passes (Phase 22's opening ratio, this phase's STRAWBERRY/WHEAT balance) have now been run; the first found and fixed a real problem, the second found the well is dry. Continuing to search the same parameter family is unlikely to be the highest-leverage next step — the close-game loss pattern observed here is a concrete, evidence-grounded reason to try Reframe 2 next, not just the next item on a predetermined list.

## Changed Files

Modified (Phase 21's own, non-frozen agent — tested, then reverted after validation):
- `agents/phase21/portfolio.py` (day 8-14 / day 15+ STRAWBERRY fractions tested at 0.70/0.70, found worse on the full 15-seed set, reverted to Phase 24's 0.65/0.80; docstring updated to record what was tried and why it wasn't kept)

New, additive:
- `scripts/phase25/ratio_sweep.py`
- `results/phase25/phase25_ratio_sweep.json`
- `results/phase25/phase25_final_validation_results.json`
- `results/phase25/PHASE25_CROP_RATIO_SWEEP_REPORT.md` (this file)

No frozen file was touched, `agents/phase15/` was not modified, and no submission is created.
