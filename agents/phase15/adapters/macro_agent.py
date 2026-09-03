"""
Phase 15 adapter: wires the macro controller (agents/phase15/macro_controller.py),
the generalized execution layer (agents/phase15/execution.py, reusing Phase 11's
bounded-tile-pool approach + Phase 13's parallel-fetch fix), and the sell-timing
layer (agents/phase15/sell_timing.py, using the verified
agents/phase4/market_model.py simulator) into one agent, following this
project's existing adapter shape (see agents/phase3_8/adapters/
competitive_v3_agent.py for the pattern -- read-only reference, NOT imported;
this is a clean, separate agent, per this phase's explicit scope).

PHASE 16 UPDATE: `sell_timing_enabled` now defaults to False. Re-tested on top
of Phase 16's execution fixes across 8 seeds: WITHOUT sell-timing mean
$44,440 vs. WITH sell-timing mean $41,035 -- the layer is now a measured net
NEGATIVE (-7.7%), not the "wash" Phase 15 found on a smaller 4-seed sample.
Per this project's standing preference for the simpler mechanism when a more
complex one isn't earning its keep, it is disabled by default; the module
itself (agents/phase15/sell_timing.py) is left in place, unmodified, and can
still be enabled explicitly for further investigation. See
results/phase16/PHASE16_EXECUTION_EFFICIENCY_REPORT.md Section 6 for the full
re-evaluation.

This is a NEW, additive agent. Nothing in agents/phase3_8/, agents/phase3_5/,
agents/phase3_3/, agents/phase2_6/, agents/phase2_3/common.py,
agents/phase2_4/common.py, or main.py is imported, modified, or depended on.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from agents.phase15.macro_controller import compute_targets  # noqa: E402
from agents.phase15.execution import make_execution_agent  # noqa: E402
from agents.phase15.sell_timing import apply_sell_timing  # noqa: E402


def make_macro_agent(sell_timing_enabled=False, trace_path=None):
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_execution_agent(compute_targets)
    state_ref = {"sell_timing_applications": 0}

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        action = execution_agent(obs)

        if sell_timing_enabled:
            player = obs["player"]
            shed = obs["private"].get("shed", {})
            market_inventory = obs.get("market", {}).get("inventory", {})
            day = obs["day"]
            new_market = apply_sell_timing(action.get("market", []), shed, market_inventory, day)
            if new_market != action.get("market", []):
                state_ref["sell_timing_applications"] += 1
            action = dict(action)
            action["market"] = new_market

        return action

    agent._opponent_logger = opponent_logger
    agent._state_ref = state_ref
    return agent
