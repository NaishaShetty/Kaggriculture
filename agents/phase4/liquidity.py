"""
Phase 4 liquidity guard and endgame liquidation.

DIRECTLY INFORMED BY Phase 3.7-B/C's F-005 forensics: the death spiral
found there was NOT preventable by an early-cash-threshold trigger (cash
looks similar in every episode until it's already too late -- Phase
3.7-C's rejected countermeasure). This module does NOT attempt to re-solve
F-005 (out of scope, no new evidence justifies a different approach this
phase) -- it instead implements the more modest, clearly-scoped
requirement actually specified for Phase 4: a minimum-reserve check that
suppresses OPTIONAL new investment (not existing commitments) when cash
is already low, and an explicit endgame liquidation window that converts
remaining inventory to cash using the REAL market-impact simulator
(market_model.py) rather than dumping everything in one shot.
"""
from agents.phase4.market_model import revenue_curve

MIN_RESERVE = 100.0          # below this, treat new discretionary spend as unsafe
ENDGAME_WINDOW_DAYS = 3      # last N days: unsold inventory has no terminal value


def liquidity_state(cash, remaining_days):
    if cash < MIN_RESERVE:
        return "CRITICAL", "cash below minimum reserve -- suppress optional investment"
    if cash < MIN_RESERVE * 3:
        return "TIGHT", "cash is low but above the hard floor -- proceed cautiously"
    return "HEALTHY", "cash reserve is adequate"


def is_endgame(day, total_days=30):
    return (total_days - day) <= ENDGAME_WINDOW_DAYS


def endgame_liquidation_plan(shed_inventory, market_inventory, params=None, max_price_impact_frac=0.5):
    """For each item with shed inventory > 0 in the endgame window, decide
    how many units to sell THIS turn using the real market-impact curve:
    sell up to the point where the marginal price would otherwise drop
    below `max_price_impact_frac` of the item's CURRENT price, since
    endgame inventory has zero terminal value if unsold -- but a single
    turn's shed contents rarely approach a crop's market depth T, so this
    safeguard mainly matters for large batches accumulated during the
    season. Returns {item: units_to_sell_this_turn}."""
    plan = {}
    for item, qty in shed_inventory.items():
        if qty <= 0:
            continue
        inv = market_inventory.get(item, 0)
        curve = revenue_curve(item, qty, inv, params)
        # find the largest n where price hasn't crashed below the safeguard fraction
        from vendor_kaggriculture.kaggriculture import market_price
        base_price = market_price(item, inv, params)
        threshold = base_price * max_price_impact_frac
        n_to_sell = qty
        test_inv = inv
        for k in range(qty):
            p = market_price(item, test_inv, params)
            if p < threshold and k > 0:
                n_to_sell = k
                break
            if p > 1:
                test_inv += 1
        plan[item] = n_to_sell
    return plan
