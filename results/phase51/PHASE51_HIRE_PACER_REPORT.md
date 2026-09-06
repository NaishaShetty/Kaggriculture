# Phase 51: HIRE Pacer — Sanity Check and 4th-Quadrant Retest

## 0. Context and goal

Submission K (`kaggriculture_phase50_submission_K.tar.gz`, Phase 48's capped-animal-target
fix composed with Phase 46's FEED-priority execution layer) is the currently live/uploaded
submission. This phase asks: can extending Phase 36/45's cash-flow-adaptive purchase-pacer
pattern to `HIRE` — the one purchase type BUY_LAND/BUY_ANIMAL/BUY_SEED all now pace, but HIRE
itself still doesn't — finally make the 4th-quadrant dedicated-hands TOMATO/GOOSE design
(Phase 33's original idea, retested through Phase 46's execution layer by Phase 48 Part B)
viable? Phase 33/48 both diagnosed that design's blocker as a HIRE cash-timing problem: the
daily-recurring Fibonacci hire cost for extra dedicated hands delays the core land ramp,
pushing the 4th (SE) quadrant purchase to day 24-26, far too late for TOMATO (`first_yield_day
=8`) or GOOSE to produce any revenue before the 30-day game ends.

**[VERIFIED]** confirmed directly from source before writing any new code:
- `agents/phase21/execution.py` lines 191-203 (byte-identical in Submission K's own shipped
  `scripts/phase46/feed_priority_execution.py`): HIRE affordability-caps the day's cumulative
  Fibonacci hire cost against the full `money` balance, with **no reserve held back at all**.
- `agents/phase21/risk_posture.py`: the posture-aware `land_purchase_reserve` ($75 BEHIND /
  $150 CLOSE / $300 AHEAD) is the concept BUY_LAND, Phase 36's BUY_ANIMAL pacer, and Phase 45's
  BUY_SEED pacer all already reuse.
- `scripts/phase36/paced_execution.py`'s own docstring explicitly documents that an EARLIER
  version of that module applied one shared reserve (including a next-hire-cost term) to HIRE,
  BUY_LAND, and BUY_ANIMAL together, and that this was reverted after a direct trace found a
  **self-defeating feedback loop**: coupling HIRE to the same feed-buffer reserve term froze
  hiring during exactly the cash-tight moments animals most needed feeding hands, causing MORE
  escapes, not fewer. Phase 36 deliberately left HIRE and BUY_LAND unchanged from
  `agents/phase21/execution.py` as a result. This phase's HIRE pacer is therefore a genuinely
  live question, not a settled one — Phase 36's warning was about coupling HIRE to the
  *feed-buffer* reserve specifically, not about gating HIRE against `land_purchase_reserve`
  alone (a smaller, flatter number). Whether that smaller gate reproduces the same failure mode
  is checked directly below, not assumed either way.
- Per the brief's own reference to a "Phase 49 lesson": `docs/BIG_SWING_PLAN.md`'s Phase 49
  update block **[OBSERVED]** confirms two independently-safe execution-layer fixes (Phase 45's
  BUY_SEED pacer + Phase 46's FEED-priority reorder) combine to a real, diffuse -9.47%
  regression despite neither fix's own diagnosed mechanism reappearing — a generalized warning
  that validating fixes independently does not certify their combination. This phase's HIRE
  pacer is therefore built on top of ONLY Phase 46's FEED-priority fix (Submission K's own
  shipped execution layer), not stacked on Phase 45's BUY_SEED pacer as well, since that
  specific combination was already found unsafe and was never shipped.

## 1. What was built

`scripts/phase51/hire_paced_execution.py::make_hire_paced_execution_agent` — a phase51-local
copy of `scripts/phase46/feed_priority_execution.py::make_feed_priority_execution_agent` with
**exactly one block changed**: the HIRE section now gates the day's cumulative affordable hire
cost against `money - land_purchase_reserve` instead of the full `money` balance. Every other
line (BUY_LAND, BUY_SEED, Phase 36's BUY_ANIMAL pacing, Phase 46's FEED tier-0.5 reorder, the
BUY_PRODUCT feed logic, and the entire task-scheduling section) is copied verbatim, composing
Submission K's own shipped execution layer rather than reimplementing it — the same
composition discipline Phase 45 used when it extended the pacer to BUY_SEED.

```python
# --- HIRE, PACED (Phase 51 -- the new piece) ---
current_hands = len(me.get("hands", []))
need_hire_target = max(0, n_hands - current_hands)
hire_budget = money - land_purchase_reserve
affordable, cum = 0, 0.0
for i in range(need_hire_target):
    c = _fib(current_hands + i)
    if cum + c > hire_budget:
        break
    cum += c
    affordable += 1
for _ in range(affordable):
    market.append(["HIRE"])
money -= cum
```

`scripts/phase51/hire_paced_capped_animal_portfolio_agent.py::make_hire_paced_capped_animal_portfolio_agent`
— mirrors `scripts/phase48/capped_animal_portfolio_agent.py` exactly, swapping in the new HIRE-paced
execution layer under Phase 48's capped-animal target wrapper (`cap_total=8`, wrapping
`agents/phase21/portfolio.py::portfolio_targets` unmodified). This is Submission K's own shipped
portfolio, unmodified, run through the new execution layer — the object under test for the
mandatory sanity check.

