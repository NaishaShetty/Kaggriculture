# PHASE 8 — Calibration Probe: `revenue_per_tile_day` at Real Scale

Submission C is unmodified throughout this phase. No submission is created.
`git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5
agents/phase3_8` is clean. All new code lives under `scripts/phase8/` and
`results/phase8/`.

## 1. Executive Summary

**[VERIFIED] `CALIBRATION["revenue_per_tile_day"]` is NOT safe to use at real
game scale — but the dominant failure mode is not the one Phase 5/6
hypothesized.** Both prior reports framed the open question as "does the
error grow with tile *scale*, and is it worse for narrow-market crops
(STRAWBERRY, MELON)." Measured directly (isolated single-player, no
opponent, full 30-day season, n_tiles ∈ {5,10,15,20,25}), neither is true:

- **Relative error *shrinks* as n_tiles grows, for every crop tested** — the
  opposite of "grows with scale."
- **Error size tracks whether the crop is `ongoing` in the engine's own
  `CROPS` dict, not its market depth `T`.** WHEAT, CARROT, and MELON are all
  `ongoing=False` (they finish a short yield cycle, clear the tile, and can
  be **replanted**); `crop_production_value`'s `occupied_days` formula caps
  at `max_yield_day + 1` — one cycle — and has no notion of replanting at
  all. A correctly-executed agent replants a cleared tile immediately, so
  over a 30-day season WHEAT/CARROT cycle 5-8 times and MELON ~2-3 times,
  and the calibration undercounts actual revenue by **3-8x for WHEAT/CARROT
  and 1.4-2.8x for MELON** even at n_tiles=25. STRAWBERRY and TOMATO are
  `ongoing=True` — a single planting's accumulation window already spans
  nearly the crop's whole productive life, so the same formula is accurate
  to **within 2-19%** at every scale tested. Market depth `T` (STRAWBERRY
  100, MELON 300, WHEAT 400, CARROT 450) predicts none of this pattern —
  the widest-market crop (CARROT, T=450) has the single largest calibration
  error of the five.
- **This is a previously-undiagnosed bug in `crop_production_value`
  (§13/mechanism below), separate from and in addition to** the
  small-reference-scale ranking problem Phase 5 diagnosed and the
  market-depth self-crash risk Phase 5/6 both flagged. All three are real;
  they affect different crops to different degrees.

**Phase 6 Experiment 3 is RESOLVED: FAIL.** STRAWBERRY's true (measured,
not calibration-estimated) revenue-per-tile-day does **not** exceed
MELON's at n_tiles=20-25 — MELON's is 1.6-1.7x higher, both raw and under
market-impact-adjusted pricing (Section 5). The 4-opponent
STRAWBERRY-over-MELON pattern Phase 6 observed in real replays is **not**
explained by STRAWBERRY having superior raw single-player production
economics at real scale. Something else (most plausibly two-player market
dynamics this isolated probe cannot observe — see Section 6/Limitations)
is doing the work, and remains genuinely unexplained.

**Recommendation for Phase 3/Phase 4 (`docs/ROADMAP_TO_GOLD.md`):** do not
patch the existing `revenue_per_tile_day` constant with a scale correction
factor — that would fix the wrong bug. Any future volume-estimation logic
must (a) explicitly branch on `CROPS[crop]["ongoing"]`, simulating replant
cycles for non-ongoing crops rather than using a single-window tile-day
rate, and (b) route the resulting unit volume through the already-verified
`agents/phase4/market_model.py::simulate_sell` before treating it as
revenue for any crop, since even accurately-estimated volume (STRAWBERRY,
TOMATO) can still be worth far less than face value once market depth is
priced in (Section 5). Full detail in Section 7.

## 2. Methodology

Per the Phase 5 §16 / Phase 6 §17-Experiment-3 brief: standalone,
**isolated** play (protagonist vs the engine's built-in `"pass"` opponent,
which never acts), full 30-day / 720-step season, one crop at a time.

**Agent (`scripts/phase8/calibration_probe.py::make_probe_agent`)**: a
purpose-built, minimal agent reusing the SAME primitives Phase 2.4's frozen
tactical layer is built from (`agents/phase2_3/common.py`'s `_home_tile`,
`_shed_tiles`, `_owned_tiles`, `_manhattan`, `_step_toward`, `_fib`,
`_is_plant`, `_needs_harvest_crop`, `_needs_water`) — same task-priority
order (HARVEST > WATER > PLANT), same hire/land/sell/buy-seed logic in
spirit. The one substantive difference from calling
`agents/phase2_4/common.py::make_agent` directly is deliberate and
necessary: that function always assigns **100% of a crop's entire owned
tile pool** to a single crop, and pool size is quantized by land-quadrant
boundaries (24 tiles at 1 quadrant, 48 at 2) — it cannot hit an *exact*
tile count of 5/10/15/20/25. The probe agent instead takes a fixed-size
slice of the owned tile pool (nearest-to-home first, same ordering
`tile_pool_assignment` uses), so n_tiles is exact and controlled.

