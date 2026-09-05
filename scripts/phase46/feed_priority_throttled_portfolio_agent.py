"""
Phase 46 Part C packaging adapter -- mirrors scripts/phase46/feed_priority_portfolio_agent.py
and scripts/phase37/paced_portfolio_agent.py's own structure; wires
scripts/phase46/feed_priority_throttled_execution.py (Part B's FEED
reprioritization plus Part C's capacity-aware BUY_ANIMAL throttle) to
agents/phase21/portfolio.py::portfolio_targets (imported unmodified).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from scripts.phase46.feed_priority_throttled_execution import make_feed_priority_throttled_execution_agent  # noqa: E402


def make_feed_priority_throttled_portfolio_agent():
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_feed_priority_throttled_execution_agent(portfolio_targets)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    agent._opponent_logger = opponent_logger
    return agent
