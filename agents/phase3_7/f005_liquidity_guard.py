"""
Phase 3.7-C: F-005 candidate countermeasure -- "Early Cash-Trajectory Guard".

DERIVED DIRECTLY FROM THE STAGE B ROOT-CAUSE FINDING (phase3_7_B_F005_forensics.md):
F-005 is a RECOVERY-FAILURE mechanism, not an over-investment one -- the routine
cash-trough-to-hands-zero window is usually survivable because a few of the many
committed crop tiles happen to get watered by the lone farmer often enough, by
chance, to reach harvest before full decay. The catastrophic case is when NONE do.

ARCHITECTURAL CONSTRAINT (honestly acknowledged): the actual damage occurs in
frozen Planner v1's day-0 sizing decision and the frozen tactical layer's
per-turn watering-priority scheduling -- neither of which any external,
post-hoc config-mutation layer (the only mechanism Phase 3.3/3.5/3.6 have ever
used) can touch AFTER the fact. Already-planted, still-viable tiles do not
retroactively vanish if the crop config later changes.

THE ONE LEVER THAT IS ARCHITECTURALLY AVAILABLE: planting happens gradually
over the first several days (day 0-4 in the observed episodes), and the
tactical layer (agents/phase2_4/common.py) recomputes its tile allocation
from the CURRENT config every cycle. If cash is depleting unusually fast in
the first 1-2 days (a leading indicator that a hands-zero window is coming),
an external layer CAN reduce the crop config's effective footprint BEFORE
most of the eventual 22 tiles are planted, reducing how many tiles the lone
farmer would need to keep watered if hands do drop to zero later.

THIS IS A HYPOTHESIS-LEVEL CANDIDATE, not a proven fix -- Stage B's root
cause for the SPECIFIC divergence (why this one game's tile-survival chance
came up empty) remains UNRESOLVED, so this countermeasure targets the
mechanism CLASS (reduce total tiles at risk), not a confirmed causal lever.
"""

CASH_DANGER_THRESHOLD = 200.0   # if cash falls below this by CHECK_DAY, treat as an early-warning signal
CHECK_DAY = 2                    # matches the observed episode: cash was already critically low by day 2 in the F-005 case
REDUCED_CROP_FRACTION_CAP = 0.5  # halve the effective crop commitment when triggered


def f005_liquidity_guard(config, obs, already_triggered):
    """Returns (new_config, triggered). Fires AT MOST ONCE per episode
    (day==CHECK_DAY, hour==0) -- checks whether cash has fallen below
    CASH_DANGER_THRESHOLD, and if so, halves the crop portfolio's tile
    commitment for all subsequent (not yet planted) tile allocations."""
    if already_triggered:
        return config, already_triggered
    if obs.get("day") != CHECK_DAY or obs.get("hour", 0) != 0:
        return config, already_triggered

    cash = obs["farms"][obs["player"]]["money"]
    if cash >= CASH_DANGER_THRESHOLD:
        return config, already_triggered

    crops = config.get("crops") or {}
    if not crops:
        return config, already_triggered
    new_crops = {c: f * REDUCED_CROP_FRACTION_CAP for c, f in crops.items()}
    new_config = dict(config)
    new_config["crops"] = new_crops
    return new_config, True
