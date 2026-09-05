"""
Phase 49 Step 1 packaging-shape adapter -- mirrors scripts/phase37/
paced_portfolio_agent.py's and scripts/phase46/feed_priority_portfolio_agent.py's
own structure exactly; the only difference is which execution-layer factory
is wired in (scripts/phase49/combined_execution.py instead of
scripts/phase36/paced_execution.py or scripts/phase46/feed_priority_execution.py).
agents/phase21/portfolio.py's `portfolio_targets` (imported unmodified -- the
SAME shipped targets) and agents/phase3/opponent_observation.py's telemetry
are unchanged. This is Submission I's existing crop fractions and portfolio,
with BOTH execution fixes applied and NO CARROT/TOMATO slice -- the sanity
check candidate for Step 1.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from scripts.phase49.combined_execution import make_combined_execution_agent  # noqa: E402


def make_combined_portfolio_agent():
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_combined_execution_agent(portfolio_targets)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    agent._opponent_logger = opponent_logger
    return agent
