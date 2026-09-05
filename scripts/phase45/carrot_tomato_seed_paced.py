"""
Phase 45 Part A, Step 2: re-test Phase 42's CARROT/TOMATO slice (target-
fraction design reused UNCHANGED from scripts/phase42/carrot_tomato_portfolio
.py::make_slice_target_fn) through the NEW BUY_SEED-paced execution layer
(scripts/phase45/seed_paced_execution.py), active from DAY 0 -- the exact
naive configuration Phase 42 found severely harmful (-37.4%) under the OLD,
unpaced BUY_SEED logic, because Phase 42's own diagnosis was that the harm
was a cash-flow collision (BUY_SEED had zero reserve), not a market-glut
problem. If the diagnosis is right, pacing BUY_SEED should let day-0-active
CARROT/TOMATO through without the collision.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase42.carrot_tomato_portfolio import make_slice_target_fn  # noqa: E402
from scripts.phase45.seed_paced_execution import make_seed_paced_execution_agent  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402

CARROT_TILES = 6
TOMATO_TILES = 2
SLICE_START_DAY = 0  # day-0-active, per this phase's brief -- the config Phase 42 found harmful pre-pacer


def make_carrot_tomato_seed_paced_agent(carrot_tiles=CARROT_TILES, tomato_tiles=TOMATO_TILES,
                                         slice_start_day=SLICE_START_DAY):
    opponent_logger = OpponentObservationLogger()
    target_fn = make_slice_target_fn(carrot_tiles=carrot_tiles, tomato_tiles=tomato_tiles,
                                      slice_start_day=slice_start_day)
    execution_agent = make_seed_paced_execution_agent(target_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    agent._opponent_logger = opponent_logger
    return agent
