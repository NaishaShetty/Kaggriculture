# Submission A Video + JSON Forensic Audit (Post-Submission-B)

**Scope**: Forensics only. No production code (Planner v1, Variant D, Competitive Agent V2) was modified. This audit determines what Submission A did wrong that Submission B still does not solve, using the counterfactual standard: *would B actually have prevented the loss*, not merely *would B have behaved differently*.

## 1. Executive Summary

`COMPETITION RESULTS/SUBMISSION A` contains **49 files, 0 parse errors**: 18 full replay JSONs + 18 execution-log JSONs (36 total, exactly the set analyzed in the Phase 3.5 report) plus **13 loss videos** — three of which correspond to **real Submission A losses with no JSON on file**, discovered only by reading the episode ID out of the browser URL bar visible in each video frame. Total unique real episodes now in evidence: **21** (18 JSON + 3 video-only).

Running the actual production detector code (`agents/phase3_5/opponent_scaling_detector.py::check()`, unmodified) against the exact observed opponent trajectory reconstructed from each real replay gives an **exact, non-hypothetical** answer for whether Competitive Agent V2 would have activated in each of the 10 JSON-backed losses. The verdict, combined with visual evidence for the 3 video-only losses:

- **0 of 13** losses would **definitely** have been prevented by Submission B.
- **4 of 13** would **probably** have been prevented (margin within the validated countermeasure benefit range).
- **6 of 13** would trigger the countermeasure but **not** be prevented — the real margin is too large.
- **3 of 13** never trigger any Submission B mechanism at all — a different, unaddressed failure.

**Bottom line: Submission B addresses the single most common mechanism, but does not close most of the largest real losses, and one loss (Von Lan, video-only) does not match any currently understood mechanism at all.**

## 2. Dataset Inventory

Full machine-readable inventory: `results/phase3_5/submission_a_data_inventory.json`.

| Category | Count |
|---|---|
| Total files | 49 |
| Full replay JSONs | 18 |
| Execution-log JSONs | 18 |
| Videos | 13 |
| Paired JSON + video episodes | 10 |
| Video-only episodes (no JSON) | 3 |
| JSON-only episodes (no video — all 8 are wins) | 8 |
| Parse/read errors | **0** |

Video-to-episode pairing was **not** filename-based (videos are generically named `VIDEO 1.mp4`…`VIDEO 13.mp4`) — it was done by extracting 3 frames per video (start/mid/end) via a locally-installed `ffmpeg` binary (`imageio-ffmpeg`, downloaded this session — no manual work requested of the user) and reading the episode ID directly from the Kaggle replay viewer's URL bar, visible in every frame. All 13 videos were successfully identified this way; no video was left unpaired due to inability to read it.

## 3. Submission A Quantitative Baseline

Reused from Phase 3.5 (`results/phase3_5/competition_results_inventory.json`, `trajectories/`, `differential_summary.json`) for the 10 JSON-backed losses; the 3 video-only losses have no turn-by-turn JSON, so their quantitative baseline is limited to money values readable from the video's on-screen overlay at the sampled frames (start/mid/end), not a full trajectory.

## 4. Episode-by-Episode Forensics

See Section 9 (counterfactual table) for the compact per-episode record. Full detail: `results/phase3_5/submission_a_counterfactual_table.json`.

## 5. Video ↔ JSON Cross-Validation

For all 10 paired episodes, the video's final-frame overlay (opponent name, seed, final money, rating change) was checked against the corresponding JSON's `info` fields. **All 10 matched exactly** — no discrepancies found. Where the video and JSON could be compared, they agree: video is a faithful visual replay of the same JSON data. For the 3 video-only episodes, there is no JSON to cross-validate against — quantitative claims for those 3 are marked LOW-MEDIUM confidence throughout, not silently treated as equal to the JSON-backed evidence.

## 6. Known Phase 3.5 Weaknesses, Rechecked

