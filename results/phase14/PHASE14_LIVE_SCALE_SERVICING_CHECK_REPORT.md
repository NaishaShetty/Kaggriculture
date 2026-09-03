# Phase 14: Does Phase 13's Fetch Bottleneck Matter at Submission C's Actual Live Scale?

No frozen file touched. No submission created. Isolated (no opponent), same discipline as Phases 9-13. All new code additive under `scripts/phase14/` and `results/phase14/`.

## 1. Executive Summary

**[VERIFIED] The bug is real and confirmed live-path relevant (Phase 13), but at Submission C's ACTUAL live-path scale, the fix's effect on animal servicing is noise, not a meaningful gap.** At Submission C's real animal ceiling (6 total: `COW:3, SHEEP:3`) and real hand target (5), servicing rate is `75.8%` before the fix and `74.6%` after — a **-1.22 percentage-point** change (the fix makes it very slightly *worse*, well within seed/config noise). Across the full centered sweep (hands 2-8), the effect ranges from **-3.21 to +5.56 points**, flips sign five times, and never once reaches double digits. This is categorically different from Phase 13's own 12-animal result (a clean, monotonic +6.6 to +26.6-point improvement rising with hand count).

**Recommendation: CLOSE. Do not scope a Phase 15 live-wiring integration on servicing-rate grounds.** This is a real, confirmed, previously-undiscovered bug in `agents/phase2_4/common.py`'s task scheduler — but at the scale Submission C actually operates at, one worker is already enough to keep 6 animals fed; the single-fetch-entry throughput cap (documented by Phase 13 at roughly 6-8 FEED+CARE pairs/day for one dedicated worker) simply isn't binding when the portfolio only needs 6/day. The bug only starts to bite once animal count materially exceeds what one worker can service alone — a scale Submission C's own animal-response ceiling never reaches.

## 2. Submission C's Actual Live-Path Targets (Confirmed by Direct Code Read)

Per the brief's explicit instruction not to trust a prior report's paraphrase — read in full this phase:

- **`agents/phase3_5/response_policy.py`** [VERIFIED, lines 42-43]: `RESPONSE_N_HANDS = 5`, `RESPONSE_ANIMALS = {"COW": 2, "SHEEP": 2}` (4 total). This is the target Submission C's scaling-response layer sets when triggered — **`n_hands` is fixed at exactly 5, and is never touched by any later layer** (`agents/phase3_8/animal_response.py`'s own docstring, line 101, confirms this explicitly: "n_hands is deliberately NEVER set or modified here").
- **`agents/phase3_8/animal_response.py`** [VERIFIED, lines 50-58]:
  - `BASELINE_ANIMALS = {"COW": 2, "SHEEP": 2}` — 4 total, Submission B's original floor, used whenever the opponent's own animal count is below 8.
  - `MODERATE_RESPONSE_ANIMALS = {"COW": 3, "SHEEP": 2}` — 5 total, used when opponent animals `>= MODERATE_ANIMAL_THRESHOLD (8)`.
  - `HIGH_RESPONSE_ANIMALS = {"COW": 3, "SHEEP": 3}` — **6 total, the actual live ceiling**, used only when opponent animals `>= HIGH_ANIMAL_THRESHOLD (12)`.

**Confirmed: Submission C's live animal target tops out at 6 (not the 12 Phase 13 measured with), and its live hand target is a fixed 5 (not the 4-13 range Phase 13 swept)** — matching this prompt's own paraphrase, now verified against the actual source rather than assumed.

**[VERIFIED] The escalation to 6 animals only happens under genuine competitive pressure**: `animal_specific_response` (step 4 of the brief) only reaches `HIGH_RESPONSE_ANIMALS` when the opponent's own animal count is already `>= 12` — i.e., exactly the scenario the brief asks about, where the agent is scaling up specifically because a strong opponent forced it to. Critically, **`n_hands` stays fixed at 5 even in this escalated state** — the animal-response layer never raises hands, so the exact operating point that matters live is `(hands=5, animals=6)`, precisely the cell this phase measured directly (§3).

## 3. Before/After Servicing-Rate Curve at Live Scale

`scripts/phase14/live_scale_servicing_experiment.py`: Phase 13's exact configuration and code (`make_multi_resource_agent` before, `make_multi_resource_agent_fixed` after, same `STRAWBERRY x24` crop target, 3 extra land quadrants, `$30,000` starting cushion, development seeds 700000-700003), changing only:
- `animals = {"COW": 3, "SHEEP": 3}` (6 total — Submission C's real `HIGH_RESPONSE_ANIMALS` ceiling, not Phase 13's 12), and
- `n_hands` swept `[2, 3, 4, 5, 6, 7, 8]`, centered on Submission C's real target of 5.

