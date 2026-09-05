"""
Phase 45 Part B: opponent-aware portfolio steering.

Wraps agents/phase21/portfolio.py::portfolio_targets (imported UNCHANGED) --
this is a phase45-local decorator around its OUTPUT, not a modification of
the function or its file. When the opponent's own PUBLIC crop-tile footprint
(read via agents/phase3/opponent_observation.py::OpponentObservationLogger,
already-built telemetry, extended at the CALL SITE only -- this module reads
nothing beyond what that logger already exposes as
`visible_crop_tile_counts`) shows a hard commitment to one of the two
glut-prone crops docs/FRESH_STRATEGY.md's table identifies as harshest under
two-producer volume (STRAWBERRY: `linear`, above_target=1.60; MELON: `sq`,
above_target=3.60 -- both collapse to the $1 price floor under real combined
selling pace, unlike WHEAT's flat `log` curve), a BOUNDED fraction of our OWN
crop-fraction allocation for that SAME crop is shifted to WHEAT instead --
"shift toward the glut-resistant backbone" rather than "double down on the
same crop the opponent is already piling into."

WHY THIS IS DIFFERENT FROM THE DORMANT MECHANISM ALREADY IN
agents/phase21/portfolio.py (`OPPONENT_STRAWBERRY_DOMINANCE_THRESHOLD = 1.1`,
deliberately unreachable, its own docstring explaining Phase 24 found
STRAWBERRY doesn't actually crash at these two agents' real combined
production/selling pace): that mechanism is left dormant, not deleted, on
purpose -- this phase's own brief asks for exactly this shape of lever to be
built and VALIDATED FRESH against three real opponents (Submission G,
Submission C, the Jonaid archetype), not assumed to repeat Phase 24's
specific finding. Two differences from the dormant version, both real: (1)
this fires on an ABSOLUTE opponent tile-count threshold, not a SHARE-of-their-
own-footprint ratio >1.1 (mathematically unreachable -- a footprint can't be
>110% one crop); (2) this ALSO covers MELON (the dormant mechanism only ever
covered STRAWBERRY), a crop portfolio_targets never revisits after day 8
regardless of opponent behavior today.

Sticky-tile discipline preserved by construction: crop_fractions only govern
`bounded_multi_crop_tile_pool_assignment`'s fill of VACANT (NEW/unplanted)
tiles -- that function's own STICKY rule (already shipped, unmodified) never
reassigns an already-growing tile no matter what fractions this wrapper
produces. This module changes NOTHING about that function; it only changes
what fractions get passed into it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from scripts.phase36.paced_execution import make_paced_execution_agent  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402

# Absolute opponent tile-count threshold that counts as a "hard commitment"
# to a glut-prone crop -- grounded in this project's own real-data
# reconstructions (scripts/phase43/jonaid_archetype.py's real Jonaid extract
# shows STRAWBERRY at 7-10 tiles as a genuine bulk allocation, not a token
# planting; Phase 24's own trace of Submission G showed a near-total
# STRAWBERRY commitment well past this range). 8 tiles is picked as a level
# clearly past "trying the crop" and into "this is a real bet," while still
# firing early enough (typically day 8-12 in the real trajectories sampled)
# to matter before our own STRAWBERRY ramp is mostly filled.
GLUT_PRONE_CROPS = ("STRAWBERRY", "MELON")
OPPONENT_TILE_COMMIT_THRESHOLD = 8
SHIFT_FRACTION = 0.15  # bounded fraction points moved from the glut-prone crop to WHEAT, per crop, per day


def _opponent_crop_counts(opponent_history):
    if not opponent_history:
        return {}
    last = opponent_history[-1]
    return getattr(last, "visible_crop_tile_counts", None) or {}


def make_opponent_aware_target_fn(base_target_fn=portfolio_targets,
                                   commit_threshold=OPPONENT_TILE_COMMIT_THRESHOLD,
                                   shift_fraction=SHIFT_FRACTION,
                                   glut_prone_crops=GLUT_PRONE_CROPS):
    def target_fn(day, obs, opponent_history=None):
        base = base_target_fn(day, obs, opponent_history)
        t = dict(base)
        fracs = dict(base["crop_fractions"])
        opp_counts = _opponent_crop_counts(opponent_history)
        if opp_counts:
            for crop in glut_prone_crops:
                if crop not in fracs or fracs[crop] <= 0:
                    continue
                if opp_counts.get(crop, 0) >= commit_threshold:
                    shift = min(shift_fraction, fracs[crop])
                    fracs[crop] -= shift
                    fracs["WHEAT"] = fracs.get("WHEAT", 0.0) + shift
        t["crop_fractions"] = fracs
        return t

    return target_fn


def make_opponent_aware_portfolio_agent(commit_threshold=OPPONENT_TILE_COMMIT_THRESHOLD,
                                         shift_fraction=SHIFT_FRACTION):
    """Uses scripts/phase36/paced_execution.py::make_paced_execution_agent
    (imported unmodified) -- Submission I's ACTUAL shipped execution layer,
    the same one scripts/phase37/paced_portfolio_agent.py builds on -- so the
    delta measured against Submission I's shipped factory isolates ONLY the
    crop-fraction steering, not any execution-layer difference. (Phase 45
    Part A's BUY_SEED pacer is intentionally NOT layered in here -- Part A
    and Part B are independently promotable per this phase's own scope, and
    combining them is explicitly deferred unless requested.)"""
    opponent_logger = OpponentObservationLogger()
    target_fn = make_opponent_aware_target_fn(commit_threshold=commit_threshold, shift_fraction=shift_fraction)
    execution_agent = make_paced_execution_agent(target_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    agent._opponent_logger = opponent_logger
    return agent
