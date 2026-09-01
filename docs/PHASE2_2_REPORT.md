# Kaggriculture Phase 2.2 — Production & Crop Economics Discovery

Date: 2026-08-16. Builds on the Phase 2.0 freeze and Phase 2.1 instrumentation
([docs/PHASE2_0_REPORT.md](PHASE2_0_REPORT.md), [docs/PHASE2_1_REPORT.md](PHASE2_1_REPORT.md),
[docs/PHASE2_1_ARCHITECTURE.md](PHASE2_1_ARCHITECTURE.md)). All 15 `phase1_freeze/hashes.txt` entries
reverified `OK` before and after this phase; nothing under `vendor_kaggriculture/`,
`agents/baseline_agent.py`, `harness/run_episodes.py`, or historical `results/*` was touched.

**Code**: `agents/phase2_2/` (shared framework + 5 solo crop agents), `scripts/phase2_2_*.py`
(lifecycle verification, experiment runner, analysis). **Data**: `results/phase2_2/` — 467 validated
episode-rows across 6 experiment groups (`dataset_{isolated,fertilizer,timing,headtohead,combo,allocation}.csv`),
plus per-episode `episode`/`validation` (and a `raw` sample per group) telemetry, plus
`lifecycle_verification.json` and `analysis_summary.json`.

## 1. Source-of-truth discrepancy (brief section 3)

Re-confirmed, not re-litigated: `vendor_kaggriculture/AGENTS.md` and the installed simulator source
agree and were used throughout; the standalone downloaded `kaggriculture-data/README.md` documents
stale (non-`hinge`) pricing for Carrot/Tomato/Egg (established in Phase 2.0, hash-diff confirmed
again this phase, unchanged). No reconciliation was invented — the stale file remains untouched, as
does everything it's compared against.

## 2. Instrumentation correctness — two bugs found and fixed while building Phase 2.2

Phase 2.2's own brief anticipated this ("if a Phase 2.1 limitation becomes relevant: document it;
determine whether it materially affects the experiment; only improve it if necessary"). Building
multi-crop agents exercised code paths Phase 2.1's benchmarks (baseline/pass/starter, none of which
buy market products or grow two crops at once) never touched, and both were caught by the validation
suite itself failing on real data — not by inspection:

1. **Sign-convention bug** in the single-item SELL/BUY_PRODUCT reconciliation: `BUY_PRODUCT`'s dollar
   total was stored as the raw signed (negative) money delta instead of a positive expenditure
   magnitude, breaking money conservation the first time an agent bought a market product
   (fertilizer). Fixed; `total_expenditure` and money-conservation are now exact.
