"""
Phase 3.1 competitive state representation -- separate from (and composed
from) the Phase 2.6 economic state, per the brief section 9:

    Own Economic State + Observable Market State + Observable Opponent
    State + Recent Opponent Behavior + Recent Market Behavior + Time/Horizon

Every field below is classified in `FIELD_CLASSIFICATION` as one of:
  mechanically_observable | derived_from_observable | experimentally_inferred | unavailable
No field is included "because it exists" -- each is consumed by at least one
of: Phase 2.6's planner (own_economic_state), a future regime-discovery
signal candidate (section 14 of the Phase 3.1 kickoff), or a competitive
metric (win-margin tracking needs opponent money, directly observable).
"""
from dataclasses import dataclass, field

from agents.phase2_6.state import PlannerState
from agents.phase3.opponent_observation import OpponentObservation
from agents.phase3.market_observation import MarketObservation

FIELD_CLASSIFICATION = {
    "own_economic_state": "mechanically_observable",
    "opponent_money": "mechanically_observable",
    "opponent_land_quadrants": "mechanically_observable",
    "opponent_crop_tile_counts": "mechanically_observable",
    "opponent_animal_tile_counts": "mechanically_observable",
    "money_margin": "derived_from_observable",          # own_cash - opponent_money, simple arithmetic
    "recent_opponent_events": "derived_from_observable",  # OpponentObservationLogger's tile/money-delta inferences
    "recent_market_unexplained_activity": "derived_from_observable",  # MarketObservationLogger's residual
    "remaining_days": "mechanically_observable",         # TOTAL_DAYS - day, both known constants/observed
    "inferred_opponent_regime": "unavailable_in_phase_3_1",  # placeholder ONLY -- Phase 3.2+ concern, never populated here
}


@dataclass
class CompetitiveState:
    own_economic_state: PlannerState
    opponent_money: float
    opponent_land_quadrants: int
    opponent_crop_tile_counts: dict
    opponent_animal_tile_counts: dict
    money_margin: float
    remaining_days: int
    recent_opponent_events: list = field(default_factory=list)
    recent_market_unexplained_activity: list = field(default_factory=list)
    inferred_opponent_regime: None = None  # ALWAYS None in Phase 3.1 -- see FIELD_CLASSIFICATION


def build_competitive_state(planner_state: PlannerState, opponent_obs: OpponentObservation,
                             market_obs: MarketObservation, recent_opponent_window=5, recent_market_window=5,
                             opponent_history=None, market_history=None) -> CompetitiveState:
    """Pure function: combines an already-adapted PlannerState with the
    latest opponent/market observations (and a short recent-history window
    for "recent behavior" fields) into one CompetitiveState. Never reads
    raw `obs` itself -- that boundary is owned by state.py/opponent_observation.py/
    market_observation.py individually."""
    recent_opponent_events = []
    if opponent_history:
        for snap in opponent_history[-recent_opponent_window:]:
            recent_opponent_events.extend(snap.derived_events)

    recent_market_unexplained = []
    if market_history:
        for snap in market_history[-recent_market_window:]:
            if snap.derived_unexplained_delta:
                recent_market_unexplained.append({"turn": snap.turn, "residual": snap.derived_unexplained_delta})

    return CompetitiveState(
        own_economic_state=planner_state,
        opponent_money=opponent_obs.visible_money,
        opponent_land_quadrants=opponent_obs.visible_land_quadrants,
        opponent_crop_tile_counts=opponent_obs.visible_crop_tile_counts,
        opponent_animal_tile_counts=opponent_obs.visible_animal_tile_counts,
        money_margin=planner_state.cash - opponent_obs.visible_money,
        remaining_days=planner_state.remaining_days,
        recent_opponent_events=recent_opponent_events,
        recent_market_unexplained_activity=recent_market_unexplained,
    )


def summarize(cs: CompetitiveState) -> dict:
    return {
        "own_cash": round(cs.own_economic_state.cash, 2), "opponent_money": round(cs.opponent_money, 2),
        "money_margin": round(cs.money_margin, 2), "remaining_days": cs.remaining_days,
        "opponent_land_quadrants": cs.opponent_land_quadrants,
        "opponent_crop_tile_counts": cs.opponent_crop_tile_counts,
        "opponent_animal_tile_counts": cs.opponent_animal_tile_counts,
        "n_recent_opponent_events": len(cs.recent_opponent_events),
        "n_recent_market_unexplained": len(cs.recent_market_unexplained_activity),
    }
