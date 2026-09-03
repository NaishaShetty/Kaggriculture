# PHASE 6 — Competitive Meta Forensics V1: Final Report

Submission C is unmodified throughout this phase. No new agent, no RL, no submission was created. `git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5 agents/phase3_8` is clean.

## 1. Executive Summary

Three findings dominate this phase, in order of concrete actionability:

1. **[VERIFIED] A confirmed, currently-live bug in Submission C's tactical layer, found via this phase's forensics on our own worst real loss.** The frozen planner (`agents/phase2_6/common.py`) sets `sell_policy["horizon_aware"] = True` believing this activates a documented "F16 safety net" (force-liquidate near the season's end regardless of price) that was designed and tested in `agents/phase2_5/common.py`. **It never does** — Planner v1 imports `make_agent` from `agents/phase2_4/common.py` directly, and that module's own `_sell_quantity` function never reads the `horizon_aware` key at all; only `agents/phase2_5/common.py`'s separate wrapper does, and Planner v1 never calls it. In our single worst real episode (episode 104797306, opponent "Lai Eu Wen", final score us $0 vs them $104,569 — the largest margin loss in all 34 recorded real episodes), this is not a hypothetical: we issued **zero SELL orders across all 720 turns**, while 59 units of harvested MELON sat in the shed from day 12 to day 29, because the market's threshold-selling condition (price ≥ base) was never met after an early two-player MELON glut, and the safety net that should have forced liquidation on the final days simply isn't wired in. A sweep of all 34 real episodes found this exact zero-sell freeze in 1 other case (0 of 32 readable episodes besides this one show a *stuck, inventory-holding* freeze — Arum Puri's separate $0 episode had an empty shed, a different, already-documented failure mode). This is a mechanical defect, not a strategy gap, and is independent of everything else in this report.
2. **[OBSERVED, n=4] Every strong real opponent examined converges on STRAWBERRY, not MELON, as its dominant crop by mid-game**, despite Submission C's own economic calibration (`revenue_per_tile_day`: MELON=69.49 > STRAWBERRY=42.88) treating MELON as the stronger anchor. This held across all 4 opponents studied (Lai Eu Wen, moushun chen, Achille Gohin, Zach Locke) — a consistent, non-overfit pattern, not a single-episode artifact.
3. **[VERIFIED, mechanic] Hands reset to zero every in-game day and must be re-hired daily** (`vendor_kaggriculture.kaggriculture._end_of_day`: `farm["hands"] = []`), which the frozen tactical layer already handles correctly (`agents/phase2_4/common.py`, comment: "hands reset daily"). Strong real opponents sustain 8-13 hands *every single day* for most of the game, meaning they pay the Fibonacci hire-cost curve (which gets steep fast: hiring the 13th hand in one day costs `fib(13) x mult`) **fresh, every day**, for a large fraction of the season. Phase 2.3's "diminishing returns beyond 2-3 hands" finding was measured at hand counts 0-4 — it was never tested in, and does not speak to, the 8-13-hands-per-day regime real strong opponents actually operate in. This is not a refutation of Phase 2.3; it is evidence the two findings describe different regimes.

