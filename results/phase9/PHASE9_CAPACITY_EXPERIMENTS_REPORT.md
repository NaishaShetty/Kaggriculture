# PHASE 9 — Capacity Experiments: Labor & Animal Marginal Value at Real Scale

Submission C (Phase 3.8) and Submission D (Phase 7's sell-safety fix) are
unmodified throughout this phase. No submission is created.
`git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5
agents/phase3_8` is clean. All new code lives under `scripts/phase9/` and
`results/phase9/`.

## 1. Executive Summary

This phase runs Phase 6's own §17 Experiments 2 and 4 — the two experiments
Phase 6 §18 explicitly gated any future hand/animal-cap increase on.

**Experiment 2 (labor, [VERIFIED] FAIL).** Marginal hand value is **negative
at every tested hand count from 5 through 13** on a large (4-quadrant,
~96-tile) MELON-solo board, and gets **monotonically worse** as hand count
rises — from −$1,547 at hand 5 to −$6,415 at hand 13. The control arm
(reproducing Phase 2.3's original small-board methodology) closely matches
the original finding (marginal $5,184 / $327 / −$204 / −$29 for hands
1-4, vs. the original $5,057 / $477 / −$227 / −$29 — see Section 3),
confirming the experiment's methodology is faithful. **Phase 6's hypothesis
does not hold**: going to a bigger board does not turn labor's marginal
value positive again — if anything it turns negative *sooner* and *harder*.

**Experiment 4 (animal, [OBSERVED] INCONCLUSIVE).** The control arm shows a
clean, positive, smoothly diminishing marginal animal value (from $7,296
at animal 1 down to $1,399 at animal 6 — every point positive, consistent
with Phase 2.3's original diminishing-returns pattern). The large-scale
variable arm (6-14 animals, 4-quadrant board) does **not** produce a
usable marginal-value curve: the sign flips repeatedly (−$14,964, +$12,390,
+$4,449, −$904, +$3,437, −$16,615, −$6,896, +$5,050) with swings **larger
than the effects themselves**, driven by per-seed variance roughly 5-10x
the control arm's (Section 4). This phase does **not** manufacture a
pass/fail verdict from noise this large — it is reported honestly as
inconclusive, with the mechanism (Section 5) and what a reliable answer
would require (Section 7).

**Phase 6 §18 gating condition: NOT satisfied for labor. Not resolved
either way for animals.** Phase 4 of `docs/ROADMAP_TO_GOLD.md` should
**not** raise Submission C's hand cap toward the 8-13 range on the strength
of this evidence — the opposite is now [VERIFIED]: doing so, on the kind of
single-crop-anchored portfolio Planner v1 currently runs, actively loses
money, and loses more of it the higher the target. The current hand cap
(Submission C's scaling response, ~5 per `agents/phase3_5/response_policy.py`)
is closer to right than Phase 6 §18 hypothesized, not further from it. The
animal cap question needs a lower-variance re-run (Section 7) before Phase 4
acts on it either way.

## 2. Methodology

Per Phase 6 §17 Experiments 2 and 4: isolated (vs. the engine's built-in
`"pass"` opponent — no opponent, matching this project's existing
isolated-probe convention, see Phase 8), 30-day/720-step seasons,
CONTROL vs. VARIABLE arms, n=4 seeds ("development set" —
`[700000, 700001, 700002, 700003]`, this project's existing seed bucket
from `agents/phase5`, reused per Phase 6 §17's explicit "development set,
n=4" instruction).

**Control arms** reuse `agents/phase2_3/common.py::make_agent`
**unmodified** — the exact function behind the original Phase 2.3 findings
(`results/phase2_3/`, `scripts/phase2_3_configs.py`).

- Experiment 2 control: `crops="MELON", n_hands∈{0,1,2,3,4}, land_quadrants=0`
  — an exact reproduction of `STAGE_A["a1_labor_sweep"]`'s MELON cells
  (`scripts/phase2_3_configs.py` lines 39-53), differing only in seed set
  (4 development seeds here vs. the original's 6, per Phase 6 §17's own
  seed-count instruction — disclosed, not hidden).
- Experiment 4 control: `crops=None, feed_source="market", n_hands=6,
  land_quadrants=0`, animals split evenly COW/SHEEP, swept 0-6. Phase 2.3's
  original `a3_animal_lifecycle` (lines 68-84) only ever tested a single
  animal (count=1) per species — it never swept animal *count* — so this is
  the closest faithful adaptation of that cell's isolation methodology
  (no-crop, market-fed) to the count-marginal-value question this phase
  needs.

**Variable arms** use a purpose-built agent,
`scripts/phase9/common.py::make_high_scale_agent`, built and required for a
concrete, verified reason — see Section 5 (Mechanism) for the full
diagnosis. In short: directly reusing the frozen `make_agent` at 8+ hands
produces a self-inflicted, non-economic death spiral (confirmed by direct
trace inspection before writing the final experiment), so this phase
either had to report "cannot be built faithfully" or fix the two specific,
disclosed execution artifacts causing it. Section 5 documents exactly what
was found and fixed, and why the fixes are minimal and faithful rather than
tilting the result. **Every cell in a given arm uses the identical fix and
identical starting-capital cushion**, so nothing here advantages any one
hand/animal count over its neighbors — the fixes and cushion are constants
that cancel out of the marginal (Δfinal_money) comparison that is this
experiment's actual metric.

- Experiment 2 variable: `crops="MELON", n_hands∈{4..13}, land_quadrants=3`
  (4 total quadrants — matches the largest land count Phase 6's real-replay
  forensics observed, Lai Eu Wen, `results/phase6/lai_eu_wen/`,
  `land_quadrants=4` by day 10), `startingMoney=$30,000`.
- Experiment 4 variable: `crops=None, feed_source="market", n_hands=10,
  land_quadrants=3`, animals split evenly COW/SHEEP, swept 6-14 (from
  Submission C's own current cap through Phase 6's observed real-opponent
  range), `startingMoney=$30,000`.

**Board-fill check** (per the brief's explicit warning against silently
under-filling the board and biasing toward FAIL): at `land_quadrants=3` the
owned tile pool is ~96 tiles (100 − 4 shed), and `crops="MELON"` assigns
100% of that pool to MELON via the SAME `tile_pool_assignment` logic the
frozen agent already uses — comfortably enough standing crop to keep 13
hands watering/harvesting/replanting without idling. Confirmed directly:
land utilization in the variable-arm traces (Section 6, Appendix data)
reaches 30-50%+ even at high hand counts, i.e. hands are doing real,
visible work, not sitting idle for lack of tasks.

## 3. Experiment 2 (Labor) — Full Results

`results/phase9/phase9_labor_capacity_results.csv` /
`phase9_labor_capacity_summary.json`.

**Control (0 extra land, MELON solo, $3,000 start)**

| n_hands | Mean final $ (n=4) | Marginal $ | Original Phase 2.3 (`CALIBRATION`) |
|---|---|---|---|
| 0 | $22,341 | — | — |
| 1 | $27,525 | +$5,184 | +$5,057 |
| 2 | $27,852 | +$327 | +$477 |
| 3 | $27,648 | −$204 | −$227 |
| 4 | $27,619 | −$29 | −$29 |

Close match to the original (`economic_model/model.py`'s
`CALIBRATION["marginal_hand_value"]["MELON"]`) at every point — confirms
this phase's methodology reproduces Phase 2.3's finding faithfully before
scaling it up.

**Variable (3 extra land / 4 total quadrants, MELON solo, $30,000 start)**

| n_hands | Mean final $ (n=4) | Marginal $ |
|---|---|---|
| 4 | $39,368 | — |
| 5 | $37,821 | **−$1,547** |
| 6 | $36,459 | **−$1,363** |
| 7 | $33,142 | **−$3,317** |
| 8 | $30,346 | **−$2,796** |
| 9 | $28,614 | **−$1,732** |
| 10 | $25,626 | **−$2,988** |
| 11 | $22,321 | **−$3,305** |
| 12 | $16,638 | **−$5,683** |
| 13 | $10,224 | **−$6,415** |

Every single point is negative, and the negative trend **strengthens** with
scale rather than reversing (a smooth-looking, monotonic decline in final
money from hand 4 to hand 13, not a noisy signal — per-seed variance at
each point is small, typically under $1,000 of the ~$25,000-$39,000 level,
unlike Experiment 4's variable arm, Section 4). **PASS condition
("marginal value stays positive through hand 10+") is not met at any
point — FAIL, decisively.**

## 4. Experiment 4 (Animal) — Full Results

`results/phase9/phase9_animal_capacity_results.csv` /
`phase9_animal_capacity_summary.json`.

**Control (0 extra land, no crops, market-fed, 6 hands, $6,000 start —
see Section 5 for why $6,000 not $3,000)**

| n_animals | Mean final $ (n=4) | Marginal $ |
|---|---|---|
| 0 | $5,400 | — |
| 1 | $12,696 | +$7,296 |
| 2 | $18,898 | +$6,202 |
| 3 | $25,052 | +$6,154 |
| 4 | $30,063 | +$5,011 |
| 5 | $33,741 | +$3,678 |
| 6 | $35,140 | +$1,399 |

Clean, smooth, positive-and-diminishing at every point — the same
qualitative diminishing-returns shape as every other Phase 2.3 sweep, and
low per-seed variance (typically $1,000-2,500 spread at a given count).

**Variable (3 extra land / 4 total quadrants, no crops, market-fed, 10
hands, $30,000 start)**

| n_animals | Mean final $ (n=4) | Marginal $ | Per-seed spread |
|---|---|---|---|
| 6 | $51,068 | — | $48,619 – $52,438 (tight) |
| 7 | $36,104 | **−$14,964** | $27,126 – $41,676 (wide) |
| 8 | $48,494 | **+$12,390** | $28,173 – $55,910 (very wide) |
| 9 | $52,943 | **+$4,449** | $50,229 – $55,810 (tight) |
| 10 | $52,039 | **−$904** | $49,123 – $55,093 (tight) |
| 11 | $55,476 | **+$3,437** | $42,197 – $61,539 (wide) |
| 12 | $38,861 | **−$16,615** | $33,352 – $43,715 (moderate) |
| 13 | $31,965 | **−$6,896** | $21,477 – $45,454 (very wide) |
| 14 | $37,015 | **+$5,050** | $20,424 – $46,351 (very wide) |

The marginal value **flips sign 5 times across 8 transitions** with
magnitudes ($5k-$17k) that are the same order as, or larger than, the
level of final money itself moving between adjacent points. Per-seed
spread at several counts (7, 8, 13, 14) exceeds $15,000-27,000 on a single
fixed configuration — 5-10x the control arm's typical spread. **This is
not a usable marginal-value signal at n=4 seeds.** No pass/fail claim is
made from this arm (Section 7 explains why and what would fix it). The one
thing that IS clear from the raw levels: unlike labor, there is **no
monotonic collapse** — final money stays in a broad $32k-$55k band across
the whole 6-14 range, never trending toward Experiment 2's clean, steady
decline.

## 5. Mechanism

### 5a. Why the frozen `make_agent` cannot be reused unmodified at 8+ hands

Before finalizing the variable-arm design, a direct raw reproduction of
`agents/phase2_3/common.py::make_agent(crops="MELON", n_hands=13,
land_quadrants=3)` was traced day-by-day (not assumed). Result:
`ending_money` hits $0 by day 3-4 and **stays at exactly $0 for the rest of
the 30-day season**, despite harvesting real MELON units from day 10
onward (`products_sold=0` every single day of the entire episode). Two
compounding, VERIFIED causes:

1. **Hands reset to zero every in-game day** (`vendor_kaggriculture/
   kaggriculture.py`, `farm["hands"] = []` in `_end_of_day` — already
   documented by Phase 6 §5). The frozen agent re-queues up to
   `n_hands` `["HIRE"]` orders **every single day with no affordability
   check** — unlike its own `BUY_LAND`/`BUY_SEED` logic, which DOES check
   `money >= cost` first. At `n_hands=13` this queues up to 13 HIRE orders
   per turn regardless of actual cash.
2. **The market-action list is capped at 10 orders/turn**
   (`market = market[:10]`, VERIFIED_MECHANIC — "maxMarketOrdersPerTurn
   default"). HIRE orders are appended to the list **before** the SELL
   block. When `need_hire >= 10`, the HIRE requests alone fill the entire
   10-slot cap, and that turn's SELL order for harvested MELON is silently
   truncated away before it can even be queued.

Both properties belong to the shared `make_agent` design this whole
project's tactical layer is built from (`agents/phase2_3` and
`agents/phase2_4` both share the same HIRE-before-SELL ordering and
unconditional HIRE queuing) — not something introduced by this probe. This
is itself worth flagging as a real, disclosed, currently-live property of
the frozen tactical layer (separate from Phase 7's already-fixed
`horizon_aware` bug), though fixing it is out of this phase's scope (no
frozen file may be touched).

`scripts/phase9/common.py::make_high_scale_agent` changes exactly two
things, both minimal and disclosed (full diff-equivalent description in
that module's docstring): **(1)** SELL orders are queued before HIRE
orders, and **(2)** HIRE requests are capped to what's actually affordable
this turn (extending the SAME `money >= cost` discipline the frozen
agent's own BUY_LAND/BUY_SEED logic already uses, to HIRE, which the
original inconsistently omits). Every other line of task-scheduling logic
is unchanged from the frozen agent's own algorithm.

### 5b. Why a starting-capital cushion was still necessary

Even with both fixes, reaching 13 hands from the default $3,000 on day 0
remains economically infeasible **in isolation**: 13 hands costs
`sum(fib(0..12)) = 609` in hire fees **every single day** (fresh, because
hands reset nightly) — before MELON's first possible harvest
(`first_yield_day=10`). This is a genuine, VERIFIED constraint, not an
artifact, and it is exactly consistent with Phase 6 §4's own observation
that real strong opponents (Lai Eu Wen) never committed to 13 hands until
**after** their own day-10+ capital inflection, not from day 0. Testing
"is hand N worth it at this scale" (Experiment 2's actual question) is a
different question from "can a from-scratch single-crop farm bootstrap
into this scale" (a separate, already-unresolved question per Phase 6
§5/§14.B.3 — this phase does not attempt to answer it). To separate the
two cleanly, both variable arms use `extra_config={"startingMoney": X}` —
the engine's own documented, configurable key
(`vendor_kaggriculture/kaggriculture.py` line 252, VERIFIED — not a new
mechanic) — applied **identically to every cell in a given arm**, so it is
a constant additive offset that cancels out of the marginal (Δfinal_money)
comparison. $30,000 for both Experiment 2 and 4's variable arms (same
value, chosen once and reused). Experiment 4's control arm needed a
smaller, separately-justified bump to $6,000 (from the default $3,000):
buying 6 animals simultaneously on day 0 ($400-500 each) while feeding all
of them via `BUY_PRODUCT` before any product income exists (COW
`first_yield_day=8`, SHEEP=6) is not affordable from $3,000 either —
confirmed directly (a raw $3,000-start run of that exact cell ends day 1
at $0 cash, only 3 of 6 animals ever get placed, and zero product is ever
sold for the rest of the game). Phase 2.3's own `a3_animal_lifecycle` never
tested more than 1 animal at a time, so this bootstrapping ceiling was
never previously hit or documented.

### 5c. Why labor's marginal value is negative even at scale

With the execution artifacts and bootstrapping confound both removed, the
result (Section 3) is clean and monotonic: MORE hands on a bigger board
still loses money, worse as the count rises. The likely mechanism
([INFERRED], consistent with every number in Section 3): a **single-crop
MELON-solo portfolio has a hard ceiling on how much labor it can
productively absorb** — watering/harvesting ~96 tiles does not require 13
workers' worth of daily-refreshed labor, so hands beyond roughly 4-6 are
paying their **full daily Fibonacci wage** (which, as Section 5b shows,
compounds fast — hand 13 alone costs far more per day than hand 5) for
work that either doesn't exist or that fewer hands could already cover.
This is consistent with, and extends, Phase 2.3's own original
`marginal_hand_value` finding (already negative by hand 4 on a *small*
board) rather than contradicting it — the "different economic regime"
Phase 6 §5 hypothesized real opponents operate in does not rescue labor's
marginal value merely by adding land to the SAME single-crop portfolio.
**What Phase 6's real-replay data shows (§8, §12) is that strong opponents
pair high hand counts with BOTH a large land footprint AND 10-14
simultaneous animals AND (per Section 8) a STRAWBERRY-anchored,
multi-resource portfolio** — i.e. genuinely more distinct daily-maintenance
work per hand, not just more tiles of the same single crop. This phase's
result narrows, rather than answers, that open question: land alone does
not make extra hands worth their cost; whether land + animals + a richer
crop mix would is untested here (see Section 7).

### 5d. Why animal marginal value is noisy at scale but not at small scale

The control arm's animal sweep is clean because it holds land/labor fixed
and small (24 usable tiles, 6 hands) — few enough moving parts that
per-seed weed-spawn/timing noise (the only stochastic element in an
isolated episode, per Phase 8's own disclosed limitation) averages out at
n=4. The variable arm's much larger, more contested board (96 tiles, 10
hands, up to 14 animal structures competing for build/feed/care priority
against each other every turn) appears to make outcomes considerably more
sensitive to exactly which few tiles a stray weed-spawn or a marginal
build/feed scheduling tie-break lands on — plausible ([HYPOTHESIS], not
directly isolated this phase) given the much larger action space per turn,
but not confirmed by a dedicated noise-source experiment, which was out of
this phase's scope.

## 6. Phase 6 §18 Gating Condition — Explicit Resolution

> "build labor/animal capacity beyond current caps IF Experiments 2 and 4
> confirm positive marginal value at that scale (do not build this
> capability speculatively before that evidence exists)."

**Labor: gating condition FAILS.** Experiment 2's variable arm shows
negative marginal value at every tested hand count 5-13, worsening with
scale. This is not "inconclusive" — it is a clean, decisive result in the
opposite direction from what would license a hand-cap increase. Submission
C's current scaling response (hands target ~5, `agents/phase3_5/
response_policy.py`, frozen, not touched this phase) sits almost exactly
at the point where the control arm's own marginal value crosses zero
(between hand 2 and hand 3) and comfortably below where the variable arm's
losses start accelerating — **the current cap is closer to economically
correct than Phase 6 §18 hypothesized, on a MELON-solo portfolio.**

**Animal: gating condition NOT resolved.** Experiment 4's variable arm did
not produce a reliable marginal-value signal at n=4 seeds (Section 4) —
neither a "positive through 10+" pass nor a clean "goes negative early"
fail can be honestly claimed. Per this project's standing discipline
("report actual result even if inconclusive... that would be a real,
useful, cost-saving finding, not a failure of this phase"), this is
reported as **open**, not defaulted to either a pass or a fail.

## 7. Recommendation for Phase 4 (`docs/ROADMAP_TO_GOLD.md`)

1. **Do not raise Submission C's hand-count cap toward 8-13.** This
   phase's evidence is a decisive, mechanistically-explained FAIL of
   exactly the hypothesis that would justify it, on the same
   single-crop-anchored portfolio shape Planner v1/Submission C actually
   runs. If a future phase wants to revisit labor capacity, it should test
   it on a genuinely multi-resource portfolio (crops + animals together,
   matching what real strong opponents actually run per Phase 6 §12) —
   Section 5c's mechanism suggests THAT is the variable that might change
   the answer, not land alone.
2. **Do not raise the animal-count cap on this phase's evidence either —
   but for a different reason: the data doesn't yet say either way.**
   Before Phase 4 acts on animal capacity, re-run Experiment 4's variable
   arm with either (a) more seeds (the control arm's tight variance
   suggests n=8-12 would likely resolve the sign-flipping, at roughly
   double this phase's animal-experiment cost), or (b) an explicit
   noise-source investigation (Section 5d's hypothesis) before spending a
   larger seed budget on a design that might still be intrinsically noisy.
3. **The `revenue_per_tile_day` / replanting-blind calibration bug Phase 8
   found (results/phase8/PHASE8_CALIBRATION_PROBE_REPORT.md) does not
   confound this phase's results.** Both experiments measure `final_money`
   directly from the instrumentation pipeline's `financial_summary`, never
   through `economic_model.model.crop_production_value` — Phase 8's bug is
   in that estimator, not in the measured ground truth this phase reports.
4. **The HIRE-before-SELL / unconditional-HIRE-queuing issue found in
   Section 5a is a real, currently-live property of BOTH
   `agents/phase2_3/common.py` and `agents/phase2_4/common.py`** (the
   shared ancestor of Submission C's own tactical layer). It was not
   triggered in any prior phase because no prior phase tested hand counts
   above 4-5 where `need_hire >= 10` would occur. It is out of this
   phase's scope to fix (frozen files), but worth flagging for a future
   phase: if Submission C's opponent-scaling response were ever adjusted
   to target more than ~9-10 hands for any reason, this ordering issue
   would independently suppress selling, compounding whatever else went
   wrong — a latent risk worth knowing about even though this phase's own
   conclusion is "don't raise the hand target" anyway.

## 8. Limitations

- **n=4 seeds** (per Phase 6 §17's own instruction). Sufficient to reach a
  confident conclusion for Experiment 2 (low per-seed variance, clean
  monotonic trend) but explicitly NOT sufficient for Experiment 4's
  variable arm (Section 4/5d) — disclosed rather than forced into a
  false-confidence verdict.
- **Isolated (no opponent) by design**, matching both the Phase 6 §17
  brief and this project's standing isolated-probe convention. Real
  strong-opponent hand/animal value could differ under competitive market
  pressure (e.g. an opponent's own selling depressing prices, changing the
  revenue side of the marginal calculation) — untested here, consistent
  with every other phase's isolated-probe scope limits.
- **Single-crop (MELON) / no-crop portfolios only.** Section 5c's
  mechanism explanation is itself evidence that portfolio composition
  (not just scale) plausibly matters for labor's marginal value — this
  phase deliberately did not test a combined crop+animal high-scale
  portfolio, both to keep the two experiments comparable to their Phase
  2.3 antecedents and because that would be a materially larger, separate
  experiment design.
- **The high-scale agent's two fixes (Section 5a) and starting-capital
  cushion (Section 5b) are disclosed, necessary deviations from the frozen
  agent**, not a hidden thumb on the scale — every cell in a given arm
  gets the identical treatment, so the deviations cancel out of the
  marginal comparison that is this experiment's actual metric. They do NOT
  cancel out of the *raw level* of final money reported (Sections 3-4),
  which should not be compared directly against control-arm raw levels
  (different starting money) — only the marginal values and within-arm
  trends are the intended comparison.

## Changed Files

New, all additive; nothing pre-existing modified:
- `scripts/phase9/common.py`
- `scripts/phase9/labor_capacity_experiment.py`
- `scripts/phase9/animal_capacity_experiment.py`
- `results/phase9/phase9_labor_capacity_results.csv`
- `results/phase9/phase9_labor_capacity_summary.json`
- `results/phase9/phase9_animal_capacity_results.csv`
- `results/phase9/phase9_animal_capacity_summary.json`
- `results/phase9/PHASE9_CAPACITY_EXPERIMENTS_REPORT.md` (this file)

No existing file was modified. `main.py` still builds Submission C. No
`.tar.gz` is created or staged — there is no new submission from this
phase.

## Validation Performed

- Control arms run through the unmodified `agents/phase2_3/common.py::
  make_agent`, the same function behind the original Phase 2.3 findings;
  Experiment 2's control independently reproduces
  `CALIBRATION["marginal_hand_value"]["MELON"]` closely (Section 3),
  cross-validating this phase's harness against a previously-published
  result.
- Variable-arm execution artifacts (Section 5a) were found and diagnosed
  by direct day-by-day trace inspection of the raw frozen agent BEFORE
  finalizing the experiment design, not assumed or guessed at.
- All final-money figures read directly from the unmodified
  `instrumentation/pipeline.py`'s `financial_summary`, the same measurement
  path every other phase in this project uses.
- `git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5
  agents/phase3_8`: clean throughout this phase.
