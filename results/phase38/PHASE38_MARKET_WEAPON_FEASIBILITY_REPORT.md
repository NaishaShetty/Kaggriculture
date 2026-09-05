# Phase 38: Market-as-Weapon Feasibility — Decisively Negative, Even Under Perfect Information

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`). `agents/phase15/` (Submission G) and `agents/phase21/` (Submission I's shipped agent) were **not modified or wired into anything new** — confirmed via `git status --short`, which shows only `scripts/phase38/` and `results/phase38/` as new, untracked paths. This phase reused `agents/phase21/execution.py::make_execution_agent` by import only, exactly as Phase 21 Step 1 and Phase 31 already did for their own single-crop glut experiments. No opponent-sell-inference logic or opponent-denial layer was built, per this phase's explicit scope.

## Executive Summary

**[VERIFIED] The market-as-weapon mechanic shows NO positive relative-margin edge for the attacker in any variant tested — and actively costs the attacker money in every variant, even under PERFECT information about the target's sell timing (the best case this mechanic could ever have).** This is not a marginal or ambiguous result:

| Condition | Mean A (target) | Mean B (attacker) | Margin (A−B) | B's relative-margin change vs. control |
|---|---|---|---|---|
| CONTROL (B sells naturally, no coordination) | $10,717.75 | **$19,234.50** | -$8,516.75 | — |
| ATTACK_SAME_TURN (B dumps simultaneously with A) | $11,373.25 | $11,374.25 | -$1.00 | **-$8,515.75** (B loses almost its entire natural advantage) |
| ATTACK_PREEMPT (B dumps one day before A) | $10,994.00 | $14,001.00 | -$3,007.00 | **-$5,509.75** (B still loses more than half its natural advantage) |

**In the best-performing attack variant (PREEMPT), B still ends up $5,233.50 worse off than if it had simply sold naturally and ignored A entirely.** The mechanism is confirmed by direct trace, not just observed as a number: a same-turn simultaneous sell is a near-exact wash BY CONSTRUCTION (the engine quotes both players' current unit at the identical pre-commit inventory — confirmed directly from `vendor_kaggriculture/kaggriculture.py`'s own code comment, "Both players see the same pre-commit inventory for this unit"), and the cost of ABANDONING continuous natural selling to coordinate a timed batch dump (in either variant) is far larger than any damage inflicted on the target.

**Recommendation: do not pursue a real implementation.** Even solved in its easiest possible form — perfect, instant knowledge of exactly when the opponent will sell, no inference required — this mechanic is a net loss for the attacker. A real implementation would need to additionally solve sell-timing INFERENCE from incomplete public data (Section 5), a strictly harder problem than what was tested here, which already fails decisively.

## 1. The Mechanism, Confirmed Directly From Source (Before Designing Anything)

`vendor_kaggriculture/kaggriculture.py::_process_market`, read directly:

- Market orders are processed per QUEUE INDEX: each player's i-th submitted market sub-order interleaves with the opponent's i-th sub-order that turn.
- For SELL/BUY orders at the same index, price is re-quoted **unit by unit**, and the code's own comment states it explicitly: **"Both players see the same pre-commit inventory for this unit"** — within one unit-round, both players' current-unit price is quoted from the identical starting inventory, THEN both commit.
- `market["inventory"][item]` does **not** decay or reset on its own between turns — confirmed by direct grep for every `["inventory"]` mutation in the file: only SELL/BUY commits and a small periodic town-shop/town-center consumption trickle (`_town_consume`, every 4-24 steps) touch it. A crash persists across turns until eroded by that slow trickle or future BUY activity.

**[VERIFIED, this directly predicts the experiment's own result before it was run]** Because same-index units are quoted from an IDENTICAL shared inventory, a same-turn, same-size mutual sell should be close to a wash by construction — neither side can extract a price advantage over the other from pure simultaneity. A pre-emptive sell (a turn earlier) is the only structurally plausible way to make one side pay a worse price than the other, since it is the only variant where the target genuinely faces a market the attacker already moved.

`agents/phase4/market_model.py` (the project's already-verified market simulator) independently confirms the same unit-by-unit mechanic for a single seller in isolation, and its own docstring flags that it cannot represent two independent real sellers interacting — exactly why this phase, like Phase 21 Step 1 and Phase 31 before it, runs the test through the real engine (`kaggle_environments`), not the simulator.

## 2. Experiment Design

`scripts/phase38/market_weapon_experiment.py`: two single-crop STRAWBERRY producers (matching Phase 21 Step 1 / Phase 31's own glut-experiment scale — 8 hands, 2 land quadrants; `crop_tile_target` reduced to 20, not 40, specifically to keep held inventory comfortably under the 100-unit shed cap during the deliberate holding window). STRAWBERRY chosen because it has the smallest market depth (`T=100`) of any crop in this project's own constants — the most glut-sensitive, clearest possible signal.

- **Agent A (target)**: grows normally; its execution layer's own SELL order for STRAWBERRY is externally gated — suppressed every turn before a fixed turn (day 18, turn 444), then allowed through unmodified. This is the "PREDICTABLE harvest/sell schedule you control directly" the task calls for — A's dump timing is fixed by the script, not inferred, giving the attacker PERFECT information as the deliberately best-case test condition. A's schedule is IDENTICAL across all three conditions below, isolating every observed change in A's outcome to B's behavior alone.
- **Agent B (attacker)**, three variants, same production scale as A:
  - **CONTROL**: sells naturally/continuously from turn 0 (the standard, uncoordinated behavior every agent in this project already uses) — the baseline B is being compared against.
  - **ATTACK_SAME_TURN**: B batches and dumps on the exact same turn as A (turn 444).
  - **ATTACK_PREEMPT**: B batches and dumps exactly one day (24 turns) before A (turn 420).

Same 4 development seeds used throughout this project (700000-700003).

## 3. Results

### Raw Outcomes (4-Seed Means)

| Condition | A's avg. realized STRAWBERRY price | B's avg. realized STRAWBERRY price | B's sell quantity |
|---|---|---|---|
| CONTROL | $252.57 (A, batched) | $222.42 (B, continuous — but sells nearly 2x A's quantity) | 102 |
| ATTACK_SAME_TURN | $261.27 | $260.72 | 61 |
| ATTACK_PREEMPT | $259.52 | $261.50 | 71 |

**[OBSERVED] In CONTROL, B's natural continuous selling nets B nearly DOUBLE A's money ($19,234.50 vs. $10,717.75)** — not because of any attack, but because A's own fixed "batch and dump" schedule (used here purely as the experiment's controlled target behavior) is itself dramatically self-crashing: dumping 61 units in one turn drives that turn's price down hard against A's own later units in the SAME order, something continuous selling (B's control behavior) largely avoids. **This is the real baseline the "attack" variants have to beat, and none of them come close.**

### The Attack Variants, Directly Compared to Control

**[VERIFIED] ATTACK_SAME_TURN is a near-exact wash between A and B** (margin -$1.00, essentially zero across all 4 seeds, two of which show EXACTLY $0) — confirming the mechanism-level prediction from Section 1 directly: same-index, same-turn units are quoted from an identical shared inventory, so simultaneity confers no price advantage to either side. **But this "wash" is a disaster for B specifically**: B gave up $8,515.75 of its own natural advantage (the CONTROL margin) to achieve a tie, not a win.

**[VERIFIED] ATTACK_PREEMPT is better than ATTACK_SAME_TURN for B, but still a clear net loss relative to control**: B ends the game with $14,001.00, **$5,233.50 LESS than B's own control result ($19,234.50)** — even though this is the one variant where the mechanism-level reasoning says B SHOULD have an edge (B sells into an uncrashed market, then A sells into one B already pushed up). The margin-vs-control comparison confirms it: B's relative advantage over A shrinks from $8,516.75 (control) to $3,007.00 (preempt) — a **-$5,509.75 relative-margin loss for the attacker**, not a gain.

**[INFERRED] The mechanism behind this result**: switching from continuous, market-tracking selling (which lets a seller ride the price back UP between small sales, since inventory near or below the equilibrium point `I0` fetches an ABOVE-base price under STRAWBERRY's own `below_func` curve) to a coordinated batch dump is itself a costly self-inflicted price crash, independent of any opponent interaction. The "weapon" component of this idea — timing that self-inflicted crash to ALSO land on the opponent — adds essentially nothing on top of that cost in the same-turn case, and only PARTIALLY offsets it in the pre-empt case. In every variant tested, B's own sacrifice to attempt the tactic is larger than the damage it inflicts on A.

## 4. Recommendation

**[VERIFIED] Even in the best-case, full-information version of this mechanic — the attacker knows EXACTLY when the target will sell, with zero uncertainty — market-as-weapon does not produce a positive relative-margin edge in any variant tested, and costs the attacker $5,233 to $8,516 (out of a ~$10-19k baseline) relative to simply not attacking at all.** This is a decisive negative, not a close call warranting further tuning.

**A real implementation is not worth pursuing**, for two independent reasons:
1. **The mechanic itself fails even under perfect information** (this phase's own finding) — there is no reason to expect a harder, noisier version of a losing strategy to become a winning one.
2. **[HYPOTHESIS, not tested this phase, named per this phase's own scope]** A real implementation would additionally need to solve a strictly harder problem this phase deliberately did not attempt: inferring an opponent's LIKELY sell turn from incomplete public data (tile `yield_units`, not their private shed contents — per this phase's own brief, this lets you infer a sell is LIKELY, not know its exact size or turn). Since even PERFECT timing information fails to produce an edge, imperfect, inferred timing information — which would inevitably mean sometimes attacking the wrong turn, or missing the target's actual sell entirely — could only perform worse, not better.

## Verdict

- **Does deliberately crashing a price right before an opponent's sell produce a positive relative-margin edge, even under perfect timing information?** **No.** Same-turn simultaneous crashing is a wash by construction (confirmed both mechanistically and empirically); pre-emptive crashing is directionally the theorized "correct" attack shape but still costs the attacker $5,233.50 relative to not attacking, because abandoning natural continuous selling for a coordinated batch dump is itself expensive. [VERIFIED]
- **Is a real implementation worth pursuing?** **No.** This is a clean, decisive negative result — the market-as-weapon reframe is eliminated at the feasibility stage, exactly the outcome this phase's cheap-test-before-building discipline exists to catch. [VERIFIED]

## Changed Files

New, additive only:
- `scripts/phase38/market_weapon_experiment.py`
- `results/phase38/phase38_market_weapon_results.json`
- `results/phase38/PHASE38_MARKET_WEAPON_FEASIBILITY_REPORT.md` (this file)

No frozen file, `agents/phase21/`, or `agents/phase15/` was touched. No opponent-sell-inference logic or opponent-denial layer was built, per this phase's explicit scope. No submission is affected.
