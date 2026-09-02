# Phase 3.6 Promotion Decision (Pre-Submission-C Gate)

## Decision: **DO NOT PROMOTE C**

No Phase 3.6 candidate (B1-B5, `agents/phase3_6/response_policy_v2.py`) meets the promotion bar (brief section 16). Checked against every required condition:

| Condition | Met? | Evidence |
|---|---|---|
| C materially improves important weaknesses | **NO** | All 5 candidates underperform the existing B0 response in every tested scenario (Stage B/C, 2 seed sets) |
| C does not introduce unacceptable regressions | Partially / inconclusive | No regression found in tested synthetic scenarios, but real winning-episode behavior cannot be counterfactually verified |
| Existing frozen behavior remains protected | YES | Planner v1, Variant D, Phase 3.5's Competitive Agent V2 all confirmed byte-unchanged |
| Scaling adaptation is experimentally supported | **NO** | H1 rejected — adaptive magnitude responses consistently underperform the fixed response |
| F-003 status honestly represented | YES | Reported as NOT SOLVED, mechanism identified but no fix built, now confirmed recurring (2 real instances) |
| Held-out results support generalization | N/A | Held-out seeds deliberately not spent on a candidate that already failed development+validation screening |
| Package is reproducible | N/A | No package was built, since no candidate qualifies |
| No major newly discovered B weakness is ignored | YES — but NOT ADDRESSED | Two new weaknesses (NEW-F-005 death spiral, NEW-F-006 land-blind-spot) are documented in full, not ignored — but no candidate touches either one |

**The decisive failure is the first and fourth rows**: not one of the 5 designed responses beats the status quo on the exact axis they were built to improve, confirmed on independent seed sets. Promoting any of them would be a regression relative to Submission B's current, already-deployed fixed response.

## What This Pre-Submission Gate Adds Beyond the Prior Phase 3.6 Conclusion

The expanded 13-game Submission B sample (up from 4) **strengthens, not weakens**, the case against promotion:
1. F-001 is now confirmed in 5 real losses (not 2), with the response firing and still failing in all but one near-miss case.
2. Two entirely new, unaddressed failure modes were discovered (NEW-F-005, NEW-F-006) that no existing or candidate response touches at all — a land-blind-spot and a catastrophic zero-recovery death spiral.
3. F-003 is now confirmed RECURRING (2 real instances), not a single anomaly.

None of this new evidence points toward any Phase 3.6 candidate being ready — if anything, it reveals the candidates were solving too narrow a slice of the real problem even where they were designed to help.

## Submission B Remains Champion

`kaggriculture_phase3_5_competitive_v2_submission_B.tar.gz` remains the valid, current, submittable package. No new submission was built or should be built from this phase's work.

## Highest-Priority Next Experiment (Phase 3.7)

Two candidates, in order of severity:
1. **NEW-F-005 root-cause investigation**: why did episode 104775830 hit exactly $0 by day 6 and never recover for 24 straight days? This is the single worst outcome category found across all 35 real episodes reviewed to date (A: 18, B: 13, wins+losses combined) and its cause is currently completely undiagnosed.
2. **A land-aware threat signal**: NEW-F-006 shows the existing detector/response, built entirely around hands/animals, is structurally blind to land-driven opponent advantage. Whether land should join the detector's trigger conditions, or the response's action space, is untested.
