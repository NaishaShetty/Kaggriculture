# Phase 53: Extending Submission K's Own Portfolio to a 4th Land Quadrant

**Scope**: isolated wrapper variant only. `agents/phase21/portfolio.py` NOT modified (imported
unmodified). `scripts/phase46/feed_priority_execution.py` and `scripts/phase48/
capped_animal_portfolio.py` NOT modified (imported/composed unmodified). New files:
`scripts/phase53/fourth_quadrant_portfolio.py`, `scripts/phase53/fourth_quadrant_portfolio_agent.py`,
`scripts/phase53/isolated_screen.py`, `scripts/phase53/trace_regression.py`,
`results/phase53/phase53_isolated_screen_results.json`, this report.

## 0. Why this phase exists

Phase 52's forensic analysis of our 3 most recent real losses found that 2 of 3 (vs. real
opponents "yuki" and "Sarthak Patel") were opponents running our own exact MELON/STRAWBERRY/WHEAT
crop portfolio, just with a 4th land quadrant we don't take. Every prior 4th-quadrant attempt
failed for a reason specific to what made it *different* from our own working schedule (a new
dedicated crop with dedicated hands — Phase 33/48; copied real-opponent target numbers at a
different scale/crop mix — Phase 43; a generic HIRE pacer that failed its own sanity check before
reaching the question — Phase 51). This phase tests the one variant nobody tried: same crops,
same ratios, same execution, just a scaled-up land/hands/crop-tile target.

## 1. Design: the 4th-quadrant rung extension

`scripts/phase53/fourth_quadrant_portfolio.py::make_fourth_quadrant_target_fn` wraps
`portfolio_targets` (or a wrapper already composed on top of it), overriding only
`land_quadrants`, `n_hands`, and `crop_tile_target`. `crop_fractions` and `animals` pass through
untouched, so the 4th quadrant's tiles are planted with the exact same `_base_crop_fractions`
ratios already validated for quadrants 1-3 — reused, not reimplemented.

**[VERIFIED]** Before picking numbers, the brief's own framing ("real yuki/Sarthak Patel episodes
reached 4 quadrants by day 9-11") was checked directly against Phase 52's already-downloaded raw
replay JSONs rather than assumed. It does not hold precisely: a fresh full-timeline trace found
**yuki** reached land=3 on day 11 (matching our own existing rung) and land=4 only on **day 17**
(hands flat at 10 the whole game, peak crop tiles 88); **Sarthak Patel** reached land=3 on day 10
and land=4 on **day 12** (hands jumped to 14 on day 11, held there, peak crop tiles 67). The real
range is day 12–17, not day 9–11.

Rung choices, grounded in this corrected data plus Phase 30/46's own idle-fraction measurement
(~7-9% idle at the current 11-hand/58-tile scale — near-zero slack, the same finding that sank
Phase 30's fertilizer attempt and Phase 33/48's dedicated-hands attempts):

| Rung | Existing (3-quadrant) | Extension (4-quadrant) | Rationale |
|---|---|---|---|
| `_LAND_RUNGS` | ..., (11, 3) | + (16, 4) | Inside the real day 12-17 range; continues our own ~5-day purchase cadence (day 6→11 is 5 days; day 11→16 continues it) |
| `_HANDS_RUNGS` | ..., (10, 11) | + (15, 13) | Real data brackets a wide 10-14 range with no clean "scale proportionally" signal (yuki succeeded with *fewer* hands than we already run); a moderate +2 was chosen over the full proportional +4 (11×4/3≈15) specifically because of the near-zero idle-fraction slack already measured |
| `_CROP_TILE_RUNGS` | ..., (15, 58) | + (16, 75) | Proportional scaling (58×4/3≈77) lands almost exactly inside the real observed range (Sarthak peaked 67, yuki peaked 88) |