`scripts/phase51/isolated_screen_sanity.py` — 4-seed isolated-economy screen, mirroring
`scripts/phase48/isolated_screen_animal_cap.py`'s structure, comparing Submission K's shipped
agent (`scripts/phase48/capped_animal_portfolio_agent.py`) against the HIRE-paced variant on the
same dev seeds (700000-700003).

`scripts/phase51/trace_sanity_regression.py` — a direct day-by-day trace (hand count, money,
land quadrants owned) for seed 700002, run under both conditions, to confirm rather than assume
the regression's mechanism.

## 2. MANDATORY sanity check: HIRE pacer on Submission K's own unmodified portfolio

Run **before** touching the 4th-quadrant idea at all, per the brief's explicit instruction.

**[VERIFIED]** `python -m scripts.phase51.isolated_screen_sanity`, 4-seed isolated-economy
screen (dev seeds 700000-700003), no 4th quadrant, no new crop:

| seed | baseline (Submission K) | hire_paced | delta |
|---|---|---|---|
| 700000 | $80,023.00 | $11,222.00 | -$68,801.00 |
| 700001 | $74,029.00 | $8,366.00 | -$65,663.00 |
| 700002 | $58,167.00 | $4,722.00 | -$53,445.00 |
| 700003 | $69,460.00 | $6,948.00 | -$62,512.00 |
| **mean** | **$70,419.75** | **$7,814.50** | **-$62,605.25 (-88.9%)** |

**All 4 of 4 development seeds regressed.** Idle-action fraction rose in every seed
(0.0950→0.1700, 0.1099→0.1552, 0.1061→0.1720, 0.1160→0.1952) — consistent with a labor
shortage, not a labor-scheduling change. This is a decisive, unambiguous failure, well past any
reasonable noise band, on the FIRST and mandatory screen.

### 2.1 Mechanism trace (seed 700002)

**[VERIFIED]** `python -m scripts.phase51.trace_sanity_regression`, day-by-day hand count and
money, same seed under both conditions:

| day | baseline hands | baseline money | hire_paced hands | hire_paced money |
|---|---|---|---|---|
| 0 | 5 | $428.00 | 5 | $428.00 |
| 2 | 5 | $77.00 | 5 | $77.00 |
| 4 | 5 | $48.00 | **0** | $32.00 |
| 6 | 4 | $1,077.00 | **0** | $7.00 |
| 8 | 2 | $0.00 | **0** | $6.00 |
| 10 | 11 | $4,275.00 | **0** | $35.00 |
| 12 | 11 | $5,186.00 | **0** | $2.00 |
| 14 | 11 | $6,462.00 | 10 | $1.00 |
| 16 | 11 | $6,982.00 | **0** | $1.00 |
| 18 | 11 | $7,637.00 | 11 | $0.00 |
| 20 | 11 | $12,991.00 | 11 | $395.00 |
| 24 | 11 | $31,920.00 | 11 | $320.00 |
| 29 | 11 | $58,167.00 | 11 | $4,722.00 |

**[VERIFIED] Hand count collapses to 0 for most of days 4 through 16** under the HIRE pacer,
versus the baseline reaching 11 hands (its full early-game target) by day 10 and holding it.
**[INFERRED]** the mechanism: `HIRE`'s cheapest possible single purchase is `_fib(0) = 1`, but
`hire_budget = money - land_purchase_reserve` goes negative (or stays below 1) whenever money
sits under the posture-aware reserve floor ($75-$300 depending on posture) — which the trace
shows happening routinely in the early game (money $32-$77 on days 2-6, well under even the
$75 BEHIND-posture floor). With `hire_budget < 1`, the very first `_fib` term already exceeds
it, so `affordable` stays at 0 and **no hiring happens at all**, no matter how small the
cheapest hire would be. And with 0 hands, there is no labor to harvest crops, feed animals, or
generate the very revenue that would let money climb back above the reserve — a self-reinforcing
freeze, not a transient dip. The baseline recovers because HIRE has no such floor and can always
afford at least the cheapest fib-cost hire once any money exists at all.

