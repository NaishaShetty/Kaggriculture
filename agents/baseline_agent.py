"""
Phase 1 baseline agent — "Wheat Patroller".

Design goal (per Phase 1 spec): correct API usage, valid actions, basic resource
management, basic crop farming (plant/water/harvest/sell), avoid unnecessary
failures, survive the full 720-turn episode, deterministic. NOT an economically
optimized agent — that is out of scope for Phase 1.

Strategy: the main farmer patrols the unlocked farm scanning for the single
most useful thing to do each turn (harvest > water > plant > move-toward-target),
farming WHEAT — the crop with the best documented yield/tile/day (0.80) and the
cheapest seed cost ($10), which minimizes idle capital and downside risk from a
single bad market swing. All harvested wheat is sold every turn (dynamic price
means small frequent sales are safer than hoarding into an unknown future price).
Money is deployed, in strict priority order, into: (1) keeping a seed in hand,
(2) buying additional land once there is a large cash cushion, so the agent
never goes broke trying to expand. No hired hands, no other crops, no animals —
those are deliberately out of scope for a Phase 1 control-condition baseline.

Stateless: recomputes everything from `obs` each call, matching the official
starter/random/pass agents' signature so it behaves identically whether run
in-process or loaded fresh from a submitted main.py.
"""

WHEAT = "WHEAT"
WHEAT_SEED_COST = 10
MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}

# Cash cushion kept in reserve before spending on land, so a land purchase can
# never strand the agent without money for seeds/emergencies.
LAND_SAFETY_MARGIN = 500


def _quadrant_of(x, y, board_size):
    half = board_size // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


def _is_plant(tile, crop=None):
    return isinstance(tile, dict) and tile.get("kind") == "PLANT" and (crop is None or tile.get("crop") == crop)


WHEAT_FIRST_YIELD_DAY = 2  # from CROPS["WHEAT"]; harvesting before this is a silent no-op in the sim


def _needs_harvest(tile, day):
    # A freshly-planted one-time crop already has yield_units=1 (see _new_plant),
    # but the sim silently no-ops HARVEST until day - planted_day >= first_yield_day.
    # Treating yield_units>0 alone as "ready" causes the agent to loop on a no-op
    # HARVEST instead of WATER, and the plant weeds out from neglect before it
    # ever matures -- this was caught via a losing-money smoke test, see docs.
    if not _is_plant(tile) or tile.get("yield_units", 0) <= 0:
        return False
    return (day - tile["planted_day"]) >= WHEAT_FIRST_YIELD_DAY


def _needs_water(tile):
    return _is_plant(tile, WHEAT) and not tile.get("watered_today", False)


def _find_target(tiles, board_size, unlocked_quadrants, fx, fy, have_seed, day):
    """Scan the whole board for the nearest actionable tile, priority:
    harvest-ready > needs-water > (if holding a seed) empty plantable tile.
    Returns (x, y) or None if nothing to do anywhere reachable."""
    best = None
    best_dist = None
    best_priority = None
    for y in range(board_size):
        row = tiles[y]
        for x in range(board_size):
            if _quadrant_of(x, y, board_size) not in unlocked_quadrants:
                continue
            tile = row[x]
            if _needs_harvest(tile, day):
                priority = 0
            elif _needs_water(tile):
                priority = 1
            elif tile is None and have_seed:
                priority = 2
            else:
                continue
            dist = abs(x - fx) + abs(y - fy)
            if best is None or priority < best_priority or (priority == best_priority and dist < best_dist):
                best, best_dist, best_priority = (x, y), dist, priority
    return best


def _step_toward(fx, fy, tx, ty):
    dx, dy = tx - fx, ty - fy
    if dx > 0:
        return "EAST"
    if dx < 0:
        return "WEST"
    if dy > 0:
        return "SOUTH"
    if dy < 0:
        return "NORTH"
    return "PASS"


def agent(obs):
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    board_size = len(me["tiles"])
    fx, fy = me["farmer"]
    tile = me["tiles"][fy][fx]
    money = me["money"]
    shed = private.get("shed", {})
    seeds = private.get("seeds", {})

    market = []

    # 1) Always liquidate wheat sitting in the shed -- avoid hoarding risk.
    wheat_in_shed = shed.get(WHEAT, 0)
    if wheat_in_shed > 0:
        market.append(["SELL", WHEAT, wheat_in_shed])

    # 2) Keep exactly one wheat seed in hand at all times when affordable.
    have_seed = seeds.get(WHEAT, 0) > 0
    if not have_seed and money >= WHEAT_SEED_COST:
        market.append(["BUY_SEED", WHEAT, 1])
        have_seed = True  # seed will land before this turn's farmer action resolves next turn

    # 3) Expand land only once cash is deep enough that the purchase can never
    # starve the seed-buying budget -- a large multiple of cost, not just a
    # fixed margin, since later land is $4k and a $500 cushion would be reckless.
    unlocked = me["unlocked_quadrants"]
    land_order = ["NE", "SW", "SE"]
    land_prices = [1000, 2000, 4000]
    next_idx = len(unlocked) - 1  # NW is free/always present
    if 0 <= next_idx < len(land_order):
        cost = land_prices[next_idx]
        if money >= cost * 3 + LAND_SAFETY_MARGIN:
            market.append(["BUY_LAND"])

    # 4) Farmer action: harvest > water > plant > move toward the nearest useful tile.
    day = obs["day"]
    if _needs_harvest(tile, day):
        farmer_action = ["HARVEST"]
    elif _needs_water(tile):
        farmer_action = ["WATER"]
    elif tile is None and seeds.get(WHEAT, 0) > 0:
        farmer_action = ["PLANT", WHEAT]
    else:
        target = _find_target(me["tiles"], board_size, unlocked, fx, fy, seeds.get(WHEAT, 0) > 0, day)
        if target is None:
            farmer_action = ["PASS"]
        else:
            farmer_action = [_step_toward(fx, fy, target[0], target[1])]

    return {"farmer": farmer_action, "hands": [], "market": market}
