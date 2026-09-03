"""
Phase 21 adapter: wires the portfolio controller (agents/phase21/portfolio.py)
to agents/phase21/execution.py's execution layer, using
agents/phase3/opponent_observation.py's existing telemetry (reused, not
re-derived) to feed the controller's opponent-aware STRAWBERRY-share check.

Clean, from-scratch agent -- does not import from agents/phase15/ (Submission
G's shipped lineage) or any other frozen file, per this phase's explicit scope.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from agents.phase21.execution import make_execution_agent  # noqa: E402


def make_portfolio_agent():
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_execution_agent(portfolio_targets)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    agent._opponent_logger = opponent_logger
    return agent
