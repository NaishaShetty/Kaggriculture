"""
Phase 4 (Submission D) market impact simulator.

VERIFIED IMPLEMENTATION BEHAVIOR (read directly from vendor_kaggriculture
.kaggriculture, lines ~585-661, not assumed): the game engine processes a
SELL order of N units ONE UNIT AT A TIME. On each iteration it re-quotes
`market_price(item, current_inventory)`, commits that single unit at that
price, and only THEN increments inventory by 1 -- EXCEPT when the quoted
price is exactly the floor ($1), in which case inventory does NOT
increase (a documented anti-exploit floor-price special case). Both
players' pending orders for the same item interleave against the SAME
shared, advancing inventory within a turn.

This means `N * current_price` is WRONG for any N > 1 once price starts
moving toward the floor -- exactly the mechanic already implicated in
Phase 3.4/3.6's self_inflicted_narrow_market_price_crash finding. This
module computes the REAL, unit-by-unit expected revenue using the exact
same `market_price` function the game itself calls -- not a re-derived
approximation.

We can only simulate OUR OWN order in isolation (we cannot observe or
predict the opponent's pending orders for the same turn) -- this is a
necessary, documented simplification, not a claim of full accuracy.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from vendor_kaggriculture.kaggriculture import market_price, MARKET_PARAMS, PRICE_FLOOR


def simulate_sell(item, n_units, current_inventory, params=None):
    """Returns (total_revenue, realized_prices, final_inventory) for selling
    n_units of `item` starting from `current_inventory`, using the EXACT
    unit-by-unit mechanic the game engine uses."""
    inv = current_inventory
    prices = []
    revenue = 0.0
    for _ in range(n_units):
        price = market_price(item, inv, params)
        prices.append(price)
        revenue += price
        if price > PRICE_FLOOR:
            inv += 1
    return revenue, prices, inv


def marginal_revenue(item, current_inventory, params=None):
    """Revenue of the NEXT single unit sold -- the true marginal value,
    not the average. Useful for comparing 'sell one more unit of X' against
    'sell one more unit of Y' on a like-for-like basis."""
    return market_price(item, current_inventory, params)


def revenue_curve(item, max_units, current_inventory, params=None):
    """Returns a list of (units_sold, cumulative_revenue) pairs, for
    building a HOLD/SELL_SMALL/SELL_PARTIAL/SELL_MOST/LIQUIDATE comparison
    without re-simulating from scratch for each candidate quantity."""
    inv = current_inventory
    cumulative = 0.0
    out = [(0, 0.0)]
    for k in range(1, max_units + 1):
        price = market_price(item, inv, params)
        cumulative += price
        if price > PRICE_FLOOR:
            inv += 1
        out.append((k, cumulative))
    return out


def estimate_buy_cost(item, n_units, current_inventory, params=None):
    """Mirrors the engine's BUY_PRODUCT quoting (WHEAT/FERTILIZER only):
    quoted at inventory-1 (a round-trip against an unchanged market nets
    zero, per the engine's own documented comment) -- inventory DECREASES
    by 1 per unit bought (the inverse of selling)."""
    inv = current_inventory
    cost = 0.0
    for _ in range(n_units):
        price = market_price(item, inv - 1, params)
        cost += price
        inv -= 1
    return cost


def market_depth(item, params=None):
    """Returns the T (depth) parameter for `item` -- the already-documented
    scale at which price movement becomes material. Smaller T = more
    sensitive to volume (e.g. STRAWBERRY=100 vs MELON=300, WHEAT=400)."""
    p = (params or MARKET_PARAMS)[item]
    return p["T"]
