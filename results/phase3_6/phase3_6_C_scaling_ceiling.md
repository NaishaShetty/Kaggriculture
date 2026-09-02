# Phase 3.6-C: Extreme Scaling / Competitive Ceiling

**Hypothesis H3**: There exists a competitive scaling ceiling beyond which additional labor/animal investment becomes economically inferior or simply cannot close the opponent's advantage.

## What Was Attempted

An archetype ladder (`agents/phase3_6/opponent_classes_scaling_ladder.py`) at 5, 7, 10, and an attempted 11-12 hands, using the project's existing `make_agent_23` factory (no new agent logic, same discipline as every prior archetype). The 10-hand tier was intended to approximate the real observed `moushun chen` profile (10 hands, 14 animals, 3 land quadrants, Phase 3.5 forensics) — **not claimed to reproduce it exactly**, per the brief's own caution.

## Finding: A Hard Wall at ~10 Hands, Not a Gradual Ceiling

Every attempted configuration at `n_hands >= 11` — 3 distinct configurations, varying land/animal purchase delay from day 0 to day 20 and crop mix (WHEAT-only, WHEAT+STRAWBERRY) — **went bankrupt** ($0-2,301 final money) before production revenue could sustain the daily re-hire cost (hands reset every day, a documented mechanic, so 11+ hands must be re-paid for every single day of the remaining season). This is not a tuning failure to iterate past — it's a structural property of the fibonacci hiring-cost curve combined with a $3,000 starting bank: **the existing archetype-building toolchain cannot produce a viable opponent above ~10 hands.**

This directly bears on H3, but not in the form the hypothesis anticipated: rather than a smooth "diminishing returns" curve, there is a **hard survivability wall** in the synthetic test environment itself, well below where real opponents (moushun chen: 10 hands + 14 animals + 3 land, won by $48,162) are demonstrably operating successfully.

## Response Frontier (from Stage B's actual data — nothing invented)

| Opponent scale | Our result (B0, fixed response) | Opponent's result | Does matching/exceeding scale (B1-B5) help? |
|---|---|---|---|
| scaler_5 (5 hands) | $46,121 mean, WIN | $10,753-14,479 | NO — underperforms B0 |
| scaler_7 (7 hands) | $47,857 mean, WIN | $18,255-22,397 | NO — underperforms B0 |
| scaler_10 (10 hands, closest to moushun chen's labor count) | $44,171 mean, WIN | $0-25,334 | NO — underperforms B0, even though B1-B5 commit MORE hands than B0's fixed 5 |
| heavy_scaler (Phase 3.5's own archetype) | $40,464 mean, WIN | $17,990-23,828 | NO — underperforms B0 |

**No data point in this frontier shows us actually losing to a synthetic opponent** — every synthetic archetype this project can currently build (achievable up to ~10 hands) loses to our own unmodified control, let alone our scaling response. This means Stage C could not measure "does matching scale prevent a loss," because no synthetic loss scenario could be constructed. The real losses (moushun chen, duckypants, Ben Wilson — Phase 3.5 forensics) remain the only evidence that a scaling opponent can actually beat us, and none of them can currently be reproduced as a controlled, repeatable test case.

## Interpretation

The ceiling finding, combined with Stage B's negative result (matching scale doesn't help even when tested) and Stage D's finding (below — a real large loss traced to selling-timing, not resource count), converges on a single, coherent hypothesis for Phase 3.7: **real opponents' competitive advantage may come substantially from EXECUTION EFFICIENCY (capital timing, selling discipline) rather than from raw resource accumulation alone** — which would mean further tuning of the labor/animal response magnitude, in isolation, is not the highest-value next step.

## Decision

H3 is **PARTIALLY SUPPORTED**: a real ceiling exists, but it is a synthetic-testing-tool limitation (bankruptcy above ~10 hands) more than a proven in-game economic ceiling. "Does matching scale help" is answered **NO** within the achievable range, based on real experimental data (Stage B). Whether it would help beyond that range is **UNKNOWN** — the tools to test it do not currently exist.
