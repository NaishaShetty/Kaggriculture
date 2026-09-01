"""
Phase 2.2 shared crop-experiment agent framework.

NOT a modification of the frozen `agents/baseline_agent.py` -- a new,
separate experimental module (per docs/03_control_contract_and_change_policy.md
rule 4: "new agents are separate experimental artifacts").

Every crop-specific agent in this package is a thin call to `make_agent()`
below, so implementation differences between crops are minimized to exactly
what section 8 of the Phase 2.2 brief asks for: crop selected, purchase
amount, planting behavior, lifecycle handling. Everything else -- tile
assignment, movement/target-selection priority, selling policy, land/hand/
animal usage -- is identical across every crop agent produced by this module.

Documented controlled-experiment policy (brief section 21, "passive market
baseline"):
  - Never expands land (NW quadrant only, 25 tiles) and never hires hands or
    buys animals -- brief section 9's control list.
  - Sells 100% of shed inventory of every crop this agent grows, every single
    turn it has any. No price-timing, no withholding, no reaction to the
    opponent. This is the one, single, documented selling rule used for
    every crop and every experiment in Phase 2.2 -- so any revenue
    difference between crops reflects production, not selling-policy choice.
  - Keeps at most one seed in hand per crop at a time (buys a replacement
    only when it holds zero), mirroring the frozen baseline's own seed
    policy, to avoid conflating "aggressive seed stockpiling" with crop
    economics.
  - `plant_delay_day`: no BUY_SEED/PLANT order is issued before this day
    (used by the Phase 2.2 timing experiment; 0 for every other experiment).
  - `fertilizer`: off by default (Condition A, section 18). When True
    (Condition B), the agent also buys and applies exactly enough fertilizer
    to keep at most one unit of FERTILIZER carried at a time, applying it
    once per plant per fertilization window as it becomes eligible again.
"""
from vendor_kaggriculture.kaggriculture import CROPS

HOME_TILE = None  # set per board_size in _home_tile()


def _home_tile(board_size):
    half = board_size // 2
    return (half - 1, half - 1)  # farmer's default spawn; also a shed-access tile, inside NW


def tile_assignment(board_size, crop_fractions):
    """Deterministic, stateless partition of the NW quadrant's tiles across
    crops by fraction, using the largest-remainder method. Same partition
    every call for the same `crop_fractions` (a pure function of static
    config, not of game state)."""
    half = board_size // 2
    tiles = [(x, y) for y in range(half) for x in range(half)]
    n = len(tiles)
    crops_sorted = sorted(crop_fractions.items())
    total_frac = sum(f for _, f in crops_sorted)
    raw = [(c, f / total_frac * n) for c, f in crops_sorted]
    counts = {c: int(v) for c, v in raw}
    remainder = n - sum(counts.values())
    order = sorted(range(len(raw)), key=lambda i: (raw[i][1] - int(raw[i][1])), reverse=True)
    for i in order[:remainder]:
        counts[raw[i][0]] += 1
    assignment = {}
    pos = 0
    for c, _ in crops_sorted:
        cnt = counts[c]
        for t in tiles[pos:pos + cnt]:
            assignment[t] = c
        pos += cnt
    return assignment


def _is_plant(tile, crop=None):
    return isinstance(tile, dict) and tile.get("kind") == "PLANT" and (crop is None or tile.get("crop") == crop)


def _needs_harvest(tile, crop, day):
    if not _is_plant(tile, crop) or tile.get("yield_units", 0) <= 0:
        return False
    return (day - tile["planted_day"]) >= CROPS[crop]["first_yield_day"]


def _needs_water(tile, crop):
    return _is_plant(tile, crop) and not tile.get("watered_today", False)


def _needs_fertilize(tile, crop, day):
    return _is_plant(tile, crop) and tile.get("fertilized_until_day", -1) < day


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


def _find_target(tiles, assignment, fx, fy, seeds, day, carrying_fertilizer, fertilizer_mode, plant_delay_day):
    best, best_dist, best_priority = None, None, None
    for (x, y), crop in assignment.items():
        tile = tiles[y][x]
        if _needs_harvest(tile, crop, day):
            priority = 0
        elif _needs_water(tile, crop):
            priority = 1
        elif fertilizer_mode and carrying_fertilizer and _needs_fertilize(tile, crop, day):
            priority = 2
        elif tile is None and seeds.get(crop, 0) > 0 and day >= plant_delay_day:
            priority = 3
        else:
            continue
        dist = abs(x - fx) + abs(y - fy)
        if best is None or priority < best_priority or (priority == best_priority and dist < best_dist):
            best, best_dist, best_priority = (x, y), dist, priority
    return best


def make_agent(crops, fertilizer=False, plant_delay_day=0):
    """`crops`: a crop name (100% allocation) or a dict {crop: fraction}."""
    crop_fractions = {crops: 1.0} if isinstance(crops, str) else dict(crops)
    crop_list = sorted(crop_fractions)

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
        inv0 = private.get("inventories", [{}])[0]
        day = obs["day"]
        home = _home_tile(board_size)
        assignment = tile_assignment(board_size, crop_fractions)

        market = []
        for crop in crop_list:
            held = shed.get(crop, 0)
            if held > 0:
                market.append(["SELL", crop, held])

        for crop in crop_list:
            if day >= plant_delay_day and seeds.get(crop, 0) == 0 and money >= CROPS[crop]["seed"]:
                market.append(["BUY_SEED", crop, 1])
                money -= CROPS[crop]["seed"]  # local bookkeeping only, doesn't mutate obs

        carrying_fertilizer = inv0.get("FERTILIZER", 0) > 0
        if fertilizer and day >= plant_delay_day:
            fert_price = obs.get("market", {}).get("prices", {}).get("FERTILIZER", 10**9)
            if not carrying_fertilizer and shed.get("FERTILIZER", 0) == 0 and money >= fert_price:
                market.append(["BUY_PRODUCT", "FERTILIZER", 1])
            elif not carrying_fertilizer and shed.get("FERTILIZER", 0) > 0 and (fx, fy) == home:
                pass  # PICKUP handled as the farmer action below when standing on `home`

        my_crop_here = assignment.get((fx, fy))
        if my_crop_here and _needs_harvest(tile, my_crop_here, day):
            farmer_action = ["HARVEST"]
        elif my_crop_here and _needs_water(tile, my_crop_here):
            farmer_action = ["WATER"]
        elif fertilizer and my_crop_here and carrying_fertilizer and _needs_fertilize(tile, my_crop_here, day):
            farmer_action = ["FERTILIZE"]
        elif my_crop_here and tile is None and seeds.get(my_crop_here, 0) > 0 and day >= plant_delay_day:
            farmer_action = ["PLANT", my_crop_here]
        elif fertilizer and (fx, fy) == home and not carrying_fertilizer and shed.get("FERTILIZER", 0) > 0:
            farmer_action = ["PICKUP", "FERTILIZER", 1]
        else:
            target = _find_target(me["tiles"], assignment, fx, fy, seeds, day, carrying_fertilizer, fertilizer, plant_delay_day)
            if target is None:
                if fertilizer and not carrying_fertilizer and shed.get("FERTILIZER", 0) > 0 and (fx, fy) != home:
                    farmer_action = [_step_toward(fx, fy, home[0], home[1])]
                else:
                    farmer_action = ["PASS"]
            else:
                farmer_action = [_step_toward(fx, fy, target[0], target[1])]

        return {"farmer": farmer_action, "hands": [], "market": market}

    return agent
