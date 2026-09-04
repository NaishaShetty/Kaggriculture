"""
Phase 37 packaging adapter for Submission I -- wires Phase 36's validated
pacer (scripts/phase21/execution.py's own primitives via
scripts/phase36/paced_execution.py::make_paced_execution_agent, which
BUY_ANIMAL-gates purchases against a cash reserve, everything else
unchanged) to agents/phase21/portfolio.py::portfolio_targets (imported
unmodified -- the SAME targets Submission H already ships: 3 land / 11
hands / 58 crop tiles / current animal ratio) and
agents/phase3/opponent_observation.py's existing telemetry, EXACTLY
mirroring agents/phase21/adapters/portfolio_agent.py::make_portfolio_agent's
own structure -- the only difference is which execution-layer factory is
wired in.

WHY THIS ADAPTER LIVES UNDER scripts/phase37/, NOT agents/phase21/adapters/:
per this phase's explicit constraint, agents/phase21/'s own files are not
modified in this phase -- packaging ships exactly what Phase 36 validated
(scripts/phase36/paced_execution.py, reused unchanged, not copied or
rewritten) rather than relocating it into agents/phase21/ as part of this
packaging step. This file is new, additive glue only -- no behavioral logic
of its own.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from scripts.phase36.paced_execution import make_paced_execution_agent  # noqa: E402


def make_paced_portfolio_agent():
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_paced_execution_agent(portfolio_targets)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    agent._opponent_logger = opponent_logger
    return agent
