"""
Phase 34 Part A, Steps 1-2: a synthetic "Sundar archetype" opponent, built
the same way Phase 21 Step 0 built its Larko-derived "realistic opponent"
(scripts/phase21/realistic_opponent.py, reused as a PATTERN here, not
copied code) -- a day-indexed target table read directly off the real,
full 30-day extraction of episode 105208327 (agents/phase6/replay_forensics.py
::extract_episode_timelines, reused unchanged -- see
results/phase34/phase34_trajectory_sundar_worstloss.json for the full dump),
fed through agents/phase21/execution.py's own generic execution layer
(imported, not modified).

Real observed opponent (Sundar) trajectory, confirmed directly from the raw
replay (not trusted from any paraphrase):
  day  0: hands=2 land=1 crops=MELON8                    animals=COW2/SHEEP2
  day  8: hands=3 land=1 crops=MELON13                    animals=COW1/SHEEP6
  day  9: hands=3 land=2 crops=MELON14                    animals=COW1/SHEEP6
  day 10: hands=6 land=2 crops=MELON13                    animals=COW1/SHEEP8
  day 11: hands=7 land=3 crops=STRAW1/MELON19             animals=COW1/SHEEP14
  day 12: hands=10 land=3 crops=STRAW1/MELON19            animals=GOOSE3/COW2/SHEEP19
  day 13: hands=10 land=3 crops=STRAW6/MELON19            animals=GOOSE4/COW2/SHEEP20
  day 14: hands=10 land=3 crops=STRAW8/MELON19            animals=GOOSE5/COW2/SHEEP19
  day 15: hands=10 land=4 crops=STRAW8/MELON19 (4th QUADRANT BOUGHT -- the
          one Submission H and every real top player in this project's prior
          data never buys) animals=GOOSE5/COW2/SHEEP19
  day 18: hands=10 land=4 crops=STRAW7/MELON14             animals=GOOSE3/COW2/SHEEP19
  day 21: hands=9  land=4 crops=STRAW7 (MELON dropped, sustained through
          day 20 -- NOT abandoned by day 10 like agents/phase21/'s own MELON
          window) animals=GOOSE3/COW2/SHEEP19
  day 29: hands=5  land=4 crops=STRAW6 (NO full liquidation -- unlike every
          real-data trajectory this project has built an opponent from
          before, Sundar keeps a small STRAWBERRY footprint all the way to
          the end) animals=GOOSE3/COW2/SHEEP19, final money $97,246

This does NOT claim to replicate Sundar's actual (unknown) code -- same
caveat Phase 21's realistic_opponent.py carries for Larko's data.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.execution import make_execution_agent  # noqa: E402

_LAND_RUNGS = [(0, 1), (9, 2), (11, 3), (15, 4)]
# SMOOTHED (see module docstring's "Reconstruction Note" below): the raw
# real-data rungs (2->10 hands in one jump at day 12, 8->19 SHEEP in one jump
# at day 12) sent a naive target-following reconstruction bankrupt in the
# isolation sanity check (Step 3) -- finer intermediate steps, matching the
# gradualness Phase 21's Larko-derived realistic_opponent.py's own rungs
# already use, were substituted so the SAME real end-state (10 hands, 19
# SHEEP by day ~14) is reached without an unsustainable single-day cash spike.
_HANDS_RUNGS = [(0, 2), (3, 3), (5, 4), (7, 5), (8, 6), (9, 7), (10, 8), (11, 9), (12, 10)]
# Animal-structure count is kept at or below the hand count at every rung
# (Larko's own realistic_opponent.py rungs keep this same ratio -- e.g. day6
# hands=8/animals=10) -- the raw real-data SHEEP ramp (2->19 by day 12-13)
# initially caused the SAME execution engine to schedule far more PASTURE
# BUILDs than available hands could service, starving FEED and triggering
# the engine's own "2 consecutive unfed days -> animal escapes" mechanic
# (vendor_kaggriculture.kaggriculture::_daily_refresh_animals, confirmed by
# direct trace -- see the Reconstruction Note in the Phase 34 report) --
# a real capital-destroying cascade, not a false economy. Slowing the ramp
# to stay within serviceable capacity reaches the SAME real end-state
# (COW2/SHEEP19/GOOSE5 by day ~14) without that collapse.
_ANIMAL_SPECIES_RUNGS = [
    (0, {}), (2, {"COW": 2, "SHEEP": 2}), (5, {"COW": 2, "SHEEP": 4}), (7, {"COW": 2, "SHEEP": 6}),
    (9, {"COW": 2, "SHEEP": 8}), (10, {"COW": 2, "SHEEP": 10}), (11, {"COW": 2, "SHEEP": 12}),
    (12, {"COW": 2, "SHEEP": 14, "GOOSE": 2}), (13, {"COW": 2, "SHEEP": 16, "GOOSE": 3}),
    (14, {"COW": 2, "SHEEP": 19, "GOOSE": 5}), (18, {"COW": 2, "SHEEP": 19, "GOOSE": 3}),
]
_CROP_TILE_RUNGS = [
    (0, 8), (8, 13), (9, 14), (10, 13), (11, 20), (12, 20), (13, 25), (14, 27),
    (18, 21), (19, 20), (20, 13), (21, 7),
]
_CROP_SCHEDULE = [
    (0, {"MELON": 1.0}),
    (11, {"STRAWBERRY": 0.05, "MELON": 0.95}),
    (13, {"STRAWBERRY": 0.24, "MELON": 0.76}),
    (15, {"STRAWBERRY": 0.30, "MELON": 0.70}),
    (18, {"STRAWBERRY": 0.33, "MELON": 0.67}),
    (21, {"STRAWBERRY": 1.0}),  # MELON dropped entirely, matching the real data
]
# NOTE: unlike Phase 21's realistic_opponent.py, there is NO liquidation-day
# wind-down here -- the real Sundar data shows crop_tile_target holding at 7
# (all STRAWBERRY) from day 21 straight through day 29, never dropping to 0.


def _rung_value(day, rungs):
    value = rungs[0][1]
    for threshold_day, v in rungs:
        if day >= threshold_day:
            value = v
        else:
            break
    return value


def sundar_archetype_targets(day, obs, opponent_history=None):
    crop_fractions = _CROP_SCHEDULE[0][1]
    for threshold_day, fractions in _CROP_SCHEDULE:
        if day >= threshold_day:
            crop_fractions = fractions
        else:
            break
    return {
        "n_hands": _rung_value(day, _HANDS_RUNGS),
        "land_quadrants": _rung_value(day, _LAND_RUNGS),
        "animals": dict(_rung_value(day, _ANIMAL_SPECIES_RUNGS)),
        "crop_tile_target": _rung_value(day, _CROP_TILE_RUNGS),
        "crop_fractions": dict(crop_fractions),
    }


def make_sundar_archetype():
    return make_execution_agent(sundar_archetype_targets)
