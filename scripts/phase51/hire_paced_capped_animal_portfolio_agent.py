"""
Phase 51 sanity-check adapter -- mirrors
scripts/phase48/capped_animal_portfolio_agent.py's own structure exactly; the
only difference is which execution-layer factory is wired in
(scripts/phase51/hire_paced_execution.py instead of
scripts/phase46/feed_priority_execution.py). Composes Submission K's own
shipped pieces (Phase 48's capped-animal target wrapper, cap_total=8,
wrapping agents/phase21/portfolio.py::portfolio_targets unmodified) with the
NEW HIRE pacer, on Submission K's EXISTING portfolio -- no 4th quadrant, no
new crop. This is the object under test for the mandatory sanity check
(step 2 of this phase's brief): does adding the HIRE pacer regress
Submission K's own shipped numbers?
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase51.hire_paced_execution import make_hire_paced_execution_agent  # noqa: E402
from scripts.phase48.capped_animal_portfolio import make_capped_animal_target_fn  # noqa: E402

CAP_TOTAL = 8  # unchanged from Phase 48 -- Submission K's own shipped cap


def make_hire_paced_capped_animal_portfolio_agent(cap_total=CAP_TOTAL):
    opponent_logger = OpponentObservationLogger()
    target_fn = make_capped_animal_target_fn(cap_total=cap_total)
    execution_agent = make_hire_paced_execution_agent(target_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    agent._opponent_logger = opponent_logger
    return agent
