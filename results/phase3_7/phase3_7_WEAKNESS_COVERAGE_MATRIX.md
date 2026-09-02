# Phase 3.7 Final Weakness Coverage Matrix

| Weakness | Severity | Frequency (updated) | C Detector | C Response | Full Causal Chain | Status |
|---|---|---|---|---|---|---|
| **F-001** scaling, response insufficient | CRITICAL | 6/9 firing episodes still lost | No | No | Reframed (animals-specific), not re-tested | NOT SOLVED |
| **F-002** scaling, within benefit range | HIGH | Unchanged, no new B evidence | No | No | N/A | UNKNOWN |
| **F-003** market exit timing | MEDIUM-HIGH | **1/13** (corrected down from 2) | No | No | Mechanism only, no response | NOT SOLVED |
| **F-004** low-footprint opponent | LOW | 0/13 B | No | No | N/A | UNKNOWN |
| **NEW-F-005** death spiral | **CRITICAL** (worst outcome) | 1/13 | No | Attempted, never fires | Mechanism class resolved, no lever found | NOT SOLVED |
| **NEW-F-006** land+animal-heavy | ~~HIGH~~ → reclassified | — | N/A | N/A | Land hypothesis REFUTED | **NOT A WEAKNESS** (folded into F-001) |

## Totals

Fully solved: **0**. Partially solved: **0**. Not solved: **3** (F-001, F-003, NEW-F-005). Unknown: **2** (F-002, F-004). Reclassified as not-a-weakness: **1** (NEW-F-006).

## No Weakness Marked SOLVED Merely Because Code Exists

F-005's countermeasure exists in code (`agents/phase3_7/f005_liquidity_guard.py`) but is honestly marked NOT SOLVED because it never fires under realistic conditions — the causal chain never gets past step 1 (detection doesn't even trigger). No weakness in this matrix reaches "SOLVED" status this phase.
