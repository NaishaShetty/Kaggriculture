# Phase 40: Competitive Throughput Report

## Executive Summary

**[VERIFIED] The isolation-harness-artifact hypothesis is REFUTED.**
Submission I's $/crop-tile/day does **not** increase under real
two-producer competition — if anything it is marginally *lower* (57.66
mean across 8 real competitive games vs. 62.9 mean across Phase 39's 4
isolated games, an ~8% decrease, well within the seed-to-seed noise both
measurements already show). Tile-idle fraction and animal-servicing rate
are also essentially unchanged (0.053 vs. 0.069 idle; 0.67 vs. 0.71
servicing — both small, and idle fraction is if anything *lower* under
competition, the opposite of a scheduling degradation). Phase 39's isolated
numbers were **not** understating Submission I's real throughput. Real
competitive pressure from Submission G or Submission C does not meaningfully
change the picture.

**What this means for the real-vs-synthetic gap:** Phase 39 already found
Submission I's own $/crop-tile/day sits inside the range of one real Crop
Dusta game (balanced mix, $62.3/tile/day) and far below the other
(STRAWBERRY-dominant, $298.6/tile/day). This phase closes off the
explanation that Submission I's own measurement methodology (solo-vs-"pass")
was hiding real throughput that only shows up under actual competition — it
isn't. That sharpens, not weakens, Phase 39's other standing recommendation:
the repeating real-vs-synthetic gap (Submission F 33% vs 100%, H 54.5% vs
60-100%, I ~50% vs 67%-equivalent) is more likely explained by
**opponent-population diversity** in the real ladder than by any execution
or measurement-methodology deficiency on Submission I's own side. Two
consecutive measurement phases (39, 40) have now each ruled out one
candidate execution-side explanation; neither found a fix to build.

## 1. Method

Per the brief, this phase confirmed the shipped-agent identity directly
from Phase 37's own report before running anything (Section 3 of
`results/phase37/PHASE37_SUBMISSION_I_PACKAGING_REPORT.md`): Submission I's
package `agent(obs)` builds
`scripts.phase37.paced_portfolio_agent.make_paced_portfolio_agent()` with no
arguments — the same factory Phase 39 already used, imported unchanged here
too.

Phase 39's own measurement code
(`scripts/phase39/matched_scale_efficiency.py`) is imported directly, not
rebuilt: `own_daily_snapshots`, `tile_idle_fraction_by_day`,
`summarize_matched_scale`, `_mean`, `MATCHED_SCALE_MIN_DAY` (=11, the day
both sides hold the full 3 land quadrants), `STEPS`, `DEV_SEEDS`
(700000-700003). The only new code is
`scripts/phase40/competitive_throughput.py::extract_own_telemetry_vs`, a
thin variant of Phase 39's own `extract_own_telemetry` — every extraction
step inside it is identical Phase 39 logic; the only change is passing a
real opponent agent as `run_episode`'s second argument instead of `"pass"`.

Two opponents were used, both imported and run exactly as
`scripts/phase23/vs_submission_g.py` already established as this project's
standard competitive-validation setup:
- **Submission G**: `agents/phase15/adapters/macro_agent.py::make_macro_agent()`
  (shipped defaults, no kwargs).
- **Submission C**: `agents/phase3_8/adapters/competitive_v3_agent.py::
  make_competitive_v3_agent(trace_path=None, liquidity_guard_enabled=False)`.

4 development seeds × 2 opponents = 8 real competitive episodes. No frozen
file touched; `agents/phase21/`, `agents/phase15/`, and `agents/phase3_8/`
all ran completely unchanged.

## 2. Comparative Telemetry (day ≥ 11)

| Source | n | Mean tile-idle fraction | Mean animal-servicing rate | Mean net $/day | Mean $/crop-tile/day |
|---|---|---|---|---|---|
| **Phase 39 isolated (vs. "pass")** | 4 seeds | 0.0694 | 0.7066 | 3,214 | **62.90** |
| **Phase 40 vs. Submission G** | 4 seeds | 0.0511 | 0.6802 | 2,904 | **58.86** |
| **Phase 40 vs. Submission C** | 4 seeds | 0.0554 | 0.6688 | 2,653 | **56.45** |
| **Phase 40 combined (both opponents)** | 8 games | 0.0533 | 0.6745 | 2,779 | **57.66** |

Per-seed detail:

| Opponent | Seed | Final money | Won | $/crop-tile/day |
|---|---|---|---|---|
| Submission G | 700000 | $55,204 | Yes | 56.97 |
| Submission G | 700001 | $62,956 | Yes | 61.32 |
| Submission G | 700002 | $52,762 | Yes | 56.55 |
| Submission G | 700003 | $56,899 | Yes | 60.61 |
| Submission C | 700000 | $58,411 | Yes | 70.66 |
| Submission C | 700001 | $64,126 | Yes | 63.57 |
| Submission C | 700002 | $50,911 | Yes | 54.46 |
| Submission C | 700003 | $43,151 | Yes | 37.12 |

