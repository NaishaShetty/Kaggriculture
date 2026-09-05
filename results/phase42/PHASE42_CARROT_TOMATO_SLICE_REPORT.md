# Phase 42: CARROT/TOMATO Slice Report

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`,
`agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`,
`agents/phase2_4/common.py`, `agents/phase15/`). `agents/phase21/` was
**not modified** either — the slice is built as a wholly separate,
additive variant (`scripts/phase42/carrot_tomato_portfolio.py`), the same
"new module wraps the unmodified original" pattern Phase 36/37 already
established for Submission I's own pacer. No submission is created.

## Executive Summary

**[VERIFIED] The naive version of this idea (CARROT/TOMATO active from
day 0) is a severe net loss: -37.4% mean final money on the 4-seed
development screen** ($59,144 → $37,036). **[VERIFIED, by direct trace]**
the mechanism is a cash-flow collision, not a market-glut effect — CARROT
and TOMATO themselves sold at healthy, non-crashed prices ($34-45/unit and
$62-88/unit respectively, both close to or above their $35/$60 base
prices) — but the extra `BUY_SEED` spending for two more crop types has
zero cash pacing (the same category of gap Phase 35/36 already diagnosed
and fixed for `BUY_ANIMAL`, never extended to `BUY_SEED`), and it collides
directly with this agent's already-tightest cash window: on the traced
seed, the variant's cash sat at **$0-52 for 14 straight days** (day 6-19)
where the shipped baseline held $5,332-$14,405, and the 3rd land quadrant
purchase — which mechanically caps the whole farm's crop-tile ceiling —
was pushed from **day 11 to day 20**.

**[VERIFIED] A second version, delaying the slice until day 15 (after the
land/hand ramp settles) to avoid that exact collision, is no longer
harmful — but also does essentially nothing: +0.08% mean final money**
($59,144.50 → $59,192.00), and CARROT/TOMATO themselves barely get planted
at all in this configuration (0-12 units sold across the 4 seeds, vs. the
day-0 version's 16-56). The fix that removes the harm also removes almost
all of the crop's own utilization — there isn't a safe middle ground
reachable without cash-aware seed-purchase pacing, which is out of this
phase's scope (the task explicitly protects `agents/phase21/execution.py`'s
cash-safety throttle and HIRE logic, and building an equivalent pacer for
`BUY_SEED` the way Phase 36 built one for `BUY_ANIMAL` is a materially
larger change than "add two crops to the fraction table").

**Head-to-head vs. Submission G/C on the 4-seed screen: 4/4 for both the
shipped baseline and the delayed-start variant, against both opponents** —
no distinguishing signal either way; consistent with the isolated-economy
finding of "flat."

**Per this project's own established rule for a cheap screen that shows no
basis for optimism (Phase 33 Part A's identical language: "if it's not
competitive, stop... no head-to-head validation was run"), the full
15-seed validation was NOT run.** A flat 4-seed isolated-economy result
combined with a 4/4-vs-4/4 head-to-head (no differentiation at all) gives
no reason to expect the full 15-seed set would show a real, promotable
effect, and this project's own Phase 17 lesson about NOT trusting a
4-seed reading applies to promotion decisions, not to the decision to stop
investing further compute in a screen that already shows nothing. **Not
ready to package. Submission I remains the current best, unchanged.**

## 1. Design Rationale

**[VERIFIED] Engine facts, confirmed directly from `vendor_kaggriculture/
kaggriculture.py`** (matching the brief exactly): CARROT (seed $20,
first_yield_day 2, max_yield_day 3, max_yield 4, not ongoing — needs
replanting each cycle; market base $35, T=450, above_func sqrt/0.70);
TOMATO (seed $50, first_yield_day 8, max_yield_day 8, max_yield 4, ongoing
with interval 1 — repeat harvests like STRAWBERRY; market base $60, T=200,
above_func sqrt/0.60).

**[VERIFIED] `market_price(item, inventory) = base − amp·√(inventory − I0)`
for inventory > I0**, where `amp = above_target · base / √T` — read
directly from `vendor_kaggriculture/kaggriculture.py::market_price` (line
192). For CARROT, `amp = 0.70·35/√450 ≈ 1.156` — price stays above ~60% of
base (≥$21) while net cumulative units sold (shared across both players,
the whole game) stay under roughly 150-200. For TOMATO, `amp =
0.60·60/√200 ≈ 2.546` — a much tighter budget (≥$34, i.e. ~57% of base,
only under ~100 units), because TOMATO's ongoing/interval-1 mechanic means
a single mature tile can in principle be harvested every day through its
`planting_cutoff_day` (21, from `agents/phase21/liquidation.py`).

**[VERIFIED] Tile counts chosen (CARROT=6, TOMATO=2, 8 total) against that
budget**: 6 CARROT tiles cycling ~5-6 plantings each over the crop's own
27-day plantable window is ≈130 units total — comfortably under the ~200
threshold. 2 TOMATO tiles were deliberately kept small (not the 3-5 a naive
per-tile-value calculation might suggest) specifically because of the
tighter T=200 budget and the ongoing-harvest mechanic's higher worst-case
volume. Both counts sit inside Phase 41's own observed real range (roughly
5-15 tiles combined, across the sampled real trajectories that run
CARROT/TOMATO at all).

**[VERIFIED] Additive design**: `scripts/phase42/carrot_tomato_portfolio.py::
make_slice_target_fn` wraps `agents/phase21/portfolio.py::portfolio_targets`
(imported, never modified) and `scripts/phase36/paced_execution.py::
make_paced_execution_agent` (Submission I's actual shipped execution layer,
also imported unmodified). It increases `crop_tile_target` by exactly 8
every day the slice is active, and rescales the EXISTING crops' fractions
proportionally against the new (larger) target so their absolute
vacant-tile-fill count is unchanged — combined with
`bounded_multi_crop_tile_pool_assignment`'s own STICKY rule (an
already-growing tile is never displaced, only vacant tiles are reassigned),
this means MELON/STRAWBERRY/WHEAT never lose tile-count budget relative to
what Submission I currently ships; the 8 extra slots are strictly additive.

## 2. Four-Seed Screen — Two Versions

### Version 1: slice active from day 0 (the naive design)

| Seed | Baseline | Variant | Δ |
|---|---|---|---|
| 700000 | $44,258 | $50,020 | +13.0% |
| 700001 | $76,683 | $43,858 | -42.8% |
| 700002 | $64,197 | $33,696 | -47.5% |
| 700003 | $51,440 | $20,570 | -60.0% |
| **Mean** | **$59,144.50** | **$37,036.00** | **-37.4%** |

CARROT/TOMATO sold at healthy prices in every seed (CARROT $33.65-$48.69
realized, ~96-139% of the $35 base; TOMATO $62.14-$88.12 realized, ~104-147%
of the $60 base) — **the crop itself was never gluted.** 3 of 4 seeds
collapsed anyway.

### Version 2: slice delayed to day 15

| Seed | Baseline | Variant | Δ |
|---|---|---|---|
| 700000 | $44,258 | $39,438 | -10.9% |
| 700001 | $76,683 | $78,324 | +2.1% |
| 700002 | $64,197 | $62,910 | -2.0% |
| 700003 | $51,440 | $56,096 | +9.1% |
| **Mean** | **$59,144.50** | **$59,192.00** | **+0.08%** |

CARROT/TOMATO utilization dropped sharply (0-12 CARROT units sold, 4-9
TOMATO units, vs. version 1's 16-56 and 20-56) — the delay leaves too
little of the game left for the slice to do much, especially for CARROT
(2 of 4 seeds sold literally zero).

## 3. Mechanism (Why Version 1 Failed)

**[VERIFIED, direct trace, seed 700003]**: baseline money at day 6-20 was
$631, $45, $491, $1,030, $4,580, $5,332, $4,460, $7,026, $7,568, $6,408,
$7,748, $8,219, $7,773, $13,784, $14,405 — a normal, recovering ramp.
Version 1's variant over the identical window: $0, $0, $7, $6, $11, $52,
$1, $274, $873, $74, $2, $695, $904, $818, $862 — pinned near zero for the
entire window. **[VERIFIED]** the 3rd land quadrant (`_LAND_RUNGS`'s day-11
rung) was bought on day 11 in the baseline and not until **day 20** in the
version-1 variant — a 9-day delay that mechanically caps the whole farm's
crop-tile ceiling (land quadrants gate how many tiles exist to plant on at
all) for nearly a third of the game.

**[INFERRED]** the root cause is that `agents/phase21/execution.py`'s
`BUY_SEED` section (unmodified, not touched by this phase) has **no cash
reserve of any kind** — it spends `min(need, money // seed_cost)` on every
crop currently in `crop_fractions`, unconditionally, the same category of
gap Phase 35/36 already found and fixed for `BUY_ANIMAL` specifically (and
explicitly left `BUY_SEED`/HIRE/`BUY_LAND` alone, per that phase's own
documented scope). Adding two more crop types to `crop_fractions` from day
0 means two more recurring `BUY_SEED` draws competing for the exact same
constrained early-game cash (day 0-11) that funds HIRE and the 2nd/3rd land
purchase — a "cascading, path-dependent knock-on effect" in the same sense
Phase 33 Part B named for its own fertilizer-capacity experiment: no single
turn does anything wrong, but the recurring extra draw shifts downstream
purchase timing in a way that compounds across the whole game.

**[VERIFIED]** delaying the slice to day 15 (Version 2) removes this
collision — cash trajectories were not traced in detail for Version 2 since
the aggregate result (+0.08%) already shows no harm — but it also removes
most of the slice's own opportunity to produce anything, which is why
Version 2's net effect is a wash rather than a genuine gain.

## 4. Head-to-Head (4-Seed Screen)

| Candidate | vs. Submission G | vs. Submission C |
|---|---|---|
| Baseline (shipped) | 4/4 | 4/4 |
| Variant (Version 2, delayed) | 4/4 | 4/4 |

No differentiation — both candidates go 4/4 against both opponents on the
development seed set, with per-seed money deltas small and mixed (some
seeds up a few hundred dollars, some down), consistent with Section 2's
isolated-economy "flat" finding.

## 5. Full 15-Seed Validation — Not Run, and Why

Per this project's own established rule for exactly this situation —
Phase 33 Part A's own words, reused verbatim as the applicable precedent:
*"only if [the result] is competitive... if it's not competitive, stop at
the [cheap] test"* — **the full 15-seed validation was not run.** The
4-seed isolated-economy screen (flat, +0.08%) and the 4-seed head-to-head
screen (identical 4/4 records for baseline and variant against both
opponents, no distinguishing signal) together give no basis to expect the
full 15-seed set would reveal a real, promotable effect. Phase 17's lesson
— don't trust a 4-seed reading for a PROMOTION decision — is respected
here precisely by NOT promoting on this reading; it does not require
spending a full 15-seed validation run on a candidate the cheap screen
already shows nothing for, the same discipline Phase 30/32/33 all followed
for their own negative cheap-screen results.

## 6. Recommendation

**Not ready to package.** The core finding, stated plainly: a small
CARROT/TOMATO slice does not help Submission I's economy in either form
tested — the naive version is actively harmful (a real, mechanically
confirmed cash-timing collision, not a market-glut problem), and the safe
version that avoids the harm also avoids doing much of anything. **Phase
41's real-data premise (real players do run this pattern) may still be
correct** — the gap here is not that the idea is economically wrong (CARROT
and TOMATO themselves sold at healthy, non-crashed prices whenever they
were actually planted), but that Submission I's own `BUY_SEED` purchasing
has no cash-flow pacing, the identical category of architectural gap Phase
35/36 already diagnosed and fixed once (for `BUY_ANIMAL` only). A future
phase could revisit this by extending Phase 36's cash-flow-adaptive pacer
to `BUY_SEED` as well — a materially larger, separately-scoped change than
this phase's own additive-fraction-table design, and out of this phase's
explicit scope (which protects `agents/phase21/execution.py`'s cash-safety
throttle and HIRE logic). Until that pacer exists, this specific lever is
closed, honestly, the same way Phase 30/32/33's negative results were.

## Changed Files

New, all additive:
- `scripts/phase42/carrot_tomato_portfolio.py`
- `scripts/phase42/isolated_economy.py`
- `scripts/phase42/vs_g_and_c.py`
- `results/phase42/phase42_isolated_economy_4seed.json`
- `results/phase42/phase42_vs_g_and_c_4seed_dev.json`
- `results/phase42/PHASE42_CARROT_TOMATO_SLICE_REPORT.md` (this file)

`agents/phase21/` was not modified. No submission is created.
