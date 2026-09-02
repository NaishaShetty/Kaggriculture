# Phase 3.6-F: Regression + Held-Out Validation

## Regression Suite

Full existing suite re-run after all Phase 3.6 experimentation: **106/106 passing** (18 Phase 2.6 + 21 Phase 3.1 + 14 Phase 3.2 + 12 Phase 3.3 + 14 Phase 3.4 + 7+20 Phase 3.5). No regressions. No new tests were added to this suite because no candidate reached the production path — the Phase 3.6 experimental code was validated entirely through its own Stage B/C/D experiment matrix (paired same-seed comparisons against 4+ archetypes, 3 development + 4 validation seeds for the closest challenger).

## Control Reproduction

Planner v1: **30/30 exact byte-for-byte matches**, re-verified after all Phase 3.6 work. Frozen file hashes (`results/phase3_1/control_reproduction/frozen_file_hashes.txt`) unchanged, checked before and after.

## Held-Out Seeds: Deliberately Not Spent

Per the brief's own instruction ("Do NOT promote based on development seeds alone" — implying held-out validation is for a candidate that has already cleared development+validation screening): since **no adaptive scaling candidate (B1-B5) beat the control on development OR validation seeds**, there was no candidate meeting the bar to justify spending held-out seeds on. This is a deliberate, principled decision, not an oversight — held-out seeds remain unused and available for a genuinely promising Phase 3.7 candidate.

## Why No "Candidate C" Evaluation Battery

Section 3.6-F's full requested battery (win rate, mean/median margin, worst margin, 10th-percentile margin, catastrophic-loss rate, activation rate, false-positive rate, response cost, production impact) is specified for evaluating an **integrated candidate C**. Stage E concluded there is no integrated candidate C to evaluate — Stage B/C's screening matrix already is the complete, decisive evidence (B0 beats every challenger in every tested cell, confirmed on 2 independent seed sets). Running the full battery on a candidate already shown to lose in the screening stage would not change the conclusion and would spend held-out seeds for no decision-relevant purpose.

## Conclusion

All frozen behavior is confirmed intact. No regressions anywhere. The evidence gate for promotion (section 3.6-F/11) is **not met** — proceed to Stage G under the "no promotion" branch.
