# Phase 26: Risk Posture — Built as Instructed, But Not the Real Mechanism

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`). `agents/phase15/` (Submission G) was not modified (confirmed via `git status --short` below — the changes present predate this phase). Per the standing exception, `agents/phase21/`'s own files were modified. No submission is created.

## Executive Summary

**[VERIFIED] The diagnosis in Phase 25 §4 — that agents/phase21/'s close losses to Submission G reflect a risk-posture gap — is REFUTED by direct trace.** All 5 traced losses (4 close, 1 moderate) show the same pattern: agents/phase21/ is AHEAD of Submission G for most of the game, often comfortably, right through day 26-27 — then Submission G surges past it specifically in the final 1-2 days, every single time. This is not a spending-behavior or risk-appetite difference; **it is an endgame-liquidation TIMING gap**: in every close loss traced, agents/phase21/ had fully liquidated all crop tiles (crop count = 0) by the end of day 28, one full day before the season ends, while Submission G still held several standing crop tiles into day 29 and captured one more real day of harvest-and-sell revenue that agents/phase21/'s own schedule had already forfeited.

**[VERIFIED] The risk-posture layer was built exactly as instructed and validated honestly: it has ZERO effect on the 5 traced seeds.** `agents/phase21/risk_posture.py` reads the live, fully-public opponent cash margin every turn and adjusts the existing cash-safety reserve parameters (smaller when behind, larger when ahead) — but re-running the exact 5 traced seeds with this layer wired in produced byte-identical final money to before it existed. This confirms the refutation directly, not just by inference: the mechanism these losses actually run on isn't the one risk posture addresses.

**[OBSERVED] A separate, directly-motivated fix (extending the endgame-liquidation schedule by one day, so the final day of the season isn't forfeited) produced a real, if partial and uneven, improvement.** On the full 15-seed set, mean margin against Submission G narrowed from -$5,126.13 (Phase 24/25) to -$4,147.00, and one previously-close loss (seed 700002) flipped cleanly to a win — but the overall win rate stayed flat at **6/15 (40.0%)**, because a different, previously-marginal win (seed 700003) flipped to a loss under the new timing, for a reason traced and reported honestly in Section 4, not glossed over.

**Recommendation: risk posture, as framed in this phase's brief, is not the missing piece for these specific losses — endgame-liquidation timing is a real, partially-fixable lever, but it interacts with each game's own harvest-cycle phase in a way that isn't cleanly solved by moving two integer day-thresholds.** See Section 5.

## 1. Diagnosing the Close Losses (Before Building Anything)

Per this project's standing discipline, the 4 closest losses (seeds 700002, 702003, 702002, 702004; margins -$3,277 to -$5,280) plus one moderate loss (701002, -$8,867) from Phase 25's final validation (`results/phase23/phase23_vs_submission_g_results.json`) were traced day-by-day, both sides, using `agents/phase6/replay_forensics.py::extract_episode_timelines` (reused unchanged; `scripts/phase26/trace_close_losses.py`).

**[VERIFIED, all 5 traces] The lead position, not the spending behavior, is what actually changes.** In every traced seed, agents/phase21/ is ahead of Submission G for the bulk of the mid-late game (e.g. seed 702003: ahead by $6,000-11,800 from day 15 through day 27), and both agents' hand/land/crop-tile counts track almost identically throughout (matching Phase 24's own earlier finding that ramp speed isn't the gap). **The lead flips specifically at day 28-29 in every single traced case.**

**[VERIFIED, direct board-state read at the turn level] The mechanism, confirmed by example (seed 700002)**:

| Turn | agents/phase21/ cash | agents/phase21/ crop tiles | Submission G cash | Submission G crop tiles |
|---|---|---|---|---|
| day 27, hour 23 | $39,733 | 51 | $34,876 | 48 |
| day 28, hour 23 | $46,469 | **0** | $44,505 | **5** |
| day 29, hour 12 | $45,901 (−$568) | 0 | $47,149 (+$2,644) | 4 |
| day 29, hour 23 (final) | $45,848 | 0 | $49,125 (+$4,620 from day 28) | 0 |

**agents/phase21/ has nothing left to harvest or sell on the actual last day of the season — it already cashed everything out a day early. Submission G still has 5 tiles standing at that same point, and captures a real, substantial cash gain ($4,620) by harvesting and selling them across day 29 — a full day of production agents/phase21/'s own schedule forfeits.** This pattern repeats, with the same shape, in all 4 other traced seeds.

**Conclusion: the diagnosis motivating this phase (a risk-posture / spending-behavior gap) is not what the traces show.** agents/phase21/ does not behave differently when ahead vs. behind in any of these games — it follows the same fixed schedule regardless, and that fixed schedule happens to end its productive season one day too early relative to Submission G's.

## 2. The Risk-Posture Classifier (Built as Instructed)

Per the brief, a simple classifier was still built and validated in full, using the live, fully-public opponent cash margin (`obs["farms"][opponent_index]["money"]` — confirmed directly from `vendor_kaggriculture/kaggriculture.py`: both players' observation records share the same `farms` list object, so this is exactly as public as the agent's own money, every turn, no telemetry needed).

**`agents/phase21/risk_posture.py::classify_posture(own_money, opponent_money)`**: `margin = own - opponent`; `CLOSE_BAND = $3,000`, grounded directly in Section 1's own traced data (real "close" margins observed: $34, $79, $682, -$543, -$754, -$950; real "clear" margins observed: +$5,007, +$9,564, -$3,565 — $3,000 sits between the two observed clusters, not picked arbitrarily).

**Levers implemented** (2, both existing cash-safety parameters in `agents/phase21/execution.py`, not new mechanisms):

| Posture | `cash_danger_threshold` | `land_purchase_reserve` |
|---|---|---|
| BEHIND | $75 (smaller — accept more risk) | $75 |
| CLOSE | $150 (unchanged, Phase 21's original) | $150 |
| AHEAD | $300 (larger — protect the lead) | $300 |

**[VERIFIED] Re-running the exact 5 traced seeds with this layer active produced byte-identical final money to the pre-Phase-26 baseline in every case.** This is the direct, honest confirmation of Section 1's conclusion — these losses are not being caused by risk-appetite differences the posture classifier could correct, since adjusting the cash-reserve levers by posture changed nothing about how these specific games played out.

## 3. The Endgame-Timing Fix (A Different Lever, Directly Motivated by Section 1)

`agents/phase21/portfolio.py`: `LIQUIDATION_START_DAY` 27→28, `DIG_ONGOING_CROPS_DAY` 28→29 — both delayed by one day, so the crop-tile-target isn't forced to 0 and standing "ongoing" crops aren't force-cleared until one day later than before, giving the final day a chance to still be productive.

**Effect on the 5 traced seeds**:

| Seed | Before (final money, ours/theirs) | After (final money, ours/theirs) | Change |
|---|---|---|---|
| 700002 | $45,848 / $49,125 (loss, -$3,277) | $49,391 / $49,101 (**win, +$290**) | **Flipped to a win** |
| 702003 | $58,166 / $62,362 (loss, -$4,196) | $60,659 / $62,341 (loss, -$1,682) | Narrowed substantially |
| 702002 | $55,282 / $60,197 (loss, -$4,915) | $59,186 / $60,130 (loss, -$944) | Narrowed substantially |
| 702004 | $50,070 / $55,350 (loss, -$5,280) | $50,823 / $55,367 (loss, -$4,544) | Marginal improvement |
| 701002 | $41,577 / $50,444 (loss, -$8,867) | $41,619 / $50,479 (loss, -$8,860) | No real change |

**[VERIFIED] The fix works exactly as diagnosed for 3 of 4 close losses, confirming the mechanism directly**, and correctly has little effect on the one moderate loss (701002) that Phase 25 already flagged as dominated by a different, non-timing factor (that seed loses under every crop ratio tested in Phase 25, independent of this mechanism too).

## 4. Full 15-Seed Validation

Both the risk-posture layer (Section 2) and the endgame-timing fix (Section 3) were kept active together for the full validation, using the same methodology Phase 23/24/25 all used.

### vs. Submission G

| Statistic | Before (Phase 24/25) | After (Phase 26) |
|---|---|---|
| phase21 mean | $49,448.13 | **$50,400.87** |
| Submission G mean | $54,574.27 | $54,547.87 |
| Mean gap | -$5,126.13 (-9.4%) | **-$4,147.00 (-7.6%)** |
| **Win rate** | **6/15 (40.0%)** | **6/15 (40.0%)** |

**[OBSERVED, honestly reported, not smoothed over] The win rate stayed flat at 6/15 despite a real mean-margin improvement, because the fix's benefit on one seed was offset by a newly-introduced loss on another.** Seed 700002 flipped from loss to win, exactly as Section 3 predicted. But seed 700003 — a narrow win before this phase (+$190) — flipped to a loss (-$1,726) under the new timing. **[VERIFIED, by direct trace] Why**: in seed 700003, Submission G finished its OWN liquidation by day 28 in this particular game (unlike the other traced seeds, where G still had standing crops into day 29) — delaying agents/phase21/'s own schedule meant it was STILL harvesting on day 29 while G, already finished, banked an even larger day-29 gain ($4,796) from a different source (its own leftover maturation cycle), outpacing agents/phase21/'s delayed-but-still-smaller day-29 harvest ($2,965). **The "right" liquidation day is not a fixed constant — it depends on each game's own specific harvest-cycle phase, which the two integer thresholds moved here cannot adapt to.**

Full per-seed data: `results/phase23/phase23_vs_submission_g_results.json` (this phase's run).

### vs. Submission C (Secondary Check)

| Statistic | Before | After |
|---|---|---|
| phase21 mean | $58,141.93 | $60,706.67 |
| Submission C mean | $32,096.47 | $32,230.87 |
| **Win rate** | **14/15 (93.3%)** | **14/15 (93.3%)** — same seed (702002) still the sole loss |

No regression against Submission C; mean margin improved.

## 5. Honest Assessment

- **[VERIFIED]** Phase 25's risk-posture hypothesis for these specific close losses does not hold. Risk posture, as built and tested here, changes nothing about these games.
- **[VERIFIED]** The real mechanism is endgame-liquidation timing, and a direct fix for it produces a genuine per-game effect (confirmed by trace, not just aggregate numbers) — but the fix is a blunt, fixed-day-threshold instrument being applied to a per-game-variable problem (when a specific tile's harvest cycle actually lines up with the season's end), so it helps some games and can hurt others, netting out to an improved mean margin but an unchanged win count on this particular 15-seed sample.
- **[HYPOTHESIS, not built this phase]** A more targeted fix would likely need to be DYNAMIC rather than a fixed day threshold — e.g., stop planting/digging based on each tile's own remaining-harvest-cycles-before-day-29 (computable from `first_yield_day`/`interval` and the current day), rather than a single global day number for every tile regardless of its own planting history. This is a concrete, well-motivated next step for a future phase, not attempted here per this phase's own scope (risk posture was the assigned mechanism to build; the endgame-timing fix was pursued as the evidence-backed alternative once risk posture was directly refuted, but a full per-tile-aware redesign of the liquidation logic would be a larger change than this phase's brief authorized).
- **[NOT CLAIMED]** This phase does not claim the gap to Submission G is closed or even reliably narrowed on any future sample — a 6/15 result before and after, on the same seeds, with the underlying wins/losses partly reshuffled, is a modest, mixed result, reported as such.

## Changed Files

Modified (Phase 21's own, non-frozen agent — the standing exception for this phase):
- `agents/phase21/execution.py` (cash-safety thresholds now come from `risk_posture.posture_params` instead of fixed `$150` values)
- `agents/phase21/portfolio.py` (`LIQUIDATION_START_DAY` 27→28, `DIG_ONGOING_CROPS_DAY` 28→29)

New, additive:
- `agents/phase21/risk_posture.py`
- `scripts/phase26/trace_close_losses.py`
- `results/phase26/PHASE26_RISK_POSTURE_REPORT.md` (this file)

`results/phase23/phase23_vs_submission_g_results.json` was overwritten by re-running Phase 23's own unchanged validation script against this phase's updated `agents/phase21/` code — the pre-Phase-26 numbers are preserved in this report's own tables (Section 4). No frozen file was touched, `agents/phase15/` was not modified, and no submission is created.