**Animal cap**: Phase 48's `cap_total=8` was left **unchanged**, per the brief's own instruction not
to touch it without a fresh measurement-based reason. The real data gave no such reason — yuki's
own animal count under land=4 was 8, matching our existing cap almost exactly; Sarthak's higher
count (10-13) came with meaningfully more hands (14) for tile/labor servicing generally, not
specific evidence that hand count raises the sustainable *animal* ceiling (a distinct FEED/CARE
labor question Phase 48's own steady-state probe already measured directly). Since the screen
below found no reason to pursue this further, no fresh animal-ceiling probe at the extended scale
was run.

## 2. 4-seed isolated-economy screen — decisive, consistent regression

**[VERIFIED]** (`scripts/phase53/isolated_screen.py`, `results/phase53/phase53_isolated_screen_results.json`)

| Seed | Baseline (Submission K) | 4th-quadrant candidate | Delta |
|---|---|---|---|
| 700000 | $80,023.00 | $76,229.00 | -$3,794.00 (-4.7%) |
| 700001 | $74,029.00 | $70,096.00 | -$3,933.00 (-5.3%) |
| 700002 | $58,167.00 | $51,266.00 | -$6,901.00 (-11.9%) |
| 700003 | $69,460.00 | $66,902.00 | -$2,558.00 (-3.7%) |
| **Mean** | **$70,419.75** | **$66,123.25** | **-$4,296.50 (-6.1%)** |

**All 4 of 4 development seeds regressed.** Per this project's own established precedent
(Phase 30/32/33/42/45/48/51), this is a clear stop signal — no 15-seed validation was run, and per
the brief's own explicit instruction, a 4-seed screen may only decide whether to continue, never to
promote; here it decides to stop.

**A genuinely interesting wrinkle, checked directly rather than assumed away**: idle-action
fraction (Phase 30/46's own capacity metric) actually *improved* under the 4th-quadrant candidate
(baseline mean 0.107 → candidate mean 0.091) — ruling out the naive "ran out of worker-turns"
explanation before it could be assumed. This meant the mechanism needed a direct trace, not a
guess.

## 3. Direct trace: the real mechanism is cash-flow timing, not worker-turn capacity

**[VERIFIED]** (`scripts/phase53/trace_regression.py`, seed 700000, full turn-by-turn trace)

The additional land and tiles ARE being serviced properly, not left idle — WATER counts and
HARVEST counts scale up correctly under the candidate (e.g. day 18: WATER 59→73; day 25: HARVEST
30→36; day 29: HARVEST 33→39), directly confirming this is **not** the same worker-turn-scheduling
capacity ceiling Phase 30/46 characterized, and **not** the recurring dedicated-hands HIRE-cost
mechanism in the exact shape Phase 33/48 diagnosed (a NEW crop's dedicated hand batch) — this
variant uses the plain shared hand pool, no dedicated hands, no new crop.

**The real mechanism, precisely quantified**: `agents/phase21/execution.py`'s HIRE section (and
`feed_priority_execution.py`'s unmodified copy of it) recomputes the Fibonacci hire-cost schedule
from `_fib(0)` **every single day**, because hired hands reset to empty at the start of each day
(confirmed directly in the trace: `HANDS 11 -> 0` at every `hour=0`, then re-hired back up during
the day). This means the target hand *count* itself — not whether those hands are "dedicated" to
anything — determines a **recurring daily** cost, not a one-time cost:

- Cost to hire up to 11 hands from 0, one day: **$232** (`sum(fib(0..10))`)
- Cost to hire up to 13 hands from 0, one day: **$609** (`sum(fib(0..12))`)
- **Extra recurring cost from the +2 hand target: $377/day**, for the 14 remaining days
  (day 16-29) = **$5,278** — plus the one-time $4,000 land price for the 4th quadrant
  (`LAND_PRICES[2]`, confirmed directly from the vendor engine).

Observed in the trace: money drops from $7,476 to $2,223 in the single turn the 4th quadrant and
extra hands are purchased (day 16, hour 2) — a combined hit close to the $4,000 + partial-day hire
cost predicted above. The gap between baseline and candidate money never fully closes over the
remaining 13 days (day 20: $18,681 vs. $11,205; day 29 final: $80,023 vs. $76,229) — the additional
~17-22 crop tiles' worth of extra harvest revenue claws back some but not all of the combined
one-time land cost and recurring hire-cost tax.

**This is a real, generalizable finding, distinct from (but related to) Phase 33/48's own
diagnosis**: Phase 33/48 attributed their dedicated-hands 4th-quadrant failure specifically to
hands being a separate "dedicated" batch reset daily. This phase shows the mechanism is actually
more general — it applies to **any** increase in the shared hand-count target at all, dedicated or
not, because the daily reset-and-rehire-from-`fib(0)` behavior is a property of the HIRE mechanic
itself, not of how the hands are subsequently used. Raising `n_hands` from 11 to 13 through the
existing, "already-working" HIRE mechanism does not escape this cost — it hits it directly.

## 4. Honest answer to the brief's explicit check

Per the brief's own constraint: does this hit the SAME worker-turn capacity ceiling Phase 30/46
already characterized (more tiles + more hands competing for the same scarce worker-turns)? **No** —
idle-fraction improved, and tile servicing (WATER/HARVEST throughput) scaled up correctly with the
extra hands. The ceiling here is a **cash-flow/ROI-timing** one: the *recurring* daily cost of
carrying more hands (a direct consequence of the HIRE mechanic's daily reset) plus the one-time,
steeply escalating land price ($1,000 / $2,000 / $4,000 per quadrant — the 4th is the single most
expensive purchase in the game) arriving too late in a fixed 30-day season to pay back, not a
scheduling/execution deficiency. This is a genuinely different, more precisely diagnosed mechanism
than any of Phases 33/43/48/51's — but it is still a real, decisive negative result for this
specific design.

## 5. Recommendation

**Not ready to package.** The 4-seed isolated-economy screen is a decisive, consistent regression
(-6.1% mean, 4/4 seeds worse), correctly stopping this phase before any 15-seed validation or
head-to-head run, per this project's own mandatory screen-first precedent. The mechanism is real,
precisely quantified, and honestly diagnosed as a cash-flow/ROI-timing problem inherent to the
HIRE mechanic's daily reset-and-rehire behavior, not a worker-turn capacity ceiling and not a
crop-mix problem — meaning the underlying idea (extend our own working schedule one quadrant
further, same crops) is not itself disproven, but this specific rung timing (land-4 at day 16,
hands-13 at day 15) is. A future attempt at this same idea would need to either (a) reach the 4th
quadrant meaningfully earlier in the season, so there is enough remaining runway to amortize the
one-time land cost and the ongoing recurring hire-cost tax against extra harvest revenue, or
(b) find a way to add land-servicing capacity without raising the shared hand-count target at all
(the actual cost driver here) — both are genuinely new, untested candidates for a future phase, not
things this phase's negative screen result rules out. Submission K remains the correct, unaffected
upload candidate; nothing in the shipped strategy was touched.
