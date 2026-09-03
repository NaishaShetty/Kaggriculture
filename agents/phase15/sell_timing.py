"""
Phase 15 sell-timing layer -- the original roadmap Phase 2 concept
(docs/ROADMAP_TO_GOLD.md's "Phase 2 -- Sell-timing, not portfolio"), never
built until now. Uses the already-verified `agents/phase4/market_model.py
::revenue_curve` (exact unit-by-unit engine mechanic, not a re-derived
approximation) to decide, for each candidate SELL order the execution layer
already proposed (full held quantity), whether dumping the full batch NOW or
holding some of it back for a later turn yields more revenue -- exactly the
"quantity is already known (harvested inventory), no volume-estimation step"
framing that made this the SAFE application of the simulator (Phase 5 already
found volume-estimation for portfolio/substitution decisions fails; this
never estimates a volume, it only re-times a sale of a quantity already sitting
in the shed).

Does not touch how much to plant, hire, or buy -- purely a quantity-per-turn
decision on SELL orders the execution layer already generated.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase4.market_model import revenue_curve  # noqa: E402

# Candidate batch fractions to compare against a full dump, cheapest to compute
# first. 1.0 (full) is always included so "just sell everything" remains a
# valid outcome when the market isn't deep enough to punish it.
_CANDIDATE_FRACTIONS = [1.0, 0.75, 0.5, 0.25]

# Force full liquidation from this day on, matching the same terminal-deadline
# safety-net PRINCIPLE already validated live (agents/phase2_5/common.py's
# horizon_aware force-liquidation, Phase 7) -- holding inventory back for
# "better timing" stops being correct once there are no more turns left to
# sell it. Not imported from agents/phase2_5/ (frozen, unrelated adapter) --
# reimplemented here as a simple day check since the mechanism is trivial.
TERMINAL_LIQUIDATION_DAY = 27

# Shed capacity guard: force full sell of any item pushing shed occupancy
# above this fraction of the engine's 100-unit shed cap, regardless of
# market-timing preference -- an overflowing shed loses production outright,
# which no amount of better pricing can be worth.
SHED_OVERFLOW_GUARD_FRACTION = 0.85
SHED_CAPACITY = 100


def _best_batch(item, held_qty, market_inventory):
    """Returns the held quantity to sell THIS turn (<= held_qty) that
    maximizes revenue-per-unit-sold among the candidate fractions, using the
    verified unit-by-unit simulator. Never returns 0 if held_qty > 0 --
    minimum sale size is always considered via the smallest fraction."""
    if held_qty <= 0:
        return 0
    best_qty, best_avg = held_qty, -1.0
    for frac in _CANDIDATE_FRACTIONS:
        qty = max(1, round(held_qty * frac))
        qty = min(qty, held_qty)
        curve = revenue_curve(item, qty, market_inventory)
        total_revenue = curve[-1][1]
        avg = total_revenue / qty
        if avg > best_avg:
            best_avg = avg
            best_qty = qty
    return best_qty


def apply_sell_timing(market_orders, shed, market_inventory, day):
    """market_orders: the execution layer's already-built list of orders
    (a list of [action, ...] lists, SELL orders shaped ["SELL", item, qty]).
    shed: dict item -> held quantity (private state, for the overflow guard).
    market_inventory: dict item -> current market inventory (obs["market"]
    ["inventory"], the same field the simulator's `current_inventory`
    parameter expects). Returns a NEW list with SELL quantities re-timed;
    every non-SELL order passes through unchanged, in its original order."""
    out = []
    for order in market_orders:
        if not order or order[0] != "SELL":
            out.append(order)
            continue
        _, item, qty = order
        held = shed.get(item, 0)
        if day >= TERMINAL_LIQUIDATION_DAY or held >= SHED_CAPACITY * SHED_OVERFLOW_GUARD_FRACTION:
            out.append(["SELL", item, qty])
            continue
        inv = market_inventory.get(item, 0)
        best_qty = _best_batch(item, min(qty, held), inv)
        if best_qty > 0:
            out.append(["SELL", item, best_qty])
    return out
