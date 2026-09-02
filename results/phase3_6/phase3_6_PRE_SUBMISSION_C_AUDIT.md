============================================================
SUBMISSION C PRE-FLIGHT VERDICT
============================================================

Submission B games reviewed: 13
Submission B wins: 4
Submission B losses: 9
Submission B win rate: 30.8%

A+B real losses reviewed: 22 (13 from Submission A, 9 from Submission B)
Known weaknesses: 6 (F-001, F-002, F-003, F-004, NEW-F-005, NEW-F-006)

Weaknesses fully solved by C: 0
Weaknesses partially solved by C: 0
Weaknesses unresolved (by C): 6
New B weaknesses (this gate): 2 (NEW-F-005, NEW-F-006)
C regressions: 0 found (in limited synthetic testing; real winning episodes could not be counterfactually verified)

FINAL DECISION:

**DO NOT PROMOTE C**

============================================================

## 1. What B Taught Us

Submission B's scaling-response countermeasure (Phase 3.5) works exactly as engineered: the detector fires on real opponent data, and the response measurably changes our own hands/animals commitment in real competitive play (directly confirmed, not inferred, across multiple episodes this gate). But engineering correctness is not competitive sufficiency — in 5 of 9 real B losses, the full detection→response→behavior-change chain completes and the loss still occurs, because the response's magnitude is fixed regardless of the opponent's actual scale.

## 2. What New B Games Revealed

The Submission B sample grew from 4 to 13 completed episodes this gate (9 new). This is not a minor update — it roughly triples the real evidence base and surfaced:
- **3 real wins with the response firing** against high-labor opponents (cheesama, Thivvin Raj, TinkerBotics) — new evidence that the existing fixed response CAN work, specifically against labor-heavy-but-not-animal/land-heavy opponents.
- **F-003 confirmed recurring** (kyunyoung joins Vishwanath N Iyer) rather than a single anomaly.
- **Two entirely new failure mechanisms**, detailed below (Sections 6-7 area / weakness matrix): a catastrophic zero-recovery death spiral, and a land-driven advantage the current detector cannot see at all.

## 3. A Weakness Coverage Audit

See `phase3_6_C_WEAKNESS_COVERAGE_MATRIX.md`/`.json` for the full table. Summary: 0 weaknesses fully solved, 1 partially solved (F-001, by the EXISTING B0 response, not by any Phase 3.6 candidate), 2 not solved (F-003, NEW-F-006), 1 new (NEW-F-005), 2 unknown (F-002, F-004).

## 4. F-001 Status

**PARTIALLY ADDRESSED BY B0 (production), NOT IMPROVED BY ANY C CANDIDATE.** Now confirmed in 5/9 real B losses (up from 2/3), with the response firing and failing to prevent the loss in 4 of those 5 (the 5th, Safin, was a near-miss at -$1,617). All 5 Phase 3.6 adaptive candidates (B1-B5), purpose-built to improve this exact weakness, underperformed the status quo in every synthetic test on two independent seed sets. **This is the project's dominant, best-evidenced, and still entirely unsolved weakness.**

## 5. F-003 Status

**NOT SOLVED. Confirmed recurring** (2 real instances now: Vishwanath N Iyer -$30,210/-146 rating, and kyunyoung -$2,987). Mechanism (`opportunistic_market_exit_timing` — selling-timing/liquidation mismatch) precisely identified for the first case via turn-level replay reconstruction in Phase 3.6; the second instance has not been analyzed to the same depth. No detector, no response, no countermeasure exists.

## 6. F-004 Status

**UNCHANGED, still UNKNOWN.** No new matching instance found in the expanded B sample. Remains a single video-only case (Von Lan, Submission A) — correctly not over-prioritized, per standing instruction.

## 7. New Weaknesses

- **NEW-F-005 (terminal cash-zero death spiral)**: episode 104775830 (Arum Puri) — our cash and ALL crop tiles hit exactly $0 by day 6-10 and never recover for the remaining 20+ days, ending at $0 — the single worst outcome across all 35 real episodes reviewed across this entire project (A+B combined). The opponent showed almost no scaling signature (2 hands, 0 animals, gradual land growth to 4 quadrants) and started POORER than us on day 0. Root cause **not diagnosed** this session — flagged as the highest-priority Phase 3.7 investigation.
- **NEW-F-006 (land+animal-heavy, hands-modest)**: episode 104772378 (Achille Gohin) — opponent reached only 5 hands (barely above threshold) but 10 animals and full 4-quadrant land expansion; the detector triggers (on animals) and the response fires, but never touches land at all, and the loss (-$43,127) was not prevented. A structural gap, not a magnitude-tuning gap — no candidate this phase has land in its response space at all.

## 8. B vs C Experimental Results

Reused from Phase 3.6's own Stage B/C matrix (not re-run — the conclusion was already unambiguous and this gate's new evidence doesn't touch it): **B0 (the existing fixed response) had higher mean final money than every one of B1-B5 in every single tested (candidate, opponent) cell**, confirmed on development (n=3) and validation (n=4) seeds. Full data: `results/phase3_6/phase3_6_B_scaling_results.json`.

## 9. Regression Analysis

No case was found, in the tested synthetic scenarios, where a C candidate turns a B0 win into a loss. This is a genuine but narrow finding — it does not cover land, selling-timing, or the actual real opponents Submission B has beaten (those cannot be counterfactually re-simulated). See `phase3_6_C_REGRESSION_AUDIT.md`.

## 10. Remaining Risks

1. F-001 — dominant, unsolved, no validated fix even attempted-and-failed designs improved on it.
2. F-003 — confirmed recurring, no fix attempted.
3. NEW-F-005 — worst-severity outcome category found in the project, completely undiagnosed.
4. NEW-F-006 — structural blind spot (land) in the entire detector/response design, not just this phase's candidates.
5. The real winning episodes (4/13 in the current B sample) cannot be verified as preserved under any candidate — only inferred from synthetic non-regression evidence.

## 11. Submission C Readiness

**NOT READY.** No candidate exists that clears the promotion bar. This is not a packaging or engineering failure — it is the correct, evidence-required conclusion given what every experiment this phase and this gate produced.

## 12. Exact Recommendation

**Keep Submission B as the champion.** Do not submit any Phase 3.6 candidate. Prioritize, for Phase 3.7: (1) root-causing NEW-F-005's death spiral (highest severity, currently zero understanding of cause), (2) determining whether land belongs in the threat-detection/response model at all (NEW-F-006), and (3) generalizing the F-003 `opportunistic_market_exit_timing` mechanism to a testable, validatable countermeasure design — in that priority order, since severity (worst-outcome-first) should drive sequencing over frequency alone.
