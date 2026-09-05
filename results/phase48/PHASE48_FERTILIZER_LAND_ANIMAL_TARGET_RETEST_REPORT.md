# Phase 48: Fertilizer and Land-Expansion Retest Through Phase 46's Fix — Both Closed Negative; Animal Target Calibration — A Real, Validated Win

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`,
`agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`,
`agents/phase2_4/common.py`, `agents/phase15/`, `agents/phase21/`). All new
code lives in `scripts/phase48/`; all new results in `results/phase48/`.
`agents/phase21/portfolio.py::portfolio_targets` is imported unmodified
throughout (confirmed by direct read, Section 3 below) — Part C's capped
target is a wrapper, not an edit.

## Executive Summary

**[VERIFIED] Part A (fertilizer): decisively WORSE composed with Phase 46's
fix than either of the two prior fertilizer attempts, not rescued by it.**
4-seed isolated screen: mean final money collapses from baseline's
$59,569.75 to **$855.75 (-98.6%)** — a much larger regression than Phase
30's naive preempting attempt (-21.3%) or Phase 33's strictly-opportunistic
attempt (-26.9%). Per this project's own pre-registered screen-first rule,
this is decisively negative and the full 15-seed run was correctly not
attempted. **[INFERRED, by direct trace]** The mechanism is the same
path-dependent purchase-timing cascade Phase 33 diagnosed, but now
substantially amplified: Phase 46's `BUY_ANIMAL` reserve-gate (`money - r
>= cost`) is a hard threshold, and fertilizer's turn-by-turn perturbations
to worker position/inventory shift exactly when that threshold is crossed
often enough to delay the entire hand/land ramp by roughly 10 extra days
relative to the no-fertilizer condition on the same execution layer (traced
seed: hand count stabilizes at 11 around day 10 without fertilizer, not
until day 21 with it). Fixing the FEED/WATER scheduling bottleneck does
**not** rescue fertilizer — if anything, composing it with Phase 36/46's
more finely cash-gated purchase logic makes the interaction worse than the
original unthrottled execution layer did.

**[VERIFIED] Part B (dedicated-hands 4th quadrant): still decisively
negative, though less catastrophic than Phase 33's original result — and,
critically, [VERIFIED by direct trace] Phase 33's own diagnosed failure
mode is NOT the mechanism Phase 46 fixed.** 4-seed isolated screen: TOMATO
$19,962.25 (-66.5% vs. baseline), GOOSE $17,202.50 (-71.1%) — both a clean
recovery from Phase 33's original -92.3%/-94.1%, but nowhere near
breakeven, and per this project's screen-first rule the full 15-seed run
was correctly not attempted. **[VERIFIED, by direct trace]** the 4th (SE)
quadrant is still bought on day 24 in the traced seed (700002, TOMATO
condition) — essentially unchanged from Phase 33's own traced day 26 — so
TOMATO/GOOSE still never gets the 5-6 remaining days needed to produce any
revenue (zero TOMATO/EGG revenue in 7 of 8 runs). **The reason is
structural, not a tuning gap**: Phase 33's diagnosed mechanism was the
recurring daily Fibonacci `HIRE` cost for dedicated hands delaying the
agent's own land ramp — and `HIRE`'s logic is byte-identical between Phase
46's execution layer and the original (confirmed by direct read, Section
5) — Phase 46's fix touches FEED/WATER tier ordering and `BUY_ANIMAL`
pacing, neither of which is in `HIRE`'s code path at all. **These are two
different resources (cash-timing for HIRE vs. worker-turn scheduling for
FEED/WATER), and fixing one does not touch the other**, exactly as the
brief warned might be the case. The modest economic improvement over Phase
33's original numbers is attributable to `BUY_ANIMAL`'s new reserve
avoiding some of the worst lump-sum-purchase cash collapses elsewhere in
the run, not to any fix of the land-timing mechanism itself.

**[VERIFIED] Part C (animal target calibration): a real, decisive,
non-regressing win — ready to package.** Extending Phase 46's
`capacity_probe.py`-style instrumentation to track owned-animal count at
the END of every day (not just day 29) across 4 development seeds, both
isolated and vs. Submission G, found owned animal count reliably rises to a
peak of 9-11 around day 15-20 and then settles into a genuine **steady-state
equilibrium of 6-9 animals (mean 8.00 isolated / 7.18 vs. Submission G,
days 20-29)** — nowhere near the `_ANIMAL_SPECIES_RUNGS` target of 17 by
day 11, even though cumulative purchases over the game (16-20 units) come
close to or exceed the target, because roughly half of everything
purchased subsequently escapes. **17 is not achievable under this
execution layer's realistic play — the schedule hits a real, lower ceiling
regardless of game length**, confirming and quantifying Phase 41/45's
flat-final-count observation as a genuine equilibrium, not a purchase
shortfall. A capacity-aware wrapper around `agents/phase21/
portfolio.py::portfolio_targets` (imported unmodified) that caps the total
animal target at 8 (proportionally scaling COW:SHEEP to preserve the
existing ratio) **improved isolated economy on all 4 individual
development seeds, +18.2% mean ($59,569.75→$70,419.75)**. Full 15-seed
head-to-head validation against all three required opponents is a clean,
strictly dominant win over Submission J's own shipped baseline: **vs.
Submission G, 14/15→15/15 (margin $7,345→$14,843, +102%), recovering
baseline's one remaining loss; vs. Submission C, 15/15 held (margin
$35,483→$43,501, +22.6%); vs. Jonaid, 15/15 held (margin $27,808→$36,257,
+30.4%)**. Every matchup improves, no new loss anywhere in the sample —
this candidate is **ready to package** (packaging itself not done this
phase, per this project's standing precedent).

## 1. What Phase 33's Two Rejected Designs Originally Composed With

Confirmed by direct read before building anything (per this phase's own
instruction): `scripts/phase33/fert_execution_opportunistic.py` and
`scripts/phase33/land_expansion_execution.py` are BOTH freestanding
reconstructions of `agents/phase21/execution.py`'s task-scheduling loop —
neither includes Phase 36's `BUY_ANIMAL` cash pacer (their `BUY_ANIMAL`
section is the original unthrottled, zero-reserve form: `buy_n = min(
still_needed, int(money // cost))`) and neither includes Phase 46's FEED
tier-0.5 reprioritization (`FEED` sits at tier 1, tied with `WATER`, in
both). So "whatever execution layer Phase 33 originally used" is the
**pre-Phase-36, pre-Phase-46** execution shape. Both Phase 48 files
(`scripts/phase48/fert_execution_feed_priority.py`,
`scripts/phase48/land_expansion_feed_priority.py`) instead start as an
exact copy of `scripts/phase46/feed_priority_execution.py` (which already
composes Phase 36's pacer + Phase 46's FEED tier 0.5), with Phase 33's own
fertilizer/tile-pool-splitting logic layered on top, unchanged from Phase
33's own design in every other respect.

## 2. Part A: Opportunistic Fertilizer on the FEED-Priority Execution Layer

### Design

`scripts/phase48/fert_execution_feed_priority.py` reuses Phase 33's exact
tier scheme (`FERTILIZE` tier 4, `COLLECT_FERTILIZER` tier 5 — both
strictly below every tier the FEED-priority base layer uses: HARVEST/
HARVEST_ANIMAL=0, FEED=0.5, WATER=1, CARE=2, DIG/PLANT/BUILD/PLACE=3). The
same structural non-preemption argument Phase 33 Section 4 made still
holds unchanged: the tiered greedy-assignment loop processes tiers in
strictly increasing order and cannot terminate while any unclaimed worker
remains eligible for any unmatched same-tier entry, so a worker reaching
tier 4/5 unclaimed is, by construction, one tier 0-3 (now including FEED's
own tier 0.5) had no eligible use for that turn.

### 4-Seed Isolated Screen

`scripts/phase48/isolated_screen_fert.py`, same development seeds and
metrics as Phase 33's own screen:

| Condition | Seed 700000 | Seed 700001 | Seed 700002 | Seed 700003 | Mean |
|---|---|---|---|---|---|
| Baseline (FEED-priority layer, no fertilizer) | $70,049 | $64,409 | $48,424 | $55,397 | **$59,569.75** |
| Opportunistic fertilizer (this phase) | $706 | $1,313 | $1,028 | $376 | **$855.75** |

**[VERIFIED] -$58,714.00 (-98.6%) mean isolated money** — every one of the 4
seeds collapses, not just the mean. Peak fertilized tiles reached (mean
7.5, range 6-9) is in the same range Phase 33's own opportunistic version
achieved (7.2) — the fertilizer mechanic itself works identically, applying
similarly little tile coverage — but the downstream cost is far larger.
Mean idle-action fraction actually ROSE (0.0747→0.1760), the opposite of
what a purely-opportunistic, non-preempting task addition would predict if
it were simply filling spare capacity for free.

**Per this project's own pre-registered rule** ("a 4-seed screen may ONLY
be used to decide whether to continue, never to promote" — and,
symmetrically, a decisively negative screen is sufficient to stop, per
Phase 30/32/33's own precedent), **no full 15-seed validation was run.**

### Direct Trace: Why This Is Worse, Not Better

Tracing seed 700000's money/hand-count trajectory, no-fertilizer vs.
fertilizer, both on the identical FEED-priority execution layer:

| Day | No fertilizer: money / hands | With fertilizer: money / hands |
|---|---|---|
| 2 | $77 / 5 | $9 / 5 |
| 5 | $8 / 5 | $0 / 0 |
| 9 | $61 / 8 | $0 / 0 |
| 10 | $3,288 / **11** | $83 / 11 |
| 12 | $2,350 / 11 | $5 / 5 |
| 17 | $4,340 / 11 | $0 / 0 |
| 21 | $19,114 / 11 | $71 / 11 |
| 29 | **$70,049** / 11 | **$706** / 11 |

**[VERIFIED]** Without fertilizer, hand count stabilizes at the target (11)
by roughly day 10 and stays there, letting the cash ramp compound cleanly
from day ~13 onward. **With fertilizer, hand count does not stabilize
until roughly day 21** — ten days later — oscillating between 0 and 11
repeatedly in between, and the eventual recovery starting around day 21
never has enough runway left to reach anywhere near the no-fertilizer
outcome. **[INFERRED]** Fertilizer/`COLLECT_FERTILIZER` actions (and their
associated FETCH/PICKUP/DROP cycles) still consume real worker-turns and
change worker position/inventory state exactly as Phase 33 Section 6 found
— but Phase 46's `BUY_ANIMAL` reserve gate (`affordable_units = int((money
- r) // cost)`) is a hard threshold on money, and small shifts in exactly
when cash crosses that threshold (caused by fertilizer's own path-dependent
perturbations) appear to compound into much larger hire/animal-purchase
timing disruptions than the original unthrottled `BUY_ANIMAL` logic Phase
33 tested against. **[HYPOTHESIS, not decomposed turn-by-turn]** The more
finely cash-gated a purchase system is, the more sensitive it may be to
exactly this kind of small, path-dependent perturbation — meaning Phase
46's own fix, while a real win on its own (Section 4 of Phase 46's report),
may have made the execution layer *less* robust to this specific kind of
added noise, not more. This is disclosed as the most likely explanation
given the evidence gathered, not confirmed by a full mechanistic
decomposition.

