# Phase 3.7-E: F-003 Market Exit Timing

## Correction to the Prior Audit

The Phase 3.6 pre-submission gate report classified `kyunyoung` (104775100) as a second F-003 instance based only on "detector did not trigger." Direct examination of kyunyoung's actual SELL action log this session shows this was premature: our sells realized $249, $236, and $108/unit for MELON, plus repeated WOOL sells around $221-223 — reasonably healthy, non-crash prices, not the same mistimed-dump pattern found in Vishwanath N Iyer. **Reclassified: kyunyoung is NOT a confirmed F-003 instance.** Its small loss (-$2,987) has an unknown mechanism, likely ordinary competitive variance.

**Updated F-003 frequency: 1/13 B losses** (corrected down from the previously reported 2/13) — confirmed for exactly Vishwanath N Iyer (104765587).

## Countermeasure: Not Attempted This Session

Given F-003's real-evidence base did not grow this session, and given the substantial remaining required scope (F-001 reassessment, integration decision, B-vs-C validation, packaging/reporting) within this phase's effort budget, designing and validating a new selling-discipline policy was deliberately deferred rather than attempted without adequate rigor. This is an honest scope decision — no candidate was built and rejected; none was attempted.

## Status

F-003 remains **NOT SOLVED**. Mechanism precisely known for 1 episode. Recommended as the top Phase 3.8 countermeasure-design priority: unlike F-005 (no viable architectural lever found) and F-006 (hypothesis refuted by controlled ablation), F-003 has both a precisely diagnosed mechanism and a plausible, not-yet-attempted countermeasure design space (trend-aware partial liquidation, inventory-age-aware selling, or end-of-season liquidation discipline).
