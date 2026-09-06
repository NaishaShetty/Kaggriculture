"""
Phase 53 agent composition -- mirrors
scripts/phase48/capped_animal_portfolio_agent.py's own structure exactly.
Composes THREE layers, all imported unmodified: Submission K's own shipped
`scripts/phase46/feed_priority_execution.py` execution layer, Submission K's
own shipped `scripts/phase48/capped_animal_portfolio.py` animal-cap wrapper
(cap_total=8, unchanged -- see fourth_quadrant_portfolio.py's own docstring
for why this phase found no reason to touch it), and this phase's NEW
`scripts/phase53/fourth_quadrant_portfolio.py` land/hands/crop-tile
extension wrapper on top. Both wrappers touch disjoint fields of
`portfolio_targets`'s own output (animals vs. land/hands/crop_tile_target),
so composing them in either order is safe -- here the animal cap is applied
first (matching Submission K's own existing chain), then the land/hands/
tile extension.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase46.feed_priority_execution import make_feed_priority_execution_agent  # noqa: E402
from scripts.phase48.capped_animal_portfolio import make_capped_animal_target_fn  # noqa: E402
from scripts.phase53.fourth_quadrant_portfolio import make_fourth_quadrant_target_fn  # noqa: E402

CAP_TOTAL = 8  # unchanged from Submission K -- see fourth_quadrant_portfolio.py docstring


def make_fourth_quadrant_portfolio_agent(cap_total=CAP_TOTAL):
    opponent_logger = OpponentObservationLogger()
    animal_capped_fn = make_capped_animal_target_fn(cap_total=cap_total)
    target_fn = make_fourth_quadrant_target_fn(base_target_fn=animal_capped_fn)
    execution_agent = make_feed_priority_execution_agent(target_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    agent._opponent_logger = opponent_logger
    return agent
