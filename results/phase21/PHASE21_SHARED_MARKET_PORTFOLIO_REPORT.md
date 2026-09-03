# Phase 21: Shared-Market Portfolio — A Fresh Agent Built on Reframe 1

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`, and — new for this phase — `agents/phase15/`, confirmed via `git status --short` below: the only `agents/phase15/` changes present predate this phase, from Phase 19/20). All new code lives under `agents/phase21/`, `scripts/phase21/`, `results/phase21/`. No submission is created, per this phase's explicit scope.

## Executive Summary

**[VERIFIED] Step 1's shared-market glut hypothesis is confirmed decisively, through the real engine, not the simulator alone.** Two single-crop agents at identical production scale (8 hands, 2 land, 40 crop tiles), run head-to-head:

| Condition | Mean final money (A) | Mean sell revenue (A) | Mean avg. sell price |
|---|---|---|---|
| A=MELON, competitor also MELON | $8,212 | $15,718 | ~$49-61/unit |
| A=MELON, competitor grows WHEAT instead | $24,566 | $32,072 | ~$85-106/unit |
| A=WHEAT, competitor also WHEAT | $5,038 | $10,528 | ~$20.4/unit |
| A=WHEAT, competitor grows MELON instead | $5,754 | $11,244 | ~$21.4/unit |

**A second producer entering the MELON pool costs A 66.5% of its final money. A second producer entering the WHEAT pool costs A only 12.4%.** This is not a subtle effect — it is the single largest lever measured in this experiment, and it holds exactly as `docs/FRESH_STRATEGY.md` predicted from reading the engine's glut-curve constants directly (MELON: `sq`, above_target=3.60; WHEAT: `log`, above_target=0.20).

**[OBSERVED] The realistic-opponent benchmark works as intended**: a synthetic agent built directly from real top-ladder day-by-day data (Dmitry Larko, episode 105027448) reaches a mean isolated final money of **$52,261** across the 4 development seeds — more than **2.4x** Submission C/E's own head-to-head performance (~$21k-22k) — confirming it is a meaningfully stronger, more realistic validation bar than this project's own prior submissions, without needing to match the real player's actual $183,147 exactly.

**[OBSERVED, first-cut, honestly reported] The Step 2 portfolio controller under-performs the benchmark in isolation but wins head-to-head against it, 4/4.** Isolated mean money ($31,875) is meaningfully below the realistic-opponent benchmark's own isolated mean ($52,261) — this first cut has real, disclosed weaknesses (Section 4). But run head-to-head against that same benchmark, the portfolio controller won every game (4/4), by wide margins in 3 of 4. This is reported as a genuine, if early, positive signal for the reframe — not proof the design is finished, and not glossed over as more than a first cut.

## 1. Reading the Engine Source Directly (Confirming, Not Trusting, the Reframe's Own Claims)

Before building anything, `vendor_kaggriculture/kaggriculture.py` was read directly:

- **`MARKET_PARAMS`** (line 41-50): confirmed MELON uses `above_func: "sq"`, `above_target: 3.60` — the single harshest combination in the table. WHEAT uses `above_func: "log"`, `above_target: 0.20` — the flattest. Both figures match `docs/FRESH_STRATEGY.md`'s own table exactly, verified against source rather than trusted from the doc.
- **`_process_market`** (line 544): confirmed the shared-pool mechanic directly — for each unit in the per-unit lockstep loop, both players' SELL orders for the SAME item are quoted against `market["inventory"][item]` ("Both players see the same pre-commit inventory for this unit"), then both committed, advancing the SAME shared inventory before the next unit's quote. This is not an inference from behavior; it is read directly from the commit loop's own structure.

## 2. Step 0: The Realistic-Opponent Benchmark

`scripts/phase21/realistic_opponent.py`, built from the FULL 30-day trajectory of Dmitry Larko's own side in episode 105027448 (extracted via `agents/phase6/replay_forensics.py::extract_episode_timelines`, reused unchanged — not rebuilt). Milan Leonard's independent trajectory (episode 105012251) corroborates the same overall shape closely enough (land 1→2→3 by day ~11, hands ramping to 10-12, MELON dropped by day 10, WHEAT overtaking STRAWBERRY from day ~21, full liquidation by day 29) that Larko's own exact day-by-day numbers were used directly as a day-indexed target table, rather than an averaged or invented curve.

**[OBSERVED] First implementation attempt collapsed**: an initial version with no cash-safety mechanism reproduced the same chronic near-$0 cash pattern this project has now documented three times (F-005/Submission C, Phase 19's agents/phase15/ recalibration, and here) — mean isolated money only $255 across 4 seeds. A minimal, freshly-written cash-safety throttle (same principle Phase 20 validated for `agents/phase15/`, written independently here since this phase does not import from that lineage: freeze hiring below a small floor and require a purchase-time reserve before buying land, both re-armed every turn) raised this to a stable **$52,261 mean** — more than double Submission C/E's own head-to-head range (~$21k-22k), and no seed collapsed or errored. **[OBSERVED] This is well below the real players' own $116k-183k** — expected and acceptable per the brief's own standard ("doesn't need to hit $116k-183k exactly — needs to be clearly stronger than Submission C/E").

## 3. Step 1: The Shared-Market Glut Experiment

`scripts/phase21/market_glut_experiment.py`. Design: two single-crop agents (`make_single_crop_agent`, reusing `agents/phase21/execution.py`), identical scale (8 hands, 2 land, 40-tile footprint), run through `kaggle_environments` directly (not the simulator alone — the point is two independent agents' real orders interacting through the shared pool in the same turn, which `agents/phase4/market_model.py`'s single-seller simulator cannot represent). 4 development seeds, 4 conditions.

Full results in Section "Executive Summary" above and `results/phase21/phase21_market_glut_experiment.json`. **[VERIFIED] The hypothesis holds decisively**: MELON's final money for the same producer drops 66.5% when a second seller also produces MELON (vs. facing a WHEAT-only competitor); WHEAT's final money drops only 12.4% under the equivalent comparison. The average realized sell price tells the same story even more starkly: MELON's price roughly halves (~$100 → ~$55) when contested, while WHEAT's barely moves (~$21.4 → ~$20.4, about a 5% decline). **This is the load-bearing check for the whole reframe, and it passed — proceeding to Step 2 is justified by this result, not by the doc's own prior reasoning alone.**

## 4. Step 2: First-Cut Portfolio Controller

`agents/phase21/portfolio.py`, wired via `agents/phase21/adapters/portfolio_agent.py`. Design, directly motivated by Section 3's confirmed result:

- **MELON is time-boxed to the opening only** (days 0-7, matching the real ladder data's own observed MELON window) — never re-entered, since Section 3 shows it's a bad SUSTAINED crop once a competitor might also be producing it.
- **WHEAT is the durable backbone** for the sustained, scaled portion of the portfolio, weighted MORE heavily than the realistic-opponent benchmark's own observed split (55-65% WHEAT here vs. the benchmark's ~40-43% at comparable game stages) — a deliberate design choice favoring market durability over the benchmark's own (real, but not necessarily optimal) balance.
- **STRAWBERRY is a bounded mid-game addition, sized opponent-aware**: `agents/phase3/opponent_observation.py`'s existing public-only telemetry (reused, not re-derived) is read every turn; if the opponent's own current crop footprint is more than 50% STRAWBERRY, this controller shifts 0.20 of its own STRAWBERRY-fraction allocation into WHEAT instead of piling into the same glut-prone pool the opponent is already scaling into.
- Land/hands/animal ramps reuse the same real-data ceilings the benchmark itself is built from (this phase's scope is the portfolio/crop-mix reframe only, not re-deriving those separately-validated numbers).

### Validation Against the Realistic-Opponent Benchmark

**Isolated (vs. "pass"), 4 development seeds**:

| Seed | Portfolio controller | Realistic-opponent benchmark |
|---|---|---|
| 700000 | $15,131 | $49,159 |
| 700001 | $25,383 | $51,019 |
| 700002 | $46,854 | $57,384 |
| 700003 | $40,132 | $51,483 |
| **Mean** | **$31,875.00** | **$52,261.25** |

**[OBSERVED, disclosed honestly] The portfolio controller's isolated economy is materially weaker than the benchmark's**, particularly on seed 700000 ($15,131). Traced directly: the controller's more WHEAT-heavy opening (40% WHEAT / 60% MELON at day 0, vs. the benchmark's 65% MELON / 35% WHEAT) generates less early cash, and the same chronic low-cash pattern documented throughout this project recurs for longer before the ramp reaches its full scale (land doesn't reach 3 until day 24 in the worst traced seed, vs. the benchmark's day 11) — the cash-safety throttle keeps it from collapsing outright, but it does not fully resolve the slower ramp this crop-mix choice causes. **This first cut has not yet balanced "favor durable crops" against "don't starve the early ramp" — a real, disclosed weakness for a follow-up phase to address, not a finished design.**

**Head-to-head vs. the realistic-opponent benchmark, same 4 seeds**:

| Seed | Portfolio controller | Realistic-opponent benchmark | Winner |
|---|---|---|---|
| 700000 | $43,913 | $19,907 | Portfolio |
| 700001 | $43,230 | $13,144 | Portfolio |
| 700002 | $14,162 | $133 | Portfolio |
| 700003 | $49,333 | $8,907 | Portfolio |

**Win rate: 4/4 (100%).** **[OBSERVED] Despite a weaker ISOLATED economy, the portfolio controller wins every head-to-head game against the benchmark, and the benchmark's own performance collapses sharply once it faces a real competitor** (its head-to-head scores, $133-19,907, are far below its own isolated mean of $52,261) — consistent with the benchmark itself having no opponent-awareness or shared-market discipline at all, exactly the gap this phase's design targets. **[INFERRED] This is a genuinely encouraging early signal for the reframe** — a portfolio that reasons about the shared market and the opponent's own commitment appears to have a real competitive edge even before its own standalone economics are tuned — but it is one data point (4 seeds) on a first-cut design, not a validated result at the rigor this project has held later-stage submissions to (Phase 17's own 15-seed lesson on small-sample luck applies here too, and was not re-run given this phase's explicit "first cut, not submission-ready" scope).

## 5. Honest Assessment and What This Phase Does NOT Claim

- **[VERIFIED]** Reframe 1's core empirical claim (shared-market glut asymmetry between MELON and WHEAT) is real and substantial, confirmed through the actual engine, not assumed from reading source code alone.
- **[OBSERVED]** A first-cut agent built around that claim already shows a real competitive edge over a realistic-ladder-grounded benchmark, despite weaker standalone economics.
- **[NOT CLAIMED]** This phase does NOT claim the portfolio controller is submission-ready, tuned, or validated at Phase 17-level rigor (small seed count, no held-out validation, isolated economy has a known real weakness). It does NOT touch Reframe 2 (win-probability objective) or Reframe 3 (market-as-weapon), per explicit scope. It does NOT claim the realistic-opponent benchmark reproduces real top-ladder play exactly (it reaches $49k-57k isolated, not $116k-183k) — only that it is a materially more honest validation bar than Submission C/E.

## Changed Files

New, all additive; nothing pre-existing modified:
- `agents/phase21/__init__.py`
- `agents/phase21/execution.py`
- `agents/phase21/portfolio.py`
- `agents/phase21/adapters/__init__.py`
- `agents/phase21/adapters/portfolio_agent.py`
- `scripts/phase21/realistic_opponent.py`
- `scripts/phase21/market_glut_experiment.py`
- `results/phase21/phase21_market_glut_experiment.json`
- `results/phase21/PHASE21_SHARED_MARKET_PORTFOLIO_REPORT.md` (this file)

No frozen file was touched, and `agents/phase15/` was not modified by this phase (the `git status` changes present there predate this phase, from Phase 19/20). No submission is created.
