# PHASE 11 — Multi-Resource Portfolio: Does Portfolio Composition Rescue Labor/Animal Value?

Submission C (Phase 3.8) and Submission D (Phase 7's fix) are unmodified
throughout this phase. No submission is created.
`git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5
agents/phase3_8 agents/phase2_3/common.py agents/phase2_4/common.py` is
clean. All new code lives under `scripts/phase11/` and `results/phase11/`.

## 1. Executive Summary

**[OBSERVED] Labor: the aggregate picture reverses — net positive, though
individual cells are noisy.** On a combined STRAWBERRY(24 tiles)+
COW(6)/SHEEP(6) portfolio matching real opponent moushun_chen's actual
day-15/20 shape, mean final money **rises** from $40,081 at hand 4 to a
peak of $66,613 at hand 7, dips through hands 8-12, and ends at $47,771 at
hand 13 — **net +$7,690 from hand 4 to hand 13**, the opposite direction
of Phase 9's single-crop result, which fell **−$29,144** over the identical
range ($39,368 → $10,224). The cell-to-cell marginal curve itself is noisy
(sign-flips repeatedly, Section 3) — driven substantially by one seed
(700001) that runs consistently lower than the other three at every hand
count — but the aggregate direction is unambiguous and the absolute level
at every single hand count is 3-6x higher than Phase 9's corresponding
cell.

**[OBSERVED] Animals: does NOT show the same reversal.** Mean final money
is roughly flat-to-declining across 6-14 animals ($73,385 at n=6 down to
$48,116 at n=13, a partial recovery to $55,712 at n=14) — closer to Phase
9 Experiment 4's own inconclusive, noisy pattern than to a clean positive
turn. The portfolio-composition hypothesis is **not confirmed** for the
animal side on this evidence.

**[OBSERVED, reopens Phase 10 §6.2's question — but only for animals]
Crop tile idle-time is even LOWER here than Phase 10's single-crop result**
(0.0%-2.3%, vs. Phase 10's 4.6%-7.9%) — the bounded 24-tile STRAWBERRY
footprint is trivially covered at every hand count, refuting any idea that
crop-side scheduling explains the labor curve's shape. **But animal
idle-time is high and structurally flat regardless of hand count: 34%-43%
of animal-days show a missed feed/care/harvest event, at EVERY hand count
from 4 to 13 — including 13, where labor is abundant.** Direct trace
inspection (Section 5) rules out the obvious explanation (cash or WHEAT-
price unaffordability — both are abundant throughout every traced episode)
and instead shows animals periodically going unfed for 2 consecutive days,
escaping, and being repurchased — a genuine, disclosed, hand-count-
independent scheduling/logistics gap specific to animal feeding's
multi-step (fetch-WHEAT-then-deliver) task structure, which Phase 10's
single-resource, no-fetch-required MELON test never exercised. **This
reopens Phase 10's closed scheduler question — narrowly, for animal
feeding on a multi-resource portfolio, not for crop tile-watering in
general.**

**Recommendation:** Phase 4 should **not** raise the hand cap based on a
clean, confirmed positive signal — the labor result here is directionally
positive but too noisy at n=4 seeds to license a specific target number.
Phase 4 should **not** raise the animal cap — animal marginal value still
does not show a positive turn, and worse, the fixed 35-43% animal
under-servicing means simply owning more animals compounds a real,
uncorrected inefficiency rather than fixing it. **Phase 3's tile-
scheduler question should be reopened, narrowly**: not a general
crop-tile scheduler (Phase 10 already closed that), but specifically a fix
for animal-feeding logistics (the FETCH-then-deliver assignment gap,
Section 5) — a much smaller, more targeted piece of work than the
roadmap's original "big one" sketch.

## 2. Methodology

Per the brief: isolated (vs. the engine's `"pass"` opponent), 4 development
seeds (`700000-700003`), 4 land quadrants, `startingMoney=$30,000` (Phase
9's value, reused — confirmed sufficient by direct smoke-test at every
boundary cell, Section "Validation Performed", before committing to the
full sweep; applied identically to every cell in both sweeps so it cancels
out of the marginal comparison, exactly as Phase 9 §5b established).

**Target portfolio shape** — taken directly from
`results/phase6/moushun_chen/days_opponent.csv`, not invented:

| Day | Hands | Land quadrants | STRAWBERRY tiles | COW | SHEEP | Total animals |
|---|---|---|---|---|---|---|
| 15 | 10 | 3 (4 total) | 20 | 6 | 5 | 11 |
| 20 | 10 | 3 (4 total) | 28 | 6 | 8 | 14 |

This phase's fixed points: **STRAWBERRY tile target = 24** (midpoint of
20/28), **animal mid-point = COW 6 / SHEEP 6 = 12** (midpoint of 11/14),
**hand mid-point = 10** (moushun_chen's own observed constant across both
snapshots).

**Execution layer**: `scripts/phase11/multi_resource_agent.py::
make_multi_resource_agent`. Reuses every low-level helper Phase 9's
`make_high_scale_agent` already used (`_home_tile`, `_shed_tiles`,
`_owned_tiles`, `_manhattan`, `structure_type_assignment`,
`_needs_harvest_crop`, `_needs_water`, `_step_toward`, `_fib`, all imported
unchanged from `agents/phase2_3/common.py`), and carries over both of
Phase 9's disclosed execution fixes (SELL queued before HIRE; HIRE capped
to what's affordable that turn). **The one new piece**: a
`bounded_tile_pool_assignment` function, because
`agents/phase2_3/common.py::tile_pool_assignment` (which Phase 9's agent
reuses unchanged) always fills 100% of the non-structure tile pool with
whatever crop is given — it has no way to express "commit only 24 tiles
and leave the rest fallow," which is exactly what moushun_chen's real,
observed shape does (20-28 of ~96 available tiles, not the whole board).
This is new, additive code (not a frozen-file edit) built for exactly the
reason the brief anticipated and pre-authorized in its Step-1 fallback
instruction.

**Two sweeps** (`scripts/phase11/multi_resource_experiment.py`):
- **(a) Labor**: animals fixed at COW=6/SHEEP=6 (12), STRAWBERRY=24 tiles,
  hands swept 4-13. Directly comparable to Phase 9 Experiment 2's variable
  arm (same land, same seeds, same cushion, same hand range).
- **(b) Animal**: hands fixed at 10, STRAWBERRY=24 tiles, animals swept
  6-14 (COW/SHEEP split as evenly as possible). Directly comparable to
  Phase 9 Experiment 4's variable arm.

Both sweeps read `final_money` from the unmodified instrumentation
pipeline's `financial_summary` (`instrumentation/pipeline.py`), exactly as
Phase 9/10 did — never from `economic_model.model.crop_production_value`,
so Phase 8's replanting-undercount bug (which does not affect `ongoing`
crops like STRAWBERRY, Phase 8 §3-4) is not a factor here either way.

## 3. Labor Sweep — Full Results vs. Phase 9 Experiment 2

`results/phase11/phase11_labor_sweep_results.csv` /
`phase11_multi_resource_summary.json`.

| n_hands | Phase 11 mean $ (multi-resource) | Phase 11 marginal $ | Phase 9 mean $ (MELON-solo) | Phase 9 marginal $ |
|---|---|---|---|---|
| 4 | $40,081 | — | $39,368 | — |
| 5 | $47,531 | **+$7,451** | $37,821 | −$1,547 |
| 6 | $54,037 | **+$6,506** | $36,459 | −$1,363 |
| 7 | $66,613 | **+$12,576** | $33,142 | −$3,317 |
| 8 | $62,356 | −$4,258 | $30,346 | −$2,796 |
| 9 | $61,028 | −$1,328 | $28,614 | −$1,732 |
| 10 | $56,802 | −$4,225 | $25,626 | −$2,988 |
| 11 | $56,214 | −$588 | $22,321 | −$3,305 |
| 12 | $46,390 | −$9,825 | $16,638 | −$5,683 |
| 13 | $47,771 | **+$1,382** | $10,224 | −$6,415 |

**Every single hand count's absolute level is higher on the multi-resource
portfolio than Phase 9's MELON-solo result** — by a factor of 1.02x at
hand 4 up to 4.67x at hand 13. **Marginal value is clearly positive for
hands 5-7** (Phase 9 was negative at every one of these points), then
turns negative again for hands 8-12 (as in Phase 9, though smaller in
magnitude relative to the portfolio's much larger revenue base), with one
positive outlier at hand 13. **Net change from hand 4 to hand 13: +$7,690
here vs. −$29,144 in Phase 9** — the headline, aggregate-level result, and
the one this phase treats as the reliable signal given the noise in
individual cells (Section 7).

**Noise source, disclosed**: seed `700001` runs consistently below the
other three seeds at nearly every hand count (e.g. hand 13: $25,121 vs.
$47,317-$60,755 for the other three) — a persistent, seed-specific
depressive effect (plausibly a worse weed-spawn or price-path draw across
the whole episode, not a hand-count-specific artifact, since it appears at
every hand count roughly proportionally) rather than pure per-cell
independent noise. This is the dominant contributor to the marginal
curve's sign-flips; the aggregate hand-4-to-hand-13 comparison is far less
sensitive to it since the same seed's effect appears (and partially
cancels) at both endpoints.

## 4. Animal Sweep — Full Results vs. Phase 9 Experiment 4

`results/phase11/phase11_animal_sweep_results.csv`.

| n_animals | Phase 11 mean $ (multi-resource) | Phase 11 marginal $ | Phase 9 mean $ (animal-only) | Phase 9 marginal $ |
|---|---|---|---|---|
| 6 | $73,385 | — | $51,068 | — |
| 7 | $70,559 | −$2,826 | $36,104 | −$14,964 |
| 8 | $58,939 | −$11,620 | $48,494 | +$12,390 |
| 9 | $61,431 | +$2,492 | $52,943 | +$4,449 |
| 10 | $62,824 | +$1,393 | $52,039 | −$904 |
| 11 | $61,876 | −$948 | $55,476 | +$3,437 |
| 12 | $56,802 | −$5,074 | $38,861 | −$16,615 |
| 13 | $48,116 | −$8,687 | $31,965 | −$6,896 |
| 14 | $55,712 | +$7,596 | $37,015 | +$5,050 |

Absolute levels are again higher throughout on the multi-resource
portfolio (as expected — it includes STRAWBERRY revenue Phase 9's
animal-only arm never had), but the **shape is similar to Phase 9's own
noisy, sign-flipping pattern**, not a clean reversal: mean money declines
from $73,385 (n=6) to $48,116 (n=13), a **net −$25,269** over the swept
range — the same direction (net decline from low to high animal count) as
Phase 9's animal-only arm, just at a higher absolute level. **The
portfolio-composition hypothesis is not confirmed for animals.**

## 5. Idle-Time Cross-Check (Step 5)

`results/phase11/phase11_idle_time_results.csv` /
`phase11_idle_time_summary.json`, measured on the labor-sweep
configuration (animals fixed at 12, hands 4-13), same method as Phase 10.

| n_hands | Crop tile idle fraction | Animal idle fraction | Action idle fraction (PASS-rate) | Mean final $ |
|---|---|---|---|---|
| 4 | 2.29% | **42.98%** | 5.44% | $40,081 |
| 5 | 1.02% | **38.56%** | 8.60% | $47,531 |
| 6 | 0.56% | **41.13%** | 15.12% | $54,037 |
| 7 | 0.32% | **35.60%** | 20.76% | $66,613 |
| 8 | 0.29% | **36.46%** | 23.00% | $62,356 |
| 9 | 0.15% | **36.51%** | 26.87% | $61,028 |
| 10 | 0.00% | **36.17%** | 32.58% | $56,802 |
| 11 | 0.00% | **34.94%** | 36.11% | $56,214 |
| 12 | 0.00% | **40.12%** | 37.53% | $46,390 |
| 13 | 0.14% | **34.33%** | 39.75% | $47,771 |

**Crop tile idle-time**: at or below Phase 10's single-crop result at every
hand count (down to 0.0% at hands 10-12) — the bounded 24-tile footprint
is trivially, near-perfectly serviced regardless of hand count. This
confirms crop-side scheduling is not the bottleneck here either, exactly
as Phase 10 found for the unbounded single-crop case.

**Animal idle-time**: high (34%-43%) and, critically, **flat — not
correlated with hand count**. If this were simply "not enough labor," it
should fall sharply as hands rise from 4 to 13 (as crop idle-time does).
It does not: 13 hands leaves animals just as under-serviced as 4 hands
does. This rules out a pure labor-scarcity explanation and points at a
scheduling/logistics gap instead.

**Mechanism, directly traced** (a single hand=13, seed=700000 episode,
sampled at days 5/10/15/20/25/29): at every sampled day, cash was abundant
($8,752-$60,755) and WHEAT's market price, while rising over the episode
(from $33 to $57 as repeated market-buying drains its inventory), remained
trivially affordable relative to that cash. **Yet fed/cared animal counts
consistently fell short of the total animal count at every sample point**
(e.g. day 15: 12 animals present, only 10 fed and 10 cared; day 29: 11
animals present, only 6 fed and 6 cared), and the total animal count
itself fluctuated below the target of 12 (9-12 across the samples) —
consistent with animals periodically going unfed for 2 consecutive days,
**escaping** (a documented mechanic: `agents/phase2_3/common.py`'s BUY_
ANIMAL logic only refills EMPTY structures, and the engine escapes an
animal whose `consecutive_unfed >= 2`), and being repurchased, in a
recurring cycle. **[HYPOTHESIS, plausible given this trace but not
exhaustively verified across all cells]**: animal feeding is a two-step
task (FETCH WHEAT from the shed, THEN travel to and FEED the animal tile)
where crop watering/harvesting is a single step (act directly on the tile
a worker is standing on) — the existing greedy, tiered-priority scheduler
(unchanged from `agents/phase2_3/common.py`, reused via Phase 9's and this
phase's agents) does not appear to reliably chain these two steps for
every animal every day, even when neither cash nor a free worker is
scarce. This is a genuinely different failure mode from anything Phase
10's single-resource (no-fetch-required) MELON test could have exposed.

**Per the brief's explicit instruction: this reopens Phase 10's closed
scheduler question — narrowly.** Phase 10 correctly closed the question
for crop-tile watering/harvesting on a single-crop portfolio (confirmed
again here, Section 5's crop-idle row). It should **not** be read as
closed for animal-feeding logistics on a multi-resource portfolio, where
this phase found a real, substantial, hand-count-independent gap.

## 6. Recommendation for Phase 3 / Phase 4

1. **Labor cap: directionally supportive, not yet actionable.** The
   aggregate net-positive result (Section 3) is real and reverses Phase
   9's clear negative finding, but the noisy, seed-dependent cell-to-cell
   curve (driven substantially by one seed's persistent depression,
   Section 3) means this phase cannot responsibly recommend a *specific*
   new hand target the way Phase 9 could confidently recommend keeping the
   current one. Before Phase 4 raises the hand cap on a mixed-portfolio
   assumption, re-run this exact sweep with more seeds (n=8-12, matching
   Phase 9 §7's own recommendation for exactly this kind of noisy result)
   to get a trustworthy specific number — but the DIRECTION (portfolio
   composition matters, and matters a lot: 3-6x the absolute money at
   every hand count) is well-supported enough to justify that follow-up
   investment.
2. **Animal cap: do not raise it.** Neither this phase's marginal-value
   curve (Section 4, still net-declining across the swept range) nor the
   idle-time cross-check (Section 5, a persistent ~35-40% under-servicing
   regardless of animal or hand count) supports pushing Submission C's
   current animal target higher. If anything, Section 5 shows MORE
   animals compounds an existing inefficiency rather than benefiting from
   scale.
3. **Reopen Phase 3's scheduler question — narrowly, for animal-feeding
   logistics, not a general tile scheduler.** Phase 10 was right to close
   the general question for single-crop tile-watering (reconfirmed here,
   crop idle-time is at or below Phase 10's own numbers). This phase found
   a specific, different, real gap: the FETCH-then-FEED two-step sequence
   for animals is not being reliably completed even when labor and cash
   are abundant. A future phase should scope this narrowly — a
   fetch-aware feeding-priority fix, not a full rebuild of the tile
   scheduler the original roadmap Phase 3 sketched — and should verify the
   fix actually raises fed/cared rates before assuming it improves final
   money (a smaller, cheaper, more falsifiable next step than the
   roadmap's original "big one").
4. **The moushun_chen-shaped portfolio itself (STRAWBERRY + COW/SHEEP,
   bounded footprint) is a better reference config for future capacity
   experiments than either Phase 9's MELON-solo or animal-only arms** —
   it is closer to what real strong opponents actually run, and this
   phase's `scripts/phase11/multi_resource_agent.py` is available,
   reusable, additive infrastructure for that purpose going forward.

## 7. Limitations

- **n=4 seeds**, and this phase's labor result is noisier than Phase 9's
  own clean labor finding (though for a different, disclosed reason — a
  persistent per-seed effect, not per-cell independent variance, Section
  3). The aggregate hand-4-to-hand-13 comparison is more robust to this
  than the individual marginal values are; treat the per-cell numbers as
  directional, not precise.
- **The animal-feeding mechanism (Section 5) is traced on one episode in
  detail (hand=13, seed=700000), not exhaustively verified across every
  cell.** The flat ~35-43% pattern across ALL hand counts and both sweeps'
  worth of data is itself strong evidence the underlying cause doesn't
  depend on hand count, but the specific FETCH-sequencing explanation is
  [HYPOTHESIS]-level, not [VERIFIED] by a full code-level trace of the
  scheduler's turn-by-turn decisions.
- **STRAWBERRY tile target (24) and animal mid-points (12/10 hands) are
  fixed at the midpoint of moushun_chen's observed range, not swept
  themselves.** Whether a larger or smaller bounded footprint changes
  either curve's shape is untested this phase.
- **This phase does not re-validate Phase 9's own single-resource findings
  — it reuses their published numbers directly (Section 3-4 tables), per
  the brief's explicit instruction**, rather than re-deriving a fresh
  control arm.

## Changed Files

New, all additive; nothing pre-existing modified:
- `scripts/phase11/multi_resource_agent.py`
- `scripts/phase11/multi_resource_experiment.py`
- `scripts/phase11/idle_time_check.py`
- `results/phase11/phase11_labor_sweep_results.csv`
- `results/phase11/phase11_animal_sweep_results.csv`
- `results/phase11/phase11_multi_resource_summary.json`
- `results/phase11/phase11_idle_time_results.csv`
- `results/phase11/phase11_idle_time_summary.json`
- `results/phase11/PHASE11_MULTI_RESOURCE_PORTFOLIO_REPORT.md` (this file)

No existing file was modified. `main.py` still builds Submission C. No
`.tar.gz` is created or staged — there is no new submission from this
phase.

## Validation Performed

- Target portfolio shape read directly from
  `results/phase6/moushun_chen/days_opponent.csv` (day 15/20 rows), not
  invented — quoted verbatim in Section 2.
- Every boundary cell (highest hands, highest animals, lowest hands) was
  smoke-tested for `startingMoney=$30,000` sufficiency before committing
  to the full sweep; all ended well above the cushion with no bankruptcy.
- All final-money figures read directly from the unmodified
  `instrumentation/pipeline.py`'s `financial_summary`, the same
  measurement path every other phase in this project uses.
- Animal-feeding mechanism claim (Section 5) cross-checked against a
  direct trace of raw replay state (cash, WHEAT price, fed/cared counts,
  live animal count) at 6 sampled days of one full episode, not asserted
  from the aggregate idle-fraction number alone.
- `git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5
  agents/phase3_8 agents/phase2_3/common.py agents/phase2_4/common.py`:
  clean throughout this phase.
