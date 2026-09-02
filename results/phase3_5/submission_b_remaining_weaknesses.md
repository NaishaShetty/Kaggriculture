# Submission B — Remaining Competitive Weaknesses

Derived from `results/phase3_5/submission_a_video_forensic_audit.md` and `submission_a_failure_database.json`. This is the evidence base for Phase 3.6 — no strategy changes are made here.

## F-001 — Opponent scaling beyond the countermeasure's fixed response magnitude

- **Evidence episodes**: 104567976 (Jatin Chawla), 104569747 (Quantum), 104570236 (all-coder), 104703432 (Phan Van Hieu), 104569297 (duckypants, video-only), 104567542 (Ben Wilson, video-only)
- **Frequency**: 6/13 losses (46%)
- **Severity**: CRITICAL — these are also the largest-margin losses in the dataset ($18,555 to $83,397)
- **B status**: PARTIALLY_SOLVED
- **Research classification**: STRONG_EMPIRICAL_SIGNAL
- **Why B does not solve it**: `agents/phase3_5/response_policy.py::competitive_scaling_response` raises `n_hands` to a fixed 5 and animals to a fixed `{COW:2, SHEEP:2}` regardless of how large the detected opponent's own commitment is. The validated benefit (+$11,750 to +$18,343/episode, from the Phase 3.5 `heavy_scaler` experiment) does not scale with opponent intensity, but the real opponents' margins do.
- **Potential countermeasure** (not implemented — Phase 3.6 territory): a response whose magnitude scales with the detected opponent's own hands/animals count (e.g., target roughly matching a fraction of the opponent's observed commitment, capped by affordability) rather than a fixed target.
- **Experiment required**: build a stronger/adaptive-magnitude variant, validate against `heavy_scaler` AND a new, more extreme synthetic archetype calibrated to the duckypants/Ben Wilson magnitude, on disjoint development/validation/held-out seeds.

## F-002 — Opponent scaling within the countermeasure's benefit range (likely, not certain)

- **Evidence episodes**: 104571150 (Deepesh Pankaj), 104574962 (Ritesh-2006), 104575529 (Acteus), 104597196 (zama)
- **Frequency**: 4/13 losses (31%)
- **Severity**: HIGH
- **B status**: PARTIALLY_SOLVED (verdict is "PROBABLY prevented," not "DEFINITELY")
- **Research classification**: STRONG_EMPIRICAL_SIGNAL (trigger fact is exact; benefit-transfer to real opponents is extrapolated from a synthetic experiment, not directly measured)
- **Why not fully SOLVED**: no real-opponent replay of Submission B exists — the benefit estimate comes from a controlled synthetic archetype (`heavy_scaler`), which itself does not fully replicate real opponents' execution efficiency (documented limitation from Phase 3.5).
- **Experiment required**: the only way to move this from PROBABLY to a confirmed verdict is Submission B's own live Kaggle results against comparable real opponents, or a closer-matched synthetic archetype.

## F-003 — Non-scaling losses with no current detector

- **Evidence episodes**: 104570723 (nguyễn huệ anh), 104615545 (explise)
- **Frequency**: 2/13 losses (15%)
- **Severity**: MEDIUM
- **B status**: UNSOLVED
- **Research classification**: HYPOTHESIS (mechanism plausible, not experimentally isolated)
- **Why B does not solve it**: confirmed by exact computation that the scaling detector never activates across the FULL 720-turn trajectory in either episode — this is not a scaling-mechanism loss at all. The working hypothesis (from Phase 3.5) is a MELON-solo self-crash combined with the opponent's better crop-price outcome (both opponents grew STRAWBERRY), but this was not isolated from other confounds this session either.
- **Potential countermeasure** (not implemented): a market-depth-aware crop ranking, flagged as future work since Phase 3.4.
- **Experiment required**: isolate whether crop choice alone (holding resource commitment constant) explains these 2 specific losses.

## F-004 — Efficient low-footprint opponent (new, unresolved, single instance)

- **Evidence episode**: 104682607 (Von Lan (VonLan233), video-only, no JSON)
- **Frequency**: 1/13 losses (8%)
- **Severity**: LOW (smallest margin in the dataset, $855) but structurally novel
- **B status**: UNKNOWN
- **Research classification**: UNKNOWN
- **Why B does not solve it**: no mechanism in the current stack targets a small-footprint, apparently-efficient opponent, and there is not yet enough evidence (a single video-only episode, 3 sampled frames, no JSON) to know whether a countermeasure is even warranted.
- **Experiment required**: obtain this episode's JSON if retrievable from Kaggle without new gameplay; otherwise, wait for `COMPETITION RESULTS/` to accumulate more instances of a similar pattern before investing in a fix for what may be ordinary variance.

## Priority Ranking (qualitative, evidence-justified — no arbitrary numeric weights)

1. **F-001** (highest severity + evidence strength: exact trigger computation for 4/6 instances, largest real-dollar impact)
2. **F-003** (confirmed exactly via non-activation; no countermeasure exists at all, unlike F-001/F-002)
3. **F-002** (likely already adequately addressed, lower research priority than F-001/F-003)
4. **F-004** (lowest confidence, single instance — monitor, don't act yet)