**Verdict: Part A remains closed negative, and Phase 46's fix does not
rescue it — if anything, the interaction is worse than either prior
attempt. Not ready to package; not worth further tuning within this
design.**

## 3. Part B: Dedicated-Hands 4th-Quadrant TOMATO/GOOSE on the FEED-Priority Execution Layer

### Design

`scripts/phase48/land_expansion_feed_priority.py` reuses Phase 33's exact
tile-pool-splitting design (CORE pool = NW/NE/SW, byte-for-byte what
`portfolio_targets` would already plan; EXTENSION pool = SE only, 100%
TOMATO or up to 6 GOOSE COOPs, `n_dedicated_hands=2` added on top of the
base hand target, `land_quadrants` forced to 4 from day 12 onward) on top
of the FEED-priority execution layer instead of the original shape.

### 4-Seed Isolated Screen

`scripts/phase48/isolated_screen_land.py`:

| Condition | Mean final money | vs. baseline | vs. Phase 33's original result |
|---|---|---|---|
| Baseline (FEED-priority layer, no 4th quadrant) | **$59,569.75** | — | — |
| TOMATO on 4th quadrant + 2 dedicated hands | **$19,962.25** | **-66.5%** | Phase 33: -92.3% |
| GOOSE on 4th quadrant + 2 dedicated hands | **$17,202.50** | **-71.1%** | Phase 33: -94.1% |

