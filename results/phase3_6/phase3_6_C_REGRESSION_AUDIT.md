# Phase 3.6 Regression Audit (Pre-Submission-C Gate)

## Test 1: Does C Improve the Weaknesses?

Reusing Phase 3.6's own paired same-seed experiment data (`phase3_6_B_scaling_results.json` — development seeds n=3, validation re-check n=4, against `scaler_5`, `scaler_7`, `scaler_10`, `heavy_scaler`): **no.** All 5 candidates (B1-B5) had lower mean final money than the existing fixed response (B0) in every single tested cell, confirmed on two independent seed sets. No new experiments were re-run this gate (none needed — the conclusion was already unambiguous and the new B evidence, analyzed above, does not touch this question; it only expanded the evidence for WHICH weaknesses need addressing).

Additionally, this gate's new evidence reveals that **even the existing B0 response — let alone any C candidate — does not cover 2 of the 4 newly-refined/newly-discovered weaknesses at all**: NEW-F-005 (death spiral) has no detector or response of any kind touching it, and NEW-F-006 (land+animal-heavy) is only partially covered (land is never in any candidate's response space, C included). **None of the Phase 3.6 candidates improve coverage of these two weaknesses beyond what B0 already does (nothing).**

## Test 2: Does C Preserve B's Wins?

Checked directly: the 5 archetypes/scenarios where B0 already wins comfortably (scaler_5, scaler_7, scaler_10, heavy_scaler, and by extension the 6 non-scaling Phase 3 archetypes which the response never touches for any candidate) all remain wins under every C candidate too — the difference is only in MARGIN (all C candidates win by smaller margins than B0, never by losing an otherwise-winning game in this synthetic test set). **No synthetic case was found where a C candidate turns a B0 win into a loss.** This has not been verified against the *real* Submission B win episodes (cheesama, Thivvin Raj, TinkerBotics, nbarlow) — those real replays cannot be re-played against a different agent (no counterfactual re-simulation of a real human opponent's actual decisions is possible), so this remains **UNKNOWN for the real wins specifically**, consistent with the project's standing rule against presenting a counterfactual as proof.

## Regressions Identified

**None found in the tested synthetic scenarios** (no B0 win becomes a C loss). However, this is a narrow finding: the synthetic archetypes tested cover only labor/animal scaling, not land, not selling-timing, and not the 4 real winning opponents' actual behaviors. The absence of an observed regression is not strong evidence of a general absence of regressions — it reflects a genuine but limited experimental footprint.

## Conclusion

**Test 1 FAILS** (no C candidate improves any weakness — not even the ones B0 already partially handles, and none touch the 2 newly discovered weaknesses at all). **Test 2 is inconclusive-but-not-failing** (no regression observed in the limited scenarios that could be tested). Since Test 1 alone is a hard requirement for promotion and it fails unambiguously, the regression-preservation result (Test 2) does not change the outcome.