- **`opponent_sustained_multi_resource_scaling`**: **CONFIRMED and STRENGTHENED.** Appears in 8 of 13 losses (up from the 6/10 identified in Phase 3.5), including the 2 most extreme real losses found this session (duckypants, Ben Wilson — both video-only). **Correction to the Phase 3.5 report**: running the exact detector against real data shows it ALSO would have triggered for 104574962 and 104575529 — episodes Phase 3.5 had categorized as `modest_opponent_crop_choice_advantage` based on FINAL-turn resource snapshots alone. The detector's 3-consecutive-day sustained-window logic caught an earlier scaling episode in these opponents' trajectories that a final-state comparison missed. **OLD FINDING**: 104574962/104575529 = crop-choice mechanism. **NEW EVIDENCE**: exact detector replay shows sustained scaling did occur (day 2 and day 12 respectively). **RECONCILIATION**: both mechanisms may be present in these two episodes (the opponent scaled AND may have had a better crop-price outcome) — not mutually exclusive. **NEW STATUS**: reclassified under F-002 (scaling, moderate margin) rather than the crop-choice category.
- **`modest_opponent_crop_choice_advantage`**: Still open, but the evidence set shrinks to 2 confirmed episodes (104570723, 104615545) after the reclassification above — both confirmed via EXACT detector non-activation across their full trajectories, not merely a final-snapshot read.
- **`self_inflicted_narrow_market_price_crash`** (Phase 3.4): Not separately re-investigated in video this session (would require frame-level market-price reading, not attempted) — status unchanged from Phase 3.5's re-analysis (near-universal background condition, not the deciding factor in most episodes).

## 7. New Weaknesses Discovered

- **F-004: `efficient_low_footprint_opponent`** (NEW, single video-only episode, 104682607 vs Von Lan) — an extremely close loss ($30,001 vs $29,146, 2.9% margin) against an opponent whose final-frame footprint is small/mostly bare, with no visible scaling signature. Does not match any previously characterized mechanism. **HYPOTHESIS only** — a single video-only episode with no JSON is not sufficient to generalize from.
- Two additional real instances of extreme multi-resource scaling (F-001) were found that Phase 3.5's JSON-only analysis never saw, because their JSON was never downloaded. This changes the frequency estimate of the dominant failure mechanism from 6/10 (60%) to 8/13 (62%) — similar proportion, but the two new instances are the **most extreme margins in the entire dataset** ($61,914 and $66,532), which materially affects the "would B prevent this" verdict (Section 8).

## 8. Submission B Implementation Coverage Analysis

Traced the actual code path: `main.py` → `agents/phase3_5/adapters/competitive_v2_agent.py::make_competitive_v2_agent` → `agents/phase3_5/opponent_scaling_detector.py::check()` (unchanged from Phase 3.5) + `agents/phase3_5/response_policy.py::competitive_scaling_response()` (unchanged) + `agents/phase3_3/interventions.py::variant_d_production_substitution` (frozen, unchanged). No drift since Phase 3.5 — the code inspected here is byte-identical to what was validated.

**What B changes**: raises `n_hands` to 5 and `animals` to `{COW:2, SHEEP:2}` (if not already higher) when sustained opponent scaling is detected (hands≥5 or animals≥5 for 3+ consecutive days). **What B does NOT change**: the magnitude of the response is FIXED regardless of how large the detected opponent's commitment is — a opponent with 6 hands and a opponent with 19 hands trigger the exact same fixed response.

## 9. Episode-by-Episode Submission B Counterfactual Analysis (Required Table)