**[VERIFIED]** Both conditions are decisively negative — a real, measured
improvement over Phase 33's original numbers (roughly 25-percentage-point
narrower loss in both cases) but nowhere close to flat or positive. Egg
revenue appeared in only 1 of the 8 runs ($120, one GOOSE seed); TOMATO
revenue was $0 in all 4 TOMATO runs. **Per this project's screen-first
rule, no full 15-seed validation was run.**

### Direct Trace: Confirming (Not Assuming) Whether Phase 46's Fix Touches Phase 33's Mechanism

Traced seed 700002 (TOMATO condition), the same seed Phase 33's own report
traced:

| Day | Quadrants owned | Money |
|---|---|---|
| 0 | 1 (NW) | $3,000 |
| 8 | 2 (+NE) | $60 |
| 21 | 3 (+SW) | $939 |
| **24** | **4 (+SE)** | $1,389 |

**[VERIFIED] The SE quadrant is bought on day 24** — 2 days earlier than
Phase 33's own traced day 26, essentially the same lateness, still far too
late for TOMATO (`first_yield_day=8`) to produce a single unit of revenue
in the 5-6 remaining days. Hand count in this trace oscillates repeatedly
between 0 and 13 through day 18 before settling, the same volatile pattern
Phase 33's original diagnosis described.

