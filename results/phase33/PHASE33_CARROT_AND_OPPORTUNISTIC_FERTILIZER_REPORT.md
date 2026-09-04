# Phase 33: CARROT, Strictly Opportunistic Fertilizer, and 4th-Quadrant TOMATO/GOOSE — All Three Negative, For Different Reasons

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`). `agents/phase15/` (Submission G) and `agents/phase21/` (Submission H) are unmodified — confirmed via `git status --short`, which shows only `scripts/phase33/` and `results/phase33/` as new, untracked paths. No submission is created.

## Executive Summary

**Part A — CARROT is decisively NOT competitive with STRAWBERRY under real two-player pressure, even fully uncontested.** CARROT-vs-CARROT nets a mean final money of just **$330**; CARROT grown with zero competition at all (opponent grows STRAWBERRY instead) reaches only **$225** — both are two orders of magnitude below STRAWBERRY's own two-player-contested result of **$27,072** (reproduced fresh this phase, matching Phase 21/31's prior number exactly). CARROT's theoretical glut-resistance (`sqrt`/0.70 above-curve, T=450 — softer and higher-threshold than STRAWBERRY's `linear`/1.60, T=100, confirmed by direct read of `vendor_kaggriculture/kaggriculture.py`) never gets a chance to matter, because CARROT's base price ($35) is so far below STRAWBERRY's ($120) that even zero glut penalty can't close the gap. Per this phase's own decision rule, this result is not "competitive with the incumbent," so **Step 3 (a portfolio test) was correctly not pursued.**

**Part B — the strictly opportunistic (non-preempting) fertilizer configuration is confirmed genuinely non-preemptive by direct trace (zero violations across 2,876 turns), but is STILL a net economic loss — and a larger one than Phase 30's naive, preempting attempt** (isolated economy -26.9% vs. Phase 30's -21.3%). This is the exact "cost is coming from somewhere else" scenario this phase's own constraints anticipated: the loss is not task-priority preemption (structurally ruled out) but a **cascading, path-dependent knock-on effect** — the fertilizer/collection/fetch turns change worker position and inventory state going into subsequent turns, which measurably shifted this agent's downstream purchase timing (traced seed: BUY_ANIMAL spend +$2,800, animal-tending actions down despite more animals owned, SELL:WHEAT revenue -30%) even though no single turn ever violated the tier ordering. Per this phase's own scope, **no full 15-seed validation was run for either part** — neither cleared its own cheap screen.

**Part C — buying the 4th land quadrant (SE, $4,000) purely for TOMATO or GOOSE, serviced by dedicated new hands and leaving STRAWBERRY/WHEAT/COW/SHEEP completely untouched, is a catastrophic negative — not a marginal one.** Isolated economy collapsed to **$4,275 mean (TOMATO, -92.3%)** and **$3,292 mean (GOOSE, -94.1%)** vs. the $55,785 baseline, with 2 of 4 seeds going fully bankrupt ($0 final money, hands never even reaching double digits). Direct trace found the cause: hands in this game are **not a persistent roster — `farm["hands"] = []` resets to empty at the end of EVERY day** (`vendor_kaggriculture/kaggriculture.py::_end_of_day`), so the Fibonacci hire cost for `n_dedicated_hands` extra hands is paid **fresh every single day of the 30-day game**, not once. This recurring cost was steep enough to starve the agent of cash before it could even complete its OWN normal (unmodified) land ramp — in the traced seed, the 4th quadrant wasn't bought until day 26, four days before the game ends, far too late for either TOMATO (first_yield_day=8) or GOOSE (needs BUILD_COOP+PLACE+first_yield_day=4) to produce a single unit of revenue. Both conditions showed **zero TOMATO or EGG revenue in every one of the 4 seeds tested.**

**No submission is created for any part. Submission H remains the current best, unchanged.**

---

## PART A: CARROT in Real Two-Player Competition

### 1. CARROT's Glut Curve, Confirmed by Direct Read

`vendor_kaggriculture/kaggriculture.py` (not modified, read only):

| Crop | base | T (glut threshold, units) | above_func | above_target |
|---|---|---|---|---|
| STRAWBERRY | $120 | 100 | linear | 1.60 |
| **CARROT** | **$35** | **450** | **sqrt** | **0.70** |
| WHEAT | $25 | 400 | log | 0.20 |
| MELON | $250 | 300 | sq | 3.60 |

CARROT's `sqrt`/0.70 above-curve is materially softer than STRAWBERRY's `linear`/1.60, and its glut threshold (T=450) is 4.5x STRAWBERRY's (T=100) — CARROT should structurally be much harder to glut. Phase 8's isolated data (reused directly, `results/phase8/phase8_calibration_probe_results.csv`) already found CARROT "middling" (revenue/tile-day $12.27 at n=25, vs. STRAWBERRY's $26.15) — but Phase 8 never tested CARROT under real two-player selling pressure, which is exactly what this phase's premise (Phase 24/31's repeated finding that STRAWBERRY/COW barely crash under real competition) says could change the picture.

### 2. The Real Two-Player Test

Reused Phase 21 Step 1 / Phase 31 Step 2's exact design unchanged (`scripts/phase33/carrot_glut_experiment.py`, importing `agents/phase21/execution.py::make_execution_agent` directly, not modified): 8 hands, 2 land quadrants, 40 crop-tile target, single-crop agents, 4 development seeds, through the real engine.

| Condition | Mean final money (A) | Mean sell revenue (A) | Mean qty sold | Mean realized price |
|---|---|---|---|---|
| A=CARROT, B=CARROT (contested) | **$330** | $6,770 | 356 | ~$15.30/unit |
| A=CARROT, B=STRAWBERRY (CARROT uncontested) | **$225** | $9,566 | 477 | ~$18.00/unit |
| A=STRAWBERRY, B=STRAWBERRY (reference, reproduced fresh) | **$27,072** | $32,024 | 175 | ~$182.50/unit |

**[VERIFIED] CARROT is not competitive with STRAWBERRY under any condition tested, contested or not.** Uncontested CARROT ($225) is not even 1% of STRAWBERRY's own CONTESTED result ($27,072) — the gap is not close enough for glut-resistance to plausibly matter; it's a base-price and per-unit-realized-price gap (CARROT sells for ~$15-18/unit even essentially unopposed, vs. STRAWBERRY's ~$91-251/unit range across seeds), not a competition-driven one. **[OBSERVED]** This is the same pattern Phase 31 already found twice (TOMATO vs. STRAWBERRY, GOOSE vs. COW): a resource that is genuinely less contested still loses decisively to an incumbent whose own absolute economics are far stronger, because the incumbent doesn't crash much under real competition either.

### 3. Step 3 (Portfolio Test): Correctly Not Pursued

Per this phase's own explicit decision rule ("only if CARROT's two-player result is competitive with STRAWBERRY's ... if it's not competitive, stop at the two-player test"), CARROT's result gives no basis to expect a partial-allocation portfolio variant to help. No portfolio test was built; no head-to-head validation against Submission G was run.

---

## PART B: Strictly Opportunistic (Non-Preempting) Fertilizer

### 4. Implementation and Non-Preemption Confirmation

`scripts/phase33/fert_execution_opportunistic.py` reconstructs Phase 30's FERTILIZE/COLLECT_FERTILIZER tasks (Phase 30's own code was fully reverted and no longer exists in the repo — rebuilt from Phase 30's own report, Section 3, not literally reused) at NEW priority tiers, strictly below every tier `agents/phase21/execution.py` currently uses (confirmed by direct read: tiers top out at 3 — 0=HARVEST/HARVEST_ANIMAL, 1=WATER/FEED, 2=CARE, 3=endgame-DIG/WEED-DIG/PLANT/BUILD/PLACE):

| Task | Phase 30's tier | Phase 33's tier |
|---|---|---|
| FERTILIZE | 2 (between WATER and DIG/PLANT/BUILD/PLACE) | **4** (strictly below everything) |
| COLLECT_FERTILIZER | 4 | **5** (strictly below FERTILIZE, same relative order) |

**Structural argument for non-preemption**: the tiered greedy-assignment loop (unchanged in structure since Phase 9) processes tiers in strictly increasing order and, within a tier, cannot terminate while any unclaimed worker remains eligible for any unmatched entry in that same tier — so by construction, every worker who reaches tier 4 unclaimed is one tier 0-3 had no eligible use for that turn.

**[VERIFIED, by direct trace, not just the structural argument]** `scripts/phase33/trace_nonpreemption.py` instruments every turn: at the moment tier-4 processing begins, it counts how many tier≤3 entries remain unmatched AND are eligible for a still-unclaimed worker (i.e., a worker about to receive a fertilizer assignment that could instead have done a higher-priority task). Across all 4 development seeds:

| Seed | Turns | Fertilizer-tier actions | Preemption violations |
|---|---|---|---|
| 700000 | 719 | 181 | **0** |
| 700001 | 719 | 109 | **0** |
| 700002 | 719 | 176 | **0** |
| 700003 | 719 | 268 | **0** |
| **Total** | **2,876** | **734** | **0** |

(An initial version of this trace found 196 apparent violations, traced to a bookkeeping bug in the trace instrumentation itself — the `combined` entry pool isn't pruned of already-matched entries by the scheduler's own loop, same as `agents/phase21/execution.py`'s original code, since it doesn't need to be for scheduling correctness — the diagnostic snapshot was fixed to account for this before the number above was trusted.)

**[VERIFIED] Zero preemption violations. The strictly-opportunistic configuration genuinely never takes a worker-turn a tier≤3 task could have used.**

### 5. Fertilized-Tile-Count and Isolated Economy

`scripts/phase33/isolated_economy_fertilizer.py`, same 4 development seeds vs. `"pass"`:

| Condition | Mean final money | Mean peak fertilized tiles | Mean idle_action_fraction |
|---|---|---|---|
| baseline_no_fertilizer | **$55,785.00** | 0.0 | 0.0713 |
| opportunistic_fertilizer (this phase) | **$40,769.00** | 7.2 | 0.0662 |
| *(for reference) Phase 30's naive, preempting fertilizer* | *$43,929.25* | *11.2* | *n/a* |

**[VERIFIED, as expected by construction] Peak fertilized tiles (7.2) is LOWER than Phase 30's naive attempt (11.2)** — exactly as predicted, since this version can only use genuinely idle turns rather than competing for tier-2 priority. **[VERIFIED] This is still a net loss — and a WORSE one than Phase 30's naive attempt** (-26.9% vs. baseline, vs. Phase 30's -21.3%), despite doing strictly less fertilizing and never displacing a single higher-priority task.

### 6. Honest Diagnosis: Where the Cost Actually Comes From

Per this phase's own explicit instruction not to assume the tier fix alone explains any remaining shortfall, seed 700000 was traced in financial detail (`fertilize=False` vs. `fertilize=True`, both isolated vs. `"pass"`):

| Metric | No fertilizer | Opportunistic fertilizer | Delta |
|---|---|---|---|
| Final money | $44,610 | $41,252 | -$3,358 |
| Total income | $80,637 | $79,862 | -$775 (-1.0%) |
| Total expenditure | $38,594 | $41,534 | **+$2,940 (+7.6%)** |
| BUY_ANIMAL spend | $6,700 (COW 8, SHEEP 7) | $9,500 (COW 10, SHEEP 11) | **+$2,800** |
| SELL:WHEAT revenue | $13,703 | $9,607 | -$4,097 (-30%) |
| SELL:STRAWBERRY revenue | $19,785 | $36,935 | +$17,150 |
| Total unit actions | 6,854 | 6,588 | -266 |
| "farm" actions (PICKUP/DROP/BUILD) | 194 | 334 | +140 |
| "animal" actions (FEED/CARE/HARVEST_ANIMAL) | 469 | 405 | -64 (despite MORE animals owned) |

**[VERIFIED] The loss is driven primarily by increased EXPENDITURE, not reduced income** — total income is nearly flat (-1.0%), while expenditure rose 7.6%, concentrated in BUY_ANIMAL (+$2,800: more COWs and SHEEP were actually purchased in the fertilizer run, despite `agents/phase21/portfolio.py`'s animal-count TARGETS being identical between both runs, since `portfolio_targets` is not itself modified). **[INFERRED]** Since non-preemption is structurally and empirically confirmed (Section 4), this divergence cannot be same-turn task displacement. It is a **path-dependent cascade**: every FERTILIZE/COLLECT_FERTILIZER/associated FETCH action still consumes a real worker-turn and changes that worker's POSITION and CARRIED INVENTORY going into the next turn — in this project's tightly-coupled greedy nearest-worker/nearest-task scheduler, run over 30 days, that is enough to shift exactly when various affordability thresholds (`money >= next_cost`, `money // cost` for BUY_ANIMAL) get crossed, producing a different realized purchase quantity and timing even though no individual turn ever violated tier ordering. The "farm" action-category jump (+140, PICKUP/DROP cycles for ferrying collected FERTILIZER to/from the shed) and the drop in animal-tending actions despite MORE animals owned (dilution: more mouths, same or fewer effectively-tending turns) are consistent with this — a genuinely idle turn was not, in fact, valueless: the position and inventory state it left a worker in for the NEXT turn had a subtle downstream effect on purchase timing that this trace can observe but not fully decompose turn-by-turn.

