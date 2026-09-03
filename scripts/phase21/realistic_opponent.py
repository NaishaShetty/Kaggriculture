"""
Phase 21 Step 0: a synthetic, real-data-grounded "realistic opponent" agent
-- a stand-in for actual current top-ladder play, to replace Submission C/E
as this project's validation bar (both confirmed weak relative to the real
ladder: C/E's own head-to-head numbers, ~$21k-22k, vs. real top players'
$116k-183k).

Built directly from `results/phase19/fresh_ladder/105027448.json` (Dmitry
Larko vs. Knight of Favonius), extracted via
`agents/phase6/replay_forensics.py::extract_episode_timelines` (reused, not
rebuilt) -- FULL day-by-day trajectory (all 30 days, not just the 7 snapshot
days Phase 19 used), reproduced verbatim below as a day-indexed lookup table.
Milan Leonard's independent trajectory (episode 105012251) corroborates the
same overall shape (land 1->2->3 by day 11, hands ramping to ~10-12, MELON
dropped by day 10, WHEAT overtaking STRAWBERRY from day ~21, full
liquidation by day 29) closely enough that Larko's own numbers were used
directly rather than averaging two independently-shaped curves.

This does NOT claim to replicate Larko's actual (unknown) code -- it is a
day-indexed target table (land/hands/animal counts, crop-tile-fraction
schedule) fed through agents/phase21/execution.py's generic execution layer,
the same architecture pattern this project has used since Phase 15 for
target-driven agents, applied here to real DATA rather than a design
hypothesis.

Real observed trajectory (episode 105027448, Dmitry Larko's own side, full
30-day extraction -- see results/phase21/larko_full_trajectory.json):
  day  0: hands=5 land=1 tiles=18 (WHEAT6/MELON12)      animals=4  (COW2/SHEEP2)
  day  5: hands=5 land=1 tiles=19 (WHEAT3/STRAW4/MELON12) animals=6  (COW4/SHEEP2)
  day  6: hands=8 land=2 tiles=31 (WHEAT7/STRAW12/MELON12) animals=8  (COW6/SHEEP2)
  day 10: hands=11 land=2 tiles=32 (WHEAT12/STRAW20, MELON DROPPED) animals=16 (COW9/SHEEP7)
  day 11: hands=11 land=3 tiles=53 (WHEAT20/STRAW33)     animals=17 (COW9/SHEEP8)
  day 15: hands=11 land=3 tiles=58 (WHEAT25/STRAW33)     animals=17 (unchanged from here)
  day 21: tiles=58 (WHEAT30/STRAW28) -- WHEAT starts overtaking
  day 25: tiles=58 (WHEAT39/CARROT6/STRAW13) -- WHEAT dominant
  day 27: tiles=49 -- liquidation begins
  day 29: tiles=0 -- fully liquidated, final $183,147
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.execution import make_execution_agent  # noqa: E402

# Day-indexed rungs, read directly off the full extraction (not interpolated
# guesses -- see the module docstring's table). Each rung is (day, value);
# the value holds until the next rung's day.
_LAND_RUNGS = [(0, 1), (6, 2), (11, 3)]
_HANDS_RUNGS = [(0, 5), (6, 8), (10, 11)]
_ANIMALS_RUNGS = [(0, 4), (2, 5), (3, 6), (4, 7), (5, 8), (6, 10), (8, 13), (9, 13), (10, 16), (11, 17)]
_ANIMAL_SPECIES_RUNGS = [
    (0, {"COW": 2, "SHEEP": 2}), (2, {"COW": 3, "SHEEP": 2}), (4, {"COW": 4, "SHEEP": 2}),
    (6, {"COW": 6, "SHEEP": 2}), (7, {"COW": 8, "SHEEP": 2}), (8, {"COW": 9, "SHEEP": 4}),
    (10, {"COW": 9, "SHEEP": 7}), (11, {"COW": 9, "SHEEP": 8}),
]
_CROP_TILE_RUNGS = [(0, 18), (6, 31), (7, 37), (10, 32), (11, 53), (15, 58)]

# Crop-fraction schedule -- read off the same table (fractions of the crop-tile
# pool at each rung's day). MELON is present days 0-9, dropped entirely by
# day 10; WHEAT/STRAWBERRY co-dominant days 11-20; WHEAT overtakes 21-26;
# liquidation (no new planting) from day 27.
_CROP_SCHEDULE = [
    (0, {"WHEAT": 0.35, "MELON": 0.65}),
    (5, {"WHEAT": 0.16, "STRAWBERRY": 0.21, "MELON": 0.63}),
    (6, {"WHEAT": 0.23, "STRAWBERRY": 0.39, "MELON": 0.38}),
    (10, {"WHEAT": 0.38, "STRAWBERRY": 0.62}),
    (11, {"WHEAT": 0.38, "STRAWBERRY": 0.62}),
    (15, {"WHEAT": 0.43, "STRAWBERRY": 0.57}),
    (21, {"WHEAT": 0.52, "STRAWBERRY": 0.48}),
    (23, {"WHEAT": 0.66, "STRAWBERRY": 0.34}),
    (25, {"WHEAT": 0.67, "CARROT": 0.10, "STRAWBERRY": 0.23}),
]

LIQUIDATION_START_DAY = 27  # observed: tiles start dropping (58 -> 49) exactly here
DIG_ONGOING_CROPS_DAY = 28  # observed: tiles 49 -> 24 -> 0 over the last 2 days


def _rung_value(day, rungs):
    value = rungs[0][1]
    for threshold_day, v in rungs:
        if day >= threshold_day:
            value = v
        else:
            break
    return value


def realistic_opponent_targets(day, obs, opponent_history=None):
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


def make_realistic_opponent():
    """Endgame liquidation (stop planting, clear ongoing crops) is handled by
    wrapping the crop-tile target down to 0 from LIQUIDATION_START_DAY --
    simpler than a dedicated DIG mechanic since this agent's job is to be a
    realistic BENCHMARK, not a submission candidate; letting existing
    non-ongoing crops (WHEAT/MELON) finish naturally and just stop the
    STRAWBERRY tile pool from being replenished is enough to reproduce the
    observed wind-down shape closely."""
    def targets_with_liquidation(day, obs, opponent_history):
        t = realistic_opponent_targets(day, obs, opponent_history)
        if day >= LIQUIDATION_START_DAY:
            t = dict(t)
            t["crop_tile_target"] = 0
        if day >= DIG_ONGOING_CROPS_DAY:
            t = dict(t)
            t["digging_ongoing"] = True
        return t
    return make_execution_agent(targets_with_liquidation)
