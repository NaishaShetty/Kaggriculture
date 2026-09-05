# Phase 39: Matched-Scale Execution-Efficiency Report

## Executive Summary

**[VERIFIED]** At matched resource scale (3 land quadrants, 11-12 hands — the
scale Submission I already ships, and the scale real gold-tier opponent Crop
Dusta plays at), Submission I does **not** show a tile-idle-time or
animal-servicing gap versus Crop Dusta. If anything Submission I is
**measurably more attentive at the tile level**: mean tile-idle fraction
0.069 vs. Crop Dusta's 0.470 (a tile is "idle" if unwatered or carrying
unharvested ripe yield at end-of-day — Phase 10's own definition, reused
unchanged). Animal servicing rate is close (0.707 vs. 0.757). The
hypothesis this phase set out to test — that a genuine execution-throughput
gap explains the real-vs-synthetic pattern — is **refuted in the specific
form hypothesized (tile idle-time / animal servicing)**.

**[OBSERVED]** A real net-dollar-throughput gap does exist in the raw
numbers (Submission I's own isolated runs average $2,113-$4,034 net/day at
matched scale vs. Crop Dusta's $3,036 and $7,516/day across its two real
episodes), but **[INFERRED]** normalizing by active crop-tile count — the
metric that actually answers "how much money gets extracted per unit of the
SAME land and labor" — shows this gap is **not systematic**: Submission I's
$/crop-tile/day (49.9-81.6, mean ≈63) is statistically indistinguishable
from Crop Dusta's own **balanced-mix** game (105373474: 62.3), and only
Crop Dusta's **STRAWBERRY-dominant** game (105341441: 298.6) is a large
outlier — nearly 5x every other data point in this measurement, ours or
theirs. With n=2 real episodes, one high outlier cannot be distinguished
from a genuinely superior sustained strategy Submission I hasn't found, or
from ordinary game-to-game variance (this project has flagged the
small-sample-generalization risk before — Phase 17, Phase 25).

**Bottom line: no clear, narrowly-scoped fix presents itself.** Per this
phase's own stopping rule, no fix was built. The recommendation is a future
phase, not a submission.

## 1. Method

Two downloaded real gold-tier episodes
(`results/phase34/raw_replays/105373474.json`,
`.../105341441.json`) were parsed with
`agents/phase6/replay_forensics.py::extract_episode_timelines` (reused
unchanged), treating Crop Dusta as the **opponent** timeline in both (viewer
= Crop Dusta's real human opponent in each game — "Knight of Favonius" in
one, "Jesse Bullard" in the other). This means every Crop Dusta field read
here comes from `farms[opp_idx]`, marked PUBLIC by that module's own
documented boundary — never Crop Dusta's own shed, seeds, inventories, or
submitted action. Selling activity for Crop Dusta is
**[INFERRED]**-only, via `infer_opponent_money_deltas` (bank delta), never
quantity/item/price.

One new helper, `opponent_tile_idle_by_day`
(`scripts/phase39/matched_scale_efficiency.py`), extends this same
public-only reading to tile-level fields (`kind`, `watered_today`,
`yield_units`, `planted_day`, `crop`) — these are public board state, not
private inventory, and the function reads them from the same viewer-owned
observation `extract_episode_timelines` already uses. It applies Phase 10's
own idle definition (`agents/phase2_3/common.py::_needs_harvest_crop`,
reused unchanged) unmodified.

Submission I's actual shipped agent —
`scripts/phase37/paced_portfolio_agent.py::make_paced_portfolio_agent`,
which Phase 37 confirmed is exactly what was packaged (Phase 36's pacer +
`agents/phase21/portfolio.py::portfolio_targets`, both unmodified) — was run
in isolation vs. `"pass"` on the 4 canonical development seeds
(700000-700003), via `instrumentation/collector.py::run_episode` +
`instrumentation/pipeline.py::analyze_replay` (both unchanged). Full access
to our own actions was used for this side only (own `daily_summary`,
`financial_transactions`, `action_efficiency`).

All comparisons are restricted to **day ≥ 11**, the day both sides are
first confirmed to hold the full 3 land quadrants
(`agents/phase21/portfolio.py::_LAND_RUNGS`) — before that, land/hand scale
is not matched and a throughput comparison would be confounded by ramp-up.

No frozen file was modified. `agents/phase21/` (and all its transitive
callees) ran completely unchanged.

## 2. Comparative Telemetry (day ≥ 11)

