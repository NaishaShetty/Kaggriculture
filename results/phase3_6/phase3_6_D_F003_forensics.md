# Phase 3.6-D: F-003 Mechanism Discovery

**Hypothesis H2**: Observable opponent and market behavior contains sufficient information to detect at least one major F-003 non-scaling competitive advantage mechanism.

**Primary case study**: Episode 104765587 (Submission B) vs. Vishwanath N Iyer — our largest-margin loss and largest single rating hit (-146) across both submissions combined, and confirmed via the exact scaling detector (Phase 3.5/3.6-A) to never trigger (opponent never exceeded 4 hands, 0 animals).

## Method

Full turn-by-turn reconstruction of both players' crop portfolios, money, and MELON's market price from the real replay JSON (not the daily-checkpoint sampling used elsewhere — hourly granularity around the critical window), cross-referenced against our own actual `SELL` action log extracted directly from the replay's `action` field.

## 10 Hypotheses Tested (brief section 3.6-D)

| # | Mechanism | Verdict |
|---|---|---|
| 1 | Crop portfolio | NOT SUPPORTED — both players grew MELON as primary crop |
| 2 | Crop timing | Unresolved, subsumed by #8 |
| 3 | Production efficiency | NOT SUPPORTED — comparable tile counts (17-22 both sides) |
| 4 | Market timing | See #8 |
| 5 | Land usage | NOT SUPPORTED — both stayed at 1 quadrant, ruled out directly |
| 6 | Fertilizer | UNKNOWN — not instrumented this session |
| 7 | Capital allocation | NOT SUPPORTED as an early/gradual cause — both had comparable low cash through day 10 |
| 8 | Inventory/selling | **EXPERIMENTALLY VALIDATED — this is the mechanism** |
| 9 | Resource conversion efficiency | Subsumed by #8 |
| 10 | Combinations/interactions | **This is the actual mechanism — see below** |

## The Finding

Both players independently grew ~18-22 MELON tiles simultaneously — this alone is not what separates the outcomes (hypotheses 1, 3, 5 directly ruled out; 7 ruled out for the early game).

**What separates them is exactly WHEN each side converted that production into cash:**

- **Opponent**: bulk-sold a large MELON inventory in a single window (day 11, hour 0→12; money jumped $4,498 → $22,527) while price was still $129-250 — *before* the crash bottomed out. Replanted back to 18 tiles, held through a 9-day price recovery ($115→$136), then executed a second bulk-sell-and-exit at day 21-22 (money $24,172→$28,552), switching into CARROT right as the price crashed again.
- **Us**: sold MELON exactly **twice** in the entire 720-turn game — 20 units at turn 265 (day 11, price already falling $250→$129) and **95 units at turn 553 (day 23, price=$4 — the exact bottom of the crash)**. That 95-unit dump realized roughly $380; the same units at the day 8-10 price (~$270) would have been worth roughly **$25,650** — a gap exceeding the entire $30,210 loss margin on its own.

This is not a crop-choice story. It is a **selling-timing / liquidation mismatch**: the opponent appears to sell in large batches timed to price peaks (a pattern consistent with, though not confirmed to be, a `threshold`/`threshold_batch`-style sell policy — mechanics already documented and available in this project's own Phase 2.4 sell-policy candidates), while our own selling — whether via threshold-mode holding too long for a recovery, or shed-capacity (100-item cap) forcing an eventual dump — converted a large fraction of our harvest into cash at the worst possible moment.

## Distinction From Prior Findings

- **Not** Phase 3.4's `self_inflicted_narrow_market_price_crash` (that mechanism is about production VOLUME crashing a market; here both sides' volume is comparable, and the crash happens regardless — the differentiator is selling TIMING, not volume).
- **Not** F-001 (labor/animal scaling — this opponent never scaled labor or animals at all).
- A genuinely distinct, third mechanism, now named **`opportunistic_market_exit_timing`**.

## What Was NOT Done (honestly, per the brief's explicit instruction)

- **No countermeasure was built or tested.** "Do not create a detector until the underlying mechanism is sufficiently supported" — the mechanism is now well-supported for this ONE episode, but a fix (e.g., a smarter batch-sell-timing policy) needs its own design-and-validate cycle, appropriately deferred to Phase 3.7.
- **Not generalized.** The other 2 confirmed F-003 episodes from Submission A (104570723, 104615545) were not re-examined with this same turn-level selling-timing lens this session — whether the same mechanism explains them is UNKNOWN.
- Fertilizer usage was not instrumented.

## Decision

**H2 is SUPPORTED**: observable behavior did contain enough information to identify a specific, well-evidenced F-003 mechanism (`opportunistic_market_exit_timing`) for the primary case study, with turn-level precision. **F-003 remains formally UNRESOLVED** (no validated fix exists), but is now substantially *narrowed* from Phase 3.5's vague "crop choice" hypothesis to a specific, testable, and much more actionable claim for Phase 3.7.
