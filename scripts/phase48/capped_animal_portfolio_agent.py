"""
Phase 48 Part C packaging-style adapter -- mirrors
scripts/phase46/feed_priority_portfolio_agent.py's own structure exactly; the
only difference is the target_fn wired in (the capped-animal wrapper from
scripts/phase48/capped_animal_portfolio.py instead of
agents/phase21/portfolio.py::portfolio_targets directly -- which the wrapper
itself still calls, unmodified, underneath).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase46.feed_priority_execution import make_feed_priority_execution_agent  # noqa: E402
from scripts.phase48.capped_animal_portfolio import make_capped_animal_target_fn  # noqa: E402

CAP_TOTAL = 8  # grounded in scripts/phase48/animal_ceiling_probe.py's own steady-state measurement


def make_capped_animal_portfolio_agent(cap_total=CAP_TOTAL):
    opponent_logger = OpponentObservationLogger()
    target_fn = make_capped_animal_target_fn(cap_total=cap_total)
    execution_agent = make_feed_priority_execution_agent(target_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    agent._opponent_logger = opponent_logger
    return agent