**[INFERRED]** this is functionally the same self-defeating feedback loop Phase 36's own
docstring already described and explicitly designed around (Section 3 of that phase's report,
quoted in `scripts/phase36/paced_execution.py`'s docstring): coupling HIRE to a reserve blocks
hiring during exactly the cash-tight moments the economy most needs new hands to recover,
worsening the shortage rather than protecting against it. Phase 36 previously observed this when
HIRE was coupled to the *feed-buffer* reserve term specifically (a per-owned-animal cost); this
phase found the SAME failure mode from gating HIRE against `land_purchase_reserve` ALONE — a
flatter, in isolation smaller-looking number — confirming the warning generalizes to any reserve
coupling on HIRE, not just the feed-buffer variant Phase 36 tested. Unlike BUY_ANIMAL or
BUY_SEED (which have no analogous recovery dependency — skipping an animal or seed purchase for
a few turns doesn't remove the labor that earns money), HIRE is the one purchase type whose own
output (hands) is a precondition for the economy's ability to ever climb back above any reserve
floor. This makes HIRE structurally unsuited to the exact reserve-gating pattern that worked for
the other three purchase types.

## 3. Per the brief's own stop-rule: 4th-quadrant retest not attempted

The brief is explicit: *"If the HIRE pacer regresses Submission K's own existing unmodified
portfolio on the 4-seed screen, STOP immediately and report that plainly — do not proceed to the
4th-quadrant retest on top of a layer that already regresses."* Step 2's result (-88.9% mean,
4/4 seeds regressed) is exactly that condition. `scripts/phase51/land_expansion_hire_paced.py`
(the recomposition of Phase 33/48's TOMATO/GOOSE design on top of this HIRE-paced layer) was
**not built**, and no 4th-quadrant screen, full 15-seed validation, or head-to-head run was
attempted this phase. This is a deliberate scope stop, not an oversight — building a 4th-quadrant
retest on top of an execution layer that already collapses the baseline economy by 89% would not
be a fair or informative test of the 4th-quadrant idea itself; any result (positive or negative)
would be confounded by the pacer's own unrelated collapse.

**[HYPOTHESIS]**, offered honestly as an open question for any future attempt, not tested this
phase: a HIRE gate that reserves against something smaller or more targeted than the flat
`land_purchase_reserve` — e.g. only refusing the LAST unit of an otherwise-affordable hire batch
rather than gating the very first, or a reserve that shrinks toward zero as hand count drops
toward some minimum floor — might avoid the zero-hands trap this design fell into, precisely
because it would never block the cheapest possible hire when hands are already critically low.
This phase does not build or validate that design; per the brief's own instruction not to force
a positive spin, this is flagged as an unexplored idea, not a recommendation.

## 4. Answer to the phase's actual scientific question

**Does HIRE pacing (as designed this phase) finally make the 4th-quadrant dedicated-hands
expansion viable?** Unknown — not reached, because the pacer itself is unsafe on Submission K's
own unmodified portfolio before the 4th-quadrant question could even be asked. This is reported
honestly as an inconclusive result for the 4th-quadrant question specifically (neither confirmed
nor refuted this phase), combined with a decisive, confirmed result for the HIRE-pacer design as
built (it does not work, by any margin, on any of the 4 development seeds).

The brief's own fallback framing — *"the daily-hand-reset Fibonacci tax may simply be too
expensive at this scale for ANY dedicated-hands expansion, regardless of purchase timing"* —
remains a live possibility, but this phase's evidence doesn't directly speak to it: the failure
found here is about HIRE's *pacing gate*, not about the Fibonacci hire cost's absolute size for
dedicated hands. A future attempt would need a HIRE-pacer design that survives its own sanity
check before that broader question could be tested at all.

## 5. Recommendation

**Not ready to package.** Nothing from this phase is a candidate for promotion. Submission K
(`kaggriculture_phase50_submission_K.tar.gz`) remains the correct, unaffected upload — this
phase's new files (`scripts/phase51/*`) are all isolated wrappers under `scripts/phase51/`;
`agents/phase21/`, `scripts/phase46/`, `scripts/phase48/`, and every other frozen file listed in
this phase's constraints were read but never modified, confirmed by the fact that
`hire_paced_execution.py` and `hire_paced_capped_animal_portfolio_agent.py` only ever *import*
from those modules.

**Recommendation for any future attempt at HIRE pacing specifically**: do not reuse the flat
`land_purchase_reserve` gate as designed here — it is too large relative to routine early-game
cash levels and, unlike BUY_ANIMAL/BUY_SEED, HIRE has no substitute mechanism to recover once
frozen (hands are the labor that earns the money needed to clear the reserve in the first
place). Any future HIRE-pacing design should be checked against this exact same mandatory
sanity check (Submission K's own unmodified portfolio, 4-seed screen) before any new-crop or
4th-quadrant idea is layered on top of it — this phase's own experience is a fresh, concrete
demonstration of why that check is mandatory and non-skippable, not a one-off surprise.

## 6. Files changed/added this phase

- `scripts/phase51/hire_paced_execution.py` (new)
- `scripts/phase51/hire_paced_capped_animal_portfolio_agent.py` (new)
- `scripts/phase51/isolated_screen_sanity.py` (new)
- `scripts/phase51/trace_sanity_regression.py` (new)
- `results/phase51/phase51_isolated_screen_sanity_results.json` (new, generated)
- `docs/BIG_SWING_PLAN.md` (new Phase 51 update block, prepended)
- `results/phase51/PHASE51_HIRE_PACER_REPORT.md` (this file)

No file under `main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`,
`agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`, `agents/phase15/`,
or `agents/phase21/` was modified.