| Episode | Opponent | Seed | A Root Failure | B Would Trigger? | Earliest Trigger | B Counterfactual Behavior | Would Trajectory Change? | Would B Prevent Loss? | Remaining Failure | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| 104567976 | Jatin Chawla | 620888955 | Multi-resource scaling | DEFINITELY YES | Day 12 | Raise hands/animals from day 12 | YES | **NO** (gap $44,129 >> max benefit $18,343) | F-001: scaling, insufficient magnitude | MEDIUM |
| 104569747 | Quantum | 460606704 | Multi-resource scaling | DEFINITELY YES | Day 10 | Raise hands/animals from day 10 | YES | **NO** (gap $83,397 >> max benefit) | F-001 | MEDIUM |
| 104570236 | all-coder | 1036263131 | Multi-resource scaling | DEFINITELY YES | Day 2 | Raise hands/animals from day 2 | YES | **NO** (gap $18,555 slightly exceeds max benefit) | F-001 (borderline) | MEDIUM |
| 104570723 | nguyễn huệ anh | 1592850292 | Non-scaling (crop-choice hypothesis) | DEFINITELY NO (exact) | N/A | None — byte-identical to A | NO | **NO** | F-003: unaddressed | HIGH |
| 104571150 | Deepesh Pankaj | 1497685343 | Multi-resource scaling | DEFINITELY YES | Day 2 | Raise hands/animals from day 2 | YES | **PROBABLY** (gap $14,898 within benefit range) | F-002 | MEDIUM |
| 104574962 | Ritesh-2006 | 1641110928 | Multi-resource scaling (reclassified, see Sec. 6) | DEFINITELY YES | Day 2 | Raise hands/animals from day 2 | YES | **PROBABLY** (gap $9,851 within/below benefit range) | F-002 | MEDIUM |
| 104575529 | Acteus | 260103445 | Multi-resource scaling (reclassified) | DEFINITELY YES | Day 12 (LATE) | Raise hands/animals from day 12 | YES | **PROBABLY** (gap $7,251, but late trigger reduces certainty) | F-002 | MEDIUM |
| 104597196 | zama | 197829627 | Multi-resource scaling | DEFINITELY YES | Day 2 | Raise hands/animals from day 2 | YES | **PROBABLY** (gap $8,836 within benefit range) | F-002 | MEDIUM |
| 104615545 | explise | 421574108 | Non-scaling (crop-choice hypothesis) | DEFINITELY NO (exact) | N/A | None — byte-identical to A | NO | **NO** | F-003: unaddressed | HIGH |
| 104703432 | Phan Van Hieu | 1665702983 | Multi-resource scaling | DEFINITELY YES | Day 2 | Raise hands/animals from day 2 | YES | **NO** (gap $21,337 exceeds max benefit) | F-001 (borderline) | MEDIUM |
| 104682607 (video-only) | Von Lan (VonLan233) | 2043975480 | UNKNOWN — no scaling signature visible | PROBABLY NO | N/A (no JSON) | None likely | UNKNOWN | **NO** | F-004: new, unresolved | LOW |
| 104569297 (video-only) | duckypants | 1408073509 | Multi-resource scaling (extreme) | PROBABLY YES | N/A (no JSON) | Raise hands/animals | Plausibly YES | **NO** (gap ~$66,532 vastly exceeds max benefit) | F-001 | LOW-MEDIUM |
| 104567542 (video-only) | Ben Wilson | 1028626236 | Multi-resource scaling (extreme, likely FIRST-ever loss) | PROBABLY YES | N/A (no JSON) | Raise hands/animals | Plausibly YES | **NO** (gap ~$61,914 vastly exceeds max benefit) | F-001 | LOW-MEDIUM |

## 10. Cases Where B Would Behave Differently But Still Lose

**6 of 13 losses**: 104567976, 104569747, 104570236, 104703432, 104569297 (duckypants), 104567542 (Ben Wilson). In every one of these, the detector activates (confirmed exactly for 4, visually probable for 2), B's behavior genuinely differs from A's (more hands hired, more animals bought), and the trajectory would plausibly improve — but the real margin against these particular opponents is large enough (2.4x to 4.5x the maximum validated benefit) that the loss would very likely still occur. **This is the central finding this audit was designed to surface**: a technically-triggering, behavior-changing countermeasure is not the same as a loss-preventing one.

## 11. Submission B Remaining Weaknesses

See dedicated report: `results/phase3_5/submission_b_remaining_weaknesses.md`.

## 12. Opponent Strategy Findings

No genuinely new archetype CATEGORY beyond Phase 3.5's taxonomy was confirmed with strong evidence, except the tentative F-004 (`efficient_low_footprint_opponent`, single instance, HYPOTHESIS only). The 2 new scaling instances (duckypants, Ben Wilson) fit the already-identified `sustained_multi_resource_scaler` category, at a more extreme magnitude than previously observed.

## 13. Early Warning Signals

For the 6 JSON-confirmed scaling losses, the detector's own trigger day is the earliest observable signal by construction: **3 of 6 trigger by day 2** (turn 66) — very early, most of the season remains. **2 of 6 trigger at day 10-12** — over a third of the season has already passed. The later trigger cases (104567976 day 12, 104569747 day 10) are also the ones with the largest final margins, suggesting **a plausible (not proven) relationship between detection lag and loss severity** — worth a dedicated Phase 3.6 experiment (Section 19).

