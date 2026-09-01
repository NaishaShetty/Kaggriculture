"""
Phase 2.6 state adapter: converts the REAL per-turn `obs` dict (exactly what
an agent legitimately receives -- see docs/PHASE2_1_ARCHITECTURE.md section 1
for the verified public/private observation boundary) into
`economic_model.model.EconomicState` plus a small number of planner-only
extras that are still 100% derivable from `obs` alone.

Never reads or infers opponent private state (shed/seeds/carried-inventory).
Only `obs["farms"][player]` (own + opponent PUBLIC farm), `obs["market"]`,
`obs["town"]`, `obs["day"]`, `obs["hour"]`, and `obs["private"]` (own only)
are touched -- exactly the fields Phase 2.1 verified are legitimately
available to an agent.
"""
from dataclasses import dataclass, field

from economic_model.model import EconomicState
from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS


@dataclass
class PlannerState(EconomicState):
    """Extends EconomicState with planner-only fields that don't belong in
    the frozen Phase 2.5 model's own state shape but are needed to generate
    candidates (e.g. counting tiles by crop requires reading the board,
    which EconomicState deliberately abstracts away as a summary count)."""
    n_animals_by_species: dict = field(default_factory=dict)
    animals_placed: int = 0
    board_size: int = 10
    turn: int = 0
    money_raw: float = 0.0
    hire_cost_next: float = 0.0


def adapt(obs) -> PlannerState:
    """The ONLY function in agents/phase2_6/ that touches raw `obs`. Every
    other planner module operates on `PlannerState`, never on `obs`
    directly -- this is the state-adapter boundary the brief (section 33.3)
    requires."""
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    day = obs["day"]
    hour = obs.get("hour", 0)
    board_size = len(me["tiles"])
    tiles = me["tiles"]

    shed = private.get("shed", {})
    money = me["money"]
    n_hands = len(me.get("hands", []))
    land_quadrants = len(me.get("unlocked_quadrants", ["NW"]))

    crop_tile_counts = {}
    n_animals_by_species = {}
    animals_placed = 0
    for row in tiles:
        for tile in row:
            if isinstance(tile, dict):
                if tile.get("kind") == "PLANT":
                    crop_tile_counts[tile["crop"]] = crop_tile_counts.get(tile["crop"], 0) + 1
                elif "animal" in tile:
                    n_animals_by_species[tile["animal"]] = n_animals_by_species.get(tile["animal"], 0) + 1
                    animals_placed += 1

    market = obs.get("market", {})
    prices = dict(market.get("prices", {}))
    inventory = dict(market.get("inventory", {}))

    # next hire cost (fib(n_hands)*mult, VERIFIED default mult=1 -- see economic_model.model.HIRE_MULT)
    from economic_model.model import HIRE_MULT
    a, b = 1, 1
    for _ in range(n_hands):
        a, b = b, a + b
    hire_cost_next = HIRE_MULT * a

    state = PlannerState(
        day=day, cash=money, land_quadrants_owned=land_quadrants, n_hands=n_hands,
        crop_tile_counts=crop_tile_counts, animal_counts=n_animals_by_species,
        shed_occupancy=dict(shed), market_prices=prices, market_inventory=inventory,
        n_animals_by_species=n_animals_by_species, animals_placed=animals_placed,
        board_size=board_size, turn=day * 24 + hour, money_raw=money, hire_cost_next=hire_cost_next,
    )
    return state


def validate_state(state: PlannerState):
    """Basic sanity checks -- the brief's "include validation for missing or
    malformed state" requirement. Returns a list of problem strings (empty
    if clean); never raises, since a planner that crashes on odd state is
    worse than one that flags it and degrades gracefully."""
    problems = []
    if state.cash < 0:
        problems.append(f"negative cash: {state.cash}")
    if not (0 <= state.day <= 40):
        problems.append(f"day out of expected range [0,40]: {state.day}")
    if state.n_hands < 0 or state.n_hands > 20:
        problems.append(f"implausible n_hands: {state.n_hands}")
    for item, qty in state.shed_occupancy.items():
        if qty < 0:
            problems.append(f"negative shed quantity for {item}: {qty}")
    return problems
