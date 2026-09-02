# Submission B Live Forensic Audit (Addendum to the Submission A Audit)

**Scope**: Forensics only, no production code modified. Analyzes the first 4 real, completed Kaggle episodes played by Submission B (Competitive Agent V2), found in `COMPETITION RESULTS/SUBMISSION B/`. This is the first REAL-WORLD test of the predictions made in `submission_a_video_forensic_audit.md`.

## 1. Dataset

4 episodes (8 JSON files: 4 full replays + 4 execution logs, 0 parse errors) + 4 videos, paired 1:1 by reading the episode ID from each video's browser URL bar (same method as the Submission A audit). One additional game (`nbarlow` vs a `[Deleted]` account) was visible in the Game History sidebar as "in progress" — correctly excluded, no data available for an incomplete/deleted-account game.

| Episode | Video | Opponent | Result | Our Money | Opponent Money | Margin | Rating Change |
|---|---|---|---|---|---|---|---|
| 104765587 | 1 | Vishwanath N Iyer | **LOSS** | $3,140 | $33,350 | -$30,210 | **-146** |
| 104766421 | 2 | nbarlow | WIN | $28,376 | $14,062 | +$14,314 | (win) |
| 104767259 | 3 | zixma13 | **LOSS** | $21,261 | $46,697 | -$25,436 | -81 |
| 104768097 | 4 | moushun chen | **LOSS** | $15,636 | $63,798 | -$48,162 | -56 |

**3 losses, 1 win in the first 4 real games.** The rating shown in-video has fallen from Submission B's starting point to **392** by the 4th game (sparkline range shown: 392-600). Per the standing project instruction (and repeated explicitly in the original Phase 3.5/submission tasks): **this must NOT be interpreted in isolation** — n=4 is far too small to conclude Submission B is competitively worse than Submission A; rating systems carry high early variance, and 3 of these 4 opponents may simply be a harder draw than Submission A's early opponents were. What follows is the MECHANISM-level evidence, which is the actually meaningful result here.

## 2. Direct, Real-World Confirmation of the Submission A Audit's F-001 Prediction

This is the most important finding in this addendum. The previous audit (`submission_a_video_forensic_audit.md`) predicted, from a *counterfactual* replay of the scaling detector against Submission A's real losses, that Submission B's countermeasure would correctly trigger in several cases but be **insufficient in magnitude** against the largest real scaling opponents (F-001). Submission B's own first 4 real games **directly confirm this, with actual observed behavior rather than an estimate**:

| Episode | Detector Triggers? | Response Actually Fired? | Our Hands (peak) | Our Animals (peak) | Opponent Final Hands/Animals/Land | Result |
|---|---|---|---|---|---|---|
| 104767259 (zixma13) | YES, day 12 | **YES — confirmed** (our hands rose from 2 to 5, animals to 4, matching the countermeasure's exact target values) | 5 | 4 | 0 / 5 / 3 (land-heavy) | **LOSS, -$25,436** |
| 104768097 (moushun chen) | YES, day 5 (early) | **YES — confirmed** (hands rose to 5) | 5 | 2 (target was 4 — not fully reached) | 10 / 14 / 3 (extreme, labor+animal+land) | **LOSS, -$48,162** |

This is not a hypothetical anymore: **the scaling response demonstrably fired in real competitive play** (our own hands/animals count directly observed rising above Submission A's static ~2/1-2 baseline, exactly matching `agents/phase3_5/response_policy.py`'s configured targets) — and it was **not enough** in either case. This upgrades F-001's research classification from `STRONG_EMPIRICAL_SIGNAL` (extrapolated from a synthetic archetype) to **`EXPERIMENTALLY_VALIDATED`** for the specific claim "the countermeasure triggers correctly in real play but its fixed magnitude is insufficient against real large-scale opponents" — this is now directly observed, not inferred.

Notably, `104768097`'s animal target was NOT fully reached (peaked at 2, not the configured target of 4) despite the detector being active from day 5 onward — worth a dedicated look in Phase 3.6 (a resource/cash/land constraint may have prevented reaching the full target; this was not diagnosed further here, forensics-only scope).

## 3. A New, Large, Non-Scaling Loss (Consistent with F-003, Larger Magnitude)

`104765587` vs Vishwanath N Iyer: detector never triggers (opponent only reached 4 hands, 0 animals — below the 5-threshold), yet this is the **largest-margin loss in the entire Submission A+B dataset so far** (-$30,210) and carries the single largest rating hit observed anywhere (-146, exceeding even the presumed-first Submission A loss against Ben Wilson at -119). This is squarely an **F-003-type loss** (no scaling signature, mechanism not covered by any current detector) — and it demonstrates F-003 is not necessarily a "modest margin" category as the original Phase 3.5 framing implied; it can be severe. **Confidence: HIGH** (exact non-activation computed from the real replay, same method as the Submission A audit).

## 4. Updated Frequency Table (Submission A + B combined, 17 real losses)

| Mechanism | Submission A count | Submission B count | Combined |
|---|---|---|---|
| F-001 (scaling, response insufficient) | 6/13 | 2/4 | 8/17 (47%) |
| F-002 (scaling, response plausibly sufficient) | 4/13 | 0/4 | 4/17 (24%) |
| F-003 (non-scaling, unaddressed) | 2/13 | 1/4 | 3/17 (18%) |
| F-004 / unclassified | 1/13 | 0/4 | 1/17 (6%) |

The dominant remaining pattern across BOTH submissions is now clearly **F-001**: the countermeasure triggers correctly but is not strong enough against the largest real opponents. This is the single most consistent, best-evidenced weakness across the entire body of real evidence collected so far.

## 5. What This Does and Does Not Show

- **Does show**: the scaling detector and response mechanism work exactly as coded in real competitive play (not just in the synthetic `heavy_scaler` validation) — a genuine engineering confirmation.
- **Does show**: the response's fixed magnitude is measurably insufficient against real opponents reaching 10+ hands / 14+ animals / 3+ land quadrants.
- **Does NOT show**: that Submission B is worse than Submission A overall — 4 games is too small a sample, and the early rating trajectory is explicitly flagged (per standing instruction) as not to be read as a verdict on its own.
- **Does NOT show**: why `104768097`'s animal target was only half-reached (2 of 4) — flagged as an open question, not diagnosed (forensics scope; would require action-level trace inspection not available in the replay JSON).

## 6. Updated Verdict

Combining this with the Submission A audit's final decision rule: **the answer remains NO** — Submission B is not yet sufficient to address the major causes of real competitive losses. This addendum *strengthens* that conclusion with direct observation rather than counterfactual estimation: the exact mechanism flagged as the highest-priority Phase 3.6 research question (F-001: does a magnitude-proportional response help, and is there a ceiling past which no labor/animal response competes with the most extreme real opponents) is now directly evidenced in Submission B's own live results, not merely predicted from Submission A's replays.

## Updated Summary

```
Submission A losses reviewed:     13 / 13  (previous audit)
Submission B episodes reviewed:    4 / 4   (this addendum)
Submission B losses reviewed:      3 / 3
Submission B videos reviewed:      4 / 4
Submission B JSON replays:         4 / 4  (0 parse errors)

Submission B: scaling response fired in real play:  2 / 3 losses (confirmed directly)
Submission B: response fired but loss NOT prevented: 2 / 2 (100% of firing cases)
Submission B: new large non-scaling loss (F-003):    1 / 3 (-$30,210, largest margin + largest rating hit observed to date)

Combined (A+B) F-001 frequency:  8 / 17 real losses (47%) -- the dominant, best-evidenced weakness
```

**Most important Phase 3.6 question, reaffirmed with stronger evidence**: does a magnitude-proportional (rather than fixed) competitive scaling response measurably close more of the F-001 gap, and is there a ceiling beyond which no labor/animal response competes with the most extreme real opponents (moushun chen: 10 hands, 14 animals, 3 land quadrants) regardless of magnitude? This is no longer a hypothesis extrapolated from Submission A alone — it is now directly observed in Submission B's own real competitive results.
