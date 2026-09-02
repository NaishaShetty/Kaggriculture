# Phase 3.7-B: NEW-F-005 Death Spiral Root-Cause Analysis

**Primary episode**: 104775830 vs Arum Puri, seed 852025866, final money $0 — the worst outcome across all 35 real episodes reviewed in this project.

## Method

Full turn-by-turn reconstruction of the real replay, cross-compared against a controlled same-seed re-run of Submission B's own unmodified agent (`agents.phase3_5.adapters.competitive_v2_agent`) against synthetic `passive`/`conservative` opponents, and against plain Planner v1 alone. Direct, turn-level comparison of cash, hands, tile state, and market prices.

## Finding 1: The Initial Collapse Is Seed-Determined, Not Opponent-Driven

The real episode's cash trajectory and WHEAT market price are **identical, turn-for-turn**, to a synthetic re-run of the same seed against a totally passive opponent, through at least turn 190 — both reach $0 by day 6-7 with hands stuck at 0. This is Planner v1's own standard front-loaded day-0 commitment (2 hands, COW+SHEEP, ~22 MELON tiles from a $3,000 start) interacting with this seed's RNG stream — not something the real opponent caused. This exact cash-trough pattern is documented as routine across every episode analyzed in this project (Phase 3.4/3.5) — not itself anomalous.

## Finding 2: The Real Failure Is Recovery, Not Investment

Both the real and same-seed synthetic runs show **all 22 MELON tiles decaying into weeds** between day 7-10, and **both animals escaping** (2 consecutive unfed days) by day 8-9 — identical collapse in both. The trajectories diverge starting turn ~194-260: the **synthetic run recovers** — at turn 265 (day 11) it sells 20 surviving MELON units for $5,174 (the payoff from a handful of the 22 tiles that, despite minimal single-farmer watering, survived to the crop's day-10 first-yield threshold), bootstrapping re-hiring and replanting to a final $28,344. The **real run never gets this**: shed inventory stays at exactly zero through the rest of the game, and final money is exactly $0.

**F-005 is a recovery-failure mechanism**, not an over-investment one. The cash-trough-to-hands-zero-to-weed-decay sequence is routine and *usually* survivable because a few of the many committed tiles happen to be watered by the lone farmer often enough, by chance, to reach harvest before full decay. In this one real game, that chance came up completely empty.

## Finding 3: The Ultimate Trigger for This Specific Divergence — UNRESOLVED

Why this real game's exact RNG/timing sequence produced zero surviving tiles, while the same-seed synthetic run produced a few, was not further isolated. A plausible contributing factor: the shared simulation's RNG stream (weed-spawn checks) and the lone farmer's exact per-turn watering priority are sensitive to the total sequence of actions from *both* players, so a different real opponent's actual behavior (vs. a near-inert synthetic `passive` bot) shifts which turns land which outcomes — a butterfly-effect sensitivity, not a strategic mechanism the opponent exploited. **Classified per the brief's own instruction: F-005 ROOT CAUSE OF THE SPECIFIC DIVERGENCE — UNRESOLVED.** The mechanism *class* (recovery-by-chance during a hands-zero window) is resolved with high confidence; the precise trigger for this one game's zero-survival outcome is not.

## Ablations Performed

| Ablation | Result |
|---|---|
| Same seed vs `passive`, Submission B's own agent | Recovers, $28,344 |
| Same seed vs `conservative`, Submission B's own agent | Recovers, $28,521 |
| Same seed, plain Planner v1 (no Phase 3.5/3.6 layers) vs `passive` | Recovers, $28,344 — **identical** to the Phase 3.5-wrapped version |

**Confirmed: this vulnerability is not introduced or worsened by any Phase 3.5/3.6 layer** — it is a latent property of frozen Planner v1's own day-0 commitment logic combined with the frozen tactical layer's per-turn watering scheduling, neither of which this project is permitted to modify.

## Severity Context

Single instance (1/13 = 7.7% of the current Submission B sample) but maximal severity — the only $0 outcome found anywhere in 35 real episodes reviewed across this entire project.
