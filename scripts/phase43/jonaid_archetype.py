"""
Phase 43 Part A, Step 3: a second, independently-reconstructed 4th-quadrant
archetype, built the exact same way (day-indexed rung table read directly
off a real 30-day extraction, fed through
`agents/phase21/execution.py::make_execution_agent`, imported unmodified)
as `scripts/phase34/sundar_archetype.py` -- reused as a PATTERN, not copied
code -- so this benchmark isn't resting on Sundar alone (which, confirmed
in this phase's own Step 1, still fails its own isolation sanity check, the
same failure Phase 34 already found and never fixed -- see the Phase 43
report Section 1 for that confirmation).

Real observed opponent (Jonaid, episode 105405216, PUBLIC state only --
agents/phase6/replay_forensics.py::extract_episode_timelines, our_name=
"shettynaisha" so Jonaid is read strictly as the opponent/public side, per
this project's standing observability discipline):
  day  0: hands=9  land=1 crops=WHEAT4/CARROT6/MELON10           animals=SHEEP1/GOOSE2/COW1 (4)
  day  6: hands=7  land=2 crops=WHEAT8/MELON13/STRAW4/CARROT4/TOMATO1 (30) animals=4
  day 10: hands=12 land=3 crops=MELON3/STRAW8/CARROT6/TOMATO3 (20) animals=SHEEP3/COW3/GOOSE4 (10)
  day 13: hands=12 land=4 (4th QUADRANT BOUGHT) crops=STRAW10/TOMATO4/CARROT10/MELON5/WHEAT5 (34) animals=SHEEP4/COW6/GOOSE7 (17)
  day 18: hands=12 land=4 crops=STRAW10/TOMATO3/MELON5 (18)      animals=SHEEP4/COW8/GOOSE10 (22)
  day 21: hands=12 land=4 crops=STRAW7/TOMATO1/CARROT1 (9)       animals=SHEEP4/COW10/GOOSE10 (24, sustained through day 29)
  day 29: hands=11 land=4 crops={} (fully liquidated)            animals=24, final money $80,988

This does NOT claim to replicate Jonaid's actual (unknown) code -- same
caveat every prior real-data reconstruction in this project carries
(Phase 21's realistic_opponent.py, Phase 34's sundar_archetype.py).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.execution import make_execution_agent  # noqa: E402

_LAND_RUNGS = [(0, 1), (6, 2), (10, 3), (13, 4)]
_HANDS_RUNGS = [(0, 5), (2, 7), (3, 9), (6, 10), (10, 12)]
_ANIMAL_SPECIES_RUNGS = [
    (0, {"COW": 1, "SHEEP": 1, "GOOSE": 2}), (9, {"COW": 2, "SHEEP": 2, "GOOSE": 4}),
    (12, {"COW": 6, "SHEEP": 4, "GOOSE": 7}), (15, {"COW": 6, "SHEEP": 4, "GOOSE": 10}),
    (18, {"COW": 8, "SHEEP": 4, "GOOSE": 10}), (21, {"COW": 10, "SHEEP": 4, "GOOSE": 10}),
]
_CROP_TILE_RUNGS = [
    (0, 20), (6, 27), (10, 22), (11, 32), (13, 32), (16, 21), (19, 16),
    (21, 9), (23, 6), (26, 10), (28, 3), (29, 0),
]
_CROP_SCHEDULE = [
    (0, {"MELON": 0.50, "WHEAT": 0.20, "CARROT": 0.30}),
    (6, {"MELON": 0.40, "WHEAT": 0.25, "STRAWBERRY": 0.15, "CARROT": 0.15, "TOMATO": 0.05}),
    (10, {"STRAWBERRY": 0.30, "MELON": 0.25, "CARROT": 0.30, "TOMATO": 0.10, "WHEAT": 0.05}),
    (13, {"STRAWBERRY": 0.35, "TOMATO": 0.15, "CARROT": 0.30, "MELON": 0.15, "WHEAT": 0.05}),
    (17, {"STRAWBERRY": 0.60, "TOMATO": 0.25, "MELON": 0.15}),
    (21, {"STRAWBERRY": 0.85, "TOMATO": 0.15}),
    (25, {"WHEAT": 0.50, "CARROT": 0.50}),  # past STRAWBERRY/TOMATO's own cutoffs (19/21); WHEAT/CARROT still plantable to day 27
]


def _rung_value(day, rungs):
    value = rungs[0][1]
    for threshold_day, v in rungs:
        if day >= threshold_day:
            value = v
        else:
            break
    return value


def jonaid_archetype_targets(day, obs, opponent_history=None):
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


def make_jonaid_archetype():
    return make_execution_agent(jonaid_archetype_targets)
