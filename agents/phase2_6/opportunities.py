"""
Phase 2.6 candidate-opportunity generator. Operates at the STRATEGIC level
(what portfolio/policy configuration should the farm run), not the tactical
per-tile level -- tactical execution (movement, watering, harvesting order)
is delegated to the already-validated Phase 2.4 task scheduler
(agents/phase2_4/common.py), per the brief section 19's explicit instruction
not to make the planner responsible for low-level movement logic.

Each candidate is a dict:
  {"kind": ..., "lane": ..., "params": {...}, "direct_cost": $, "description": "..."}

`lane` groups mutually-substitutable candidates for opportunity-cost
comparison (decisions.py compares within and across lanes, never silently
assuming independence).
"""
from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS, LAND_PRICES

MAX_HANDS_CONSIDERED = 4          # F1/F2 only calibrated hand counts 0-4; do not generate beyond calibration
MAX_LAND_QUADRANTS = len(LAND_PRICES) + 1  # NW (always owned) + 3 purchasable
CANDIDATE_PORTFOLIOS = {
    # name -> crop_fractions; kept small and enumerable (Phase 2.5's crop calibration is
    # solid for MELON/WHEAT/STRAWBERRY revenue-per-tile-day, per Phase 2.2 section 6) --
    # NOT a continuous optimizer, a deliberately small, evidence-backed candidate set.
    "melon_solo": {"MELON": 1.0},
    "melon_strawberry": {"MELON": 0.5, "STRAWBERRY": 0.5},
    "wheat_solo": {"WHEAT": 1.0},
}
CANDIDATE_ANIMALS = ["COW", "SHEEP", "GOOSE"]  # F5 ranking order (best first), not arbitrary
SELL_POLICY_CANDIDATES = ["passive", "threshold", "threshold_batch"]  # excludes pure "batch" (F16 risk)


def generate_candidates(state, current_config):
    """current_config: the planner's currently-committed
    {crops, n_hands, land_quadrants, animals, sell_policy_mode} -- candidates
    are proposed CHANGES relative to this, not absolute restatements."""
    candidates = []

    # --- labor lane ---
    # IMPORTANT: hands are cleared every day by design (VERIFIED,
    # kaggriculture.py::_end_of_day) -- `state.n_hands` (freshly adapted from
    # `obs` at this exact day-boundary planning moment) is ALWAYS 0 here,
    # regardless of any previously-committed target. An earlier planner
    # version generated candidates off `state.n_hands` directly and
    # therefore proposed "hire hand #1" every single day forever, never
    # progressing to hand #2/#3 -- a real bug, caught by the smoke test's
    # trace output (the same n_hands, same candidate, every cycle), fixed by
    # reading the planner's own COMMITTED target from `current_config`
    # instead of the momentarily-reset observed value.
    committed_hands = current_config.get("n_hands", 0)
    if committed_hands < MAX_HANDS_CONSIDERED and state.cash >= state.hire_cost_next:
        candidates.append({
            "kind": "HIRE_HAND", "lane": "labor",
            "params": {"n_hands": committed_hands + 1},
            "direct_cost": state.hire_cost_next,
            "description": f"hire hand #{committed_hands + 1} (recurring daily cost ${state.hire_cost_next})",
        })
    if committed_hands > 0:
        candidates.append({
            "kind": "REDUCE_HANDS", "lane": "labor",
            "params": {"n_hands": committed_hands - 1},
            "direct_cost": 0.0,
            "description": f"stop hiring back down to {committed_hands - 1} hands (saves recurring hire cost)",
        })

    # --- land lane ---
    n_extra_owned = state.land_quadrants_owned - 1
    if n_extra_owned < len(LAND_PRICES):
        cost = LAND_PRICES[n_extra_owned]
        if state.cash >= cost:
            candidates.append({
                "kind": "BUY_LAND", "lane": "land",
                "params": {"land_quadrants": n_extra_owned + 1},
                "direct_cost": cost,
                "description": f"buy quadrant #{n_extra_owned + 1} for ${cost}",
            })

    # --- animal lane ---
    # Cap TOTAL animals (across every species) at 2: the only multi-animal
    # configuration ever jointly validated is Phase 2.3 F13's GOOSE+COW pair
    # (results/phase2_3/knowledge_base.json). F5/F6/F7 each individually
    # tested exactly ONE animal alongside a crop -- three simultaneous
    # species was never evidence-tested and a smoke-test run of an earlier
    # planner version bought COW+SHEEP+GOOSE together on day 0, over-
    # committing labor no experiment ever validated jointly. Documented as
    # a real planner-v1 finding, not silently patched away -- see the
    # Phase 2.6 report's failure-analysis section.
    total_animals_committed = sum((current_config.get("animals") or {}).values())
    if total_animals_committed < 2:
        for animal in CANDIDATE_ANIMALS:
            current_n = current_config.get("animals", {}).get(animal, 0)
            cost = ANIMALS[animal]["cost"]
            if state.cash >= cost and current_n < 1:  # 1/species, within the 2-total cap
                candidates.append({
                    "kind": "BUY_ANIMAL", "lane": f"animal_{animal}",
                    "params": {"animal": animal, "n": current_n + 1},
                    "direct_cost": cost,
                    "description": f"buy a {animal} (#{current_n + 1}) for ${cost}",
                })

    # --- crop portfolio lane ---
    # Only generated on day 0 (initial choice) or if the CURRENT portfolio has
    # never actually been set -- switching portfolios mid-game is NOT modeled
    # as free by economic_model.crop_production_value (it evaluates each
    # portfolio from a fresh planting, not accounting for abandoning an
    # already-growing crop's sunk seed cost/tile-days). An earlier planner
    # version generated a switch candidate every day whenever any alternative
    # portfolio's (independently-evaluated) estimate edged out the current
    # one, causing daily thrashing between near-tied portfolios and a
    # measured near-total loss of production value -- a real Phase 2.6
    # finding (documented in the report's failure analysis), fixed here by
    # only ever proposing the initial portfolio choice once, since
    # economic_model v0.1 has no switching-cost function to evaluate a
    # LATER switch honestly.
    current_portfolio_name = current_config.get("_portfolio_name")
    if current_portfolio_name is None:
        for name, fractions in CANDIDATE_PORTFOLIOS.items():
            candidates.append({
                "kind": "SWITCH_PORTFOLIO", "lane": "crop_portfolio",
                "params": {"crops": fractions, "_portfolio_name": name},
                "direct_cost": 0.0,
                "description": f"initial crop portfolio choice: {name} ({fractions})",
            })

    # --- selling-policy lane (operationalizes Phase 2.5 open hypothesis H2) ---
    current_sell_mode = current_config.get("sell_policy", {}).get("mode", "passive")
    n_active_resource_types = (len(current_config.get("crops") or {}) +
                                len(current_config.get("animals") or {}))
    for mode in SELL_POLICY_CANDIDATES:
        if mode == current_sell_mode:
            continue
        candidates.append({
            "kind": "SWITCH_SELL_POLICY", "lane": "sell_policy",
            "params": {"mode": mode},
            "direct_cost": 0.0,
            "description": f"switch selling policy to {mode} (currently {current_sell_mode}, "
                            f"portfolio has {n_active_resource_types} active resource types)",
        })

    return candidates
