"""
Phase 45: Submission I's own shipped targets (agents/phase21/portfolio.py::
portfolio_targets, imported unchanged) run through the new BUY_SEED-paced
execution layer (scripts/phase45/seed_paced_execution.py) instead of Phase
36's original pacer. Mirrors scripts/phase37/paced_portfolio_agent.py's
structure exactly -- the only difference is which execution-layer factory is
wired in.

Used as the "ours, with the new pacer" side of Part A's validation, and as
the base execution layer for the re-tested CARROT/TOMATO slice (Part A Step
2).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from scripts.phase45.seed_paced_execution import make_seed_paced_execution_agent  # noqa: E402


def make_seed_paced_portfolio_agent():
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_seed_paced_execution_agent(portfolio_targets)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    agent._opponent_logger = opponent_logger
    return agent
