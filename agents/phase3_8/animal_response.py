"""
Phase 3.8 Submission C: animal-specific scaling response.

DERIVED DIRECTLY FROM PHASE 3.7's VALIDATED FINDING (results/phase3_7/
phase3_7_F_F001_results.json): across all 9 real Submission B episodes
where the scaling detector fired, opponent ANIMAL count cleanly separated
wins (mean 2.0) from losses (mean 9.2), while opponent HANDS count showed
no separation at all (9.0 vs 9.0). The existing hands target (5) is
therefore left completely untouched; only the animal target is adjusted,
and only for opponents whose animal count is materially above what B
already handles.

TRIGGER: reuses agents.phase3_5.opponent_scaling_detector.check() UNCHANGED
-- Phase 3.5/3.6/3.7 already established detection works; this candidate
only changes what happens once triggered.

RESPONSE: a simple, bounded, piecewise animal target -- NOT a proportional
optimizer (explicitly out of scope per the Phase 3.8 brief, and Phase 3.6
already found proportional/optimizer-style designs underperform the fixed
response). B's own existing target (COW:2, SHEEP:2 = 4 total) is preserved
as the floor for low/moderate opponent animal counts; only materially
higher opponent animal counts raise the target, by a small, capped amount.

CRITICAL IMPLEMENTATION FINDING (investigated per the Phase 3.8 brief's
explicit instruction, documented rather than silently patched): the real
moushun chen episode (104768097) shows the scaling response's config
target reaching COW:2/SHEEP:2 (4) but the ACTUAL achieved animal count
staying at 2 for most of the episode. Root cause, confirmed by direct
tile-grid inspection of the real replay: with only 1 land quadrant owned
(the standard, expected state -- Planner v1 essentially never buys land in
isolation, consistent with Phase 2.3's original negative-land-value
finding, reconfirmed by Phase 3.7-D's controlled ablation) and Planner
v1's own ~20-22 tile MELON commitment, the single 25-tile quadrant is
ALREADY full (PLANT:20, WEED:2, PASTURE:2, empty:1 in the inspected
episode) -- there is essentially NO free tile space to build additional
PASTURE/COOP structures beyond what Planner v1 already committed on day 0.
This is NOT a code defect and NOT a new mechanic -- it is the ALREADY-
DOCUMENTED finite-tile-space mechanic interacting with a response that
(in Submission B) set a target without regard to whether the tiles exist
to house it. THE FIX APPLIED HERE: the animal target increase is kept
SMALL (at most +2 over B's baseline of 4) to stay within the realistic
1-2 tile headroom actually observed, rather than requesting a large
increase that would silently fail to materialize the same way B's did.
This is a bound on the RESPONSE'S OWN AMBITION, not a change to any land,
crop, or tactical-layer logic (all of which remain completely untouched).
"""
from agents.phase3_5.opponent_scaling_detector import check as check_scaling

# B's existing baseline -- UNCHANGED, used as the floor here (never reduced below this)
BASELINE_ANIMALS = {"COW": 2, "SHEEP": 2}  # 4 total, identical to agents.phase3_5.response_policy

# Piecewise thresholds, derived from Phase 3.7's real-data win/loss animal-count separation
# (wins clustered <=6, losses clustered >=8) -- NOT arbitrary, grounded in that comparison.
MODERATE_ANIMAL_THRESHOLD = 8   # at/above this, opponent animal count is in the Phase 3.7 loss cluster
HIGH_ANIMAL_THRESHOLD = 12      # at/above this, opponent is in the most extreme observed range (iBooNDK=16, moushun chen/deleted=14)

MODERATE_RESPONSE_ANIMALS = {"COW": 3, "SHEEP": 2}  # +1 over baseline (5 total) -- within the ~1-2 tile headroom observed
HIGH_RESPONSE_ANIMALS = {"COW": 3, "SHEEP": 3}       # +2 over baseline (6 total) -- the outer bound of realistic tile headroom


def animal_specific_response(config, opponent_history, current_day):
    """TRIGGER: identical to Submission B's existing detector (unchanged).
    RESPONSE: adjusts ONLY the 'animals' config key -- 'n_hands' is never
    touched, preserving B's existing (validated-adequate, per Phase 3.7)
    hands target exactly. Never DOWNGRADES an already-higher commitment
    the planner or a prior activation independently chose (same
    non-regression discipline as every prior Phase 3.5/3.6 response)."""
    detection = check_scaling(opponent_history, current_day)
    if not detection.active:
        return config, detection

    last_snap = opponent_history[-1]
    # Use the SAME stable daily-late-hour sampling discipline as the detector itself
    # (agents.phase3_5.opponent_scaling_detector._daily_late_samples) to avoid the
    # documented daily hands-reset read noise -- animals are not daily-reset, but for
    # consistency and to avoid any transient mid-turn read, sample the same way.
    by_day = {}
    for snap in opponent_history:
        if snap.hour >= 18 or snap.day not in by_day:
            by_day[snap.day] = snap
    latest = by_day[max(by_day)]
    opp_animals = sum(latest.visible_animal_tile_counts.values())

    if opp_animals >= HIGH_ANIMAL_THRESHOLD:
        target = HIGH_RESPONSE_ANIMALS
    elif opp_animals >= MODERATE_ANIMAL_THRESHOLD:
        target = MODERATE_RESPONSE_ANIMALS
    else:
        target = BASELINE_ANIMALS

    current_animals = dict(config.get("animals") or {})
    new_animals = dict(current_animals)
    for species, count in target.items():
        new_animals[species] = max(current_animals.get(species, 0), count)

    if new_animals == current_animals:
        return config, detection

    new_config = dict(config)
    new_config["animals"] = new_animals
    # n_hands is deliberately NEVER set or modified here -- Submission B's own value
    # (set by the frozen agents.phase3_5.response_policy.competitive_scaling_response,
    # applied upstream by the C adapter before this function runs) passes through unchanged.
    return new_config, detection
