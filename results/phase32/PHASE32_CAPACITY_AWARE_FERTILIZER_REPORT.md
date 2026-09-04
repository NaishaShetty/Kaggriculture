# Phase 32: Capacity-Aware Fertilizer — Freeing Slack Doesn't Save It

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py` — read-only reference, not modified — `agents/phase2_4/common.py`). `agents/phase21/` (Submission H) and `agents/phase15/` (Submission G) are unmodified — confirmed via `git status --short`, which shows only `scripts/phase32/` and `results/phase32/` as new, untracked paths. No submission is created.

## Executive Summary

**[VERIFIED] Neither capacity-freeing approach beats the no-fertilizer isolated-economy baseline.** Deliberately earmarking hands for fertilizer duty (Approach A) is decisively worse than doing nothing about capacity at all (mean $19,408–$30,956 vs. Phase 30's naive $43,929 vs. the $55,785 no-fertilizer baseline). Trading crop-tile ceiling for fertilizer capacity (Approach B) at a mild -10% reduction gets closest to break-even ($51,023, -8.5% vs. baseline) but still loses; a -20% reduction collapses even harder than Approach A ($6,519, -88%). **Per this phase's own pre-registered decision rule, neither approach cleared the cheap isolated-economy screen, so no full 15-seed head-to-head was run and no submission is created.** Submission H (`agents/phase21/`, 9/15 vs. Submission G) remains the best version, unchanged.

**[INFERRED] The failure mode is not "still not enough slack" — it's that manufacturing slack costs more than fertilizer returns.** Both approaches directly reduce this agent's core economic engine (extra idle-prone hires under Fibonacci hiring costs for A; a smaller crop footprint for B) to make room for a task whose own yield is a slow, opportunistic trickle (`fertilizer_available` triggers at most once per animal per day) — the trade is structurally lopsided at this agent's scale, not merely under-resourced.

## 1. Idle-Capacity Recheck (Step 1, Before Building Anything)

Re-ran Phase 30's exact idle-capacity measurement (`scripts/phase32/idle_probe.py`, reusing `instrumentation/pipeline.py::analyze_replay`'s `action_efficiency`) on the current, unmodified `agents/phase21/` shipped agent, isolated vs. `"pass"`:

| Seed | idle_action_fraction |
|---|---|
| 700000 (Phase 30's exact measurement point) | **0.0703** |
| 700001 | 0.0803 |
| 700002 | 0.0633 |
| 700003 | 0.0712 |
| **Mean (4 dev seeds)** | **0.0713** |

**[VERIFIED] Phase 30's 7.0% figure reproduces exactly at seed 700000** (0.0703 vs. Phase 30's reported 7.0%), confirming nothing has changed since Phase 30 — the tight-capacity premise this phase tests against still holds.

## 2. Approach A: Dedicated Fertilizer Hands

Built `scripts/phase32/fert_execution.py::make_fert_execution_agent`, a from-scratch adaptation of `agents/phase21/execution.py` (new code, does not modify the frozen lineage) that reserves the last `n_dedicated_fert_hands` hand slots — added ON TOP of `agents/phase21/portfolio.py`'s own `n_hands` rungs — for FERTILIZE/COLLECT_FERTILIZER duty first, falling back to normal tasks when no fertilizer work is pending. Fertilizer tasks themselves are reconstructed at Phase 30's exact priority tiers (FERTILIZE tier 2, COLLECT_FERTILIZER tier 4) since Phase 30's own implementation was fully reverted and no longer exists in the repo — reconstructed, not literally reused, per this phase's honest accounting.

| Condition | Mean final money (4 dev seeds) | Mean peak fertilized tiles | vs. baseline |
|---|---|---|---|
| baseline_no_fertilizer | $55,785.00 | 0.0 | — |
| phase30_repro (fertilizer, no capacity freeing) | $43,929.25 | 11.2 | -21.3% |
| **+1 dedicated hand** | **$19,408.50** | 13.0 | **-65.2%** |
| **+2 dedicated hands** | **$30,956.00** | 17.0 | **-44.5%** |

**[VERIFIED] Both dedicated-hand variants are decisively worse than even Phase 30's naive no-capacity-freeing attempt**, despite reaching a higher peak fertilized-tile count (13–17, vs. 11.2 without dedicated hands) and, on two seeds with 2 dedicated hands, briefly exceeding 20 fertilized tiles. Per-seed detail shows the mechanism: seeds 700000 and 700003 collapsed to near-zero money ($160–$4,703) with `idle_action_fraction` spiking to 0.28–0.34 — well above the 7% baseline, not below it. **[INFERRED]** Extra hires are paid for under the agent's existing Fibonacci hire-cost curve (`_fib(current_hands + i)`), which grows steeply at the hand counts `agents/phase21/` already operates at (rungs up to 11); a dedicated hand that is frequently idle (fertilizer's own supply — `fertilizer_available` triggers at most once per animal per day — doesn't scale with added labor) is a hire whose cost is real and immediate but whose fertilizer payoff is thin and opportunistic. The cash drain then trips the agent's own cash-danger throttle, which caps hiring and starves other tasks — the same kind of cascading collapse Phase 21's execution layer was built to prevent, triggered here by a capacity-freeing mechanism that was supposed to prevent exactly this.

## 3. Approach B: Traded Crop-Tile Ceiling

Same `scripts/phase32/fert_execution.py` execution layer, `n_dedicated_fert_hands=0`, with `agents/phase21/portfolio.py::portfolio_targets`'s `crop_tile_target` wrapped and scaled down by a fixed factor (no dedicated hands — the freed capacity comes purely from a smaller crop footprint).

| Condition | Mean final money (4 dev seeds) | Mean peak fertilized tiles | vs. baseline |
|---|---|---|---|
| baseline_no_fertilizer | $55,785.00 | 0.0 | — |
| **-10% crop-tile ceiling** | **$51,023.00** | 17.5 | **-8.5%** |
| **-20% crop-tile ceiling** | **$6,518.50** | 12.0 | **-88.3%** |

**[VERIFIED] The -10% variant is this phase's best-performing fertilizer condition by a wide margin** — closest to the real-player 27–35-tile sustained scale of anything tried (peak 15–21 tiles across seeds, one seed reaching a full day at 20+ tiles) and by far the smallest economic loss (-8.5%, vs. -21.3% for Phase 30's naive attempt and -44/-65% for Approach A). **It still does not clear the no-fertilizer baseline.** **[VERIFIED] The -20% variant collapses even more severely than Approach A** — two seeds (700001, 700002) dropped to $39 and $352, again with `idle_action_fraction` spiking (0.16–0.24) rather than falling, the same cash-cascade signature as Approach A's worst seeds. **[INFERRED]** A -20% cut removes enough of the crop-tile footprint that the agent's own core revenue engine is measurably weakened before fertilizer's yield-doubling can compensate — the crop-tile ceiling is not slack in the idle-capacity sense (Section 1's 7% figure is about worker-TURNS, not tile count), so reducing it trades away real production, not waste.

## 4. Direct Comparison and the Pre-Registered Decision

Per this phase's own scope (Step 4): a full 15-seed head-to-head against Submission G/C was to be run ONLY for an approach that beat the no-fertilizer isolated-economy baseline on this cheap 4-seed screen first. Neither approach did:

| Approach | Best variant | Mean final money | vs. $55,785 baseline |
|---|---|---|---|
| A — dedicated hands | +2 hands | $30,956.00 | -44.5% |
| B — reduced tile ceiling | -10% | $51,023.00 | -8.5% |

**Neither result clears the baseline, so Step 5 (full 15-seed validation) was not run**, per the phase's own explicit instruction not to spend the more expensive validation on an approach that already failed the cheaper check. No submission is created.

## 5. Honest Diagnosis: Why Deliberately Freeing Capacity Didn't Rescue Fertilizer

**[VERIFIED]** The 7.0% idle-capacity ceiling Phase 30 found is real and reproduces exactly. **[VERIFIED]** Both capacity-freeing mechanisms tried here did measurably increase the fertilized-tile count reached (up to 17–22 peak tiles, vs. 11.2 with no capacity freeing) — closer to, though still below, the real-player 27–35-tile sustained scale. **[INFERRED, directly supported by the per-seed idle_action_fraction spikes in Sections 2–3]** The reason this doesn't translate into a win is that both mechanisms for freeing capacity have their own direct, immediate economic cost — extra Fibonacci-priced hires for Approach A, forgone crop production for Approach B — and fertilizer's own payoff (a roughly-doubled yield rate, but gated behind a slow, opportunistic `fertilizer_available` trickle that doesn't scale with added labor) is too thin and too slow to repay that cost at this agent's scale. **[HYPOTHESIS, not tested this phase]** Real top players (Larko, Milan Leonard) may sustain fertilizer profitably because their OWN baseline economy runs at a different equilibrium entirely (different hire-cost history, different land/hand ratios reached earlier) where the marginal cost of the same capacity-freeing move is smaller — but reproducing that equilibrium would be a much larger redesign than this phase's scope (test capacity-freeing on top of `agents/phase21/`'s existing, validated design) called for.

**[VERIFIED] This is the legitimate final answer this phase's brief asked for**: both approaches were given a genuine, honest attempt (real capacity was freed, real fertilizer tasks were run on top of it, in both a labor-side and a footprint-side variant), and both failed the same cheap screen Phase 30's naive attempt failed, for a related but distinct reason (the cost of freeing capacity, not the tightness of capacity itself). Fertilizer is not a fit for `agents/phase21/`'s specific design, even with deliberate capacity freeing attempted two different ways.

## Changed Files

New, additive only:
- `scripts/phase32/fert_execution.py` — fertilizer-aware execution layer with optional dedicated-hand support (isolated from `agents/phase21/`)
- `scripts/phase32/idle_probe.py` — Step 1 idle-capacity recheck
- `scripts/phase32/isolated_economy.py` — Steps 2–4 isolated-economy screen for both approaches
- `results/phase32/phase32_idle_probe_results.json`
- `results/phase32/phase32_isolated_economy_results.json`
- `results/phase32/PHASE32_CAPACITY_AWARE_FERTILIZER_REPORT.md` (this file)

No frozen file, `agents/phase21/`, or `agents/phase15/` was touched. No submission is created — Submission H (Phase 29) remains the current best.