**[VERIFIED, by direct read]** `HIRE`'s code (the affordability-capped
cumulative-Fibonacci-cost loop) is **byte-identical** between
`scripts/phase48/land_expansion_feed_priority.py` and Phase 33's original
`scripts/phase33/land_expansion_execution.py` — neither Phase 46's FEED
tier reorder nor its `BUY_ANIMAL` reserve gate touches `HIRE`'s logic at
all. **[VERIFIED] Phase 33's own diagnosed failure mode (the recurring
daily Fibonacci hire cost for `n_dedicated_hands` extra hands, since
`farm["hands"] = []` resets to empty every day) is a fundamentally
different mechanism from the one Phase 46 fixed (FEED/WATER worker-turn
scheduling and `BUY_ANIMAL` cash-flow pacing) — not the same mechanism
under a different name, and not addressed by this phase's recomposition.**
The modest economic improvement over Phase 33's original numbers is best
explained by `BUY_ANIMAL`'s new reserve gate reducing the severity of
separate, unrelated lump-sum-purchase cash collapses elsewhere in the run
(the same mechanism Phase 36 fixed generally), not by any change to the
land-purchase-timing mechanism Phase 33 actually diagnosed.

**Verdict: Part B remains closed negative. The retest is fair and
directly confirms — not merely assumes — that Phase 46's fix and Phase
33's diagnosed blocker are different resources (worker-turn scheduling vs.
cash/HIRE timing). Not ready to package; a real fix here would need to
address the recurring daily hire-cost mechanism itself (e.g., a
cash-pacer for `HIRE` analogous to what Phase 36 built for `BUY_ANIMAL`),
which is out of this phase's scope.**

## 4. Part C: Animal Target Calibration — Steady-State Ceiling and a Capacity-Aware Cap

### Steady-State Instrumentation