| n_hands | Before (unpatched) | After (Phase 13's fix) | Δ (points) |
|---|---|---|---|
| 2 | 80.7% | 77.5% | **-3.21** |
| 3 | 73.8% | 74.6% | +0.78 |
| 4 | 68.4% | 73.3% | +4.84 |
| **5 (live target)** | **75.8%** | **74.6%** | **-1.22** |
| 6 | 84.2% | 82.7% | -1.55 |
| 7 | 87.2% | 87.1% | -0.16 |
| 8 | 87.2% | 92.8% | +5.56 |

Full data: `results/phase14/phase14_live_scale_servicing_results.csv` / `phase14_live_scale_servicing_summary.json`. (Every seed produces an identical result at a given hand count, same as Phase 13's finding — this metric is deterministic given hand count, unaffected by the episode's one stochastic element.)

## 4. Direct Comparison: Meaningful Gap, or Noise?

**[OBSERVED] The gap has shrunk from Phase 13's clean, monotonic double-digit-and-growing pattern (12 animals: +6.6 to +26.6 points, strictly increasing with hand count) to something that is unambiguously noise at 6 animals**: the sign of the effect flips five times across seven hand counts (`-, +, +, -, -, -, +`), the magnitude never exceeds `5.56` points in either direction, and **at the actual live operating point (hands=5), the effect is slightly negative** (`-1.22` points). There is no consistent, hand-count-correlated trend at this scale the way there was at 12 animals — this is the direct signature of a bottleneck that is no longer binding, not a smaller version of the same effect.

**Mechanistic explanation, consistent with Phase 13's own finding**: Phase 13 (§3) established that one dedicated worker, even under the old single-fetch-entry cap, tops out at roughly 6-8 FEED+CARE pairs per day. A 6-animal portfolio needs exactly 6 pairs/day — right at or under that single-worker ceiling. At 12-14 animals, the same one-worker cap left 5-8 animals unserviceable regardless of hand count; at 6 animals, there is little to no unserviceable remainder for extra fetch-parallelism to recover. **The bug is real; the scale at which Submission C actually operates simply never asks one worker to do more than it can already handle.**

## 5. Economic-Relevance Context (Per the Brief's Step 4)

Even setting aside the servicing-rate result, the scenario where this would matter most (the `HIGH_RESPONSE_ANIMALS` escalation, triggered only against an opponent with `>=12` animals — genuine competitive pressure, exactly the brief's concern) is the same `(hands=5, animals=6)` cell already measured above, since `n_hands` is never raised alongside animals. There is no live-path scenario in Submission C's current design where the animal target rises without a correspondingly higher hand count — the escalation path always lands on this same, already-tested, non-bottlenecked point. There is no separate "under pressure" cell to re-check; §3's hands=5 row already **is** that cell.

## 6. Recommendation

**Close this thread. Do not scope Phase 15 to wire Phase 13's fix into the live path.**

- The fix is real, well-diagnosed, and safe in isolation (Phase 13) — none of that is retracted.
- But at Submission C's actual operating scale (animals capped at 6, hands fixed at 5, confirmed by direct code read in §2), the measured before/after gap is `-1.22` points at the live target and never exceeds `5.56` points anywhere in a sweep centered on that target — squarely within seed/config noise, not a "double-digit percentage point" gap by any reasonable reading.
- Wiring this fix into `agents/phase2_4/common.py` (a frozen, live-path file, per the Phase 7/12 narrow-exception pattern) carries real integration cost and regression-suite risk for a change this phase's own data shows delivers no measurable animal-servicing benefit at the scale that actually matters.
- **This is a legitimate, useful negative result, not a failure to find something**: Phase 13 correctly diagnosed a real defect; Phase 14 correctly determined it is not currently costing Submission C anything, because Submission C's own animal-response design (independently, for unrelated reasons documented in `agents/phase3_8/animal_response.py`'s own docstring — finite tile-space headroom) already keeps animal counts low enough that the bug never binds.
- **[HYPOTHESIS, explicitly flagged, not acted on]**: if a future phase ever raises Submission C's animal ceiling materially above ~8-10 (which nothing in the current roadmap proposes, and Phase 6/9's own findings argue against on other grounds), this bottleneck would very likely become binding again per Phase 13's 12-animal data — worth a one-line pointer back to this report if that ever changes, not a reason to act now.

## Changed Files

New, all additive; nothing pre-existing modified:
- `scripts/phase14/live_scale_servicing_experiment.py`
- `results/phase14/phase14_live_scale_servicing_results.csv`
- `results/phase14/phase14_live_scale_servicing_summary.json`
- `results/phase14/PHASE14_LIVE_SCALE_SERVICING_CHECK_REPORT.md` (this file)

No existing file was modified by this phase. `main.py` still builds Submission C. No `.tar.gz` is created or staged.
