"""
Phase 3.1 market observation interface. Three explicitly separated layers,
per the brief section 11:
  1. DIRECT OBSERVATION -- obs['market']['prices'|'inventory'], obs['town'],
     verbatim, every turn (VERIFIED public/shared, Phase 2.1/2.4 Stage A).
  2. DERIVED MARKET SIGNAL -- a computation over direct observations, e.g.
     the per-turn inventory delta attributable to the documented town
     consumption schedule (the EXACT formula validated in Phase 2.4 Stage A,
     100% explanatory when no player is trading -- reused here, not
     re-derived) versus an "unexplained" residual (attributable to either
     player's own trading, since both players' trades pool into the same
     shared market inventory and cannot be separated further without also
     knowing this player's own trade record, which IS available and
     subtracted out below).
  3. HYPOTHESIZED MARKET REGIME -- NOT implemented in Phase 3.1. No regime
     label is assigned anywhere in this module.
"""
from dataclasses import dataclass, field

from vendor_kaggriculture.kaggriculture import SHOPS, MARKET_PARAMS


@dataclass
class MarketObservation:
    turn: int
    day: int
    hour: int
    prices: dict           # direct observation
    inventory: dict        # direct observation
    unlocked_shops: list   # direct observation
    derived_town_consumption: dict = field(default_factory=dict)   # derived signal
    derived_unexplained_delta: dict = field(default_factory=dict)  # derived signal (opponent + self trading, pooled)


class MarketObservationLogger:
    """Stateful, per-episode logger. `observe(obs, own_transactions_this_turn)`
    -- `own_transactions_this_turn`: dict {item: net_qty_delta_from_MY_OWN_trades}
    used to subtract this player's own known activity from the unexplained
    residual, isolating what's left (opponent trading + any other cause)."""

    def __init__(self):
        self.history = []
        self._prev = None

    def observe(self, obs, own_transactions_this_turn=None) -> MarketObservation:
        own_transactions_this_turn = own_transactions_this_turn or {}
        market = obs.get("market", {})
        town = obs.get("town", {})
        turn = obs["day"] * 24 + obs.get("hour", 0)
        snap = MarketObservation(
            turn=turn, day=obs["day"], hour=obs.get("hour", 0),
            prices=dict(market.get("prices", {})), inventory=dict(market.get("inventory", {})),
            unlocked_shops=list(town.get("unlocked_shops", [])),
        )
        if self._prev is not None:
            snap.derived_town_consumption, snap.derived_unexplained_delta = self._derive(
                self._prev, snap, own_transactions_this_turn)
        self.history.append(snap)
        self._prev = snap
        return snap

    def _derive(self, prev: MarketObservation, cur: MarketObservation, own_txns):
        """Reuses the EXACT town-consumption schedule validated in Phase 2.4
        Stage A (scripts/phase2_4_stage_a_verify.py) -- the check_turn = turn-1
        offset there is the same replay-indexing convention documented in
        docs/PHASE2_1_ARCHITECTURE.md section 2, re-applied here."""
        check_turn = cur.turn - 1
        town_delta = {}
        for item in MARKET_PARAMS:
            expected = 0
            if check_turn % 4 == 0:
                for shop in cur.unlocked_shops:
                    products = SHOPS.get(shop, [])
                    if item in products:
                        expected -= 2 if len(products) == 1 else 1
            if check_turn % 24 == 0 and item != "FERTILIZER":
                expected -= 1
            town_delta[item] = expected

        unexplained = {}
        for item in MARKET_PARAMS:
            actual_delta = cur.inventory.get(item, 0) - prev.inventory.get(item, 0)
            explained = town_delta.get(item, 0) + own_txns.get(item, 0)
            residual = actual_delta - explained
            if residual != 0:
                unexplained[item] = residual
        return town_delta, unexplained

    def to_records(self):
        return [
            {"turn": s.turn, "day": s.day, "hour": s.hour, "prices": s.prices, "inventory": s.inventory,
             "unlocked_shops": s.unlocked_shops, "derived_town_consumption": s.derived_town_consumption,
             "derived_unexplained_delta": s.derived_unexplained_delta}
            for s in self.history
        ]