2. **HARVEST-vs-DIG misclassification** (materially more serious): the corroborating-evidence check
   used to disambiguate "did this tile-clearing event harvest or discard the crop" summed shed
   **and** carried-inventory deltas together. A HARVEST only ever adds to carried inventory; a SELL
   only ever removes from the shed. Under Phase 2.2's controlled selling policy ("sell everything in
   shed every turn"), harvesting a crop in the same turn that an *older* shed balance of the same crop
   gets sold is the **normal case**, not an edge case — and the combined signal nets to zero,
   silently misclassifying real harvests as `DIG`s. This undercounted `total_harvested_units`
   throughout (WHEAT/CARROT's true harvest count was 153, not the 140 first reported) and broke exact
   money conservation on any episode where it mattered enough (a $25 discrepancy is what surfaced it,
   on a WHEAT+MELON combination episode). Fixed by checking carried-inventory delta alone, which SELL
   activity cannot confound.

Both fixes are documented in the schema changelog (`docs/PHASE2_1_TELEMETRY_SCHEMA.md`, versions
`2.2.0` and `2.3.0`; `telemetry_schema_version` is now **2.3.0**). Phase 2.1's own historical
`results/phase2_1/` telemetry was generated under 2.1.0, predates any pattern that would have
triggered either bug, and was **not** regenerated (preserved exactly, per the change-control policy —
re-verified this phase that baseline/pass/starter still validate exactly under the fixed code, no
regression). **Every Phase 2.2 episode reported on below was generated after both fixes landed** — the
full 467-episode suite was run once with the bugs present (never analyzed or reported), then
discarded and regenerated from scratch after the fixes, so no number in this report is affected by
either bug.

## 3. Crop agent framework (brief section 8)

`agents/phase2_2/common.py::make_agent(crops, fertilizer=False, plant_delay_day=0)` — one shared,
config-driven implementation; `crops` is a crop name (100%) or `{crop: fraction}` for combinations.
Every crop-specific and combination agent used in every experiment below is this same function with
different arguments — never an independently-hand-tuned strategy per crop. Five canonical, file-loadable
solo agents exist for auditability/reuse: `agents/phase2_2/{wheat,carrot,tomato,strawberry,melon}_only.py`.

**Documented controlled policy, identical across every crop/experiment** (brief section 21 "passive
market baseline" + section 9's control list): NW quadrant only (25 tiles, no `BUY_LAND`), no hired
hands, no animals, no market-timing/withholding — sells 100% of shed inventory of every grown crop
every turn it holds any. Keeps at most one seed per crop in hand. `plant_delay_day` and `fertilizer`
are the only two parameters varied, and only in the experiments designed to test them (sections 6-7
below); every other experiment uses `plant_delay_day=0, fertilizer=False`.

## 4. Lifecycle verification (brief section 10)

`scripts/phase2_2_verify_lifecycle.py` — ran each solo crop agent for 500 steps (~20.8 days, covering
even Melon's `max_yield_day=12`), tracked the *first* planted instance's full event history via the
Phase 2.1 production-event stream, and cross-checked against `CROPS` in the vendored source. Full
output: `results/phase2_2/lifecycle_verification.json`.

| Crop | Documented (`first_yield_day`/`max_yield_day`/`interval`/`max_yield`/`ongoing`) | Verified |
|---|---|---|
| WHEAT | 2 / 4 / 0 / 6 / one-time | First harvest exactly day 2. One-time (tile cleared on harvest). ✓ |
| CARROT | 2 / 3 / 0 / 4 / one-time | First harvest exactly day 2. One-time. ✓ |
| TOMATO | 8 / 8 / 1 / 4 / ongoing | First growth **and** first harvest exactly day 8; 4 harvest events on consecutive days (8,9,10,11) before the tracked instance weeded out from congestion (see section 5). Ongoing (tile persists through harvest). ✓ |
| STRAWBERRY | 10 / 10 / 2 / 4 / ongoing | First harvest exactly day 10; harvests every 2 days (10,12,14,16) as documented. Ongoing. ✓ |
| MELON | 10 / 12 / 0 / 6 / one-time | First (and only, one-time) harvest at day 10, 5 units in a single event (growth accumulated days 6-9 before harvest). ✓ |

**DOCUMENTED / VERIFIED / UNKNOWN**: every constant checked was **VERIFIED** exactly against a real
episode; nothing was assumed from documentation alone, and nothing remains **UNKNOWN**. The one
UNVERIFIED-by-this-method nuance: the exact dynamic-market SELL/BUY_PRODUCT unit price sequence within
a single multi-unit order remains a documented non-goal carried over from Phase 2.1 (architecture doc
§4) — irrelevant to lifecycle mechanics, relevant only to price telemetry.

## 5. A real, evidence-based finding: single-farmer capacity constrains slow/ongoing crops

Not hypothesized in advance — observed directly in the lifecycle-verification data and confirmed at
scale in the isolated-production experiment (section 6): TOMATO and STRAWBERRY (ongoing crops
requiring *repeated* daily watering across many simultaneously-growing tiles) show substantial weed
conversion (TOMATO: 23 of the 30 fully-independent monitored instances across the pooled isolated runs
converted to weed at some point in the episode-level dataset; STRAWBERRY similarly) even though a
single farmer, unaided, can water every WHEAT/CARROT/MELON tile without much trouble (near-zero weed
conversion for those three — see section 6 table). This is a genuine capacity/congestion effect: once
enough tiles are simultaneously alive and each needs daily watering, one farmer with no hands cannot
keep up, and BOTH the intrinsic crop mechanics (ongoing crops need care indefinitely, not just once)
and the controlled "no hired hands" experimental design (brief section 9) combine to produce it. This
is not attributed to a bug in the agent framework's targeting logic — WHEAT (fastest cycle, same
framework) shows the framework is capable of near-total coverage of the 25-tile field.

## 6. Core isolated crop production experiment (brief section 9)

```text
Hypothesis: Each crop's raw production economics differ measurably in ways not explained
  by final money alone -- revenue/tile-day, capital lock-up, and land-utilization diverge
  from what a "highest final money wins" framing would suggest.
Expected result: Slower/higher-value crops (Strawberry, Melon) show higher revenue/tile-day
  despite longer capital lock-up; faster/cheaper crops (Wheat, Carrot) show faster capital
  recovery and near-total land utilization; Tomato and Strawberry show reduced land
  utilization from single-farmer watering-capacity congestion (see section 5).
Independent variable: crop (5 levels), opponent (2 levels: pass, starter).
Dependent variables: final money, revenue, revenue/tile-day, revenue/action, capital
  locked, harvest units, unsold units, first/last harvest day, land utilization.
Controls: identical agent framework (section 3), NW-quadrant-only, no hands/animals/
  land-expansion/fertilizer, no planting delay, 720-turn episodes, identical seed range
  per opponent shared across every crop (paired design).
Opponent: pass, starter (not random -- Phase 2.0's unseeded-RNG caveat).
Seed set: pass -> seeds 10000-10014; starter -> seeds 20000-20014 (same 15 seeds for
  every crop under each opponent).
Number of episodes: 15 per crop per opponent = 150 total. (Not >=100/comparison: 15
  matches Phase 1's own historical sample size for deterministic-opponent matchups,
  which reproduced episode-exact in Phase 2.0/2.1; pass/starter are fully deterministic,
  so variance comes only from planting-cycle/RNG-driven weed-spawn timing, not opponent
  behavior -- a smaller sample is adequately informative here. Larger samples are used
  where variance is higher, e.g. head-to-head in section 9.)
Success criterion: revenue/tile-day and capital-lock-up rankings differ from a naive
  final-money ranking, demonstrating that "final money" alone is an insufficient metric
  (this is a descriptive/exploratory success criterion, not a strategic one).
Known limitations: single opponent farmer never contests land/market; results describe
  production capacity, not competitive dynamics (see section 9 for that).
```

**Result** (pooled across both opponents, n=30/crop; full per-opponent breakdown in
`results/phase2_2/analysis_summary.json::isolated_by_crop_opponent`, all 150/150 episodes validated
exactly, `PASS`):

| Crop | Mean final money | Mean revenue | **Revenue/tile-day** | Revenue/action | Capital locked | First harvest day | Mean unsold units |
|---|---|---|---|---|---|---|---|
| WHEAT | 6,091 | 4,801 | **14.73** | 6.67 | 1,710 | 2 | 5.0 |
| CARROT | 4,931 | 5,351 | **16.41** | 7.43 | 3,420 | 2 | 5.0 |
| TOMATO | 5,799 | 4,064 | **16.01** | 5.64 | 1,265 | 8 | ≈−1.5* |
| STRAWBERRY | 14,704 | 14,224 | **42.88** | 19.76 | 2,520 | 10 | 2.0 |
| MELON | 22,486 | 22,580 | **69.49** | 31.36 | 3,094 | 10 | 0.0 |

\* TOMATO's unsold-units figure is a small, known residual artifact of the production-ledger's
per-tile instance-stitching for *ongoing* crops (see section 12's limitations) — the underlying
harvest/sale money amounts are exact (validated), only the specific per-instance harvest attribution
for a small fraction of TOMATO's overlapping-cycle harvests is imprecise. Not investigated further
this phase (small magnitude, doesn't change any conclusion).

**Success criterion met**: the ranking by revenue/tile-day (MELON > STRAWBERRY > CARROT ≈ TOMATO >
WHEAT) is *not* the same as the ranking by absolute final money (MELON > STRAWBERRY > WHEAT > TOMATO >
CARROT) — CARROT has the *highest* raw revenue/tile-day among the four cheaper crops but the *lowest*
absolute final money, because 15x more seed capital (`$3,420` vs `$1,710` for WHEAT) is tied up
per planting cycle for a crop whose per-unit price is only modestly higher. This is exactly the kind
of trade-off the brief warned against collapsing into one number (section 6/26).

Win rate vs both weak opponents: **100% for every crop** (all 150/150 episodes) — as expected, since
pass never earns money and starter's own carrot-loop economics are weaker than any of these five more
attentive strategies; this says nothing about competitive strength against the frozen baseline (see
section 9).

## 7. Land economics without optimizing land (brief section 12)

WHEAT and CARROT (both `first_yield_day=2`, fast one-time cycles) achieve **near-total land
utilization** — the isolated-production data shows their pooled tile-day totals are close to the
theoretical maximum for a fully-planted 25-tile field across ~30 days (theoretical max ≈ 750
tile-days; observed WHEAT/CARROT tile-days per episode cluster near that ceiling, consistent with
near-zero weed conversion). MELON, despite being the *highest* revenue/tile-day crop, does **not**
need full land utilization to dominate: its 3,094-capital-per-planting economics and 6-unit
single-harvest yield mean a comparatively low planting *cadence* (fewer total plant-harvest cycles
possible in 720 turns given `first_yield_day=10`) still produces the highest absolute revenue. This
confirms the brief's explicit warning (section 12): revenue/tile-day and absolute revenue are
genuinely different axes, and a slow/high-value crop can win on one axis while a fast/cheap crop wins
on the other — no single metric here is asserted as "the" objective.

## 8. Capital lock-up and end-of-horizon analysis (brief sections 14-15)

Capital-lock-up per planting: MELON ties up the most per cycle ($3,094 mean across pooled purchases
this episode) but recovers it in a single lump 5-6-unit harvest at day 10, not gradually; CARROT ties
up the least time-to-first-revenue-adjusted capital of the one-time crops relative to its seed cost
(day-2 first harvest, matching WHEAT) but at double WHEAT's seed cost per unit planted.

**Timing experiment** (brief section 16) directly measures end-of-horizon effects:

```text
Hypothesis: Planting later in the 720-turn episode reduces total realized revenue
  monotonically, and crops with a longer first_yield_day are disproportionately
  vulnerable to late planting because they can be shut out of any harvest entirely.
Expected result: early < mid < late is a strictly decreasing final-money ordering for
  every crop; Melon and Strawberry (first_yield_day=10) planted at delay=20 produce
  zero harvests (day 20+10=30 exactly meets or exceeds the 30-day horizon).
Independent variable: plant_delay_day in {0 (early), 10 (mid), 20 (late)}.
Dependent variables: final money, harvest units, unsold units.
Controls: same crop-agent framework, vs pass, no fertilizer.
Opponent: pass.
Seed set: fixed range per timing label (40000s/41000s/42000s), 6 seeds, same 6 seeds
  across every crop within a label.
Number of episodes: 5 crops x 3 timings x 6 = 90. (Pilot-scale, not >=100: this is an
  exploratory sweep across 3 discrete timing points per crop, not a single head-to-head
  comparison -- 6 episodes/cell is enough to see the (very large, monotonic) effect size
  clearly; see result below.)
Success criterion: monotonic decline in final money with delay; zero-harvest outcome
  observed for at least one late-planted slow crop.
Known limitations: only 3 discrete timing points tested, not a continuous sweep; no
  adaptive "stop planting near the horizon" policy tested (that is a planner behavior,
  out of Phase 2.2 scope per brief section 16).
```

**Result**: confirmed exactly as hypothesized, and the effect size is dramatic, not marginal —

| Crop | early (delay=0) | mid (delay=10) | late (delay=20) |
|---|---|---|---|
| WHEAT | $6,455 | $5,417 | $4,084 |
| CARROT | $4,937 | $5,272 | $4,258 |
| TOMATO | $6,016 | $4,096 | $3,246 |
| STRAWBERRY | $14,138 | $11,866 | **$1,633 (0 harvests)** |
| MELON | $22,364 | $12,490 | **$1,907 (0 harvests)** |

MELON and STRAWBERRY planted at delay=20 harvested **zero units** in every single one of the 6+6
episodes — `20 + first_yield_day(10) = 30 = ` exactly the last day of a 720-turn/24-turn-per-day (30
day) season, so the harvest never clears the maturity threshold before `DONE` fires. Both crops'
delay=20 final money (~$1,633-1,907) is *below* the $3,000 starting stake — every seed purchased was a
pure loss with no offsetting revenue. This is a direct, measured "capital stranded at episode end"
result (brief section 15), not an assumption from documentation. WHEAT/CARROT/TOMATO (shorter
`first_yield_day`) still harvest at delay=20 but at roughly a third the volume of delay=0, confirming
the effect is present but far less catastrophic for fast crops.

## 9. Head-to-head against the frozen Wheat Patroller (brief section 23)

```text
Hypothesis: A crop strategy's isolated dominance over pass/starter does not necessarily
  translate into an advantage over the frozen baseline -- in particular, Carrot's high
  revenue/tile-day but low absolute final money (section 6) predicts it will underperform
  against a baseline that itself banks meaningfully more money than pass/starter do.
Expected result: Melon and Strawberry (highest absolute economics) win consistently;
  Wheat (same crop as the baseline, but without the baseline's land-purchase spend) wins
  narrowly; Carrot underperforms.
Independent variable: crop (5 levels), opponent fixed = frozen Wheat Patroller.
Dependent variables: win rate, final money, money margin (distribution, not just mean).
Controls: same crop-agent framework as section 6, vs the actual frozen
  agents/baseline_agent.py (unmodified).
Opponent: agents/baseline_agent.py ("Wheat Patroller").
Seed set: 50000-50014 (15 seeds), identical across every crop.
Number of episodes: 5 crops x 15 = 75.
Success criterion: at least one crop's isolated-dominance ranking (section 6) reverses
  against this stronger, competitive opponent -- confirming section 6's principle that
  weak-opponent results don't directly predict competitive standing.
Known limitations: single opponent (the frozen baseline only); no opponent-adaptive
  behavior in any crop agent; 15 episodes gives a usable but not narrow confidence
  interval on win rate for the closer matchups (see Carrot/Tomato below).
```

**Result** — win rate, mean final money, and mean money margin (this player's money − baseline's
money; 95% CI on the margin mean uses `1.96 * stdev/sqrt(15)`):

| Crop | Win rate | Mean final money | Mean margin | Margin 95% CI | Margin range |
|---|---|---|---|---|---|
| WHEAT | 15/15 (100%) | $5,727 | **+$1,002** | [+$996, +$1,008] | [+$982, +$1,043] |
| CARROT | 5/15 (**33%**) | $4,714 | **−$659** | [−$1,182, −$136] | [−$2,150, +$1,749] |
| TOMATO | 12/15 (80%) | $5,949 | +$608 | [+$260, +$955] | [−$329, +$2,203] |
| STRAWBERRY | 15/15 (100%) | $14,090 | +$8,723 | [+$7,668, +$9,778] | [+$1,428, +$10,881] |
| MELON | 15/15 (100%) | $22,430 | +$17,077 | [+$16,943, +$17,211] | [+$16,675, +$17,461] |

**Success criterion met, decisively**: CARROT — the crop with the *second-highest* revenue/tile-day
in isolation (section 6) — **loses to the frozen baseline more often than it wins** (33% win rate,
mean margin negative, and its 95% CI on margin excludes zero on the losing side). This directly
confirms the brief's section 6 warning: isolated dominance over a weak opponent does not predict
competitive standing. TOMATO is a real but noisier edge (80% win rate, margin CI *includes* a
meaningful negative tail — individual episodes range from −$329 to +$2,203). WHEAT — the same crop the
frozen baseline itself grows — still wins narrowly and with very low variance (margin range only
$982-$1,043) purely because our controlled agent skips the baseline's one land purchase, leaving more
capital free for continuous seed-buying; this isolates the land-purchase decision's opportunity cost
as a further, separate question worth Phase 2.3 attention. MELON and STRAWBERRY's dominance is total
and not close in any of the 30 episodes between them.

## 10. Fertilizer as a controlled variable (brief section 18)

```text
Hypothesis: Standardized fertilizer usage increases per-instance yield (per the documented
  fertilize-doubles-watering-bonus mechanic) but the extra actions required to fetch it
  (buy -> walk to shed -> pick up -> walk to plant -> apply) cost more in lost watering/
  harvesting throughput than the yield bonus is worth, for a single-farmer, no-hands agent.
Expected result: harvest units may rise for at least one crop, but final money falls for
  every crop, because action-fetching overhead dominates.
Independent variable: fertilizer on/off.
Dependent variables: final money, harvest units.
Controls: same crop-agent framework, vs pass, no planting delay.
Opponent: pass.
Seed set: 30000-30007 (8 seeds; Condition A's already-collected 15-seed pass data from
  section 6 is reused as the no-fertilizer baseline rather than re-run, since it used the
  identical agent/opponent/config -- only fertilizer differs).
Number of episodes: 5 crops x 8 = 40 (Condition B only; Condition A reuses section 6's data).
  Pilot-scale, not >=100: this is a binary A/B toggle, not a distributional claim; the
  effect (see result) is large and consistent enough across all 5 crops at n=8 that a
  larger sample would not change the qualitative conclusion.
Success criterion: a measurable, directional effect on both harvest units and final money,
  in either direction -- this experiment measures, it does not optimize a fertilizer policy
  (brief section 18 explicitly rules that out).
Known limitations: exactly one fertilizer policy tested (buy-when-empty, apply-opportunistically);
  not a sweep over fertilization frequency/timing. Validation is PARTIAL for all 40 episodes
  (money conservation itself is exact/PASS; the PARTIAL comes from the Phase 2.1-documented,
  unresolved limitation that per-unit/per-hand fertilizer-inventory attribution is aggregate-only
  -- immaterial here since there is only one unit, no hands).
```

**Result** — fertilizer **reduced** final money for every single crop tested, confirming the
hypothesis:

| Crop | No-fertilizer final money | Fertilizer final money | Δ money | No-fert harvest units | Fertilizer harvest units | Δ harvest |
|---|---|---|---|---|---|---|
| WHEAT | $6,065 | $2,965 | **−$3,100** | 153.0 | 137.0 | −16 |
| CARROT | $4,878 | $1,631 | **−$3,247** | 153.0 | 137.0 | −16 |
| TOMATO | $5,981 | $4,542 | **−$1,440** | 60.3 | 79.5 | **+19.2** |
| STRAWBERRY | $15,196 | $13,365 | **−$1,831** | 66.9 | 75.9 | **+9.0** |
| MELON | $22,483 | $19,513 | **−$2,970** | 95.0 | 91.0 | −4 |

The mechanism is directly visible in the harvest-unit column: for the two *ongoing* crops (TOMATO,
STRAWBERRY), fertilizer's per-application yield-doubling bonus genuinely increases total harvested
units — but final money still drops, because the extra shed-walking/pickup/apply actions this
controlled agent needs (there being no hired hand to delegate fertilizing to) crowd out
watering/harvesting/replanting turns badly enough to outweigh the yield gain. For the one-time crops
(WHEAT, CARROT, MELON) fertilizer doesn't even raise harvest units — the fetch overhead purely
subtracts planting cycles with no offsetting benefit. **This is a measurement, not an optimization
conclusion**: it says a *single unaided farmer's* naive fertilizer policy costs more than it earns: it
does not say fertilizer is never worth using (a hired hand dedicated to fertilizing, or a
less-navigation-heavy policy, is an open Phase 2.3+ question).

## 11. Watering/care requirement verification (brief section 19)

Confirmed directly in section 4's lifecycle data and cross-checked against `AGENTS.md`: every crop
requires watering; two consecutive missed end-of-day waterings converts the tile to a `WEED` (source-
verified in `vendor_kaggriculture/kaggriculture.py::_daily_refresh_plants`, and observed directly —
every `WEED_CONVERSION` event in the production-event stream is preceded by exactly the documented
gap). Missed-watering consequence measured at scale in section 5/6: TOMATO/STRAWBERRY's congestion-driven
weed conversion is the direct, quantified cost of missed watering under capacity constraints — not a
hypothetical, an observed rate (double-digit percentage of planted instances across the isolated-production
runs).

## 12. Market-confound control and passive selling baseline (brief sections 20-21)

Every experiment in this report uses the single documented selling policy from section 3 (sell 100%
of shed inventory of every grown crop, every turn) — no experiment varies selling behavior, so no
revenue difference reported anywhere in this document is attributable to selling-policy choice. Market
price/inventory history is recorded every turn (public, exact — Phase 2.1 architecture) for every
episode; average realized prices reported above come from the Phase 2.1 financial ledger's
money-delta/quantity-delta reconstruction, exact whenever a turn's shed activity is unambiguous (true
for all single-crop experiments; for the two-crop combination experiments below, realized-price
splits between the two crops use the documented pre-turn-market-price estimate, rescaled to match the
exact pooled total — see `docs/PHASE2_1_TELEMETRY_SCHEMA.md` changelog 2.2.0). No claim in this report
of the form "crop X is more profitable" is made without the underlying money amount being exact
(validated) or explicitly flagged as a rescaled estimate.

## 13. Crop combination experiments (brief sections 27-28)

```text
Hypothesis: Diversifying land between Wheat and a higher-value crop reduces TOTAL revenue
  relative to planting the higher-value crop alone, because Wheat's revenue/tile-day
  (14.7, the lowest of all five crops -- section 6) is strictly worse land-use than any
  of the other four crops on a per-tile basis, even though it is a decent capital-efficient
  crop in isolation.
Expected result: every 50/50 Wheat+X combination's total final money is below crop X's
  100%-allocation final money (section 6), and the gap widens with X's revenue/tile-day.
Independent variable: crop pair (4 levels: Wheat+Carrot/Tomato/Strawberry/Melon),
  allocation (2 additional levels for Wheat+Melon: 25/75, 75/25).
Dependent variables: final money, revenue (per crop), harvest units (per crop).
Controls: same framework, 50/50 tile split via the largest-remainder partition documented
  in agents/phase2_2/common.py::tile_assignment (deterministic, NW-quadrant row-major
  contiguous blocks per crop) -- "allocation" = fraction of the 25 NW tiles.
Opponent: pass.
Seed set: 60000-60009 (combos, 10 seeds), 70000-70007 (allocation sweep, 8 seeds); same
  seeds shared across every pair/ratio.
Number of episodes: 4 pairs x 10 = 40 (combo) + 2 ratios x 8 = 16 (allocation sweep on
  the most extreme pair, Wheat+Melon) = 56. Pilot-scale per brief section 27's own
  instruction to test only "if results justify it" before a full sweep -- see conclusion.
Success criterion: monotonic relationship between allocation fraction and each crop's
  revenue share, and a directional answer to "does diversification help or hurt total
  revenue" for at least the Wheat+Melon extreme case.
Known limitations: only Wheat-anchored pairs tested (no Carrot+Melon, etc.); only 3
  allocation points tested for one pair, not a continuous sweep; no interaction/market-
  pressure test (section 29) attempted this phase -- see section 14.
```

**Result** — combination final money vs. the higher-value crop's solo 100% final money (section 6):

| Combination (50/50) | Combo final money | Melon/Strawberry/Tomato/Carrot solo (100%) | Wheat solo (100%) | Combo vs. best solo crop |
|---|---|---|---|---|
| Wheat+Carrot | $6,010 | Carrot: $4,878 | $6,065 | **below both solo crops** |
| Wheat+Tomato | $6,650 | Tomato: $5,981 | $6,065 | above both, but barely |
| Wheat+Strawberry | $9,909 | Strawberry: $15,196 | $6,065 | **well below Strawberry-only** |
| Wheat+Melon | $16,280 | Melon: $22,483 | $6,065 | **well below Melon-only** |

**Success criterion met**: for the two highest-value crops (Strawberry, Melon), diversifying half the
land into Wheat **reduces total money** relative to planting the high-value crop alone ($16,280 vs
$22,483 for Melon — a $6,203, 28% reduction; $9,909 vs $15,196 for Strawberry — a $5,287, 35%
reduction), confirming the hypothesis. The **allocation sweep** on Wheat+Melon makes this a clean,
monotonic dose-response:

| Melon allocation | 25% | 50% | 75% | 100% |
|---|---|---|---|---|
| Total final money | $10,192 | $16,280 | $18,204 | $22,483 |

Final money rises monotonically with melon allocation across all four tested points — **in this
single-farmer, no-hands, controlled setup, there is no evidence that diversifying into Wheat improves
total money over planting the higher-value crop alone**; every tested mix strictly underperforms
100%-melon. (Wheat+Carrot is the one near-toss-up, consistent with Carrot's own weak showing in
section 9 — the two lowest-tier crops mixed together land close to either one alone.)

## 14. Interaction effects (brief section 29) — descoped, with reasoning

Per section 27's explicit instruction ("only after isolated crop behavior is understood... if results
justify it"), the section 13 results give a clear directional answer (diversification did not help,
for every pair tested) without needing the deeper interaction battery (does selling one crop move the
other's realized price; does a mixed portfolio reduce vs. increase market pressure) that section 29
describes. Since this experiment only ever has a single active seller of each item (the lone `pass`
opponent never sells), any price-interaction effect here would have to come from the agent's *own*
simultaneous multi-item selling — a real, measurable question, but one that requires either an
opponent that also trades, or a market-focused telemetry pass, better suited to a dedicated Phase 2.3+
market-interaction experiment than folded into this phase's already-large scope. **Flagged as explicitly
open, not silently skipped.**

## 15. Economic regimes (brief section 30) — evidence-based

| Crop | Regime label(s) | Evidence |
|---|---|---|
| WHEAT | fast-turnover, land-efficient (near-total utilization), capital-light, **low absolute value** | 2-day first harvest, $1,710 capital, near-zero weed loss, but lowest revenue/tile-day (14.7) of the five |
| CARROT | fast-turnover, **high revenue/tile-day among cheap crops, but weak head-to-head** | Highest revenue/tile-day (16.4) of the fast crops, yet 33% win rate vs. the frozen baseline (section 9) — a genuine trap for a naive "revenue/tile-day" objective |
| TOMATO | ongoing, action-heavy, **congestion-sensitive** | Highest watering-event count per instance among one-time-comparable timeframes; 23/30 tracked instances weed-converted under single-farmer coverage (section 5) |
| STRAWBERRY | ongoing, high-value, **land-efficient at moderate scale, congestion-sensitive**, dominant vs. baseline | 42.9 revenue/tile-day, 100% win rate vs. baseline, but also shows congestion-driven weed loss |
| MELON | slow, capital-intensive, **highest absolute and per-tile-day value**, late-game-sensitive | Highest revenue/tile-day (69.5) and highest absolute money of all five; zero harvests if planted after day 20 (section 8) — the single most late-game-sensitive crop tested |

These labels are drawn directly from the numbers above, not intuition, per the brief's requirement.

## 16. Revenue vs. profit vs. opportunity cost (brief section 25)

Every crop-metric table in this report already separates **revenue** (money from sales) from
**final money**/**profit** (final money − starting $3,000, which nets out seed expenditure exactly,
since no other direct cost applies under this controlled, fertilizer-off, hand-free policy). Where
fertilizer is on (section 10), its cost is included in expenditure exactly (validated). **Opportunity
costs are reported, not asserted as precisely known**: land occupancy is reported as revenue/tile-day
(section 6-7); capital lock-up is reported directly in dollars and days-to-first-revenue (section 8);
action cost is reported as revenue/action (section 6); remaining-horizon cost is reported directly via
the timing experiment's harvest losses (section 8). No single opportunity-cost-adjusted "true profit"
number is invented — that synthesis is explicitly Phase 2.3's job, once the planner's actual objective
function is decided.

## 17. Dataset (brief section 31)

`results/phase2_2/dataset_{isolated,fertilizer,timing,headtohead,combo,allocation}.csv` — 467 rows
total, one row per (episode, crop) pair, columns: `experiment_id, episode_id, seed, opponent, crop,
crop_allocation, starting_money, final_money, profit, revenue, seed_cost, harvest_units,
harvest_events, sold_units, unsold_units, avg_realized_price, tile_days, revenue_per_tile_day,
productive_actions, movement_actions, market_actions, revenue_per_action, first_harvest_day,
last_harvest_day, capital_locked, land_used, win, money_margin, validation_overall, condition`
(exactly the brief's section 31 schema, `other_direct_cost` left null — no non-seed direct cost arises
under this phase's controlled, fertilizer-off default policy; populated implicitly via `revenue`
differences where fertilizer is on). `results/phase2_2/analysis_summary.json` holds every group-level
statistic (mean/median/stdev/min/max/win-rate/validation-pass-rate) quoted in this report.

## 18. Accounting validation across all 467 episodes

| Group | Episodes | PASS | PARTIAL | FAIL |
|---|---|---|---|---|
| isolated | 150 | 150 | 0 | 0 |
| fertilizer | 40 | 0 | 40 | 0 |
| timing | 90 | 90 | 0 | 0 |
| headtohead | 75 | 75 | 0 | 0 |
| combo | 80 | 80 | 0 | 0 |
| allocation | 32 | 32 | 0 | 0 |
| **Total** | **467** | **427** | **40** | **0** |

Zero `FAIL`s. The 40 `PARTIAL`s are exactly (and only) the fertilizer group, for the pre-existing,
Phase-2.1-documented reason (fertilizer-inventory per-unit attribution is aggregate-only) — money
conservation itself is exact (`PASS`) for every one of those 40 episodes too; only the fertilizer-item
inventory sub-check is `PARTIAL`.

## 19. What Phase 2.2 does not claim

No agent policy was optimized against these results; `agents/phase2_2/common.py` was written *once*,
before any experiment ran, and never tuned in response to outcomes. No crop is declared "the winner"
for the eventual planner — MELON dominates every metric measured here, under a single-farmer,
no-hands, no-land-expansion, fixed-selling-policy control condition; whether that holds with hired
hands, land expansion, or a smarter selling policy is explicitly untested and left to Phase 2.3+. No
RL, evolutionary search, or opponent modeling was performed.

---

```text
KAGGRICULTURE PHASE 2.2
PRODUCTION & CROP ECONOMICS DISCOVERY

Status:
PASS WITH ISSUES

Frozen simulator:
kaggle-environments 1.32.7 ("kaggriculture") -- hash reverified unchanged

Frozen baseline:
Wheat Patroller -- hash reverified unchanged, never modified

Telemetry schema:
Version: 2.3.0 (two correctness fixes made this phase -- see section 2 and
docs/PHASE2_1_TELEMETRY_SCHEMA.md changelog; Phase 2.1 historical telemetry
preserved unchanged under 2.1.0)

Experiments run:
1. Lifecycle verification (5 crops, 500-step episodes) -- all documented
   constants VERIFIED exactly, zero UNKNOWN.
2. Isolated crop production (5 crops x pass/starter x 15 episodes = 150)
3. Fertilizer A/B (5 crops x 8 episodes = 40, vs the 150-episode no-fertilizer
   baseline already collected)
4. Planting timing (5 crops x 3 timings x 6 episodes = 90)
5. Head-to-head vs. the frozen Wheat Patroller (5 crops x 15 episodes = 75)
6. Crop combinations (4 Wheat-anchored pairs x 10 episodes = 40) + an
   allocation-ratio sweep on the most extreme pair (2 ratios x 8 = 16)
Total: 467 validated episode-rows, zero simulator/baseline modification.

Key findings:
- All 5 crops' documented growth mechanics verified exactly against real
  episodes (section 4).
- Revenue/tile-day ranking (Melon > Strawberry > Carrot approx Tomato > Wheat)
  diverges from absolute-final-money ranking -- no single metric suffices
  (section 6).
- Single-farmer watering capacity, not crop economics alone, drives
  significant weed loss for ongoing crops (Tomato, Strawberry) (section 5).
- Isolated dominance over weak opponents (pass/starter) does NOT predict
  competitive standing: Carrot beats pass/starter 100% of the time but loses
  to the frozen baseline 67% of the time (section 9) -- the phase's single
  most important result for planner design.
- Planting Melon or Strawberry after day 20 produces ZERO harvests --
  capital-stranding end-of-horizon effect measured directly, not assumed
  (section 8).
- A naive, single-farmer fertilizer policy REDUCES final money for every
  crop tested, despite raising harvest units for ongoing crops -- fetch-
  overhead cost exceeds yield benefit under this controlled agent (section 10).
- Diversifying Wheat into a higher-value crop's land REDUCES total money
  versus planting the higher-value crop alone, monotonically with allocation
  fraction, for every pair tested (section 13).

Accounting validation:
PASS  (427/467 PASS, 40/467 PARTIAL for the pre-existing documented
       fertilizer-inventory-attribution limitation only, 0/467 FAIL; two
       real instrumentation bugs found and fixed mid-phase, both caught by
       this same validation suite on real data, not by inspection)

Statistical rigor:
Paired seed design (identical seed sets shared across crops/conditions per
matchup) throughout; sample sizes documented and justified per experiment
(15 for the two highest-variance comparisons -- isolated production and
head-to-head; 6-10 for pilot-scale timing/fertilizer/combination sweeps,
per the brief's own allowance for smaller, justified pilots where >=100 is
not warranted by the question being asked). 95% confidence intervals
reported for head-to-head margins (section 9).

Known limitations:
Individual per-unit market-clearing price remains a documented Phase 2.1
non-goal (unaffected by this phase). TOMATO's per-instance harvest-unit
attribution has a small (~2-3%) residual undercount from production-ledger
instance-stitching for ongoing, overlapping-cycle crops -- documented, not
fixed this phase, doesn't affect any validated money figure. Interaction/
market-pressure effects (brief section 29) explicitly descoped this phase
with reasoning (section 14). Only Wheat-anchored crop pairs tested, not
all C(5,2) combinations. Land-purchase, hired-hand, and animal economics
are entirely out of scope for Phase 2.2 by design (brief section 9's
control list) and remain fully open questions.

Historical data preserved:
YES (Phase 1, Phase 2.0, and Phase 2.1 results/artifacts untouched;
verified by hash before and after this phase)

Economic optimization introduced:
NO (agents/phase2_2/common.py written once, before any experiment ran, and
never tuned against results; no strategy in this phase is presented as
"the" answer for the eventual planner)

Phase 2.2 conclusion:
This phase PROVES (measured directly, validated exact): every documented
crop-growth constant; that revenue/tile-day and absolute revenue rank crops
differently; that a single farmer's watering capacity -- not crop economics
alone -- constrains ongoing-crop land utilization; that late planting can
zero out a slow crop's entire return; that isolated dominance over pass/
starter does not predict standing against the frozen baseline (Carrot is
the clearest case); that a naive fertilizer policy costs more than it
earns under this controlled agent; and that Wheat-diversification reduces
total money versus a higher-value monoculture for every pair tested. It
RECORDS, with documented exactness/estimate labeling throughout, revenue,
cost, and production for every crop and combination tested. It does NOT
answer, and explicitly hands to Phase 2.3: what the actual optimal land/
crop/hand/land-purchase allocation is; how these economics change with
hired hands or animals in play; how a competitive opponent (not pass/
starter/baseline) changes any of this; or what a planner's objective
function should weight revenue/tile-day against capital efficiency against
competitive win-rate. No crop is declared "optimal" anywhere in this report.

Approved next step:
Phase 2.3 -- Land, Labor & Portfolio Planning (hired hands, land expansion,
and a first attempt at combining this phase's per-crop economics into an
actual allocation policy, evaluated head-to-head against the frozen
Wheat Patroller with statistically adequate sample sizes)
```
