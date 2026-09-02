"""
Phase 3.6 scaling-intensity ladder -- 4 synthetic opponent archetypes at
increasing labor/animal/land commitment, built to test where Submission
B's fixed response (target hands=5, animals=4) stops being sufficient and
to construct a competitive-scaling response frontier (brief section 3.6-C).

Reuses the existing, already-tested make_agent_23 factory (no new agent
logic), same discipline as agents/phase3_5/opponent_classes_extended.py.

HONEST LIMITATION, discovered while tuning these (not hidden): an
`n_hands=11` or `n_hands=12` configuration was attempted with several
land/animal buy-day delays and crop mixes (WHEAT-only, WHEAT+STRAWBERRY)
and went BANKRUPT ($0 final money) in every attempt -- the fibonacci daily
re-hire cost for 11-12 hands, paid EVERY day since hands reset daily, could
not be sustained by make_agent_23's simple staged-purchase model regardless
of how late land/animal purchases were delayed. This means the real
opponent "moushun chen" (observed: 10 hands, 14 animals, 3 land quadrants,
final money $63,798) achieved a capital-timing and/or crop-selection
efficiency this project's existing synthetic-archetype-building tools
cannot straightforwardly replicate. `scaler_10` (below) is therefore used
as the closest ACHIEVABLE approximation of the extreme real-opponent
profile, explicitly NOT claimed to reproduce moushun chen's animal count or
overall efficiency -- see Phase 3.6-C's report for the resulting ceiling
discussion.
"""
from agents.phase2_3.common import make_agent as make_agent_23


def scaler_5():
    """~5 hands, minimal animals/land -- just above Submission B's detector threshold."""
    return make_agent_23(crops="WHEAT", n_hands=5, land_quadrants=1, land_buy_day=0,
                          animals={"COW": 1, "SHEEP": 1}, animal_buy_day=5)


def scaler_7():
    """~7 hands, moderate animals/land."""
    return make_agent_23(crops="WHEAT", n_hands=7, land_quadrants=2, land_buy_day=8,
                          animals={"COW": 2, "SHEEP": 1}, animal_buy_day=6)


def scaler_10():
    """~10 hands, 6 animals, 2 land -- the strongest VIABLE (non-bankrupt) archetype found;
    used as the approximate stand-in for the observed moushun chen profile
    (10 hands, 14 animals, 3 land quadrants) -- labor dimension is close,
    animal/land dimensions are NOT fully matched (see module docstring)."""
    return make_agent_23(crops="WHEAT", n_hands=10, land_quadrants=2, land_buy_day=10,
                          animals={"COW": 3, "SHEEP": 3}, animal_buy_day=8)


def scaler_12_extreme_UNVIABLE():
    """DOCUMENTED AS UNUSABLE: every tested configuration at n_hands=11-12
    (varied land/animal buy-day delays from day 0 to day 20, WHEAT-only and
    WHEAT+STRAWBERRY crop mixes) went bankrupt ($0 final money) before
    production revenue could sustain the daily re-hire cost. Kept here,
    clearly marked, as a negative result -- not deleted, not silently
    dropped, and NOT used in any experiment (would bias results toward
    "matching scale is bad" for the wrong reason: bankruptcy, not
    competitive dynamics)."""
    return make_agent_23(crops="WHEAT", n_hands=12, land_quadrants=3, land_buy_day=20,
                          animals={"COW": 4, "SHEEP": 3}, animal_buy_day=18)


OPPONENT_CLASSES_SCALING_LADDER = {
    "scaler_5": scaler_5,
    "scaler_7": scaler_7,
    "scaler_10": scaler_10,
}
