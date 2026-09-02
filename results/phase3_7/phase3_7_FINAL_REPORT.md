============================================================
PHASE 3.7 FINAL VERDICT
============================================================

Submission B games reviewed: 13
Submission B wins: 4
Submission B losses: 9
Submission B win rate: 30.8%

A+B real losses reviewed: 22
Known weaknesses: 6 (F-001, F-002, F-003, F-004, NEW-F-005, NEW-F-006)

F-005 status: NOT SOLVED (root cause substantially characterized; no viable countermeasure lever found)
F-006 status: NOT A WEAKNESS (hypothesis refuted by controlled ablation; folded into F-001)
F-003 status: NOT SOLVED (evidence corrected DOWN to 1 confirmed instance; no countermeasure attempted)
F-001 status: NOT SOLVED (reframed around opponent animal count via new real-data evidence; no new candidate tested)

New weaknesses: 0 confirmed net-new (NEW-F-005/006 were carried in from Phase 3.6; F-006 reclassified out this phase)
B vs C result: N/A -- no C candidate was produced
C regressions: N/A

FINAL DECISION:

**SUBMISSION C NOT EARNED**

CURRENT CHAMPION: **Submission B**

============================================================

## 1. What Was Learned From New B Games

No new games appeared this session — `COMPETITION RESULTS/SUBMISSION B` still holds exactly 13 completed episodes, confirmed by recursive rescan (39 files, unchanged count). The value this phase added came from re-examining the existing 13 more deeply, not from new data volume.

## 2. F-005 Root Cause

Substantially characterized via same-seed replay ablation: the **initial** cash-trough-to-hands-zero collapse is deterministic and seed-driven, reproducing identically against a totally passive synthetic opponent — not opponent-caused. The **actual failure is recovery**: crops decay to weeds in both real and synthetic runs, but recovery depends on whether *any* of the ~22 unwatered tiles survive by chance long enough to reach harvest. In the real game, zero did; in a same-seed synthetic replay, a few did, funding a $5,174 sale that bootstrapped full recovery. The precise trigger for *this specific* zero-survival outcome remains unresolved — classified honestly as `F-005 ROOT CAUSE OF THE SPECIFIC DIVERGENCE: UNRESOLVED`, per the brief's own standard.

## 3. F-005 Countermeasure

One candidate (early cash-trajectory guard, reducing crop commitment if cash drops early) was designed and tested. It **never triggered** under realistic conditions — cash doesn't look distinguishably critical until *after* the crop commitment is already locked in. Rejected as structurally non-viable, not as a tuning failure. **No F-005 fix exists.**

## 4. F-006 Land Investigation

A controlled ablation (land=1 vs land=4, hands/animals held constant, 3 seeds) found land **independently hurts**, not helps, an opponent's outcome — consistent with Phase 2.3's original finding. **The land-threat hypothesis is refuted.** NEW-F-006 is reclassified as an animals-driven instance of F-001, not a distinct mechanism.

## 5. F-003 Market Timing

A prior classification (kyunyoung as a second F-003 instance) was checked against its actual sell log and found **incorrect** — its selling was disciplined, not mistimed. F-003's confirmed frequency is corrected **down** to 1/13 (Vishwanath N Iyer only). No countermeasure was attempted this session, given remaining effort budget — deliberately deferred, not attempted-and-failed.

## 6. F-001 Reassessment

New evidence across all 9 real episodes where the response fired shows a clean signal: **opponent animal count**, not hands, discriminates wins (mean 2.0) from losses (mean 9.2) — hands shows no separation at all (9.0 vs 9.0). This reframes F-001 as an animals-specific under-calibration, not a generic labor-scale problem — genuinely new evidence, distinct from what Phase 3.6's 5 rejected candidates tested. **Not built or validated into a new candidate this session** — reported as the top Phase 3.8 hypothesis.

## 7. Integrated C

None assembled — Stages B-F produced zero validated components. Integrating an unfixed death spiral, a refuted land hypothesis, an unattempted selling policy, and an untested reframing would violate the brief's explicit prohibition on integrating unresolved hypotheses.

## 8. B vs C Results

Not applicable — no C candidate exists.

## 9. B Wins Preserved?

Yes, trivially — Submission B was not modified anywhere this phase.

## 10. Weakness Coverage

0 fully solved, 0 partially solved, 3 not solved (F-001, F-003, NEW-F-005), 2 unknown (F-002, F-004), 1 reclassified as not-a-weakness (NEW-F-006). Full matrix: `phase3_7_WEAKNESS_COVERAGE_MATRIX.md`/`.json`.

## 11. Remaining Risks

F-005 (worst-severity, currently no architectural fix available within the frozen-Planner-v1/frozen-tactical-layer constraint); F-003 (largest confirmed loss+rating-hit, mechanism known, fix not attempted); F-001 (now sharper diagnosis, still no validated fix).

## 12. Submission C Validation

Not applicable — no package was built. See `phase3_7_SUBMISSION_C_VALIDATION.md`.

## 13. Exact Archive Path

**None created this phase.** The current, valid, submittable package remains `C:\Kaggriculture\kaggriculture_phase3_5_competitive_v2_submission_B.tar.gz` (Phase 3.5, unchanged).

## 14. Git Commit/Push Commands

See the dedicated section below.

## 15. Recommended Phase 3.8 Research Question

**Does an animals-specific response adjustment (raising only the animal-purchase target, leaving the already-well-calibrated hands target at its current fixed value) close more of the F-001 gap than the hands+animals-together proportional designs Phase 3.6 already rejected?** This is the single most actionable, best-evidenced open question from this phase — grounded in a clean, real-data pattern (9 real episodes, animals cleanly separating wins from losses while hands does not) rather than another synthetic-archetype-only hypothesis.

Secondary priorities: (2) whether F-005 is fixable at all without permission to touch frozen Planner v1/tactical-layer code, or whether it must simply be accepted as an irreducible tail risk; (3) designing and testing the F-003 selling-discipline countermeasure that was diagnosed but not attempted this phase.

============================================================
GITHUB COMMIT / PUSH COMMANDS
============================================================

See the final section of this response for exact, verified commands reflecting only the files this phase actually created.