**[OBSERVED]** Submission I won all 8/8 of these real competitive games
(consistent with the 4-seed development set's known behavior — Phase 37
Section 5c reported the identical 4/4 record vs. Submission G on these same
seeds, matching exactly). This 4-seed sample is not a re-validation of the
full 15-seed 66.7%/100% record (already established by Phase 36/37) — it is
reused here only as the substrate for the throughput measurement.

**[VERIFIED]** Tile-idle fraction under real competition (0.051-0.055) is
in the same low range as isolation (0.069) — Submission I remains far more
tile-attentive than real Crop Dusta play (0.470, per Phase 39) regardless of
opponent. **[VERIFIED]** Animal-servicing rate is likewise stable across all
three conditions (0.67-0.71) — no evidence that having a real competitor
changes how the execution layer's task-priority/scheduling logic behaves in
practice.

**[OBSERVED]** $/crop-tile/day is modestly lower under real competition
(56.45-58.86) than in isolation (62.90) — the opposite direction from what
the isolation-harness-artifact hypothesis predicted (it predicted isolation
was *understating* real throughput). The magnitude of this decrease (≈6-11%)
is small relative to the spread already present within each condition
(isolated range 49.9-81.6; competitive range 37.1-70.7 — overlapping
distributions) and far too small to explain the ~5x gap to Crop Dusta's
STRAWBERRY-dominant outlier game (298.6).

## 3. Diagnosis

**[VERIFIED]** The isolation-harness-artifact hypothesis, as specifically
framed by this phase's brief ("if higher under real competition, Phase 39's
isolated numbers were understating Submission I's real throughput") is
**refuted**. $/crop-tile/day is not higher under real competition — it is
slightly lower.

**[HYPOTHESIS]** The small decrease that IS present is directionally
consistent with ordinary shared-pool market pressure from a real second
producer (Phase 21 Step 1's own confirmed mechanism for MELON, plausibly
extending in a smaller way to Submission I's own STRAWBERRY-heavy mid/late
portfolio competing against Submission G's/C's own STRAWBERRY exposure) —
but at only ~6-11%, this is a minor effect, not the dominant driver of
anything. This phase did not attempt to isolate the mechanism further
(e.g., a direct realized-sell-price comparison, as Phase 21 Step 1 did for
MELON) because the effect size does not warrant it — Section 5's honest-null
clause governs here: the result is small and unremarkable, not a new
problem to chase.

**[VERIFIED]** No scheduling-side effect was found either: tile-idle
fraction and animal-servicing rate are essentially flat across isolation
and both competitive opponents. Having a real competitor present does not
measurably change how `agents/phase21/execution.py`'s task-assignment logic
performs in practice.

## 4. Fix

**None built — and none warranted.** The measured question (is isolation
an artifact that hides real throughput?) came back negative. There is
nothing here to fix: Submission I's execution behavior is stable across
isolation and two different real competitors, and the isolation harness
was not "wrong" in a way that requires correction — it was, if anything,
a very slightly generous (not pessimistic) proxy for real-competitive
throughput. This is consistent with this phase's own scope: build only on
a clear, narrowly-scoped diagnosis, and this diagnosis implies no code
change.

## 5. What This Means for the Real-vs-Synthetic Gap

Phases 39 and 40 have now each closed off one candidate execution-side
explanation for the standing real-vs-synthetic performance gap:

- Phase 39: tile idle-time / animal-servicing lag — **refuted** (Submission
  I is more attentive, not less, than real Crop Dusta play).
- Phase 40: isolated-measurement understating real competitive throughput —
  **refuted** (real competition does not raise $/crop-tile/day; if
  anything it's marginally lower).

Both results point the same direction: Submission I's own execution is
sound and stable across every condition tested at matched scale. The
outstanding puzzle — Crop Dusta's STRAWBERRY-dominant game reaching
$298.6/tile/day, roughly 5x every other data point measured across both
phases — remains unexplained by anything on Submission I's execution side.
Per Phase 39's own Section 5 recommendation #3, **opponent-population
diversity in the real ladder** (archetypes/strategies this project's
synthetic seed set does not sample) is now the most likely remaining
explanation, not execution quality or measurement methodology. A future
phase should pursue that directly — e.g., by seeking more real gold-tier
episodes to determine whether Crop Dusta's outlier game reflects a
repeatable strategy or one favorable draw — rather than continuing to
audit Submission I's own execution layer, which two independent
measurement phases have now found no fault with.

No submission is created from this phase.