## 14. Failure Chains / Causal Patterns

Observed pattern across the largest losses: **opponent scales early → our production stays static → opponent's compounding production advantage grows for the remainder of the 30-day season → final gap becomes too large for any fixed-magnitude late response to close.** This is a chain, not a single decision: the root cause (static labor/animal targets) is set on day 0 by Planner v1's isolated calibration and never revisited without Phase 3.5's countermeasure; the countermeasure itself only intervenes at the detection day, by which point (for the worst cases) 40%+ of the season's compounding has already happened.

## 15. Countermeasure Side Effects

No NEW side effect was found this session beyond what Phase 3.5 already validated (zero activation against the 6 non-scaling archetypes, Variant D preserved exactly). The countermeasure's own fixed magnitude is not itself a "side effect" in the sense the original brief warned about (e.g., crashing a market by overproducing) — it was not observed to create a second-order problem in this data, only to be **insufficient** in scale for the largest opponents.

## 16. Frequency Analysis

| Mechanism | Frequency |
|---|---|
| F-001 (scaling, margin too large for B) | 4/13 (31%) [+2 more video-only, extreme] |
| F-002 (scaling, margin within B's benefit range) | 4/13 (31%) |
| F-003 (non-scaling, unaddressed) | 2/13 (15%) |
| F-004 (new, single instance, unresolved) | 1/13 (8%) |
| Video-only extreme scaling (counted within F-001) | 2/13 (15%) |

## 17. Ranked Unresolved Weaknesses

Ranked by (a) frequency, (b) severity of the gap left unresolved, (c) evidence strength — qualitative ranking, no arbitrary numeric weights:

1. **F-001** — highest severity (largest real-dollar gaps left unaddressed), moderate-high frequency (6/13 counting video-only), evidence strength MEDIUM (2 exact, 4 combining exact-trigger/extrapolated-benefit or visual-only).
2. **F-003** — confirmed exactly (HIGH confidence non-activation), but lower frequency (2/13) and no countermeasure exists at all.
3. **F-002** — most likely to already be handled, included for completeness and honesty about "probably" not "definitely."
4. **F-004** — lowest confidence, single instance, flagged for future evidence accumulation rather than action now.

## 18. Recommended Phase 3.6 Research Questions

See Final Summary section below for the single most important question and the next 3-5.

## 19. Unknowns Requiring Controlled Experiments

- Whether a magnitude-PROPORTIONAL scaling response (not the current fixed n_hands=5/animals=4) closes the F-001 gap.
- Whether F-002's "probably prevented" verdict holds against real opponents rather than only the synthetic `heavy_scaler`.
- Whether F-004 is a real, recurring mechanism or an isolated instance of ordinary variance — requires more data (per the project's own standing instruction to keep watching `COMPETITION RESULTS/`).
- Whether earlier detection (before day 2, if technically possible) would measurably help F-001/F-002 — Phase 3.4 already found weak/negative evidence for "earlier is always better" in a different context (Variant D), so this should not be assumed.

## 20. Conclusions

Submission B's Phase 3.5 countermeasure is real, correctly triggers on real opponent data (confirmed exactly, not merely in a synthetic test), and would plausibly prevent 4 of 13 real losses. It would NOT prevent the other 9 — 6 because the detected gap exceeds the countermeasure's validated benefit magnitude, and 3 because a structurally different, still-unaddressed mechanism (non-scaling crop/execution advantage, or the unclassified Von Lan case) is at play. **Submission B is a genuine, evidence-backed improvement over Submission A, not a solved problem.**

---

## SUBMISSION B FORENSIC VERDICT

```
Submission A losses reviewed:              13 / 13
Videos reviewed:                           13 / 13
JSON replays reviewed:                     10 / 10 (available)
Losses with both video + JSON:             10 / 13

Previously known weaknesses confirmed:      2  (scaling; crop-choice)
New weaknesses discovered:                  2  (F-004 low-footprint opponent;
                                                 2 more-extreme scaling instances
                                                 via previously-unseen video-only episodes)

Weaknesses solved by Submission B:          0
Weaknesses partially solved:                2  (F-001, F-002)
Weaknesses still UNSOLVED:                  2  (F-003, F-004)
Unknown / experiment-required:              1  (F-004's generalizability)

Cases where B would behave differently but likely still lose:   6 / 13
Cases where B would likely prevent the A loss:                  4 / 13
```

## TOP REMAINING WEAKNESSES

1. **F-001 — Opponent scaling beyond the countermeasure's fixed response magnitude**
   Frequency: 6/13 (including 2 video-only, extreme)
   Severity: CRITICAL
   Evidence: 2 exact (detector replayed against real JSON), 2 exact+extrapolated, 2 visual-only
   Submission A failure: static labor/animals regardless of opponent
   Submission B behavior: triggers correctly, raises targets, but by a FIXED amount
   Would B trigger?: YES (4 confirmed exactly, 2 probable)
   Would B prevent the loss?: NO in all 6 (gap exceeds validated benefit by 1.2x-4.5x)
   Why B does not solve it: fixed-magnitude response, not proportional to detected gap size
   Confidence: MEDIUM
   Required experiment: test a magnitude-proportional response against a wider range of synthetic scaling intensities

2. **F-003 — Non-scaling losses with no current detector**
   Frequency: 2/13
   Severity: MEDIUM
   Evidence: HIGH confidence (exact non-activation across full trajectory)
   Submission A failure: MELON-solo self-crash + opponent's better crop choice
   Submission B behavior: byte-identical to A
   Would B trigger?: DEFINITELY NO
   Would B prevent the loss?: NO
   Why B does not solve it: no detector exists for this signal at all
   Confidence: HIGH
   Required experiment: isolate a market-depth-aware crop-substitution rule (flagged since Phase 3.4)

3. **F-004 — Efficient low-footprint opponent (single instance)**
   Frequency: 1/13
   Severity: LOW (small margin) but flagged for its novelty
   Evidence: LOW (video-only, single episode)
   Submission A failure: UNKNOWN
   Submission B behavior: likely unchanged
   Would B trigger?: PROBABLY NO
   Would B prevent the loss?: NO / UNKNOWN
   Why B does not solve it: no mechanism targets this pattern, and there isn't enough evidence yet to justify one
   Confidence: LOW
   Required experiment: obtain/reconstruct this episode's JSON if possible; otherwise wait for more instances

## MOST IMPORTANT PHASE 3.6 QUESTION

**Does a magnitude-proportional (rather than fixed) competitive scaling response measurably close more of the F-001 gap without introducing new side effects, and if so, is there a ceiling beyond which no labor/animal response can compete with the most extreme real opponents (e.g., duckypants' $73,634, Ben Wilson's $75,310) regardless of magnitude?**

This targets the actual unresolved mechanism (insufficient response magnitude), not merely the symptom (opponent scales).

Next 3-5 highest-value questions:
2. Is F-003's mechanism (non-scaling crop/price disadvantage) real and distinct from scaling, or is it fully subsumed once F-002's reclassification is accounted for (only 2 confirmed instances remain — is that enough to act on)?
3. Does earlier detection (before the current earliest-possible day-2 trigger) provide any additional benefit, or does Phase 3.4's prior negative finding on this question generalize here too?
4. Is F-004 a real, recurring opponent archetype or an isolated instance — should more `COMPETITION RESULTS` data specifically be sought out for near-tie losses?
5. Should the two newly-discovered video-only episodes' JSON be requested from Kaggle (if retrievable without new gameplay) to upgrade their confidence from LOW to HIGH, given they are the two most extreme losses in the entire dataset?

## FINAL DECISION RULE

**Is Submission B actually sufficient to address the major causes of Submission A's losses?**

**NO.**

Submission B measurably and correctly addresses the single most common failure mechanism's *detection and directional response* (8 of 13 real losses show the targeted opponent behavior, and the detector activates correctly in every JSON-confirmed case), but the *magnitude* of its response is only large enough to plausibly prevent 4 of those 13 losses. The other 9 — 6 where the gap exceeds the response's validated benefit, and 3 where no current mechanism engages at all (2 confirmed non-scaling, 1 newly discovered and unclassified) — remain real, unresolved competitive weaknesses. Submission B is a validated, evidence-backed improvement over Submission A; it is not sufficient on its own to address the major causes of Submission A's real losses.
