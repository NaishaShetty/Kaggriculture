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

CASH_DANGER_THRESHOLD = 200.0   # if cash falls below this on any CHECK_DAYS day, treat as an early-warning signal
# Widened per Phase 12 forensics re-read (both real data points came from prior phases,
# not re-measured this phase):
#   - Phase 3.7-C (phase3_7_C_F005_countermeasure.md): reconstructed death-spiral seed
#     852025866 had cash == $572 at day==2 (above the old single-checkpoint threshold --
#     this is WHY the original CHECK_DAY=2 guard "never fires" in that episode) and did not
#     visibly enter crisis territory until day 4-6, by which point ~21-22 tiles were already
#     planted.
#   - Phase 6 report Section 11 (Lai Eu Wen episode 104797306, our own side): cash was $630
#     at day==1 and already $0 by day==3 -- a much faster collapse than 852025866's, and one
#     the old day==2-only checkpoint could have caught only by luck.
# A single fixed CHECK_DAY cannot cover both observed collapse speeds (day 3 vs. day 4-6).
# Checking once per day across this whole window costs nothing extra: the guard fires at
# most once (already_triggered), and mutating config["crops"] after the tactical layer has
# already planted a tile is a no-op for that tile (already-planted tiles are not retroactively
# resized) -- it only affects tiles not yet planted, so extending the check later in the game
# cannot make an already-fine game worse. Days 1-6 span both documented collapse windows;
# day 0 is excluded because Planner v1's day-0 sizing decision (the thing this guard reacts
# to) hasn't executed yet when day==0 observations are seen.
CHECK_DAYS = frozenset({1, 2, 3, 4, 5, 6})
REDUCED_CROP_FRACTION_CAP = 0.5  # halve the effective crop commitment when triggered


def f005_liquidity_guard(config, obs, already_triggered):
    """Returns (new_config, triggered). Fires AT MOST ONCE per episode, checked once
    per day at hour==0 across CHECK_DAYS -- checks whether cash has fallen below
    CASH_DANGER_THRESHOLD, and if so, halves the crop portfolio's tile
    commitment for all subsequent (not yet planted) tile allocations."""
    if already_triggered:
        return config, already_triggered
    if obs.get("day") not in CHECK_DAYS or obs.get("hour", 0) != 0:
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
