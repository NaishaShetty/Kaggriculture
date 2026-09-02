# Phase 3.7-A: Live Submission B Evidence Update

`COMPETITION RESULTS/SUBMISSION B` was recursively rescanned: **39 files (26 JSON, 13 video)** — identical to the count found in the prior Phase 3.6 pre-submission gate audit. **No new episodes appeared this session.** The baseline (13 games, 4 wins, 9 losses, 30.8% win rate) is therefore unchanged from `results/phase3_6/phase3_6_B_LIVE_UPDATED_BASELINE.md` — see that file for the full per-episode table.

## What Does B Do Correctly in Its Real Wins? (New Analysis)

Comparing all 4 real wins against the 9 real losses reveals a clean, previously-unexamined distinction:

- **3 of 4 wins had the scaling response actively firing** (cheesama, Thivvin Raj, TinkerBotics) — the response is not merely inert in winning games, it is doing real work.
- In every one of those 3 winning cases, the **opponent's animal count stayed low** (0, 6, 0) even when hands were high (10, 7, 10 respectively).
- The 4th win (nbarlow) never triggered the response — the opponent stayed low-footprint throughout (0 hands, 3 animals, 1 land) and no response was needed.
- By contrast, in the 6 losses where the response fired, the opponent's animal count was high in 5 of 6 (8, 14, 14, 16, 10) — only Safin (animals=3) breaks the pattern, and Safin was also the smallest-margin loss of the six.

**Conclusion: B's existing fixed response succeeds specifically against labor-heavy-but-not-animal-heavy opponents (its hands target of 5 is well-calibrated even against 10-11 real hands), and fails specifically when opponent animals exceed roughly 8** — a materially sharper diagnosis than Phase 3.6's original "response magnitude is insufficient" finding. Full detail and the complete comparison table: `phase3_7_F_F001_results.json`.