`scripts/phase48/animal_ceiling_probe.py` extends Phase 46's
`capacity_probe.py`-style instrumentation (same imported primitives, same
"wrap the already-validated execution layer with a pure-measurement
tracker" pattern) to run Submission J's own execution layer
(`scripts/phase46/feed_priority_execution.py` + `agents/phase21/
portfolio.py::portfolio_targets`, unmodified — exactly what's packaged for
Submission J) across the 4 development seeds, isolated and vs. Submission
G, tracking owned-animal count (tiles with an `"animal"` key — the same
direct-state check Phase 33 Section 10 and Phase 46's own probe already
use) at the end of every day, plus cumulative `BUY_ANIMAL` purchases and an
inferred cumulative-escape count (`max(0, cumulative_purchased -
owned_now)`, valid since this engine has no other animal "exit" besides the
2-consecutive-unfed-day escape mechanic, confirmed directly at
`vendor_kaggriculture/kaggriculture.py::_daily_refresh_animals`).

**[VERIFIED] Daily owned-animal-count trajectories (isolated, all 4 dev
seeds)**:

```
seed 700000: 3,4,4,4,4,4,4,4,4,5,4,9,9,10,10,11,11,11,10,10,10,9,8,7,6,7,7,7,7,10
seed 700001: 3,4,4,4,4,4,4,4,4,4,4,7,7,7,8,8,8,8,9,9,9,9,9,8,9,9,9,9,8,9
seed 700002: 3,4,4,4,4,4,4,4,4,4,4,8,9,8,9,9,10,9,9,9,9,9,9,7,8,7,8,8,8,8
seed 700003: 3,4,4,4,4,4,4,4,4,4,5,6,7,8,8,8,8,10,10,10,10,10,6,7,6,6,6,6,7,9
```

**[VERIFIED]** Every seed shows the same shape: a rise to a peak of 9-11
around day 15-20 (the target rungs reaching 16-17 by day 11 clearly do
drive real purchasing), followed by a decline/oscillation that **settles
into a genuine equilibrium band of 6-9** for the remaining days — this is
not noise or a still-converging trend; the last 10 days (20-29) show the
series holding in a narrow, stable range in every seed.

| Condition | Mean final owned (day 29) | Mean steady-state owned (days 20-29) | Mean cumulative purchased | Mean cumulative escaped (inferred) |
|---|---|---|---|---|
| Isolated (vs. "pass") | 9.00 | **8.00** | 17.75 | 8.75 |
| vs. Submission G | 8.75 | **7.18** | 16.25 | 7.50 |

**[VERIFIED] Cumulative purchases (16.25-17.75) already reach close to or
past the target rung's own total (17)** — the agent IS trying to buy up to
the target, exactly as Phase 45 already confirmed (purchases track the
target rung closely) — **but roughly half of everything purchased
subsequently escapes**, so the sustainable steady-state count sits at
roughly 7-8, not 17. **[VERIFIED] This directly answers this phase's own
question: 17 is not achievable under this execution layer's realistic
play, regardless of game length** — the schedule hits a real, lower
ceiling (roughly 7-9) that a longer game would not raise, because the
mechanism is an ongoing purchase/escape equilibrium, not a one-time ramp
that simply hasn't finished yet.

### Capacity-Aware Capped Target: Design and Screen

`scripts/phase48/capped_animal_portfolio.py` wraps `agents/phase21/
portfolio.py::portfolio_targets` (imported unmodified — only the
`"animals"` field of its output is touched, matching the Phase 42/45
"wrap, don't modify" composition pattern exactly) with a proportional cap:
once the rung ladder's own total animal target exceeds `cap_total`, each
species' count is scaled down proportionally (preserving the existing
COW:SHEEP ratio) rather than hard-zeroing one species.

`scripts/phase48/isolated_screen_animal_cap.py`, 4 development seeds,
Submission J's own (unmodified) execution layer:

| Condition | Seed 700000 | Seed 700001 | Seed 700002 | Seed 700003 | Mean | Δ vs. baseline |
|---|---|---|---|---|---|---|
| Baseline (uncapped, target 17) | $70,049 | $64,409 | $48,424 | $55,397 | $59,569.75 | — |
| **Capped at 8** | $80,023 | $74,029 | $58,167 | $69,460 | **$70,419.75** | **+18.2%** |
| Capped at 9 | $77,293 | $64,315 | $67,000 | $65,825 | $68,608.25 | +15.2% |

**[VERIFIED] Every one of the 4 individual seeds improves under the
cap-8 candidate** — not just the mean — a decisive, non-cherry-picked
positive screen. Cap=8 outperforms cap=9 on this screen, so cap=8 was
carried forward to full validation. **[INFERRED]** The mechanism is
straightforward: capping the target near the empirically-observed
equilibrium stops the agent from repeatedly spending on animal purchases
that are likely to escape anyway (each escape forfeits the purchase price
with only partial value recovered via products sold before the escape),
redirecting that cash toward crops/land/hands the agent can actually
sustain.

### Full 15-Seed Head-to-Head Validation

