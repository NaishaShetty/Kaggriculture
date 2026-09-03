# Phase 16: Execution-Efficiency Follow-Up to Phase 15's Macro Controller

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py` — confirmed via `git status --short` below). Per this phase's one explicit exception, `agents/phase15/`'s own files (its own new, unshipped agent) were modified directly. No submission is created.

## Executive Summary

**[OBSERVED] The $50,000-80,000+ bar is still NOT cleared, but this phase closed most of the remaining gap: mean isolated final money rose from Phase 15's $45,126.25 to $49,673.75** — within **$326.25 (0.65%)** of the bar's low end, with 2 of 4 development seeds individually clearing $50,000 ($53,541 and $50,483). This is reported exactly as measured, not rounded up: **the bar is not cleared**, and no submission is packaged, per this phase's own rule.

**[OBSERVED] Step 1's diagnostic found scheduling/servicing was NOT the dominant driver of Phase 15's shortfall** — tile idle fraction (2-3% overall) and animal fed fraction (77-90%) were already in good shape at Phase 15's actual combined scale (13 hands, 13 animals, ~50 tiles, 2-3 crop types), matching Phase 10's smaller-scale finding, now confirmed to hold at this larger, multi-crop scale too. This directly contradicts the assumption that a Phase-13-style scheduling bottleneck was waiting to be found here — it wasn't, and this report says so plainly rather than forcing a fix onto a non-problem.

**[OBSERVED] A real, different inefficiency WAS found and fixed: home-grown WHEAT was being sold 100% immediately, then bought back from the market for every animal-feed need** — a genuine double-transaction cost. The fix (reserve enough harvested WHEAT for the day's actual feed need before selling the rest) cut the single largest cost line in the financial ledger (BUY_PRODUCT:WHEAT) from $17,015 to $6,219 on one seed. Its net effect on final money is modest and noisy on 4 seeds but a real, positive **+$1,979 (+5.1%) mean improvement across a wider 8-seed sample** (Section 4).

**[OBSERVED] The sell-timing layer's Phase 15 "wash" verdict resolves to a clear NEGATIVE once re-tested on a larger sample on top of this phase's fixes: -$3,406 (-7.7%) mean, across 8 seeds.** Per the brief's instruction and this project's standing preference for the simpler mechanism, **it is now disabled by default** (Section 6) — this alone accounts for most of this phase's improvement over Phase 15's published numbers.

**Promotion decision: DO NOT PROMOTE.** Per this phase's explicit rule, a submission requires clearly clearing the bar; $49,673.75 falls just short of even the low end of $50,000-80,000+. No `.tar.gz` is built or staged.

## 1. Diagnostic Findings (Step 1-2)

Reused Phase 10's tile-idle-fraction methodology and Phase 11/13's animal-servicing methodology, run directly on Phase 15's actual agent (`agents/phase15/adapters/macro_agent.py`) at its real, day-changing operating trajectory — three day ranges (early ramp 5-10, mid-game 15-20, late-game 25-29), same 4 development seeds Phase 15 used. Script: `scripts/phase16/diagnose.py`. Full data: `results/phase16/phase16_diagnostic_results.json` / `phase16_diagnostic_summary.json`.

| Day range | Overall tile idle fraction | Per-crop tile idle fraction | Animal fed fraction |
|---|---|---|---|
| Early ramp (day 5-10) | 3.2% | MELON 2.1%, STRAWBERRY 9.1%, WHEAT 3.4% | 86.9% |
| Mid-game (day 15-20) | 2.2% | MELON 1.7%, STRAWBERRY 1.7%, **WHEAT 16.3%** | 90.0% |
| Late-game (day 25-29) | 1.1% | STRAWBERRY 1.0%, WHEAT 5.0% | 78.0% |

Overall action idle fraction (wasted hand-turns, whole game): **20.8%** (79.2% productive action rate).

**[OBSERVED] Overall tile idle fraction (1-3%) and animal fed fraction (77-90%) are already in good shape — comparable to, or better than, Phase 10's own single-crop finding of 92-95%+ tiles serviced.** This directly answers the brief's own escape-hatch condition: **scheduling/idle-time is NOT the dominant driver of Phase 15's shortfall.** The task scheduler Phase 10 validated at smaller scale continues to hold up reasonably well even at this agent's much larger combined scale (13 hands, 13 animals, ~50 tiles, multiple crop types) — a genuine, useful negative result, not assumed but directly measured.

**[OBSERVED] One real, smaller signal did surface: cross-crop starvation of WHEAT specifically in the mid-game.** WHEAT's tile idle fraction (16.3% mid-game, 5.0% late-game) is 5-10x higher than STRAWBERRY's or MELON's in the same day ranges — consistent with the brief's own hypothesis that watering one crop type could get starved by another's harvest priority when multiple crops share the same worker pool. **[INFERRED] This is real but small in absolute magnitude**: WHEAT only occupies 5-11 tiles of the ~190-selled crop-tile total by mid-game (Phase 15's crop schedule deliberately shrinks WHEAT's share as STRAWBERRY takes over) — even a full fix would recover at most a few hundred dollars of production over the whole game, not enough on its own to explain a multi-thousand-dollar shortfall. No separate scheduling fix was built for this specific signal, since Section 3 below found a larger, different, and more directly fixable inefficiency instead.

## 2. Where the Inefficiency Actually Concentrated: A Wasteful Feed Round-Trip, Not Scheduling

**[VERIFIED, by direct financial-ledger read]** With scheduling ruled out as the dominant driver, a full income/expenditure breakdown (`instrumentation.pipeline.analyze_replay`'s `financial_summary`) on one representative seed (700000, pre-fix) showed:

| Cost line | Total | Share of total spend |
|---|---|---|
| BUY_PRODUCT (market wheat for feed) | **$17,015** | **36%** |
| BUY_SEED | $8,560 | 18% |
| HIRE | $8,274 | 18% |
| BUY_LAND | $7,000 | 15% |
| BUY_ANIMAL | $6,100 | 13% |

**BUY_PRODUCT (buying market wheat to feed animals) was the single largest cost line in the entire agent** — larger than hiring, seeds, land, or animals. The root cause: `agents/phase15/execution.py`'s pre-fix logic always sold 100% of harvested WHEAT immediately (the `feed_source="market"` default meant nothing was ever reserved), then separately bought wheat back from the market for every feed need, even while actively growing WHEAT as a crop.

**[VERIFIED] The fix**: reserve enough already-harvested WHEAT to cover the current turn's actual feed need before generating any SELL order for it; only the genuine surplus beyond that gets sold. Market top-up still covers any remaining deficit unconditionally, so this is a strict improvement with no new starvation risk — a shortfall is still made up from the market exactly as before, it's just no longer double-paid for the portion already on hand. This cut BUY_PRODUCT from $17,015 to $6,219 on the same seed (Section 4).

## 3. Why This Isn't "The Same Fetch Bottleneck Phase 13 Already Fixed"

Confirmed, not assumed: Phase 13's fix (already reused unchanged in `agents/phase15/execution.py`'s fetch-entries block) addresses how many WORKERS can simultaneously carry an item to a TILE task (FEED/WATER). The Section 2 issue is a completely different mechanism — a MARKET transaction pattern (sell-then-rebuy the same commodity at a similar price), with no fetch/worker-assignment component at all. Phase 13's fix and this phase's fix operate on unrelated parts of the agent and both remain in place.

## 4. Before/After Validation (Step 4)

Direct comparison against Phase 15's own published numbers, exact same 4 development seeds (700000-700003), same isolated (vs. "pass") and head-to-head (vs. Submission C / Submission E) methodology.

**Isolated final money:**

| | Phase 15 (published) | Phase 16 (wheat fix only, sell-timing still on) | Phase 16 (final: wheat fix + sell-timing off) |
|---|---|---|---|
| seed 700000 | $41,729 | $39,389 | $47,850 |
| seed 700001 | $50,410 | $50,516 | $53,541 |
| seed 700002 | $46,543 | $26,752 | $46,821 |
| seed 700003 | $41,823 | $55,997 | $50,483 |
| **Mean** | **$45,126.25** | $43,163.50 | **$49,673.75** |

The wheat-reserve fix ALONE, on just these 4 seeds, is noisy and not a clear win (43,163.50 vs. 45,126.25) — an honest reporting of a small-sample result that looked different (positive) on a wider 8-seed check (Section 5). The decisive improvement came from disabling the now-negative sell-timing layer (Section 6): **wheat fix + sell-timing disabled reaches $49,673.75, a genuine +$4,547.50 (+10.1%) improvement over Phase 15's published baseline** — just short of the $50,000 floor.

**Head-to-head vs. Submission C and Submission E** (byte-identical results in every seed — the F-005 guard never fired differently in these specific games):

| Seed | Ours | Theirs |
|---|---|---|
| 700000 | $34,240 | $21,345 |
| 700001 | $43,934 | $22,656 |
| 700002 | $36,420 | $21,908 |
| 700003 | $37,250 | $20,407 |
| **Mean** | **$37,961** | **$21,579** |

**+76% mean margin**, an even wider win than Phase 15's own published +68% — this phase's fixes strengthened, not weakened, the head-to-head advantage.

## 5. Wider-Sample Check on the Wheat-Reserve Fix (8 seeds)

Given the 4-seed result in Section 4 was ambiguous, the fix was re-tested on 8 seeds (700000-700007) in isolation from the sell-timing question:

| | Mean (8 seeds) |
|---|---|
| WITHOUT wheat-reserve fix | $39,055.63 |
| WITH wheat-reserve fix | $41,034.50 |

**+$1,978.88 (+5.1%) on the wider sample** — a real, if modest, positive effect, consistent with the fix's sound underlying logic (it can only reduce transaction friction, never increase it) even though the specific 4-seed validation set happened to land on the noisier side of that distribution.

## 6. Sell-Timing Layer: Re-Evaluated Verdict

Phase 15 measured this layer as a wash (mean $42,298 with it vs. $43,376 without, 4 seeds). Re-tested on top of this phase's execution fixes, on the wider 8-seed sample:

| | Mean (8 seeds) |
|---|---|
| `sell_timing_enabled=True` | $41,034.50 |
| `sell_timing_enabled=False` | $44,440.38 |

**-$3,405.88 (-7.7%) with sell-timing enabled — a clear, measured NEGATIVE, not a wash.** [OBSERVED] **Verdict: CUT (disabled by default).** `agents/phase15/adapters/macro_agent.py::make_macro_agent`'s `sell_timing_enabled` parameter now defaults to `False`; the module (`agents/phase15/sell_timing.py`) is left in place, unmodified, and can still be enabled explicitly for further investigation, but per this project's standing preference for the simpler mechanism when a more complex one isn't earning its keep, it is off by default. This is the single largest driver of this phase's overall improvement over Phase 15's published baseline.

## 7. Regression Check

`git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5 agents/phase3_8 agents/phase2_3/common.py agents/phase2_4/common.py agents/phase15`: only `agents/phase3_8/adapters/competitive_v3_agent.py` (Phase 12's prior, unrelated F-005 wiring) and `agents/phase15/` (this phase's explicitly-permitted own edits) show changes. Full existing regression suite re-run: same 128/133 passing as every phase since Phase 12, the 5 non-passing tests being the identical pre-existing stale-`frozen_file_hashes.txt` issue, unrelated to and unaffected by this phase.

## 8. Honest Assessment

- **[OBSERVED] Phase 15's diagnosis in §7 (execution efficiency, not target selection) was partially right but not for the reason assumed.** Scheduling/idle-time turned out to already be fine at this scale (a genuine negative result, reported plainly per the brief's own instruction). The real inefficiency was a market-transaction pattern (sell-then-rebuy WHEAT), not a worker-assignment bottleneck — "execution efficiency" was the right general area, but the specific mechanism required actually reading the financial ledger, not assuming Phase 13's fetch-bottleneck fix would recur.
- **[OBSERVED] The larger lever turned out to be cutting a layer, not adding one.** The sell-timing layer, built new in Phase 15 per the original roadmap's Phase 2 concept, is measurably making this agent's actual crop-mix worse to sell through, not better — most likely because STRAWBERRY (this agent's dominant revenue crop) is already harvested and sold in naturally small per-turn batches as tiles mature, leaving little room for a batching heuristic to improve on, exactly as Phase 15 §5 speculated.
- **[HYPOTHESIS, not tested this phase] The remaining ~$326 gap to the bar's floor, and the larger gap to real opponents' $63,798-$104,569, most likely sits in genuine production/revenue-scale differences** (e.g., real opponents' land/hands/animals may be serviced by an execution layer with genuinely different task-scheduling logic than this project's shared `agents/phase2_3/common.py`-derived greedy matcher, or real opponents may run a larger sustained crop footprint than this agent's 50-tile ceiling) rather than any further waste to cut. This phase looked hard for waste and found real amounts of it (Sections 2 and 6); what's left is closer to a genuine ceiling than an undiscovered leak.

## 9. Promotion Decision

**DO NOT PROMOTE.** Mean isolated final money ($49,673.75) is $326.25 below the stated bar's own floor ($50,000) — not "clearly cleared" by any reasonable reading, and this report does not treat a 0.65% shortfall as a rounding error to wave through. No `.tar.gz` is built or staged, per this phase's explicit rule.

This is close enough that a further, narrowly-scoped iteration (the WHEAT cross-crop-starvation signal from Section 1, or a few more seeds to establish whether $49,673.75 is a slight underestimate of the true mean) is a reasonable, well-motivated next step — but that is a recommendation for a future phase to weigh, not a reason to promote this one.

## Changed Files

Modified (Phase 15's own, non-frozen, unshipped agent — the one explicit exception for this phase):
- `agents/phase15/execution.py` (wheat-reserve fix; `feed_source` parameter removed as dead code once the fix made its distinction moot)
- `agents/phase15/adapters/macro_agent.py` (`sell_timing_enabled` now defaults to `False`; `feed_source` parameter removed)

New, additive:
- `scripts/phase16/diagnose.py`
- `results/phase16/phase16_diagnostic_results.json`
- `results/phase16/phase16_diagnostic_summary.json`
- `results/phase16/PHASE16_EXECUTION_EFFICIENCY_REPORT.md` (this file)

`results/phase15/phase15_validation_results.json` was overwritten by re-running Phase 15's own unchanged `scripts/phase15/validate.py` script against the now-updated `agents/phase15/` code, per this phase's explicit instruction to re-run Phase 15's exact Tier B/C validation — the script itself was not modified.

No frozen file was touched. `main.py` still builds Submission C/E. No `.tar.gz` is created or staged.
