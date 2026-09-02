# Phase 3.6 Final Report — Adaptive Scaling Response & F-003 Investigation

## 1. Executive Summary

Phase 3.6 tested whether an adaptive, threat-aware scaling response could outperform Submission B's fixed response (H1), whether a major F-003 non-scaling mechanism could be isolated (H2), and whether a competitive scaling ceiling exists (H3). **H1 is REJECTED** — all 5 adaptive candidates underperformed the existing fixed response in every tested scenario, confirmed on two independent seed sets. **H2 is SUPPORTED** — a specific, precisely-evidenced mechanism (`opportunistic_market_exit_timing`, a selling-timing/liquidation mismatch) was identified from a real Submission B loss, though not yet generalized or fixed. **H3 is partially supported** — a hard synthetic-archetype bankruptcy wall exists at ~10 hands, below where real opponents (moushun chen) demonstrably operate. **No candidate met the promotion bar. Submission B remains the champion. No Submission C was created.** This is reported as the honest, evidence-backed outcome the phase's own instructions explicitly permit and require when the evidence doesn't support promotion.

## 2. A+B Evidence Baseline

Consolidated in `phase3_6_A_live_evidence.md`/`.json` from existing Phase 3.5 forensic artifacts (no new data collection): 17 real losses across Submissions A and B, classified F-001 (8, 47% — scaling, response insufficient/borderline), F-002 (4, 24% — scaling, response likely sufficient), F-003 (3, 18% — non-scaling, unaddressed), F-004 (1, 6% — unclassified, low confidence).

## 3. F-001 Findings

Direct, real-world confirmation (Phase 3.5/3.6-A) that Submission B's scaling response fires correctly in live play but its FIXED magnitude is insufficient against the largest real opponents (moushun chen: 10 hands, 14 animals, 3 land, won by $48,162 despite the response firing at day 5).

## 4. F-003 Findings

Precisely identified for the primary case study (episode 104765587): the opponent bulk-sold MELON in two large, price-timed batches; we sold MELON exactly twice across the entire game, the larger dump (95 units) landing at $4/unit — the exact bottom of a crash — worth roughly $25,650 less than the same units sold at the day 8-10 price. This single mistimed sell accounts for most of the $30,210 loss margin. Named `opportunistic_market_exit_timing`. **Not generalized to the other 2 F-003 episodes. No countermeasure built.**

## 5. Scaling-Response Experiments (Stage B)

5 candidates (B1 absolute-proportional, B2 relative-gap, B3 growth-rate-aware, B4 budget-constrained, B5 hybrid) tested against 4 archetypes (scaler_5/7/10, heavy_scaler), development seeds (n=3) + validation re-check (n=4) for the closest challenger. **B0 (the existing fixed response) had the highest mean final money in every single cell tested, with no exception.** Full data: `phase3_6_B_scaling_results.json`.

## 6. Competitive Scaling Frontier (Stage C)

No synthetic archetype achievable with existing tools (`make_agent_23`) ever beat our own control — every configuration attempted at 11+ hands went bankrupt regardless of purchase-timing or crop mix. The frontier measured (Stage B's real data) shows: matching or exceeding opponent scale did NOT help in any tested case — B0's smaller, fixed commitment outperformed every proportional/adaptive attempt to match the opponent more closely.

## 7. Integrated Policy (Stage E)

None assembled — nothing from Stages B-D cleared the bar for integration. Submission B's existing architecture is retained unchanged.

## 8. Regression Results

**106/106** existing tests passing, unchanged from before Phase 3.6. No new production-path tests needed (no candidate reached production).

## 9. Held-Out Results

Deliberately not spent — no candidate cleared development+validation screening, so held-out seeds were not used to evaluate a candidate already shown to lose (per the brief's own "do not promote on development seeds alone" logic, inverted: there's no basis to spend held-out seeds validating a loser either).

## 10. Submission C Package Validation

Not applicable — no Submission C was built. Submission B remains the current, valid, submittable package (`kaggriculture_phase3_5_competitive_v2_submission_B.tar.gz`, unchanged).

## 11. Known Limitations

- The adaptive-response underperformance (Stage B) has two candidate explanations (configuration churn from daily re-evaluation; possible diminishing/negative marginal labor value) — neither isolated as the definitive cause.
- Synthetic archetypes cap out at ~10 hands (bankruptcy above that) — the actual competitive ceiling against opponents like moushun chen (10 hands + 14 animals + 3 land, viable and winning) cannot currently be tested in a controlled, repeatable way.
- F-003's mechanism was validated for exactly 1 episode; generalization is unknown.
- No Phase 3.6 experiment ever produced a synthetic scenario where WE lost — all conclusions about "does a stronger response help" are drawn from margin/efficiency differences in scenarios we already win, not from loss-prevention evidence (the real loss-prevention question can currently only be answered by Submission A/B's actual live results, per the existing forensic audits).

## 12. Remaining Weaknesses

Unchanged from the Phase 3.5 audits, now with sharper evidence: F-001 (response magnitude insufficient against extreme real opponents — confirmed, no validated fix), F-003 (mechanism now well-understood for 1 case, no fix), F-004 (still low-confidence, unchanged).

## 13. Evidence Classification Summary

- **EXPERIMENTALLY VALIDATED**: B0 outperforms B1-B5 in every tested scenario (Stage B, 2 seed sets); the synthetic-archetype bankruptcy wall at n_hands≥11 (Stage C); the `opportunistic_market_exit_timing` mechanism for episode 104765587 (Stage D).
- **STRONG EMPIRICAL SIGNAL**: F-001's real-world confirmation (from Phase 3.5, reused here).
- **HYPOTHESIS**: configuration-churn and diminishing-marginal-labor-value explanations for B1-B5's underperformance; generalization of the F-003 mechanism beyond episode 104765587; real opponents' efficiency (not scale) being the true decisive factor.
- **UNKNOWN**: whether matching scale would help beyond the ~10-hand synthetic ceiling; fertilizer's role in F-003.

## 14. Exact Reasons for Rejecting Promotion

No candidate satisfies the brief's success condition (section 11): none "materially improves performance against validated scaling threats" (all 5 candidates measurably underperformed the existing response), and F-003 was narrowed but not resolved into a countermeasure. Per the brief's own explicit rule, this means: **do not force a promotion.**

## 15. Recommended Phase 3.7 Question

**Does execution efficiency (selling-timing discipline, specifically) matter more than raw resource-scaling response for closing the gap against both F-001 and F-003 opponents — and can a validated batch-sell-timing countermeasure be built and tested for the `opportunistic_market_exit_timing` mechanism identified this phase?** This reframes the Phase 3.6 question (was: response magnitude) around what the evidence now actually points to (was: raw scale; is now: timing/execution).

---

## SUBMISSION C STATUS: NOT CREATED

**Champion**: Submission B (unchanged).
**Reason**: No Phase 3.6 candidate met the evidence gate for promotion. H1 rejected (adaptive response underperforms fixed response in every test). H2 supported but no countermeasure built (F-003 mechanism identified, not fixed). This is the honest, evidence-required outcome — not a failure to execute the phase, but its correct conclusion given what the experiments showed.
