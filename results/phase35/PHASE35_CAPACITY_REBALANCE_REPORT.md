# Phase 35: Capacity Rebalance Toward More Animals — Worker-Turn Slack Confirmed, Capital Crunch Kills It Anyway

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`). `agents/phase15/` (Submission G) and `agents/phase21/` (Submission H) are unmodified — confirmed via `git status --short`, which shows only `scripts/phase35/` and `results/phase35/` as new, untracked paths. No submission is created.

## Executive Summary

**[VERIFIED] The worker-turn premise behind this phase is confirmed correct: reducing `agents/phase21/`'s crop-tile target alone, with NO animal-target change at all, genuinely frees worker-turn capacity and does not hurt isolated economy** (idle-action fraction 7.1% → 18.8% at a crop-tile cap of 30, final money flat-to-slightly-up, +8.5%). This is real, measured spare capacity, not a guess.

**[VERIFIED] Every candidate that actually spent that freed capacity on more animals failed decisively anyway — not from the daily-hand-tax mechanism this phase was explicitly designed to avoid, but from a DIFFERENT, previously-undiagnosed cost: animals are capital-expensive to BUY (COW $400, SHEEP $500 — one-time, but large relative to crop seeds at $10-100), and ramping the animal target up on the same day-0–11 timeline the original ratio already uses front-loads a large capital demand into the game's tightest cash window, made worse by simultaneously cutting the crop revenue that would otherwise fund it.** Candidate A (SHEEP-heavy, Sundar-informed): -77.3% vs. baseline. Candidate B (A + 4th land quadrant, no hand change): -87.9%. Candidate C (COW-heavy, Crop Dusta-informed): -88.2%. A follow-up variant, A2 (identical end-state as A, but the extra SHEEP purchases staggered out to day 20 instead of day 11), recovered much of the loss (-29.2%, vs. A's -77.3%) — directly confirming the capital-timing diagnosis — but still did not clear the baseline.

**No candidate cleared the cheap isolated-economy screen, so no full 15-seed validation was run for any of them, per this phase's own decision rule. No submission is created. Submission H remains the current best, unchanged.**

**[INFERRED] This is a legitimate, important finding, not a failed phase**: the crop-heavy allocation `agents/phase21/` already ships is close to right FOR THIS EXECUTION LAYER's cash-flow dynamics, even though real winning opponents (Sundar, Crop Dusta) run measurably different ratios — those opponents' own (unknown) code evidently paces capital-intensive animal purchases very differently than a same-day-window rung-table reallocation does, and that pacing, not the target ratio itself, appears to be the real differentiator.

## 1. Real Trajectories (Full Day-by-Day, Reused From Phase 34's Extraction)

Both `agents/phase6/replay_forensics.py::extract_episode_timelines` dumps (`results/phase34/phase34_trajectory_sundar_worstloss.json`, `..._gold_105373474.json`, `..._gold_105341441.json`) already contain the full 30-day breakdown from Phase 34 — reused directly here, not re-extracted, since nothing about the underlying replays has changed.

| | Sundar (real, beat Submission H) | Crop Dusta (real gold-tier, rank #1, ep. 105373474) |
|---|---|---|
| Land | 3→4 at day 15 | Stays at 3 |
| Hands | Never exceeds 10 (below our 11) | 11-12 (close to our 11) |
| Animals by mid-game | COW2/SHEEP19/GOOSE3-5 (~24-26 total) | COW9/SHEEP4/GOOSE2 (~13-17 total) — COW-heavier |
| Crop tiles | Peak 27, cut to just 6-7 from day 20 | Stays HIGH, 55-59 — similar to or above our own 58 |

**[VERIFIED, confirmed directly, not just cited from the prompt]** Sundar trades crop tiles for a much larger, SHEEP-dominant animal footprint. **[VERIFIED] Crop Dusta does NOT make this trade at all** — Crop Dusta runs both a crop-tile footprint at least as large as ours AND a COW-heavier (not SHEEP-heavier) animal mix, at hand counts close to our own. These two real winners are informative in different, partially-conflicting ways — this phase treats both as data points, not templates to copy.

## 2. Idle-Capacity Confirmation (Step 2, Before Touching Animals)

`scripts/phase35/idle_capacity_check.py`: `agents/phase21/portfolio.py::portfolio_targets` reused unchanged, only `crop_tile_target` capped, land/hands/animals untouched — isolating the crop-tile variable alone, same idle-fraction methodology Phase 10/16/30 all used:

| Condition | Mean idle_action_fraction | Mean final money (4 dev seeds, vs. "pass") |
|---|---|---|
| baseline (crop_tile_target uncapped, 58 max) | 7.1% | $55,785.00 |
| capped at 40 | 13.3% | $55,517.00 (-0.5%, essentially flat) |
| **capped at 30** | **18.8%** | **$60,533.50 (+8.5%)** |

**[VERIFIED] The premise holds cleanly: cutting crop-tile target alone, before adding a single animal, nearly TRIPLES idle worker-turn capacity and does not cost money — it even helps slightly at the 30 cap.** This confirmed the reallocation was worth attempting with real spare capacity to spend, not a guess.

## 3. Candidates (Step 3)

`scripts/phase35/rebalance_candidates.py` — all wrap `agents/phase21/portfolio.py::portfolio_targets` unchanged; `_HANDS_RUNGS` is NEVER touched by any candidate, per this phase's explicit constraint.

| Candidate | Crop-tile target (final rung) | Animals (final rung) | Land | Informed by |
|---|---|---|---|---|
| A | 32 (down from 58) | COW9/SHEEP16 = 25 (up from 17) | 3 (unchanged) | Sundar (SHEEP-heavy), scaled down |
| B | 32 | COW9/SHEEP16 = 25 | **4** (new rung, day 18) | A + Sundar's 4th quadrant, no hand change |
| C | 32 | COW20/SHEEP5 = 25 | 3 (unchanged) | Crop Dusta (COW-heavy), same total-animal budget as A |
| A2 (follow-up) | 32 | COW9/SHEEP16 = 25, reached by **day 20** instead of day 11 | 3 (unchanged) | A, with the SHEEP ramp staggered later |

## 4. Isolated Economy: A, B, C All Fail Decisively — But NOT From the Hand-Tax Mechanism

`scripts/phase35/isolated_economy.py`, same 4 development seeds vs. `"pass"`:

| Condition | Mean final money | vs. baseline | Mean idle_action_fraction |
|---|---|---|---|
| baseline | $55,785.00 | — | 7.1% |
| Candidate A | $12,675.00 | **-77.3%** | 20.6% |
| Candidate B | $6,742.00 | **-87.9%** | 20.7% |
| Candidate C | $6,606.25 | **-88.2%** | 24.1% |
| Candidate A2 | $39,467.00 | **-29.2%** | 16.9% |

**[VERIFIED] All four are net negative; none clears the baseline.** **[OBSERVED] Idle_action_fraction ROSE in every candidate relative to baseline (17-24%, vs. baseline's 7.1%), the opposite of what a genuine worker-turn-shortage failure would show** — this is the signature of the agent's own cash-danger throttle repeatedly capping hands (idle time rising BECAUSE fewer hands are affordable, not because there's nothing for existing hands to do).

**[VERIFIED, by direct trace of Candidate A, seed 700000]** Money oscillates near-zero for most of the first 15 days (e.g., $621 → $7 → $234 → $0 → $184 → $8 → $19 → $7 → $14 → $1), with hands repeatedly bouncing between 5 and 11 as the cash-danger throttle engages and releases. **[INFERRED, confirmed by A2's partial recovery]** The cause is capital, not worker-turns: SHEEP costs $500/unit and COW $400/unit — buying 8 MORE sheep than the shipped ratio (SHEEP8→16) demands roughly $4,000 in ADDITIONAL one-time capital, requested on the SAME day-0–11 timeline the original COW/SHEEP ramp already uses, precisely while the SAME candidate's crop-tile reduction is also cutting the revenue that would fund it. **[VERIFIED] Staggering the identical end-state SHEEP target out to day 20 (Candidate A2) recovered most — not all — of the loss** (-29.2% vs. A's -77.3%), directly confirming this diagnosis: it is capital-purchase TIMING, not the target ratio itself or worker-turn availability, that is the dominant failure mode here. **[VERIFIED] Candidate B (adding the 4th land quadrant, $4,000 one-time, on top of Candidate A's already-strained cash flow) is even worse than A** — an additional one-time capital hit landing on an already cash-crunched schedule, consistent with the same mechanism.

## 5. Steps 5: No Full Validation, No Submission

Per this phase's own decision rule ("reject any candidate that doesn't clear agents/phase21/'s current baseline here... before spending a full validation on it"), no candidate (A, A2, B, or C) cleared the isolated-economy screen, so **no full 15-seed head-to-head validation against Submission G/C was run for any candidate.**

**On testing against a synthetic Sundar archetype specifically**: Phase 34 completed, but its Sundar-archetype reconstruction was found non-viable (it went bankrupt even in isolation vs. `"pass"` — `results/phase34/PHASE34_ARCHETYPE_AND_ROTATION_REPORT.md` Section 2-3) and was never established as a valid stand-in. Testing any Phase 35 candidate against it would not be informative for the same reason Phase 34 itself declined to — this leg of Step 5 is correctly skipped, not overlooked.

## 6. Honest Diagnosis: Why This Genuinely Different Approach Still Failed

**[VERIFIED]** This phase set out specifically to avoid the daily-hand-reset-tax mechanism that killed every prior additive attempt (Phase 30 fertilizer, Phase 31 TOMATO/GOOSE, Phase 33 Part C TOMATO/GOOSE-on-new-land) — and it succeeded at that: no candidate here added a single hand, and the idle-capacity check (Section 2) confirmed genuine, real worker-turn slack existed to spend. **[VERIFIED] The rebalance failed anyway, for a related but genuinely different reason**: this project's prior failures were about a RECURRING daily cost (hire fees, paid fresh every day for the whole game); this phase's failure is about a ONE-TIME cost (`BUY_ANIMAL`) that is nonetheless large enough, and requested early enough, to create the same kind of cash-crisis cascade this project has now seen from three structurally distinct sources (recurring hire tax, land-purchase timing in Phase 33 Part C, and now animal-purchase timing here). **[INFERRED]** All three share a common root: `agents/phase21/`'s execution layer commits to a target ratio's FULL requested state as soon as a rung's day threshold is crossed, with only a blunt, reactive cash-danger throttle (cap hands, don't spend below a reserve) to protect against overcommitment — there is no forward-looking, budget-aware pacing of one-time capital purchases (land, animals) the way real winning opponents' own (unknown) code evidently achieves.

**[HYPOTHESIS, not tested this phase]** A more thoroughly-staggered version of Candidate A2 (animal purchases paced even more gradually, or gated behind an explicit cash-reserve check similar to the existing `land_purchase_reserve` mechanism in `agents/phase21/execution.py`, rather than a day-indexed rung) might close more of the remaining -29.2% gap — but this would be a real architectural change (a budget-aware purchase-pacing mechanism, not a rung-table edit), a different and larger undertaking than this phase's scope of testing whether a straightforward rebalance of the existing rung tables helps. Per this project's standing discipline, that is a new hypothesis for a future phase to test with its own evidence, not a reason to keep tuning rung numbers here.

## Verdict

- **Worker-turn slack from reducing crop tiles**: real and confirmed. [VERIFIED]
- **Spending that slack on more animals (any of 3 ratios tested)**: fails decisively, driven by one-time capital-purchase timing colliding with the game's tightest early-cash window, NOT the daily-hand-tax mechanism this phase was designed to avoid. [VERIFIED]
- **Staggering the same end-state animal target later in the game**: recovers much, not all, of the loss — confirms the diagnosis but does not clear the baseline. [VERIFIED]
- **None of the four candidates (A, A2, B, C) is worth shipping.** No submission is created.

## Changed Files

New, additive only:
- `scripts/phase35/idle_capacity_check.py`
- `scripts/phase35/rebalance_candidates.py`
- `scripts/phase35/isolated_economy.py`
- `results/phase35/phase35_idle_capacity_results.json`
- `results/phase35/phase35_isolated_economy_results.json`
- `results/phase35/PHASE35_CAPACITY_REBALANCE_REPORT.md` (this file)

No frozen file, `agents/phase21/`, or `agents/phase15/` was touched. No submission is created — Submission H (Phase 29) remains the current best.