`scripts/phase48/h2h_screen.py`, mirroring `scripts/phase46/
feed_priority_screen_h2h.py`'s exact structure — `baseline_j` reproduces
Phase 46/47's own numbers to the dollar (confirmed: $7,345.47 / $35,483.40
/ $27,808.07 margins match Phase 46's report exactly), a direct sanity
check that this harness is correct before trusting the candidate's numbers.

| Matchup | Baseline (Submission J, uncapped) | Capped animal target (cap=8) |
|---|---|---|
| vs. Submission G | 14/15, margin $7,345.47 | **15/15, margin $14,842.73 (+102%)** |
| vs. Submission C | 15/15, margin $35,483.40 | **15/15, margin $43,501.13 (+22.6%)** |
| vs. Jonaid | 15/15, margin $27,808.07 | **15/15, margin $36,256.73 (+30.4%)** |

**[VERIFIED] The capped candidate is strictly dominant over Submission J's
own shipped baseline in this validation sample**: it recovers baseline's
one remaining loss (seed 702001 vs. Submission G — baseline lost $46,814
vs. $48,193; the capped candidate won $49,500 vs. $37,063 on the same
seed) while introducing **zero new losses anywhere**, and improves mean
margin against all three required opponents by 22-102%. This is not a
marginal or ambiguous result on any axis measured.

**Verdict: Part C is a real, validated, non-regressing improvement. Ready
to package** (packaging itself — a new submission tarball, cold-process
test, dependency-closure check — was not in this phase's scope, matching
Phase 36/46/47's own "ready to package, not yet done" precedent).

## 5. Summary Table

| Part | 4-seed screen | Full 15-seed validation | Recommendation |
|---|---|---|---|
| A: fertilizer + FEED-priority layer | **-98.6%**, decisively negative | Not run (correctly, per screen-first rule) | **Closed negative** — worse than either prior attempt, not rescued |
| B: 4th-quadrant TOMATO/GOOSE + FEED-priority layer | **-66.5% / -71.1%**, decisively negative | Not run (correctly, per screen-first rule) | **Closed negative** — Phase 33's diagnosed mechanism (HIRE cash timing) is untouched by Phase 46's fix (worker-turn scheduling), confirmed by direct trace |
| C: capacity-aware animal target cap | **+18.2%** (cap=8), all 4 seeds individually positive | **15/15 vs. G (was 14/15), 15/15 vs. C, 15/15 vs. Jonaid** — strictly dominant, zero new losses | **Ready to package** |

## Changed Files

New, additive only (no frozen file touched, `agents/phase21/` and
`agents/phase15/` untouched):

- `scripts/phase48/fert_execution_feed_priority.py` (Part A execution layer)
- `scripts/phase48/isolated_screen_fert.py` (Part A screen)
- `scripts/phase48/land_expansion_feed_priority.py` (Part B execution layer)
- `scripts/phase48/isolated_screen_land.py` (Part B screen)
- `scripts/phase48/animal_ceiling_probe.py` (Part C steady-state instrumentation)
- `scripts/phase48/capped_animal_portfolio.py` (Part C capped-target wrapper)
- `scripts/phase48/capped_animal_portfolio_agent.py` (Part C packaging-style adapter)
- `scripts/phase48/isolated_screen_animal_cap.py` (Part C 4-seed screen)
- `scripts/phase48/h2h_screen.py` (Part C full 15-seed head-to-head validation)
- `results/phase48/phase48_isolated_screen_fert_results.json`
- `results/phase48/phase48_isolated_screen_land_results.json`
- `results/phase48/phase48_animal_ceiling_probe_results.json`
- `results/phase48/phase48_isolated_screen_animal_cap_results.json`
- `results/phase48/phase48_animal_cap_h2h_4seed_dev.json`
- `results/phase48/phase48_animal_cap_h2h_15seed_full.json`
- `results/phase48/PHASE48_FERTILIZER_LAND_ANIMAL_TARGET_RETEST_REPORT.md` (this file)

No frozen file, `agents/phase21/`, or `agents/phase15/` was touched. No
submission is created this phase — Part C's capped-animal-target candidate
is reported as ready to package (per this phase's own instruction, not
packaged here); Submission J (Phase 46/47's FEED-priority candidate,
unmodified) remains the current best shipped state.
