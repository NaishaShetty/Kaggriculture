"""
Phase 3.1 controlled opponent classes (brief section 17) -- experimental
archetypes for FUTURE Phase 3.2+ adaptation experiments, not claims about
real Kaggle competitors. Every archetype reuses an EXISTING, already-tested
make_agent configuration from Phase 2.2-2.4 rather than inventing new agent
logic -- each one's behavior is therefore already characterized by prior
phases' experiments, and all of it is legal/observable (no archetype here
does anything the real environment wouldn't allow a normal agent to do).
"""
from agents.phase2_3.common import make_agent as make_agent_23
from agents.phase2_4.common import make_agent as make_agent_24


def passive():
    """Built-in `pass` agent -- never acts. Used throughout Phase 2.2-2.4 as
    the cheapest control opponent."""
    return "pass"


def production_heavy():
    """Phase 2.3's F13 winning integrated config -- the strongest tested
    non-planner strategy, reused here unchanged as a controlled opponent."""
    return make_agent_23(crops={"MELON": 0.5, "STRAWBERRY": 0.5}, n_hands=4, land_quadrants=1,
                          land_buy_day=0, animals={"GOOSE": 1, "COW": 1}, animal_buy_day=0)


def market_selling():
    """Same production config as above, but with Phase 2.4's best-found
    market-aware selling policy -- an archetype that trades more actively."""
    return make_agent_24(crops={"MELON": 0.5, "STRAWBERRY": 0.5}, n_hands=4, land_quadrants=1,
                          land_buy_day=0, animals={"GOOSE": 1, "COW": 1}, animal_buy_day=0,
                          sell_policy={"mode": "threshold_batch", "threshold_frac": 1.1, "batch_interval_days": 7})


def expansion_oriented():
    """Buys land aggressively (all 3 quadrants) regardless of labor --
    deliberately the F3/F4-negative-evidence regime, useful as a controlled
    'suboptimal but observably distinct' opponent for future contrast
    experiments (does the planner notice and capitalize on a land-heavy,
    labor-light opponent?)."""
    return make_agent_23(crops="MELON", n_hands=1, land_quadrants=3, land_buy_day=0)


def animal_oriented():
    """Crop-light, animal-heavy -- the complement of production_heavy on the
    animal_orientation_score axis defined in agents/phase3/strategy.py."""
    return make_agent_23(crops="WHEAT", n_hands=2, animals={"COW": 1, "SHEEP": 1}, animal_buy_day=0)


def conservative():
    """Minimal footprint: single crop, no hands, no land, no animals --
    the 'do very little, keep it simple' archetype."""
    return make_agent_23(crops="WHEAT", n_hands=0)


def aggressive_investment():
    """Buys everything affordable as early as possible (hands, land, both
    animal types, high-value crop) -- deliberately front-loaded capital
    deployment, the archetype most likely to hit F3's land-negativity and
    F16-adjacent overcommitment risk."""
    return make_agent_23(crops="MELON", n_hands=4, land_quadrants=3, land_buy_day=0,
                          animals={"GOOSE": 1, "COW": 1}, animal_buy_day=0)


OPPONENT_CLASSES = {
    "passive": passive,
    "production_heavy": production_heavy,
    "market_selling": market_selling,
    "expansion_oriented": expansion_oriented,
    "animal_oriented": animal_oriented,
    "conservative": conservative,
    "aggressive_investment": aggressive_investment,
}