**MTN could not be analyzed.** No episode tagged, named, or attributable to "MTN" exists anywhere in `COMPETITION RESULTS/` (34 real episodes checked; team names extracted from each episode's public `info.TeamNames` metadata). Episode `104816153`, specifically requested, is not present in this repository. Section 3 documents this and the substitution used instead: the actual strongest real opponent in our data by final bank (Lai Eu Wen, $104,569, also incidentally the episode above) plus 3 other strong/notable real opponents (moushun chen, Achille Gohin, Zach Locke).

## 2. Data Sources

| Source | Used for |
|---|---|
| `vendor_kaggriculture/kaggriculture.py` (engine source) | DOCUMENTED/VERIFIED mechanics: hand-reset-daily, market price formula, HIRE cost curve, tile/board structure |
| `COMPETITION RESULTS/SUBMISSION {A,B,C}/*.json` (34 real, uploaded Kaggle replay files) | All OBSERVED data in this report |
| `economic_model/model.py`, `agents/phase2_x/`, `agents/phase3_x/` (existing repo implementation) | Cross-referencing our own agent's actual behavior against replay evidence |
| Official Kaggriculture rules/README | Consulted; no discrepancy found with the engine source for anything analyzed here |
| Public competitor material outside the repo | Not used — none was needed or available within rules |

No opponent's private state (shed, seeds, carried inventory, or literal submitted action) was read for opponent-side analysis at any point — see Section 15/`scripts/phase6/phase6_regression_tests.py`'s `test_no_private_leakage`.

## 3. Replay Coverage

35 real, completed episodes are present across Submissions A (19), B (14), C (2). Team names (public `info.TeamNames`) were successfully extracted for 33 of the 35 (2 Submission A files hit a text-encoding error in this environment, unrelated to their content, and were not re-attempted, since neither opponent was a top performer by final money); **none of the 33 readable episodes is "MTN"**. The 2 Submission C episodes are the only real data on the current frozen champion.

Note on Submission C's real-data sample size: **n=2**. Any conclusion about Submission C's real-world behavior in this report is drawn from only 2 games — explicitly flagged wherever it matters (Section 11).

**Substitution used for "MTN" throughout this report**: since the requested episode/opponent does not exist locally, Part 2's "MTN deep forensic analysis" and Part 9's "MTN vs C" comparison instead use the actual strongest available real opponent, **Lai Eu Wen** (final bank $104,569, episode 104797306) — which has the added property of being a genuine Submission C episode, so the "vs C" comparison in Section 11 is not a proxy pairing but the literal same game. Section 12 additionally covers moushun chen, Achille Gohin, and Zach Locke as the other 3 highest-final-bank real opponents with full-episode data quality (excluding 2 files with a non-ASCII-name read error, not investigated further as they were not top performers).

## 4. Day-by-Day Strategy: Lai Eu Wen (substituting for MTN)

Full data: `results/phase6/lai_eu_wen/days_opponent.csv`. Selected days (all fields OBSERVED, extracted from public `farms[opponent]` state only):

| Day | Bank | Hands | Animals (C/S/G) | Land | Crop mix (tiles) | Fertilized | Notable event |
|---|---|---|---|---|---|---|---|
| 0 | $108 | 5 | 0/0/0 | 2 | WHEAT 11, CARROT 2, MELON 19 | 0 | Starts with 2 land quadrants already (not the default 1) |
| 1 | $65 | 7 | 0/0/0 | 2 | WHEAT 15, CARROT 6, MELON 20 | 0 | First labor expansion (5→7) |
| 3 | $51 | 2 | 0/0/0 | 2 | WHEAT 15, CARROT 4, MELON 20 | 0 | Cash trough; hands cut back to 2 (can't afford re-hiring the prior day's count) |
| 4-9 | $92→$58 | 8-12 | 0/0/0 | 2 | ~WHEAT 8-12, MELON 25 | 0 | Setup/thrashing phase: hands oscillate 8-12, bank stays under $600 the entire time |
| **10** | **$8,903** | 12 | 5 (3C/2S) | **4** | WHEAT 18, CARROT 6, MELON 6, STRAWBERRY 2 | 0 | **First major inflection: land 2→4 (all 4 quadrants) AND first animals AND a $8,845 single-day bank jump, simultaneously** |
| 11-14 | $10.6k→$10.3k | 13 | 7→13 | 4 | MELON share collapsing, STRAWBERRY rising (2→20 tiles) | 0 | Animal count nearly triples in 4 days (7→13); portfolio pivots hard toward STRAWBERRY |
| 15-20 | $12.2k→$33.6k | 13 (held) | 13 (held) | 4 (held) | STRAWBERRY 20-30, WHEAT 33-51, MELON falling to 0 | 0 | **Acceleration phase**: hands/animals/land all plateau at their maximum, bank grows fastest here (deltas $1.3k-$7.9k/day) |
| 21-27 | $40k→$85.2k | 13 | 12-13 | 4 | WHEAT 16-53, STRAWBERRY 25-29, MELON 0 | 0 | Sustained compounding; MELON fully abandoned |
| 28-29 | $93k→$104.6k | 13→8 | 12 | 4 | Crop tiles collapse 21→12 (harvest/liquidation) | 0 | **Endgame transition**: crop tile count falls sharply (converting standing crops to shed/sold), hands drop 13→8 on the final day |

**Discovered phases (not assumed in advance):** (a) days 0-9, a noisy, cash-constrained **setup phase** with land/labor churn and no animals; (b) day 10, a **single-turn inflection** combining land expansion, first animal purchase, and the first large cash inflow; (c) days 11-14, a **rapid animal build-out** (7→13 in 4 days); (d) days 15-27, a **sustained compounding/acceleration phase** with labor/animals/land held constant at their peak and bank growing at an increasing rate; (e) days 28-29, a short **endgame liquidation** transition.

**Fertilizer: never used, 0 tiles fertilized on any day of the entire game**, despite holding 12-13 animals (which make `fertilizer_available` true on their tile) for most of the game — see Section 6.

## 5. MTN (Lai Eu Wen) Capacity Analysis

[VERIFIED_MECHANIC, from engine source] Hands reset to `[]` every day (`_end_of_day`); `agents/phase2_4/common.py` already re-hires to a target count daily (`need_hire = max(0, n_hands - current_hands)`), and hire cost is `sum(fib(current_hands+i) for i in range(need_hire))` — a **Fibonacci curve paid fresh every day**, not a one-time cost.

Lai Eu Wen holds **13 hands for 15 of the 30 days** (days 11, 13-27; the days-11-14 ramp went 13→13→13→13). At 13 hands, hiring from 0 that day would cost `fib(0)+fib(1)+...+fib(12) = 1+1+2+3+5+8+13+21+34+55+89+144+233 = 609` (times `mult`, VERIFIED default mult=1) *per day, every day* — a recurring daily labor bill an order of magnitude larger than anything Phase 2.3's tested range (0-4 hands) ever paid.

[INFERRED] Phase 2.3's "diminishing/negative returns beyond 2-3 hands" finding cannot be directly compared to this regime: it measured marginal value at hand counts 0-4 for a MELON-focused portfolio with **1 land quadrant**. Lai Eu Wen's 13-hand phase runs concurrently with **4 land quadrants** (100 tiles) and up to **83 crop tiles + 13 animals** simultaneously needing daily water/feed/care/harvest actions — a fundamentally larger action-demand surface than anything the 1-quadrant, MELON-solo Phase 2.3 sweep tested. **We were measuring a different economic regime, not a wrong one** — this reframes, and does not overturn, the earlier finding, per this phase's instruction.

**Direct worker value vs. system/capacity value**: cannot be separated from this replay data alone — the replay records only farm-level state (bank, tile counts, hand count), not which specific hand performed which action each turn. [HYPOTHESIS, not measured]: the value of hands 5-13 is plausibly dominated by *system/capacity effects* (more simultaneous watering/harvesting/feeding across 60-83 tiles and 12-13 animals, preventing missed-maintenance decay) rather than *direct per-hand output*, because Phase 2.3's own marginal-hand-value curve for MELON already goes negative by the 4th hand in a small-portfolio context — the large-scale regime's hands are doing something Phase 2.3 never modeled (maintaining a much bigger board), not simply "more of the same thing that already had negative marginal value." **This is not confirmed by this phase's data** — it would require an experiment that logs per-hand action assignment, which the replay format does not provide. Listed as Experiment 1 in Section 14.

**Marginal capacity per worker**: not computable from this dataset at the needed resolution (would require per-turn attribution of harvest/water/feed actions to individual hands, not available in the replay's farm-level aggregates). Labeled UNKNOWN, not estimated.

## 6. Capital Deployment Analysis

Lai Eu Wen's bank never exceeds $600 through day 9 (9 days of a 30-day game, cash-constrained the entire time), then jumps to sustained 4-5-figure daily growth from day 10 onward. This is a clear, OBSERVED **short-term cash sacrifice pattern**: hands are hired to 8-12 as early as day 4-9 while bank sits under $600 (implying purchases are financed nearly hand-to-mouth, immediately after each day's income, not from an accumulated reserve) — this is "invests before/regardless of a cash cushion," not "preserves a large reserve." The land-quadrant purchases (culminating in all 4 by day 10) and the first animal purchases land exactly at the point where this investment starts paying off, consistent with "accept short-term cash sacrifice to build a higher future production rate," though the replay data alone cannot separate cause from coincidence for this single episode (n=1 for this specific claim; the "sustained high hands + high land + high animals" *pattern* is corroborated across all 4 opponents in Section 10, but the specific "hand-to-mouth financing" claim is only directly OBSERVED in this one episode).

**Cost → first return / cost → cumulative return** for major investment classes: not reliably computable from public data alone for the opponent (their per-purchase cost is observable via the LAND_PRICES/hire-cost constants, VERIFIED_MECHANIC, but the REVENUE attributable to a specific investment cannot be separated from simultaneous other activity using bank-delta alone). Left as UNKNOWN rather than approximated with a fabricated attribution model.

## 7. Resource Interaction / Farm Economic Loop Analysis

| Loop | Status (Lai Eu Wen) | Status (other 3 opponents) |
|---|---|---|
| LABOR → more maintenance → more harvest → more revenue | [INFERRED] consistent with the data (crop tile count peaks at 83 only once hands=13; bank growth is fastest exactly during the 13-hands/13-animals plateau) | Consistent pattern, not separately isolated |
| ANIMALS → products → revenue | [INFERRED] animal count and bank both rise together from day 10; cannot separate animal-product revenue from crop revenue in aggregate bank-delta data | Same limitation |
| ANIMALS → fertilizer → crops → harvest → revenue | **[OBSERVED: NOT USED]** `fertilized_tile_count = 0` for every single day of the entire game, despite `fertilizer_available=True` being set on animal tiles most of the game | **[OBSERVED, 3 of 4]** moushun chen and Zach Locke also show 0 fertilized tiles all game; only Achille Gohin used it, and only lightly (max 6 tiles, 17/30 days). **This loop is NOT a consistent signature of strong play in this sample — reject as a general explanation.** |
| LAND → more productive tiles → more labor demand → production → revenue | [OBSERVED] land 2→4 and hands ramping to 12-13 land within the same 1-2 day window (day 9-11) | Achille Gohin: land 1→3→4 at days 12-19, hands held flat at 5 the whole time (land expanded WITHOUT a parallel labor increase) — **this loop does NOT hold uniformly**; at least one strong opponent decoupled land expansion from labor scaling entirely. |
| HIGH LABOR → increased parallelism → higher production capacity | [HYPOTHESIS] plausible given the timing coincidence in Section 5, not independently measured | Not measured |

## 8. Portfolio Analysis

Trajectory (crop tile counts) at Day 1/5/10/15/20/25/29, all 4 opponents, full tables in `results/phase6/*/days_opponent.csv`. Summary:

| Opponent | Day 1 dominant crop | Day 15 dominant crop | Day 29 dominant crop | Pattern |
|---|---|---|---|---|
| Lai Eu Wen | MELON (20) + WHEAT (15) | WHEAT (33) + STRAWBERRY (20) | STRAWBERRY (12, everything else liquidated) | MELON abandoned by ~day 20; converges on WHEAT+STRAWBERRY |
| moushun chen | MELON (12) | STRAWBERRY (20), MELON=0 | STRAWBERRY (26) | Full MELON→STRAWBERRY switch by day 15, held to the end |
| Achille Gohin | MELON (5) + WHEAT (5) | WHEAT (4), MELON (2) | WHEAT (5), STRAWBERRY (1) | Smallest crop footprint of the 4 (labor stayed flat at 5 hands); modest, mixed |
| Zach Locke | WHEAT (31) + MELON (11) | STRAWBERRY (24), MELON (7) | STRAWBERRY (6, mostly liquidated) | WHEAT→STRAWBERRY pivot by day 15 |

**[OBSERVED, n=4, no exceptions]: MELON is abandoned or reduced to a minority share by every strong opponent by day 15-20, in favor of STRAWBERRY.** This directly contradicts our own `economic_model.model.CALIBRATION["revenue_per_tile_day"]` ranking (MELON 69.49 > STRAWBERRY 42.88), which underlies Planner v1's MELON-anchored default and every scaling/substitution response's implicit ranking. None of the 4 opponents diversify broadly (no opponent runs 3+ crops at meaningful scale simultaneously past the early game) — they **specialize**, but the specialization target is consistently STRAWBERRY, not MELON.

## 9. Market / Selling Analysis

**Our own side (OBSERVED, exact — read from our own submitted actions, never the opponent's):** across all 34 real episodes, we issued 0-34 SELL orders per game; the Lai Eu Wen episode is one of exactly 2 episodes with 0 sells all game (the other, Arum Puri, is a different, already-documented failure mode — empty shed, not stuck inventory). See Section 1/12 for the mechanism (dead `horizon_aware` wiring).

**Opponent side (INFERRED only — quantity/price/timing of opponent sales cannot be directly observed without their private action; only net bank-delta is public):** Lai Eu Wen's bank delta is negative on 4 of the first 9 days (setup-phase net spending exceeding income) and strongly, increasingly positive from day 10 onward (see Section 4 table) — consistent with, but not proof of, a shift from "mostly buying" to "mostly selling" exactly at the land/animal expansion inflection. We cannot determine batch size, timing relative to price peaks, or whether sales were split, because none of those require money to change in an separable way from simultaneous purchases.

**On F-003 (opportunistic_market_exit_timing):** cannot be newly confirmed or refuted for these 4 opponents with public data alone — the same limitation applies. This finding remains at its previously-established evidence level (1 confirmed instance, Vishwanath N Iyer, from Phase 3.7 — not revisited here).

## 10. Opponent Acceleration Analysis

Full first/second differences: `results/phase6/*/velocity_opponent.csv`. For Lai Eu Wen (Δbank/day, smoothed by eye from the table in Section 4): near-zero or negative through day 9, a single large positive spike at day 10 (+$8,845), then a **sustained, mostly-increasing** Δbank/day from day 15 (+$1,251) to day 29 (+$11,557) — i.e., **positive second-order acceleration (Δ²bank > 0) for most of days 15-29**, not just sustained linear growth. Δhands/day and Δanimals/day are both large and positive only in the days 10-14 window, then flatten to ~0 for days 15-27 (a plateau, not continued acceleration) — **the bank's acceleration phase (days 15-29) is decoupled in time from the resource-acquisition acceleration phase (days 10-14)**: labor/animal/land growth happens FIRST and bank acceleration follows with a lag, not simultaneously. This is a genuine, discovered pattern (not assumed), consistent with a "build capacity, then harvest the compounding return" strategy rather than continuous simultaneous scaling.

## 11. MTN (Lai Eu Wen) vs Submission C Comparison

Same episode (104797306), both sides, at the required day markers (full table, Section 4 + our own days_self.csv):

| Day | Opp bank | Opp hands/land/animals | Us bank | Us hands/land/animals |
|---|---|---|---|---|
| 1 | $65 | 7/2/0 | $630 | 2/1/2 |
| 3 | $51 | 2/2/0 | **$0** | 2/1/2 |
| 5 | $382 | 8/2/0 | $0 | 0/1/0 |
| 10 | $8,903 | 12/4/5 | $0 | 0/1/0 |
| 15 | $12,245 | 13/4/13 | $0 | 0/1/0 |
| 20 | $33,596 | 13/4/13 | $0 | 0/1/0 |
| 25 | $68,701 | 13/4/12 | $0 | 0/1/0 |
| 29 | $104,569 | 8/4/12 | $0 | 0/1/0 |

**WHAT DECISION CREATED THE DIVERGENCE?** Not, primarily, the opponent's day-10 expansion. **We were already at $0, with 0 hands, by day 3-5** — 5-7 days *before* the opponent's own inflection point. Our side's collapse matches the already-documented NEW-F-005 death-spiral pattern (Phase 3.7): rapid early cash exhaustion, hands falling to 0 and never recovering. What is NEW here is that our side **did eventually harvest 54-59 units of MELON** (shed inventory appears from day 11 onward) — a partial recovery of the death-spiral's production side — but the Section 1 sell-freeze bug converted that harvest into permanently stranded, unrealized value instead of a cash recovery. **The true divergence has two separable causes: (a) an early cash collapse by day 3 (pre-existing NEW-F-005 pattern, cause still not fully diagnosed per Phase 3.7), compounded by (b) a confirmed bug preventing any of the harvested production from ever converting to cash.** The opponent's own day-10-onward performance is a genuinely strong, independent reference trajectory, but in this specific episode it was not competing against a "normally functioning but out-scaled" Submission C — it was competing against a Submission C that had already, separately, failed.

## 12. Other Strong-Opponent Comparison

Grouping by OBSERVED characteristics (not forced categories):

| Opponent | Peak hands | Peak land | Peak animals | Dominant crop | Category |
|---|---|---|---|---|---|
| Lai Eu Wen | 13 | 4 | 13 | STRAWBERRY | high-labor + high-land + high-animal (all three at once) |
| moushun chen | 10 | 3 | 14 | STRAWBERRY | high-animal, moderate-labor/land |
| Achille Gohin | 5 | 4 | 10 | WHEAT/mixed, low volume | high-land, LOW-labor (decoupled from land, see Section 7) |
| Zach Locke | 8 | 2 | 12 | STRAWBERRY | high-animal, moderate everything else |

No opponent in this sample is "market-aggressive" or "low-footprint/high-efficiency" in a way distinguishable from the others using only public data — those categories from the brief's suggested list are **not supported by this evidence** and are not forced. The clearest, most consistent category across all 4 is **animal-heavy (10-14 animals) + STRAWBERRY-anchored**, which subsumes the "high-labor" and "high-land" variation as secondary axes that differ per opponent (Achille Gohin proves high-land does not require high-labor).

## 13. Competitive Meta Table

| Mechanism | Observed in top agents | Observed in C | Evidence strength | Likely competitive importance | Test needed |
|---|---|---|---|---|---|
| STRAWBERRY (not MELON) as anchor crop at scale | 4/4 | No (MELON default) | OBSERVED, n=4, no exceptions | High | Re-run Phase 2.2's revenue_per_tile_day calibration sweep at large tile counts specifically for STRAWBERRY vs MELON under 2-player market pressure |
| Sustained 8-13 daily hands (paid fresh every day) | 3/4 (Achille Gohin stayed at 5) | No (our real episodes show n_hands targets of ~5, per Submission B/C's scaling response threshold) | VERIFIED mechanic + OBSERVED trajectory | High, but regime-dependent (see Section 5) | Experiment 1, Section 14 |
| Animal count 10-14 sustained | 4/4 | Partial (Submission C's animal response tops out around 3, per `agents/phase3_8/animal_response.py`'s HIGH_RESPONSE_ANIMALS) | OBSERVED, n=4 | High | Experiment 2, Section 14 |
| Animal→fertilizer→crop loop | 1/4 (weakly) | No | OBSERVED, REFUTED as a general pattern | Low (contrary to the brief's example hypothesis) | None needed — deprioritize |
| Land expansion decoupled from labor | 1/4 (Achille Gohin) | Untested (land response was explicitly rejected in Phase 3.6/3.7) | OBSERVED, single case | Unknown | Would need more high-land, low-labor real examples; none currently available |
| A build-then-harvest acceleration lag (resource growth precedes bank acceleration) | 1/4 directly measured (Lai Eu Wen) | Not applicable (C never reaches a comparable scale in available real data) | OBSERVED, single case | Medium (plausible general pattern, not confirmed) | Would need per-turn attribution data this replay format cannot provide |
| Dead `horizon_aware` sell-safety wiring | N/A (opponent-side, not applicable) | **Yes — confirmed bug in the live champion** | VERIFIED (code + data cross-check) | **Critical** (single worst real loss traced directly to this) | Fix verification: re-run the Lai Eu Wen episode's exact market conditions with the wiring fixed and confirm SELL orders fire near day 29 |

## 14. Confirmed Architectural Gaps

**A. CONFIRMED GAPS**
1. `agents/phase2_6/common.py`'s `horizon_aware` sell-safety flag is set but never consumed — a live, currently-shipping bug, not a strategic limitation. [VERIFIED]
2. C cannot commit to labor/animal scale comparable to strong real opponents (Submission C's scaling/animal responses cap around 5 hands / 3 animals; strong opponents sustain 8-13 hands / 10-14 animals) — this is a genuine ceiling in the current response design, separate from the Section 5 regime question of whether that scale is even affordable/beneficial for us specifically. [OBSERVED gap, VERIFIED as a config-level ceiling by reading `agents/phase3_5/response_policy.py` and `agents/phase3_8/animal_response.py`'s constants]
3. C's crop-substitution/response layers (Variant D, animal response) have no mechanism that would ever select STRAWBERRY as the PRIMARY (not substitute) anchor crop — Planner v1's default is MELON-first, unconditionally. [CONFIRMED by reading `agents/phase2_6/common.py`'s default candidate generation]

**B. STRONG HYPOTHESES**
1. Hands 5-13 in a strong opponent's build derive most of their value from system/capacity effects (parallel maintenance across a much larger board), not from the same kind of marginal per-hand output Phase 2.3 measured at small scale.
2. A "build capacity first (days ~10-14), harvest compounding growth after (days ~15-29)" staged strategy outperforms continuous simultaneous scaling — observed once (Lai Eu Wen), plausible as a general pattern, not confirmed at n=1.
3. Our own real-data sample (n=2 for Submission C) is too small to know whether the Lai Eu Wen bug (dead sell-safety net) is a rare edge case or a meaningfully-probable outcome against any opponent that also floods the MELON market early.

**C. UNKNOWN**
1. Direct worker value vs. system/capacity value (Part 3's central ask) — not separable from farm-level replay aggregates; would need per-turn, per-hand action-assignment data this format does not expose.
2. Cost→first-return / cost→cumulative-return for opponent investment classes — not separable from aggregate bank-delta alone.
3. Whether F-003 (opportunistic market exit timing) generalizes beyond its 1 previously-confirmed instance — this phase found no new public-data method to confirm or refute it for additional opponents.
4. Whether the STRAWBERRY-over-MELON pattern (Section 8) holds beyond this 4-opponent sample, or whether it's specific to the particular seeds/market conditions these 4 games happened to have.

## 15. Engineering / Test Compliance

New, additive code only:
- `agents/phase6/replay_forensics.py` — the reusable parser/analytics pipeline (Section 1 requirement)
- `scripts/phase6/run_forensics.py` — the runner that produced every CSV/JSON referenced above
- `scripts/phase6/phase6_regression_tests.py` — **31/31 passing**, covering: replay parsing, player separation, day aggregation, market/worker/animal/crop extraction, no-private-leakage (explicitly asserts opponent snapshots never carry shed/seed/inventory/own-action data), and deterministic re-analysis.

No frozen file was modified. No opponent private state (shed, carried inventory, seeds, or literal submitted action) was read for opponent-side analysis anywhere in this pipeline — verified both by code construction (Section on observability discipline in `agents/phase6/replay_forensics.py`'s docstring) and by an explicit passing test.

## 16. RL Readiness Assessment

| Dimension | Assessment |
|---|---|
| State space | Large but enumerable (bank, hands, land, per-crop tile counts, per-animal counts, market inventory/prices for 9 items) — tractable for a model-based approach; not obviously requiring learned representations |
| Action space | Small, structured, mostly discrete (HIRE, BUY_LAND, BUY_SEED, BUY_ANIMAL, SELL with quantity, movement) — well-suited to explicit search/heuristics |
| Macro action space | Not yet defined by this project (portfolio/scale "modes" have been hand-designed per phase, not learned) |
| Reward design | Final-bank-relative-to-opponent is a clean, low-ambiguity terminal reward; no reward-shaping work has been attempted or is obviously needed for a non-RL approach |
| Credit assignment | **This phase's single biggest blocker for any learned approach**: the replay format provides no per-turn, per-hand action-outcome attribution, meaning even understanding OUR OWN past games' turn-by-turn causal structure well enough to build a credit-assignment-aware reward is currently not possible without new instrumentation (which would require modifying frozen files this phase was told not to touch, or running fresh self-play with denser logging) |
| Opponent model | 34 real games total (n=2 for Submission C specifically); nowhere near enough diverse real self-play data to train against a realistic opponent distribution. Synthetic archetypes (Phase 3.1-3.8) are already known (project history) to be unable to reach the resource scale (13 hands, 13 animals) real strong opponents reach. |
| Training distribution | Would currently have to be synthetic-archetype-only, which this project's own history has repeatedly found cannot replicate real-opponent behavior at the scale that matters (see Section 5) |
| Simulator fidelity | High for the parts we've verified (market pricing: exact, per Phase 4/5's live validation) — but the simulator IS the real engine here, not a separate model, so this is not actually a blocker in the way it would be for an external simulator |
| Compute requirements | Not assessed (out of scope given the recommendation below) |
| Offline data availability | 34 real episodes, of which 2 involve the current champion — far below what any RL approach (tabular or deep) would need for reliable policy learning, and this phase found no reason to expect that number to grow quickly |

**Recommendation: (A) Model-based macro controller.** The evidence does not support RL of any form at this time — not because RL is unfashionable, but because two of RL's basic prerequisites are absent: (1) no credit-assignment-capable data exists yet (Section 16, "Credit assignment" row) and manufacturing it would require exactly the kind of new instrumentation and possibly frozen-file changes this phase was told to avoid, and (2) the offline data volume (34 games, 2 on the current champion) is far too small for either tabular or deep RL to generalize, while this phase's forensics (Sections 8, 10-13) instead point to concrete, hand-specifiable regularities — a consistent anchor-crop choice, a consistent animal-scale target, a build-then-harvest staging pattern — that a deterministic model-based controller can encode directly, with much less data and much more auditability, matching this project's established discipline of preferring evidence-grounded, explainable mechanisms over black-box learning. Hierarchical RL (B) is not ruled out forever, but is premature until (1) is resolved. Full end-to-end RL (C) is not justified by any evidence gathered in this project's history to date.

## 17. Ranked Experiments To Run After Forensics

Ranked by ability to falsify a major assumption cheaply:

1. **[HIGHEST PRIORITY, not really an "experiment" — a verified bug]** Confirm the `horizon_aware` dead-wiring bug (Section 1) reproduces deterministically by re-running the Lai Eu Wen episode's exact seed against a synthetic opponent calibrated to also flood the MELON market early, and verify SELL orders are still absent. **Pass condition**: 0 SELL orders confirmed again under the same conditions with a patched-nothing control. **Fail condition**: SELL orders appear, meaning the real bug is somewhere else (e.g., configuration-dependent, not a pure wiring gap) and this report's Section 1 diagnosis needs revision. (This experiment does not touch or fix C — it only reproduces the finding under controlled conditions, consistent with this phase's "do not modify C" rule.)
2. **High-scale labor capacity re-test.** HYPOTHESIS: marginal hand value at 8-13 hands, on a large (3-4 quadrant) board, is positive (unlike the negative marginal value found at 4 hands on a 1-quadrant board). CONTROL: current Phase 2.3-style single-crop, 1-quadrant sweep. VARIABLE: hands 5-13 on a 3-4 quadrant board. METRIC: marginal $ per additional hand. SEEDS: development set, n=4. PASS: marginal value stays positive through hand 10+. FAIL: marginal value goes negative before hand 8, confirming the regime difference is about something other than board size.
3. **STRAWBERRY-vs-MELON anchor-crop re-calibration**, at the tile scale (20-30 tiles) strong opponents actually commit to, not the small reference scale (`n_tiles=10`) the current calibration uses. PASS: STRAWBERRY's revenue-per-tile-day at 25 tiles, market-impact-adjusted (reusing the Phase 4/5 verified simulator), exceeds MELON's. FAIL: it does not, meaning the 4-opponent pattern (Section 8) has a cause other than raw crop economics (e.g., a mechanic advantage this project hasn't identified yet).
4. **High-scale animal capacity re-test** (10-14 animals vs. Submission C's current 2-3 cap), same structure as Experiment 2, for animal marginal value instead of hand marginal value.
5. **Labor × land interaction** at the scale Achille Gohin demonstrates (4 land quadrants, only 5 hands) — does land expansion without labor scaling actually work, or did Achille Gohin simply lose less badly than the 3 higher-labor opponents (compare final banks directly: Achille Gohin $76,076 vs. Lai Eu Wen $104,569 — Achille Gohin's LOWER final bank among the 4 is at least consistent with, though does not prove, land-without-labor being the weaker of the observed strategies).
6. Labor × animal interaction, crop × labor interaction, animal × fertilizer × crop loop (already weakly refuted, Section 7 — low priority), aggressive early capital deployment, selling timing/batch size, portfolio allocation under market pressure, macro strategy vs. Planner v1 — all listed per the brief's required coverage but ranked below the above 5 given this phase's evidence; **not run this phase** to avoid the scope explosion the brief explicitly warns against.

## 18. Recommended Architecture For Next Phase

**Immediate, separate, minimal-scope action (not this phase, not a new submission by itself): fix the `horizon_aware` wiring bug.** This is a 1-2 line change (make Planner v1 route sell-quantity decisions through the already-written, already-tested `agents/phase2_5/common.py` mechanism, or port its check directly into `agents/phase2_4/common.py`) with a pre-existing, already-validated fallback design — the highest-confidence, lowest-risk improvement identified in this entire project's history, because it is a bug fix restoring INTENDED behavior, not a new strategic bet.

**For the next strategic phase**: a model-based macro controller (per Section 16), built around the two most robust findings here — (a) an anchor-crop choice informed by the market-impact simulator at realistic scale rather than the current small-reference calibration, and (b) a labor/animal capacity target that can reach the 8-13/10-14 range strong opponents operate in, IF Experiments 2 and 4 confirm positive marginal value at that scale (do not build this capability speculatively before that evidence exists).

## 19. Limitations

- MTN itself was never analyzed — no data exists locally. Every "MTN" finding in this report is drawn from a substitute (Lai Eu Wen), which is the strongest available real opponent but is not confirmed to be the same entity, playstyle, or skill tier as the specifically-requested MTN.
- Submission C's real-world sample is n=2 games. Every "C" claim in this report should be read as "observed in 2 real games," not as a general characterization of Submission C's behavior.
- Opponent-side selling behavior (timing, batch size, price-relative-to-peak) cannot be directly observed with only public replay data — every claim about it here is explicitly labeled INFERRED, at best.
- Direct per-hand/per-action value attribution is not possible with the replay format as-is; several "capacity vs. direct value" questions the brief explicitly prioritized (Part 3) remain UNKNOWN, not answered, for this reason.
- All patterns in Sections 8/12/13 are drawn from 4 opponents. This is enough to say a pattern is "not a single-episode artifact," not enough to say it is universal.