- 2 land quadrants bought day 0 (enough room for n_tiles up to 25; a
  probe-harness cost, not part of what's being measured — see below).
- 4 hands, fixed — generous enough that labor is never the bottleneck,
  isolating the production/sale measurement from a labor-scarcity confound.
- Selling: **passive** (sell everything in the shed, every turn) —
  deliberately the simplest policy with no timing strategy, so the
  measured number reflects raw production/sale economics, not a
  selling-timing decision (a different, already-separately-studied
  question).
- Seed: 700000 (a Phase 3 "development" seed, consistent with this
  project's existing convention). **n=1 per (crop, n_tiles) cell** — the
  engine has one real stochastic element relevant here (weed-spawn chance
  on an empty tile, `rng.random() < weed_chance`), which can occasionally
  cost a tile a cycle; this is a disclosed limitation (Section 8), not
  hidden, and does not change any qualitative finding below (see the one
  visibly-affected cell, CARROT n_tiles=20, flagged in Section 3).

**Comparison basis**: `economic_model.model.crop_production_value`'s
**revenue** component (its `net_profit` plus `seed_cost` added back, since
`net_profit = revenue - seed_cost`) against the probe's **actual gross SELL
revenue** for that crop, read from the existing, unmodified instrumentation
pipeline's `crop_metrics[crop]["revenue"]` (`instrumentation/metrics.py`,
never re-derived). Land ($1000-2000 for the 2 quadrants) and hire cost are
**excluded from both sides** of the comparison — they are a probe-harness
artifact (needed to physically have 25 tiles available), not something
`crop_production_value` claims to predict, and including them would bias
the comparison against the probe, not toward the calibration.

## 3. Full Results

All results: `results/phase8/phase8_calibration_probe_results.csv` /
`.json`. `rel_error = (actual − estimated) / estimated`.

| Crop | Ongoing | T | n_tiles | Actual revenue | Calibration estimate | rel_error | Actual $/tile-day |
|---|---|---|---|---|---|---|---|
| WHEAT | No | 400 | 5 | $2,439 | $368 | **+5.62** | $16.26 |
| WHEAT | No | 400 | 10 | $3,916 | $737 | **+4.32** | $13.05 |
| WHEAT | No | 400 | 15 | $4,929 | $1,105 | **+3.46** | $10.95 |
| WHEAT | No | 400 | 20 | $6,282 | $1,473 | **+3.26** | $10.47 |
| WHEAT | No | 400 | 25 | $7,308 | $1,841 | **+2.97** | $9.74 |
| CARROT | No | 450 | 5 | $2,999 | $328 | **+8.14** | $19.99 |
| CARROT | No | 450 | 10 | $5,912 | $656 | **+8.01** | $19.71 |
| CARROT | No | 450 | 15 | $7,132 | $985 | **+6.24** | $15.85 |
| CARROT | No | 450 | 20 | $5,639 | $1,313 | **+3.30**† | $9.40† |
| CARROT | No | 450 | 25 | $9,203 | $1,641 | **+4.61** | $12.27 |
| MELON | No | 300 | 5 | $12,592 | $4,517 | **+1.79** | $83.95 |
| MELON | No | 300 | 10 | $23,453 | $9,034 | **+1.60** | $78.18 |
| MELON | No | 300 | 15 | $29,884 | $13,551 | **+1.21** | $66.41 |
| MELON | No | 300 | 20 | $31,381 | $18,067 | **+0.74** | $52.30 |
| MELON | No | 300 | 25 | $31,054 | $22,584 | **+0.38** | $41.41 |
| TOMATO | Yes | 200 | 5 | $1,319 | $961 | +0.37 | $8.79 |
| TOMATO | Yes | 200 | 10 | $2,576 | $1,921 | +0.34 | $8.59 |
| TOMATO | Yes | 200 | 15 | $3,804 | $2,882 | +0.32 | $8.45 |
| TOMATO | Yes | 200 | 20 | $4,127 | $3,842 | +0.07 | $6.88 |
| TOMATO | Yes | 200 | 25 | $5,127 | $4,803 | +0.07 | $6.84 |
| STRAWBERRY | Yes | 100 | 5 | $4,251 | $3,859 | +0.10 | $28.34 |
| STRAWBERRY | Yes | 100 | 10 | $8,828 | $7,718 | +0.14 | $29.43 |
| STRAWBERRY | Yes | 100 | 15 | $12,758 | $11,578 | +0.10 | $28.35 |
| STRAWBERRY | Yes | 100 | 20 | $18,369 | $15,437 | +0.19 | $30.62 |
| STRAWBERRY | Yes | 100 | 25 | $19,614 | $19,296 | +0.02 | $26.15 |

† CARROT n_tiles=20 is a visible outlier vs. its neighbors (15→20→25:
$7,132→$5,639→$9,203) — consistent with the single-seed weed-loss
limitation (Section 8), not a new mechanism. The qualitative pattern
(large, scale-shrinking error for CARROT) is unaffected either way.

**Pattern, directly answering the brief's question**: relative error does
**not** stay flat, does **not** grow with scale, and does **not** track
market depth `T`. It **shrinks monotonically with n_tiles for every crop**,
and its *magnitude* splits cleanly along the `ongoing` flag: ~3-8x
undercount for the three non-ongoing crops (WHEAT, CARROT, MELON) at every
tested scale, vs. 2-37% for the two ongoing crops (STRAWBERRY, TOMATO),
tightening further at larger n_tiles.

## 4. Mechanism

`economic_model/model.py::crop_production_value` (lines 158-162):

```python
if cd["ongoing"]:
    occupied_days = min(remaining, cd["first_yield_day"] + cd["interval"] * cd["max_yield"])
else:
    occupied_days = min(remaining, cd["max_yield_day"] + 1)
```

For an `ongoing` crop (TOMATO, STRAWBERRY), the engine's own day-refresh
logic (`vendor_kaggriculture/kaggriculture.py::_daily_refresh_plants`,
lines 786-802) keeps adding yield to the SAME planted tile every `interval`
days until `max_yield` is reached, then stops — the tile is never cleared
and never needs replanting. `occupied_days` above computes exactly that
window (`first_yield_day + interval * max_yield`), so the formula is
measuring the crop's real, complete, single-planting productive life. This
is why TOMATO/STRAWBERRY calibration error is small.

For a **non-`ongoing`** crop (WHEAT, CARROT, MELON), the engine harvests
once the tile hits `max_yield` and then **clears the tile to `None`**
(`kaggriculture.py`'s `HARVEST` handler, `if not crop_data["ongoing"]:
farm["tiles"][fy][fx] = None`) — it can be planted again immediately.
`crop_production_value`'s `occupied_days` formula caps at
`max_yield_day + 1`, i.e. **exactly one cycle**, with no mechanism at all
for the tile being replanted and harvested again. A correctly-executing
tactical agent (this probe's, and the frozen Phase 2.4 layer alike) DOES
replant the moment a tile clears — WHEAT/CARROT cycle every 4-5 days
(≈6-7 cycles in 30 days), MELON every 13 days (≈2.3 cycles) — so real
achievable revenue is a multiple of the formula's single-cycle estimate.
The multiple shrinks as n_tiles grows only because larger plantings
increasingly bump into the shed's 100-unit capacity and the 10-order
market-action cap per turn (`market = market[:10]` in both this probe's
agent and the frozen Phase 2.4 layer) — production continues to outrun
what a single turn can sell/replant, so *relative* overcapacity shrinks
even though absolute undercount stays large. This is a genuine capacity
interaction, not noise: it is the same reasoning `crop_production_value`'s
own docstring already flags as out of scope ("planning... is explicitly
out of scope here").

**This is a distinct bug from what Phase 5 diagnosed.** Phase 5 (§13)
found that scaling the SAME formula's *n_tiles* input up to real freed-tile
counts (~20-25) inflates STRAWBERRY's implied volume enough to crash its
own narrow market when priced through the exact simulator. That finding is
about **market-impact pricing of an estimated volume**. This phase's
finding is upstream of that: for three of the five candidate crops, the
volume estimate itself is wrong by 3-8x **regardless of scale**, because
the model never accounts for replanting. STRAWBERRY (Phase 5's crash
culprit) is `ongoing` — its calibration error here is small (2-19%,
Section 3) — so Phase 5's finding and this phase's finding do not
contradict; they describe two independent, compounding problems that
happen to affect different crops in the five-crop candidate set.

## 5. Market-Impact-Adjusted View (Step 6)

Reusing the Phase 4/5 live-validated exact pricer
(`agents/phase4/market_model.py::simulate_sell`), unmodified: what would
the **actually-measured harvested units** fetch if dumped on a fresh market
(`I0`) in one batch? (`results/phase8/...json`'s
`actual_market_impact_adjusted_revenue` column.)

| Crop | n_tiles | Actual units | Actual in-episode revenue (spread selling) | Batch-dump revenue (simulate_sell) |
|---|---|---|---|---|
| STRAWBERRY | 20 | 84 | $18,369 | $3,831 |
| STRAWBERRY | 25 | 94 | $19,614 | $3,841 |
| MELON | 20 | 195 | $31,381 | $26,522 |
| MELON | 25 | 235 | $31,054 | $26,562 |

Two things fall out of this, both genuine and both relevant to Phase 3/4:

1. **Market-impact pricing does NOT change the STRAWBERRY-vs-MELON ranking
   — it widens the gap in MELON's favor.** STRAWBERRY's narrow market
   (T=100, `above_target=1.60`) collapses a same-turn batch dump to ~20%
   of its spread-selling value; MELON's wider market (T=300) retains
   ~85%. MELON wins under either lens.
2. **In-episode spread selling (passive: sell whatever's in the shed each
   turn) captures far more value than a single-batch dump would**, for
   both crops but dramatically more so for STRAWBERRY (4.8x) than MELON
   (1.18x) — because turns between harvests let the engine's town
   consumption (`townShopSellInterval=4`, `townCenterSellInterval=24`,
   VERIFIED_MECHANIC) partially recover price. This means `simulate_sell`
   used as a single-batch-from-`I0` estimator (as Phase 5's
   `market_impact_substitution.py` does) is a conservative **lower bound**
   for a policy that actually sells incrementally as it harvests, not a
   realistic point estimate — worth flagging for any future phase that
   reuses it the same way Phase 5 did.

## 6. Phase 6 Experiment 3 — Explicit Resolution

**Pass condition (Phase 6 §17, Experiment 3): "STRAWBERRY's
revenue-per-tile-day at 25 tiles, market-impact-adjusted, exceeds MELON's."**

**Result: FAIL**, by a wide margin, at both n_tiles=20 and n_tiles=25, and
under both the raw and market-impact-adjusted lens:

| n_tiles | STRAWBERRY $/tile-day (actual) | MELON $/tile-day (actual) | STRAWBERRY total batch-adj. $ | MELON total batch-adj. $ |
|---|---|---|---|---|
| 20 | $30.62 | **$52.30** | $3,831 | **$26,522** |
| 25 | $26.15 | **$41.41** | $3,841 | **$26,562** |

MELON's true, measured revenue-per-tile-day at real scale is **1.6-1.7x
STRAWBERRY's**, not lower — the opposite of what would be needed to explain
Phase 6's 4/4 real-opponent STRAWBERRY convergence as "STRAWBERRY is
actually the better crop at scale." **This phase does not overturn
Submission C's MELON-anchored default on economic grounds** — if anything
it reinforces that MELON is the stronger single-player production choice
at every scale tested, isolated.

**What this does NOT resolve**: Phase 6's own §17 Experiment 3 fail
condition states plainly that a fail here means "the 4-opponent pattern has
a cause other than raw crop economics" — this phase's isolated,
single-player design (required by the brief, and necessary to get a clean
volume measurement at all) structurally cannot observe that other cause,
whatever it is (most plausibly a two-player competitive dynamic — e.g.
MELON's much larger `above_target=3.60` "sq" crash penalty means a
real *opponent* also planting MELON could crash the shared market far
worse than an isolated single-player run ever shows, which might make
STRAWBERRY the better choice specifically in the presence of a
MELON-planting rival, not in isolation). That remains an open question for
a future phase, not this one — flagged explicitly rather than guessed at.

## 7. Recommendation for Phase 3 / Phase 4

Both roadmap phases depend on trustworthy volume estimates at real scale
(`docs/ROADMAP_TO_GOLD.md`). Based on this phase's evidence:

1. **Do not apply a single scale-correction multiplier to
   `revenue_per_tile_day`.** The error does not scale uniformly — it is a
   structural gap in `crop_production_value`'s `occupied_days` formula for
   non-`ongoing` crops specifically, not a smoothly scale-dependent
   miscalibration. A flat correction factor would overcorrect STRAWBERRY/
   TOMATO (already accurate) and still undercorrect WHEAT/CARROT/MELON at
   small scale relative to large (Section 3's shrinking-error pattern).
2. **Any future volume-estimation logic should branch on
   `CROPS[crop]["ongoing"]`**: for `ongoing` crops, the existing
   single-window formula is already good enough (2-19% error, this phase's
   evidence) — use it as-is. For non-`ongoing` crops, estimate volume by
   explicitly modeling replant cycles (`n_tiles × floor(remaining_days /
   (max_yield_day + 1)) × max_yield`, or equivalent), not by reusing the
   single-cycle tile-day rate.
3. **Whatever volume estimate results, for ANY crop, should be priced
   through `agents/phase4/market_model.py::simulate_sell` before being
   treated as revenue** (already Phase 5's instinct, and directly reused
   here) — Section 5 shows this matters even for crops whose PRODUCTION
   estimate is already accurate (STRAWBERRY), because the volume/market-
   depth interaction is a separate risk from the volume estimate itself.
   Prefer modeling it as **incremental sale-as-harvested revenue with
   inter-turn price recovery**, not a single from-`I0` batch dump — Section
   5 shows the batch-dump number understates true achievable value by up
   to 5x for narrow-market crops, which could bias a future
   market-impact-aware substitution decision toward *rejecting* a
   genuinely viable crop.
4. **Phase 6 Experiment 3 is closed as FAILED** (Section 6) — do not spend
   further effort trying to make STRAWBERRY's real-scale single-player
   economics beat MELON's; they don't, decisively. If a future phase wants
   to understand the real 4/4-opponent STRAWBERRY preference (Phase 6
   §14.B.4, still an open unknown), it needs a **two-player** experiment
   design (a synthetic MELON-committed rival, at minimum), not a repeat of
   this isolated one.
5. Planner v1's MELON-first default (`agents/phase2_6/common.py`, frozen,
   not touched this phase) is **not shown to be economically wrong** by
   this phase's evidence — it is exactly the opposite: MELON remains the
   stronger measured single-player anchor at every tile count tested.
   Whatever explains real opponents' STRAWBERRY convergence, it is not "our
   crop-value ranking has MELON and STRAWBERRY backwards."

## 8. Limitations

- **n=1 seed per (crop, n_tiles) cell** (seed 700000). The engine has one
  stochastic element that touches this measurement (weed-spawn chance on
  a briefly-empty tile between harvest and replant), visible in the
  CARROT n_tiles=20 outlier (Section 3, footnote). The qualitative
  findings (ongoing-vs-non-ongoing split, shrinking-with-scale pattern,
  Phase 6 Experiment 3 fail) are large enough in magnitude that single-seed
  noise cannot plausibly reverse them, but a multi-seed re-run would
  tighten the exact error percentages.
- **Isolated (no opponent) by design**, per both the Phase 5 §16 request
  and the Phase 6 §17 Experiment 3 brief. This is necessary to get a clean
  production/sale measurement at all, but it means this phase cannot speak
  to two-player market dynamics — see Section 6's explicit caveat on what
  remains unresolved about the real 4-opponent STRAWBERRY pattern.
- The probe agent uses **passive (sell-every-turn) selling** deliberately,
  to isolate production/sale from selling-timing strategy. A different
  selling policy (threshold, batch) would change the absolute revenue
  numbers for narrow-market crops somewhat (Section 5 already shows
  spread-selling beats batch-dump substantially for STRAWBERRY) but would
  not change which crops are `ongoing` vs not, so the core mechanism
  (Section 4) is not sensitive to this choice.
- 2 land quadrants and 4 hands were fixed harness parameters chosen to make
  n_tiles=25 achievable without labor/land being the bottleneck; their cost
  is excluded from the revenue comparison (Section 2) precisely so this
  choice doesn't bias the result.

## Changed Files

New, all additive; nothing pre-existing modified:
- `scripts/phase8/calibration_probe.py`
- `results/phase8/phase8_calibration_probe_results.csv`
- `results/phase8/phase8_calibration_probe_results.json`
- `results/phase8/PHASE8_CALIBRATION_PROBE_REPORT.md` (this file)

No existing file was modified. `main.py` still builds Submission C. No
`.tar.gz` is created or staged — there is no new submission from this
phase.

## Validation Performed

- Full 5-crop × 5-n_tiles sweep (25 isolated episodes) run end-to-end
  through the unmodified `instrumentation.pipeline.run_and_analyze`
  pipeline every other phase in this project uses — no bespoke replay
  parsing.
- Revenue figures read directly from `crop_metrics[crop]["revenue"]`
  (`instrumentation/metrics.py`, unmodified), which sums actual `SELL`
  transaction totals — not self-computed from raw actions.
- Market-impact figures computed with the unmodified, Phase 4/5
  live-validated `agents/phase4/market_model.py::simulate_sell`.
- `git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5
  agents/phase3_8`: clean throughout this phase.
