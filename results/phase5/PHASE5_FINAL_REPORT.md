# PHASE 5 — Targeted Market-Impact Counter Experiment: Final Report

## 1. Executive Summary

**Hypothesis REJECTED.** A market-impact-aware replacement for Variant D's crop-substitution decision (the mechanism that redirects freed MELON capacity when the expansion-oriented detector fires) was built, verified against the real engine, and tested across the exact 15 seeds that established the existing frozen Variant D. It **lost every single seed (0/15 wins)**, versus the frozen control's 10/15, with a mean final-money loss of **-$10,371/episode** (mean $12,161 vs $22,532). A diagnostic ablation using naive current-price pricing did even worse (0/15, mean $4,919). A third alternative (Phase 3.3's existing proportional-diversification variant) also lost every seed (0/15, mean $10,906).

**Submission C is not modified. It remains champion.** No Submission E was created, per the brief's explicit instruction not to manufacture a new submission from a failed experiment.

The failure has a concrete, diagnosed mechanism (Section 13): estimating the *true* freed-tile production volume and feeding it through the verified market simulator does not, by itself, fix the underlying problem — it exposes a *different*, previously-invisible flaw in reusing the Phase 2.2 calibrated $/tile-day constant outside the small reference scale (n_tiles=10) at which the frozen Variant D uses it. The market simulator itself remains validated, useful infrastructure (Section 5); the volume-estimation step built on top of it this phase is what failed.

## 2. Hypothesis

"When Variant D detects an expansion-oriented opponent and redirects production away from MELON, selecting the replacement crop using the verified market-impact simulator may reduce self-inflicted market crashes and improve competitive performance," specifically targeting Phase 3.4's `self_inflicted_narrow_market_price_crash` finding.

## 3. What Changed

New, additive-only code under `agents/phase5/`:
- `agents/phase5/market_impact_substitution.py` — two drop-in replacement functions for `agents/phase3_3/interventions.py::variant_d_production_substitution`, matching its exact 3-argument signature so they plug directly into the *existing* `market_response_fn` parameter of `agents/phase3_8/adapters/competitive_v3_agent.py::make_competitive_v3_agent` (Submission C's own production adapter). No new adapter or controller was needed — this is the minimal possible integration point.
  - `make_market_impact_substitution()` — the primary experimental candidate: estimates freed tile capacity, backs out an implied unit count from the existing Phase 2.5 calibration, and prices that batch using the verified unit-by-unit market simulator (`agents/phase4/market_model.simulate_sell`).
  - `make_naive_price_substitution()` — diagnostic ablation D: same unit-count methodology, but priced with a single current-price quote (no decay), isolating whether any effect comes from decay-modeling specifically.
- `scripts/phase5_market_model_validate.py` — live re-validation of the market simulator against the real engine (Section 5).
- `scripts/phase5_run_experiments.py` — the experiment runner.
- `results/phase5/` — this report, raw results CSV, and per-decision traces.

## 4. What Remained Frozen

Untouched: `main.py`, Planner v1 (`agents/phase2_6/`), the Phase 2.5 economic model, the Phase 2.4 tactical scheduler, Variant D's own detection logic (`agents/phase3_3/expansion_detector.py`) and its existing substitution function (`variant_d_production_substitution`, imported and reused unchanged as the fallback and as the frozen control), the Phase 3.5 scaling response, the Phase 3.8 animal response, and Submission C's adapter itself. `git status --short main.py agents/phase3_3 agents/phase3_5 agents/phase3_8` shows no changes from this phase.

## 5. Market Simulator Validation

Before trusting any result, `agents/phase4/market_model.simulate_sell` was re-validated **live against the running engine** (not just by re-reading source, per Section 15), via `scripts/phase5_market_model_validate.py`: a scripted agent bought 40 units of WHEAT into its shed (bypassing production timing) and sold 40 units in one turn against a "pass" opponent (no interleaving).

| | Actual engine | `simulate_sell` prediction |
|---|---|---|
| Final WHEAT market inventory | 9999 | 9999 |
| SELL revenue | $1175.00 | $1175.00 |

**Exact match.** The simulator remains verified, useful infrastructure. It was NOT the source of this phase's failure (see Section 13).

## 6. Candidate Replacement Methodology

For each candidate crop (WHEAT, STRAWBERRY, CARROT, TOMATO, and MELON itself — no diversification or single-crop assumption was forced):
1. Freed tile capacity ≈ `melon_frac × land_quadrants_owned × 25` (an approximation, disclosed in code comments — it does not subtract animal-structure tiles; the frozen Variant D has no tile-accurate estimate either, so this is not a new regression, only a newly-explicit one).
2. Implied unit count = the existing, validated `economic_model.model.crop_production_value`'s isolated-$ estimate for that many tiles, divided by the crop's *current* market price.
3. That unit count is priced with `simulate_sell` (real decay) for the experimental candidate, or `units × current_price` (no decay) for the naive diagnostic.
4. Net value = simulated/naive revenue − seed cost. Highest net value wins (MELON included, so "keep MELON" is a legitimate outcome).

**On timing (Section 6):** searched the real engine source directly — there is no inventory-recovery-over-time mechanic (market inventory only moves via BUY/SELL orders; the brief's own phrase "town-demand recovery" does not correspond to any implemented mechanic, and none was invented here). Given that, `simulate_sell`'s cumulative revenue for a fixed number of *our own* units is mathematically identical whether sold in one batch or spread across turns, as long as no other order lands in between — which we cannot predict without using the opponent's private state (disallowed). A single N-unit batch anchored at the current public market inventory is therefore exact for our own contribution, not an approximation glossed over as one.

**Partial allocation / split candidates (Section 8): NOT implemented this phase.** Disclosed scope reduction — given the single-crop version's decisive, mechanistically-explained failure (Section 13), building a combinatorial or even a small fixed split-allocation search on top of the same flawed volume-estimation step would not have changed the conclusion, and was not run.

## 7. Ablation Design

| Label | Description |
|---|---|
| A / B | Submission C (already includes the existing frozen Variant D — this codebase does not have a "bare Variant D without C's other layers" as a separately meaningful control, since C's scaling/animal response layers touch disjoint config keys and never interact with the crop-substitution decision) |
| C | A/B + market-impact-aware replacement (this phase's primary candidate) |
| D | A/B + naive current-price diagnostic (same unit estimate, no decay-awareness) |
| E | A/B + Phase 3.3's existing `variant_c_melon_avoidance` (simple proportional diversification, reused unchanged) |

## 8. Target Failure-Seed Results

Evaluated against `expansion_oriented`, across the exact seeds (development 700000-700003, validation 701000-701004, held_out 702000-702005) that originally established the frozen Variant D (`results/phase3_3/experiments/intervention_results.csv`). These include the 3 seeds (700002, 701001, 702001) already on record as Variant D's own worst episodes — the highest-value diagnostic cases per Section 12.

| Candidate | n | Mean final $ | Median final $ | Mean margin | Win rate | Worst | Best |
|---|---|---|---|---|---|---|---|
| A/B (Submission C) | 15 | $22,532 | $24,182 | +$446 | **10/15** | $10,568 | $28,063 |
| C (market-impact) | 15 | $12,161 | $12,459 | -$5,671 | **0/15** | $9,350 | $14,012 |
| D (naive price) | 15 | $4,919 | $4,867 | -$12,913 | **0/15** | $4,170 | $5,940 |
| E (diversified) | 15 | $10,906 | $11,234 | -$11,275 | **0/15** | $8,891 | $11,877 |

Per-seed delta (C vs A/B), all 15 seeds:

| Seed | A/B | C | Δ |
|---|---|---|---|
| 700000 | $28,063 | $12,548 | -$15,515 |
| 700001 | $23,987 | $9,875 | -$14,112 |
| 700002 (Variant D failure seed) | $19,367 | $13,682 | -$5,685 |
| 700003 | $24,182 | $12,613 | -$11,569 |
| 701000 | $27,371 | $12,254 | -$15,117 |
| 701001 (Variant D failure seed) | $13,371 | $9,350 | -$4,021 |
| 701002 | $21,422 | $12,498 | -$8,924 |
| 701003 | $20,993 | $12,161 | -$8,832 |
| 701004 | $25,044 | $12,921 | -$12,123 |
| 702000 | $24,929 | $12,962 | -$11,967 |
| 702001 (Variant D failure seed) | $10,568 | $11,995 | **+$1,427** |
| 702002 | $23,386 | $14,012 | -$9,374 |
| 702003 | $24,464 | $11,941 | -$12,523 |
| 702004 | $26,589 | $11,147 | -$15,442 |
| 702005 | $24,243 | $12,459 | -$11,784 |

Even on the one seed (702001) where C improved over A/B's own number, C still lost to the opponent ($11,995 vs opponent's $17,856) — the "improvement" did not convert to a win.

## 9. Variant D Regression Results

A/B (Submission C, i.e. C with the frozen Variant D active) reproduces the previously-recorded Variant D numbers from Phase 3.3 exactly on the `expansion_oriented` seeds (protagonist-side; the `financial_summary`-derived total revenue differs from Phase 3.3's raw `final_money` only by C's other, disjoint layers never activating for this archetype — confirmed via `market_activations>0, scaling_activations==0, animal_response_activations==0` in the run logs). No regression in the frozen control was introduced by this phase.

## 10. Non-Target Regression Results

Ran A/B and C against all 6 non-`expansion_oriented` Phase 3.2 archetypes (passive, production_heavy, market_selling, animal_oriented, conservative, aggressive_investment), 2 seeds each (12 pairs, 24 episodes):

**Every pair is byte-identical in final money**, and `market_activations == 0` in all 24 episodes — the detector never fires for these archetypes, so the new substitution logic is never invoked. The experimental module is confirmed **fully inert outside its target scope**, exactly as required by Section 14.

## 11. Market-Price Analysis

`melon_harvested` for seed 700000: A/B = 0 units (its own chosen substitute crop fully replaces MELON, and no sunk MELON tiles survived to harvest in this trace); C = 55 units (some already-growing MELON tiles were harvested normally before the day-15 switch, exactly as the "don't destroy sunk assets" design intends). Despite harvesting *more* MELON, C's **total revenue was little more than half of A/B's** ($19,824 vs $34,336) — the loss is not explained by lost MELON production, it is explained by what happened to the *substitute* crop's own market (Section 13).

## 12. Win-Rate Analysis

A/B: 10/15 (67%) against `expansion_oriented` — consistent with its original Phase 3.3 promotion record. C, D, E: 0/15 (0%) each. This is not a marginal or seed-specific regression; it is a uniform, decisive loss across every seed tested, satisfying Section 19's "not a seed-specific accident" bar for confidence — just in the negative direction.

## 13. Failure Analysis / Mechanistic Explanation

Both new candidates share one methodology step: estimate the crop's implied unit count by dividing `crop_production_value`'s isolated-$ estimate (computed at the crop's **actual freed tile count**, ~20-25 tiles) by the crop's current market price. The frozen, validated `variant_d_production_substitution` never does this — it calls `crop_production_value` at a **fixed, small reference scale (n_tiles=10)** purely to *rank* crops, and never attempts to estimate the true batch size at all.

`CALIBRATION["revenue_per_tile_day"]` (Phase 2.2) is an empirically-measured *rate*, not a volume-independent constant — it was validated as a ranking signal at the scale it was measured at, not as something safe to multiply up to ~2.5x that scale. STRAWBERRY has the second-highest rate (42.88, behind only MELON's 69.49) among the candidates, and the narrowest market depth (T=100). Scaling its isolated-$ estimate up to the true freed-tile count inflates its implied *pre-decay* revenue enough that, on the seeds it was selected (e.g. day 15 in seed 700000, per `results/phase5/traces/`), it still outranks WHEAT/CARROT's more modest, decay-insensitive economics even *after* running that inflated volume through the decay-aware simulator — because the simulator can only crash a number that started too high; it cannot detect that the number itself was an artifact of an invalid scale-up of a small-reference calibration constant.

In short: this phase attempted to fix Variant D's real limitation (using a scale-blind calibrated ranking) by estimating true volume — but the *only* validated volume-scaling knowledge in this codebase is that same calibration constant, applied at a scale it was never validated for. Making the pricing step exact (the market simulator, which IS exact) does not compensate for an inexact volume estimate feeding into it. The naive diagnostic (D) confirms this is the dominant effect: removing the decay-correction entirely made results markedly *worse* ($4,919 vs $12,161 mean), meaning the decay-awareness was doing real, partial mitigation of an already-bad volume estimate — it just wasn't enough to overcome it.

E (Phase 3.3's existing proportional diversification) also lost every seed, consistent with Phase 3.3's own original finding that Variant D (single-best-crop) outperformed Variant C (diversification) — reconfirmed here under this phase's testing, not a new finding.

## 14. Promotion Decision

**NOT PROMOTED.** Per Section 19's criteria: the targeted failure-seed cases were not reliably improved (1/3 of the original crash seeds improved, and even that seed remained a loss against the opponent); Variant D's overall performance was not preserved (10/15 → 0/15 win rate); the regression is severe, uniform, and mechanistically explained as a genuine flaw in the new approach, not noise. **Submission C remains champion.**

## 15. Remaining Weaknesses

- The core, unresolved problem `self_inflicted_narrow_market_price_crash` targets is still open: the frozen Variant D's small-reference-scale ranking avoids this phase's specific new failure, but by construction it also never checks whether its chosen substitute's market can actually absorb the TRUE freed-tile volume — it simply got lucky that its calibration-based ranking (at n_tiles=10) tends to favor WHEAT/CARROT (lower $/tile-day but much wider, less crash-prone markets: T=400/450) over STRAWBERRY, for reasons that were never validated as intentional crash-avoidance.
- No validated method exists in this codebase for estimating true achievable production volume at an arbitrary tile count; `crop_production_value`'s calibration is only trustworthy at/near its own reference scale.

## 16. Recommended Next Experiment

Do not attempt to fix the volume-estimation step by further tuning it — that is exactly the kind of "cosmetic parameter change" this project's discipline warns against repeating. Instead: **directly measure `crop_production_value`'s calibration error as a function of tile count** (a small, cheap, standalone experiment: compare the calibrated estimate against actual harvested-and-sold revenue at n_tiles = 5, 10, 15, 20, 25 for each candidate crop, isolated, no opponent) before attempting any further market-impact-aware substitution work. If the calibration is confirmed scale-invariant within an acceptable error band, a corrected volume estimate could be re-attempted; if not (more likely, given this phase's evidence), the market-impact simulator's more promising use is probably a **selling-timing** decision (already-harvested inventory, known quantity, no volume-estimation problem at all) rather than a **planting/portfolio** decision.

---

## Validation Performed

- Market simulator: live-validated against the real engine (Section 5), exact match.
- Regression suite: not re-run this phase (no frozen file was touched; `git status --short` on every frozen path listed in Section 4 is clean).
- Target failure seeds: 15/15 run, paired, same seeds as Variant D's original promotion record.
- Non-target archetypes: 6 archetypes × 2 seeds × 2 candidates = 24 episodes, 100% byte-identical / fully inert.
- Full raw results: `results/phase5/phase5_results.csv`. Per-decision traces: `results/phase5/traces/*.json`.

## Changed Files

New (all additive; nothing pre-existing modified):
- `agents/phase5/__init__.py`
- `agents/phase5/adapters/__init__.py`
- `agents/phase5/market_impact_substitution.py`
- `scripts/phase5_market_model_validate.py`
- `scripts/phase5_run_experiments.py`
- `results/phase5/phase5_results.csv`
- `results/phase5/traces/*.json`
- `results/phase5/PHASE5_FINAL_REPORT.md` (this file)

No existing file was modified. `main.py` still builds Submission C.

## Git

```powershell
cd C:\Kaggriculture
git status
```

```powershell
git add agents\phase5 scripts\phase5_market_model_validate.py scripts\phase5_run_experiments.py results\phase5
```

```powershell
git status
git diff --cached --stat
```

```powershell
git commit -m "Phase 5: market-impact-aware Variant D substitution tested and rejected — verified market simulator confirmed exact against the live engine, but the volume-estimation step built on top of it (backing out unit counts from Phase 2.2 calibration at true freed-tile scale) inflates implied production for narrow-market, high-value crops (STRAWBERRY), losing 15/15 target seeds against the frozen control's 10/15; mechanism diagnosed, no submission created, Submission C remains champion"
```

```powershell
git status
```

```powershell
git push origin main
```

No `.tar.gz` is created or staged — there is no new submission from this phase.
