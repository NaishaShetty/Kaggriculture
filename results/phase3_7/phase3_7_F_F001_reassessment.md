# Phase 3.7-F: F-001 Reassessment

## New Evidence From the Expanded B Sample

Comparing all 9 real episodes where the scaling response fired (3 wins, 6 losses):

| | Mean opponent hands | Mean opponent animals |
|---|---|---|
| **Wins** (cheesama, Thivvin Raj, TinkerBotics) | 9.0 | **2.0** |
| **Losses** (zixma13, moushun chen, deleted-account, iBooNDK, Achille Gohin, Safin) | 9.0 | **9.2** |

**Hands shows essentially no separation between wins and losses (9.0 vs 9.0) — the existing fixed hands target (5) appears reasonably well-calibrated even against 10-11-hand real opponents. Animals shows a clean, large separation (2.0 vs 9.2).** The one exception, Safin (animals=3, still a loss), produced the *smallest* margin of the 6 losses (-$1,617, a near-miss) — consistent with, not contradicting, the pattern.

## Reframing

F-001 is better understood as a threat-estimation problem specifically around **animal commitment**, not a generic "match total labor scale" problem. This is a genuinely different framing from what Phase 3.6's 5 candidates (B1-B5) tested — those scaled hands *and* animals together proportionally, and all failed. Whether an animals-specific adjustment (leaving the hands target as-is) performs differently is **untested**.

## NEW-F-006 Folds In Cleanly

Achille Gohin (5 hands — the *lowest* in the loss sample, 10 animals, 4 land) fits this reframing exactly once land is set aside (Stage D showed land is not independently causal): a moderate-hands, high-animals opponent, consistent with the animals-driven pattern.

## Why No New Candidate Was Built This Session

The brief explicitly cautions against retrying the same 5 adaptive approaches with cosmetic changes, and requires new evidence to justify a genuinely different approach. The animals-specific signal is new, real-data-grounded evidence that arguably supports a genuinely different design (adjust animals response magnitude/threshold independently of hands) — but building and properly validating such a candidate (development → validation → held-out, with side-effect checks) was not completed within this session's remaining effort budget after Stages B-E. This is reported honestly as a **well-evidenced, promising, but UNTESTED hypothesis for Phase 3.8** — not a validated fix, and not claimed as one.

## Status

**F-001 remains OPEN.**
