"""
Phase 2.6 baseline wrappers (brief section 33.12) -- a common interface for
the 3 comparison agents, none of which are modified from their frozen form.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase2_3.common import make_agent as make_agent_23  # noqa: E402
from agents.phase2_4.common import make_agent as make_agent_24  # noqa: E402

# Phase 2.3 F13's winning integrated config (results/phase2_3/knowledge_base.json, finding F13;
# same config used in Phase 2.4's c6_inventory_bottleneck/inv_high and Stage F head-to-head).
INTEGRATED_CONFIG = {
    "crops": {"MELON": 0.5, "STRAWBERRY": 0.5}, "n_hands": 4, "land_quadrants": 1, "land_buy_day": 0,
    "animals": {"GOOSE": 1, "COW": 1}, "animal_buy_day": 0,
}

# Phase 2.4's best-found market-aware policy for the SAME integrated config
# (results/phase2_4/knowledge_base.json, Stage F head-to-head cell
# c1_integrated_inv_high_threshold_batch).
BEST_MARKET_AWARE_SELL_POLICY = {"mode": "threshold_batch", "threshold_frac": 1.1, "batch_interval_days": 7}


def wheat_patroller():
    """The frozen control baseline -- never modified. Passed through as the
    file path string, exactly as every prior phase's harness does."""
    return "agents/baseline_agent.py"


def phase2_3_integrated():
    """Phase 2.3's strongest validated integrated strategy, passive selling."""
    return make_agent_23(**INTEGRATED_CONFIG)


def phase2_4_best():
    """Phase 2.4's best-found market-aware variant of the same config."""
    return make_agent_24(**INTEGRATED_CONFIG, sell_policy=BEST_MARKET_AWARE_SELL_POLICY)


BASELINES = {
    "wheat_patroller": wheat_patroller,
    "phase2_3_integrated": phase2_3_integrated,
    "phase2_4_best": phase2_4_best,
}
