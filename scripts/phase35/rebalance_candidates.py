"""
Phase 35 Step 3: 2-3 candidate rebalanced target sets, informed by (not
copied wholesale from) Sundar's and Crop Dusta's real trajectories
(results/phase34/phase34_trajectory_sundar_worstloss.json,
phase34_trajectory_gold_105373474.json, phase34_trajectory_gold_105341441.json
-- full day-by-day dumps already extracted in Phase 34, reused here).

agents/phase21/portfolio.py::portfolio_targets is imported UNCHANGED --
every candidate below WRAPS it, overriding only crop_tile_target and/or
animals and/or land_quadrants via new rung tables. n_hands (_HANDS_RUNGS) is
NEVER touched by any candidate, per this phase's explicit constraint -- the
whole point is reallocating existing, already-paid-for capacity, not adding
more of it.

Real data that informs these candidates (summarized from the full
day-by-day dumps, confirmed in Phase 34):
  - Sundar (real, beat Submission H $97,246 vs $30,699): land 3->4 at day 15,
    hands never exceed 10 (LESS than our 11), animals ramp to COW2/SHEEP19/
    GOOSE3-5 (~24-26 total) by day ~14, crop tiles correspondingly LOW (peak
    27, cut to just 7 from day 20 onward).
  - Crop Dusta (real gold-tier, rank #1): land stays at 3 (like us), hands
    11-12 (close to our 11), animals COW9-13/SHEEP2-4/GOOSE0-2 (13-17 total,
    COW-heavier than SHEEP-heavier), crop tiles stay HIGH (55-59, similar to
    or higher than our own 58) -- Crop Dusta does NOT trade crop tiles for
    animals the way Sundar does.

Phase 35 Step 2's idle-capacity check found: capping crop_tile_target at 30
(vs. the shipped 58) TRIPLES idle worker-turn fraction (7.1% -> 18.8%) while
NOT hurting (in fact slightly helping, +8.5%) isolated economy even with NO
animal-target change at all -- confirming real spare capacity exists to
reallocate before any animal increase is even added.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402

# --- Candidate A: SHEEP-heavy (Sundar-informed), same land(3)/hands(11) ---
# crop_tile_target ramp shape mirrors the original's own proportions, scaled
# down to the Step 2 idle-check's near-best point (final rung 32, close to
# the tested cap=30). Animal target roughly doubles SHEEP (COW ramp
# untouched) -- informed by Sundar's SHEEP-heavy real ratio, but far short of
# Sundar's own 19 (this agent's execution layer/tile footprint differs, so
# the real number is a data point to test toward, not to copy).
_CROP_TILE_RUNGS_A = [(0, 10), (6, 17), (10, 18), (11, 29), (15, 32)]
_ANIMAL_SPECIES_RUNGS_A = [
    (0, {"COW": 2, "SHEEP": 2}), (4, {"COW": 4, "SHEEP": 4}), (6, {"COW": 6, "SHEEP": 6}),
    (10, {"COW": 9, "SHEEP": 12}), (11, {"COW": 9, "SHEEP": 16}),
]
# Candidate A2: same END STATE as A (COW9/SHEEP16 by day 11), but the FIRST
# attempt (A) put the entire ~$8,000 extra SHEEP capital demand on the same
# day-0-11 window the original agent's own crop/land/hire ramp already needs
# -- direct trace (Phase 35 report Section 5) found this collapses cash
# (final money -77% to -88% on all 3 original candidates, idle_action_fraction
# actually RISING to 20-25%, the cash-danger-throttle oscillation signature,
# not a worker-turn shortage). A2 staggers the SAME extra SHEEP count later
# (reached by day 20 instead of day 11), letting the reduced-but-nonzero
# crop revenue accumulate capital before the animal purchases are due.
_ANIMAL_SPECIES_RUNGS_A2 = [
    (0, {"COW": 2, "SHEEP": 2}), (6, {"COW": 6, "SHEEP": 4}), (10, {"COW": 9, "SHEEP": 8}),
    (14, {"COW": 9, "SHEEP": 11}), (17, {"COW": 9, "SHEEP": 14}), (20, {"COW": 9, "SHEEP": 16}),
]

# --- Candidate B: A + the 4th land quadrant, NO hands change ---
_LAND_RUNGS_B = [(0, 1), (6, 2), (11, 3), (18, 4)]

# --- Candidate C: COW-heavy (Crop Dusta-informed), same crop reduction as A ---
# Same total animal-count budget as Candidate A (25), but skewed toward COW
# instead of SHEEP, matching Crop Dusta's real ratio (COW9-13 > SHEEP2-4).
_ANIMAL_SPECIES_RUNGS_C = [
    (0, {"COW": 2, "SHEEP": 2}), (4, {"COW": 6, "SHEEP": 3}), (6, {"COW": 10, "SHEEP": 3}),
    (10, {"COW": 15, "SHEEP": 4}), (11, {"COW": 20, "SHEEP": 5}),
]


def _rung_value(day, rungs):
    value = rungs[0][1]
    for threshold_day, v in rungs:
        if day >= threshold_day:
            value = v
        else:
            break
    return value


def make_candidate_a_targets():
    def targets(day, obs, opponent_history=None):
        t = dict(portfolio_targets(day, obs, opponent_history))
        t["crop_tile_target"] = _rung_value(day, _CROP_TILE_RUNGS_A)
        t["animals"] = dict(_rung_value(day, _ANIMAL_SPECIES_RUNGS_A))
        return t
    return targets


def make_candidate_b_targets():
    def targets(day, obs, opponent_history=None):
        t = dict(portfolio_targets(day, obs, opponent_history))
        t["crop_tile_target"] = _rung_value(day, _CROP_TILE_RUNGS_A)
        t["animals"] = dict(_rung_value(day, _ANIMAL_SPECIES_RUNGS_A))
        t["land_quadrants"] = _rung_value(day, _LAND_RUNGS_B)
        return t
    return targets


def make_candidate_a2_targets():
    def targets(day, obs, opponent_history=None):
        t = dict(portfolio_targets(day, obs, opponent_history))
        t["crop_tile_target"] = _rung_value(day, _CROP_TILE_RUNGS_A)
        t["animals"] = dict(_rung_value(day, _ANIMAL_SPECIES_RUNGS_A2))
        return t
    return targets


def make_candidate_c_targets():
    def targets(day, obs, opponent_history=None):
        t = dict(portfolio_targets(day, obs, opponent_history))
        t["crop_tile_target"] = _rung_value(day, _CROP_TILE_RUNGS_A)
        t["animals"] = dict(_rung_value(day, _ANIMAL_SPECIES_RUNGS_C))
        return t
    return targets
