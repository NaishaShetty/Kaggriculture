"""
Phase 2.6 decision engine: compares OK-classified candidates ACROSS lanes
(labor vs. land vs. animals vs. portfolio vs. selling-policy) using each
candidate's own $/$-spent ratio as the opportunity-cost ranking basis --
not an arbitrary weight, but the model's own dollar estimates normalized by
what they cost, which is the direct definition of "which use of scarce
capital returns more per dollar." Zero-cost candidates (REDUCE_HANDS,
SWITCH_PORTFOLIO, SWITCH_SELL_POLICY) are ranked by raw net_expected_value
since there's no capital to ratio against.

Greedy knapsack over the day's cash budget: candidates are taken in
descending value-per-dollar order until cash runs out. This is deterministic
for identical (state, config) -- required by the brief section 33.7.

At most ONE candidate is selected per lane per planning cycle (a lane
represents mutually-substitutable choices -- e.g. you don't hire AND lay off
a hand in the same cycle).
"""


def select_decisions(evaluated_and_classified, state, cash_reserve_frac=0.1):
    """`evaluated_and_classified`: list of {evaluated, classification} dicts.
    Returns (selected_decisions, rejected_with_reasons)."""
    ok = [ec for ec in evaluated_and_classified if ec["classification"]["category"] == "OK"]

    # best candidate per lane, by net_expected_value (already positive for OK)
    best_per_lane = {}
    for ec in ok:
        lane = ec["evaluated"]["candidate"]["lane"]
        net = ec["evaluated"]["net_expected_value"]
        if lane not in best_per_lane or net > best_per_lane[lane]["evaluated"]["net_expected_value"]:
            best_per_lane[lane] = ec

    def value_per_dollar(ec):
        cost = ec["evaluated"]["direct_cost"]
        net = ec["evaluated"]["net_expected_value"]
        if cost <= 0:
            return float("inf") if net > 0 else 0.0
        return net / cost

    ranked = sorted(best_per_lane.values(), key=value_per_dollar, reverse=True)

    budget = state.cash * (1.0 - cash_reserve_frac)  # keep a small liquidity reserve, not "always spend everything"
    # Cross-lane cap: total animals (across every species, committed + selected
    # this cycle) must not exceed 2 -- the only jointly-validated multi-animal
    # config is Phase 2.3 F13's GOOSE+COW pair (see opportunities.py's comment
    # for why per-lane independence alone doesn't enforce this).
    animals_committed = sum((getattr(state, "animal_counts", None) or {}).values())
    animals_selected_this_cycle = 0
    selected = []
    for ec in ranked:
        cost = ec["evaluated"]["direct_cost"]
        kind = ec["evaluated"]["candidate"]["kind"]
        if kind == "BUY_ANIMAL" and animals_committed + animals_selected_this_cycle >= 2:
            ec["rejection_reason"] = "cross-lane animal cap (2 total, F13-validated) already reached this cycle"
            continue
        if cost <= budget:
            selected.append(ec)
            budget -= cost
            if kind == "BUY_ANIMAL":
                animals_selected_this_cycle += 1
        else:
            ec["rejection_reason"] = f"opportunity-cost ranked but insufficient remaining budget " \
                                      f"(needs ${cost}, ${budget:.0f} left after higher-ranked picks)"

    rejected = [ec for ec in evaluated_and_classified if ec not in ok] + \
               [ec for ec in ok if ec not in selected]

    return selected, rejected
