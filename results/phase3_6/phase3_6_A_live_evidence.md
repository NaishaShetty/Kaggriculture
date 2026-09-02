# Phase 3.6-A: Unified A+B Live Competitive Evidence

Consolidated from `results/phase3_5/` artifacts (Submission A/B forensic audits, counterfactual table, differential summary, live analysis, failure database) -- no new data collection, no production code touched.

**Total real losses across both submissions: 16** (13 from Submission A, 4 episodes from Submission B, 1 of which is a win).

| Sub | Episode | Opponent | Result | Margin | Rating Δ | Opp Hands | Opp Animals | Opp Land | Our Hands | Our Animals | Detector | Response | Mechanism | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 104567976 | Jatin Chawla | LOSS | -44129.0 | None | 12 | 19 | 4 | 2 | 2 | DEFINITELY YES | N/A -- Submission A predates the countermeasure | F-001 | MEDIUM (trigger fact is exact; benefit-transfer to this real opponent is extrapolated from a synthetic-archetype experiment) |
| A | 104569747 | Quantum | LOSS | -83397.0 | None | 12 | 15 | 3 | 2 | 2 | DEFINITELY YES | N/A -- Submission A predates the countermeasure | F-001 | MEDIUM (trigger fact is exact; benefit-transfer to this real opponent is extrapolated from a synthetic-archetype experiment) |
| A | 104570236 | all-coder | LOSS | -18555.0 | None | 7 | 20 | 1 | 2 | 2 | DEFINITELY YES | N/A -- Submission A predates the countermeasure | UNCLASSIFIED | MEDIUM (trigger fact is exact; benefit-transfer to this real opponent is extrapolated from a synthetic-archetype experiment) |
| A | 104570723 | nguyễn huệ anh | LOSS | -8154.0 | None | 0 | 0 | 2 | 2 | 1 | DEFINITELY NO (computed exactly from real replay data) | N/A -- Submission A predates the countermeasure | F-003 | HIGH (detector run against exact real observed opponent trajectory) |
| A | 104571150 | Deepesh Pankaj | LOSS | -14898.0 | None | 9 | 3 | 2 | 2 | 1 | DEFINITELY YES | N/A -- Submission A predates the countermeasure | F-002 | MEDIUM (trigger fact is exact; benefit-transfer to this real opponent is extrapolated from a synthetic-archetype experiment) |
| A | 104574962 | Ritesh-2006 | LOSS | -9851.0 | None | 0 | 4 | 1 | 2 | 2 | DEFINITELY YES | N/A -- Submission A predates the countermeasure | F-002 | MEDIUM (trigger fact is exact; benefit-transfer to this real opponent is extrapolated from a synthetic-archetype experiment) |
| A | 104575529 | Acteus | LOSS | -7251.0 | None | 0 | 1 | 2 | 2 | 2 | DEFINITELY YES | N/A -- Submission A predates the countermeasure | F-002 | MEDIUM (trigger fact is exact; benefit-transfer to this real opponent is extrapolated from a synthetic-archetype experiment) |
| A | 104597196 | zama | LOSS | -8836.0 | None | 6 | 0 | 3 | 2 | 1 | DEFINITELY YES | N/A -- Submission A predates the countermeasure | F-002 | MEDIUM (trigger fact is exact; benefit-transfer to this real opponent is extrapolated from a synthetic-archetype experiment) |
| A | 104615545 | explise | LOSS | -11863.0 | None | 2 | 0 | 2 | 2 | 1 | DEFINITELY NO (computed exactly from real replay data) | N/A -- Submission A predates the countermeasure | F-003 | HIGH (detector run against exact real observed opponent trajectory) |
| A | 104703432 | Phan Van Hieu  | LOSS | -21337.0 | None | 11 | 0 | 4 | 2 | 1 | DEFINITELY YES | N/A -- Submission A predates the countermeasure | UNCLASSIFIED | MEDIUM (trigger fact is exact; benefit-transfer to this real opponent is extrapolated from a synthetic-archetype experiment) |
| A | 104682607 | Von Lan (VonLan233) | LOSS | -855 | None | None | None | None | None | None | PROBABLY NO (no scaling behavior visually observed; opponent's footprint stays modest throughout the frames inspected) | N/A -- Submission A predates the countermeasure | F-004 | LOW-MEDIUM (video-only, 3 sampled frames per episode, no turn-by-turn data) |
| A | 104569297 | duckypants | LOSS | -66532 | None | None | None | None | None | None | PROBABLY YES (visual evidence consistent with the pattern; not computed exactly, no JSON available) | N/A -- Submission A predates the countermeasure | F-001 | LOW-MEDIUM (video-only, 3 sampled frames per episode, no turn-by-turn data) |
| A | 104567542 | Ben Wilson | LOSS | -61914 | None | None | None | None | None | None | PROBABLY YES (visual evidence consistent with the pattern; not computed exactly, no JSON available) | N/A -- Submission A predates the countermeasure | F-001 | LOW-MEDIUM (video-only, 3 sampled frames per episode, no turn-by-turn data) |
| B | 104765587 | Vishwanath N Iyer | LOSS | -30210.0 | -146 | 4 | 0 | 1 | 2 | 2 | NOT TRIGGERED | DID NOT FIRE | F-003 (non-scaling, unaddressed) | HIGH (exact, from real replay JSON) |
| B | 104766421 | nbarlow | WIN | 14314.0 | None | 0 | 3 | 1 | 2 | 2 | NOT TRIGGERED | DID NOT FIRE | N/A (win) | HIGH (exact, from real replay JSON) |
| B | 104767259 | zixma13 | LOSS | -25436.0 | -81 | 0 | 5 | 3 | 5 | 4 | TRIGGERED | FIRED (confirmed) | F-001 (response fired, insufficient) | HIGH (exact, from real replay JSON) |
| B | 104768097 | moushun chen | LOSS | -48162.0 | -56 | 10 | 14 | 3 | 5 | 2 | TRIGGERED | FIRED (confirmed) | F-001 (response fired, insufficient) | HIGH (exact, from real replay JSON) |

## Mechanism Frequency (A+B combined, 17 real losses)

- F-001: 6/17 (35%)
- F-002: 4/17 (24%)
- F-003: 3/17 (18%)
- UNCLASSIFIED: 2/17 (12%)
- F-004: 1/17 (6%)