**[VERIFIED, incidental finding] A phantom "BUY_PRODUCT:FERTILIZER" line item appears in the instrumentation's reconstructed transaction summary** ($1,088 on the traced seed) despite the agent never actually submitting a BUY_PRODUCT order for FERTILIZER (confirmed by direct inspection of the raw replay actions — zero such orders exist). This is a pre-existing gap in `instrumentation/ledger.py`'s delta-based transaction reconstruction (it doesn't recognize `COLLECT_FERTILIZER` as an explained source of a worker's FERTILIZER inventory, and infers a phantom purchase from the otherwise-unexplained delta) — a measurement artifact, not a real expenditure; `record["outcome"]["final_money"]` (the actual game-state money used for every "final money" figure in this report) is unaffected by it. Flagged here for completeness, not something this phase's scope calls for fixing.

### 7. Step 5's Decision Rule: No Full Validation Run

Per this phase's own scope ("only if isolated economy is flat-or-positive"), isolated economy for the opportunistic-fertilizer configuration is decisively negative (-26.9%), so **no full 15-seed head-to-head validation against Submission G/C was run.**

---

## PART C: TOMATO/GOOSE as a Pure Addition on the 4th Land Quadrant

### 8. Design: Genuinely Non-Competing With the Existing Portfolio

`scripts/phase33/land_expansion_execution.py` reuses `agents/phase21/execution.py`'s own `bounded_multi_crop_tile_pool_assignment` (imported, not modified) and its entire task-scheduling loop UNCHANGED. The only new logic is tile-pool splitting: the owned tile set is partitioned by quadrant (`vendor_kaggriculture.kaggriculture._quadrant_of`, read-only) into a CORE pool (NW/NE/SW — everything `agents/phase21/portfolio.py::portfolio_targets` would already plan for, passed through with its own crop_tile_target/crop_fractions/animals completely UNCHANGED) and an EXTENSION pool (SE only, the 4th quadrant, $4,000, confirmed by direct read of `agents/phase21/portfolio.py::_LAND_RUNGS = [(0,1),(6,2),(11,3)]` to be never bought by the shipped agent). The two pools are disjoint by construction — they can never compete for the same tile, so STRAWBERRY/WHEAT/COW/SHEEP are, by design, byte-for-byte what Submission H would already do. The extension pool gets a 100% TOMATO crop allocation (TOMATO condition) or up to 6 GOOSE COOPs (GOOSE condition, matching Phase 31's own isolated-GOOSE test scale). `n_hands` is the base target PLUS 2 dedicated hands (added on top, never substituted). `land_quadrants` is forced to 4 starting day 12 (else left at the base target's own value) — `agents/phase21/execution.py`'s existing BUY_LAND logic (reused unchanged) purchases quadrants strictly in `LAND_ORDER = ["NE","SW","SE"]`, so this simply requests the 4th purchase once the first three are already owned; no new land-purchase logic was needed.

### 9. Isolated Economy: A Catastrophic, Not Marginal, Negative

`scripts/phase33/land_expansion_isolated_economy.py`, same 4 development seeds vs. `"pass"`. Per this phase's own explicit framing, the bar is "does this beat NOT buying the 4th quadrant at all" — not whether TOMATO/GOOSE beats STRAWBERRY/COW on the same land:

| Condition | Mean final money | vs. baseline | Seeds reaching $0 |
|---|---|---|---|
| baseline (no 4th quadrant, as shipped) | **$55,785.00** | — | 0/4 |
| TOMATO on 4th quadrant + 2 dedicated hands | **$4,275.00** | **-92.3%** | 2/4 |
| GOOSE on 4th quadrant + 2 dedicated hands | **$3,291.75** | **-94.1%** | 2/4 |

**[VERIFIED] Both conditions are decisively negative, and two of four seeds in each condition went fully bankrupt** (final money $0.00, confirmed by direct inspection of the replay's per-turn money trajectory). **[VERIFIED] Zero TOMATO or EGG revenue was recorded in ANY of the 8 runs (4 seeds x 2 conditions)** — the new crop/animal never produced a single sellable unit.

### 10. Root Cause, Confirmed by Direct Trace

Traced seed 700000 (TOMATO condition) turn-by-turn: money fell from $3,000 (day 0) to $0 by day 5 and never recovered, with hand count stuck near 0-7 (never reaching the nominal 7-hand target for more than a few turns at a time). Traced seed 700002 (a surviving run) for WHEN the 4th quadrant was actually bought:

| Day | Quadrants owned | Money |
|---|---|---|
| 0 | NW | $3,000 |
| 11 | NW, NE | $3,654 |
| 11 | NW, NE, SW | $1,414 |
| **26** | **NW, NE, SW, SE** | $2,714 |

**[VERIFIED, by direct read of `vendor_kaggriculture/kaggriculture.py::_end_of_day`, line 880] Hands are NOT a persistent roster in this game — `farm["hands"] = []` resets to EMPTY at the end of every single day**, along with `hires_today = 0`. This means the Fibonacci hire cost (`_fib(n_already_hired_today)`) is paid **fresh every day of the 30-day game** for every hand in the target count, not once at the start. `agents/phase21/portfolio.py`'s own `_HANDS_RUNGS = [(0,5),(6,8),(10,11)]` were tuned around this recurring cost already; this phase's `+2 dedicated hands` on top of that is not a one-time $X purchase but a recurring daily tax for the entire game, and the marginal hands in a larger daily cohort sit at a steeper point on the Fibonacci curve than the base hands do.

**[VERIFIED] This recurring cost was steep enough to delay the agent's OWN unmodified land ramp**, not just the new SE purchase — NE (normally bought around day 6 per the base rungs) wasn't bought until day 11 in the traced seed, and SE (this phase's target) wasn't reached until day 26, four days before the 30-day episode ends. **[VERIFIED]** TOMATO needs `first_yield_day=8` after planting and GOOSE needs a COOP built, an animal PLACEd, and `first_yield_day=4` after that — none of this is achievable in a 3-4 day window, which directly explains the zero TOMATO/EGG revenue in every run.

**[INFERRED]** This is the same underlying mechanism Phase 32's Approach A (dedicated fertilizer hands) collapsed from, now confirmed by direct trace rather than inferred: any design that adds hands as a flat `+K` on top of an existing target is not adding a one-time cost, it's adding a recurring daily cost that compounds over the whole game — and because this project's existing hand-count rungs are already tuned close to the edge of what the agent's cash flow can sustain (Phase 30's own 7.0% idle-capacity finding), there is very little room to add MORE daily-recurring hand cost without displacing the timing of the agent's own core land/animal ramp, even when the new work itself (TOMATO/GOOSE on disjoint tiles) never competes for a single worker-turn or a single tile.

### 11. Decision: No Full Validation, No Submission

Per this phase's own scope ("If either shows a genuine net positive on the 4-seed isolated screen, validate... If it's flat or negative, report that honestly"), both conditions are decisively negative (not flat), so **no full 15-seed head-to-head validation against Submission G was run for either.**

## Verdict

- **CARROT**: not competitive with STRAWBERRY under real two-player pressure — not close, uncontested or not. [VERIFIED]
- **Strictly opportunistic fertilizer**: confirmed genuinely non-preempting by direct trace [VERIFIED], but still a net economic loss, and a worse one than Phase 30's naive preempting version [VERIFIED]. The cost traces to path-dependent purchase-timing cascades, not task-priority displacement [INFERRED, well-supported but not fully turn-by-turn decomposed].
- **TOMATO/GOOSE as a pure 4th-quadrant addition**: catastrophically negative [VERIFIED], driven by the daily-recurring Fibonacci hire cost of "dedicated hands" delaying the agent's own existing land ramp so much that the new crop/animal never had time to produce anything [VERIFIED, by direct trace of the purchase timeline].
- **None of the three is worth shipping.** No submission is created for any part.

## Changed Files

New, additive only:
- `scripts/phase33/carrot_glut_experiment.py`
- `scripts/phase33/fert_execution_opportunistic.py`
- `scripts/phase33/trace_nonpreemption.py`
- `scripts/phase33/isolated_economy_fertilizer.py`
- `scripts/phase33/land_expansion_execution.py`
- `scripts/phase33/land_expansion_isolated_economy.py`
- `results/phase33/phase33_carrot_glut_results.json`
- `results/phase33/phase33_isolated_economy_fertilizer_results.json`
- `results/phase33/phase33_land_expansion_results.json`
- `results/phase33/PHASE33_CARROT_AND_OPPORTUNISTIC_FERTILIZER_REPORT.md` (this file)

No frozen file, `agents/phase21/`, or `agents/phase15/` was touched. No submission is created — Submission H (Phase 29) remains the current best.