| Metric | Crop Dusta (n=2 real episodes) | Submission I (n=4 dev seeds) |
|---|---|---|
| Mean total crop tiles | 50.45 | 45.04 |
| Mean tile-idle fraction | **0.470** | **0.069** |
| Mean animal-servicing rate | 0.757 | 0.707 |
| Mean hands / land quadrants | 12.0 / 3.0 | 11.0 / 3.0 |
| Fraction of days with positive bank delta **[INFERRED]** | 0.974 | — |
| Mean products sold/day **[OBSERVED]** | — | 27.5 |
| Mean crops harvested/day **[OBSERVED]** | — | 12.25 |

Per-episode / per-seed net-dollar throughput (day ≥ 11, matched land/hands):

| Source | Mean net $/day | Mean $/crop-tile/day |
|---|---|---|
| Crop Dusta 105373474 (balanced WHEAT/STRAWBERRY, final $66,091) | 3,036 | **62.3** |
| Crop Dusta 105341441 (STRAWBERRY-dominant, final $148,520) | 7,516 | **298.6** |
| Submission I seed 700000 | 2,113 | 49.9 |
| Submission I seed 700001 | 4,034 | 81.6 |
| Submission I seed 700002 | 3,242 | 67.5 |
| Submission I seed 700003 | 2,466 | 52.6 |

**[OBSERVED]** Submission I's own $/crop-tile/day range (49.9-81.6) brackets
Crop Dusta's balanced-mix game (62.3) almost exactly. Only the
STRAWBERRY-dominant game is an outlier, at ~4-5x every other value in the
table.

**[INFERRED]** A weak negative correlation (r = -0.13, n=76 player-days)
between Submission I's own daily sell-batch size and its own realized
per-unit sell price was checked as a candidate mechanism (self-inflicted
market-glut from bursty selling) — present in the expected direction but
too weak to explain a multi-thousand-dollar/day gap on its own.

## 3. Diagnosis

**[VERIFIED]** The originally hypothesized mechanism — tile idle-time or
animal-servicing lag in `agents/phase21/execution.py`'s scheduling logic —
does not exist. Submission I is measurably *more* attentive at the tile
level than real Crop Dusta play (idle fraction 7x lower). This hypothesis
is closed.

**[HYPOTHESIS]** The raw net-$/day gap that IS visible in the table above
is largely explained by one outlier real episode's exceptional
$/tile/day, not by a systematic Submission-I-vs-gold-tier throughput
deficit — but this cannot be confirmed or ruled out on n=2 real episodes.
Two real episodes is not enough to know whether 105341441's 298.6 $/tile/day
is: (a) ordinary gold-tier execution this project simply hasn't replicated
yet, (b) a favorable crop-price/timing draw specific to that one seed, or
(c) inflated by something the `"pass"`-opponent isolation setup doesn't
capture (e.g., real market dynamics with an actual second producer sharing
the pool differ from solo-vs-pass, which this project's own Phase 21 Step 1
market-glut experiment already showed matters a great deal for STRAWBERRY
specifically).

## 4. Fix

**None built.** Per this phase's own scope constraint (Section 5 of the
brief), a fix requires a diagnosis that is both clear and narrowly scoped.
The only clear finding here (tile idle-time is not the problem) implies no
fix — there is nothing to change. The dollar-throughput gap, the one
finding that IS real, does not have a clear, narrowly-scoped mechanism
behind it (crop-mix outlier vs. genuine strategy gap vs. isolation-harness
artifact are not distinguished by this measurement) — building anything on
top of it now would be exactly the "speculative build on an unclear
diagnosis" this phase was instructed to resist.

## 5. Recommendation for a Future Phase

1. **Grow the real gold-tier sample.** Two episodes is too few to tell
   outlier from pattern — if more real Crop Dusta (or other #1-3 ranked)
   episodes become available, re-run this same $/crop-tile/day comparison
   before drawing further conclusions.
2. **Test the isolation-harness artifact hypothesis directly**: re-run
   Submission I's STRAWBERRY-heavy mid/late portfolio in a real two-producer
   competitive match (vs. Submission G or C, not `"pass"`) and compare
   $/crop-tile/day to the solo-vs-pass numbers here — Phase 21 Step 1
   already showed solo-vs-pass and two-producer STRAWBERRY economics can
   differ sharply.
3. **Revisit opponent-population diversity** as the task brief itself
   flagged: the repeating real-vs-synthetic gap (Submission F 33% vs 100%,
   H 54.5% vs 60-100%, I ~50% vs 67%-equivalent) may be explained by the
   real ladder containing opponent archetypes/strategies this project's
   synthetic seed set doesn't sample, rather than by any execution
   deficiency on Submission I's own side — this phase's finding (comparable
   or better tile-level execution) makes that explanation relatively more
   likely, not less.

No submission is created from this phase — it produced a measurement and a
refuted hypothesis, not a validated change.
