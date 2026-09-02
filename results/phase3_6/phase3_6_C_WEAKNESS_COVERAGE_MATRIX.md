# Phase 3.6 Weakness Coverage Matrix (Pre-Submission-C Gate)

"C" = the Phase 3.6 experimental candidate pool (`agents/phase3_6/response_policy_v2.py`, B1-B5). No Phase 3.6 candidate was ever promoted to production. This matrix evaluates that pool against the now-expanded 13-game Submission B evidence set (up from 4 at the time of the prior Phase 3.6 report).

| Weakness | A Freq | B Freq | Severity | C Detector | C Response | Behavior Change | Trajectory Effect | Validated | Status | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| **F-001** scaling, magnitude insufficient | 6/13 | 5/9 (was 2/3) | CRITICAL | Yes | Yes | Yes | Positive, insufficient | Real-world CONFIRMED insufficient; all 5 C candidates underperform B0 | PARTIALLY SOLVED (by B0 only) | HIGH |
| **F-002** scaling, margin in benefit range | 4/13 | 0/9 | HIGH | Yes | Yes | Yes | Plausible, unconfirmed | HYPOTHESIS, unchanged | UNKNOWN | LOW-MEDIUM |
| **F-003** selling-timing mismatch | 2/13 | 2/9 (confirmed recurring: Vishwanath N Iyer + kyunyoung) | MEDIUM-HIGH | No | No | No | N/A | Mechanism validated for 1 episode only | NOT SOLVED | HIGH (mechanism) |
| **F-004** low-footprint efficient opponent | 1/13 | 0/9 | LOW | No | No | No | N/A | No | UNKNOWN | LOW |
| **NEW-F-005** terminal cash-zero death spiral | 0/13 | 1/9 | **CRITICAL** (worst-ever outcome: $0) | No | No | No | N/A | No — root cause not diagnosed | **NEW** | HIGH (observation) / LOW (cause) |
| **NEW-F-006** land+animal-heavy, hands modest | 0/13 | 1/9 | HIGH | Partial (triggers on animals only) | Partial (never touches land) | Yes, insufficient | Insufficient | Real-world observed, not isolated | NOT SOLVED | MEDIUM |

## Totals

- Fully solved: **0**
- Partially solved: **1** (F-001, by the existing B0 fixed response — not by any Phase 3.6 candidate)
- Not solved: **2** (F-003, NEW-F-006)
- New: **1** (NEW-F-005)
- Unknown: **2** (F-002, F-004)

## The Critical Standard Was Applied Throughout

No weakness above is marked SOLVED merely because a detector or response function exists in the codebase. F-001 is marked PARTIALLY SOLVED only because the causal chain (detection → response fires → behavior changes → trajectory improves) is directly confirmed in real play for the *existing* fixed response (B0) — but the FULL chain through to "prevents the loss" fails for the largest opponents, so it is not marked SOLVED. NEW-F-006 shows detection and response firing but stops at "trajectory effect: insufficient" — not solved. F-003 and NEW-F-005 have no detector or response at all, so they cannot be anything but NOT SOLVED / NEW.
