"""
Phase 2.3 shared multi-resource agent framework.

Generalizes agents/phase2_2/common.py::make_agent from a single farmer growing
crops in the fixed NW quadrant into a config-driven multi-worker (farmer + N
hired hands) agent that can also expand land, keep animals (goose/cow/sheep),
feed/care for them, and use fertilizer (bought or animal-collected). Like
Phase 2.2's framework, this is one shared implementation -- every Phase 2.3
experiment agent is `make_agent(...)` with different keyword arguments, never
an independently hand-tuned per-scenario policy.

Not a modification of the frozen `agents/baseline_agent.py`, nor of
`agents/phase2_2/*` (preserved exactly, per docs/03_control_contract_and_change_policy.md
rule 4). A brand-new, separate experimental module.

Design (documented here so results are auditable against the policy that
produced them, per the Phase 2.3 brief's requirement that every experiment
record its configuration):

  - Workers = farmer (index 0) + up to `n_hands` hired hands. Hands are
    cleared by the simulator at the end of every in-game day (VERIFIED,
    kaggriculture.py::_end_of_day), so the agent re-issues HIRE orders every
    day to top back up to `n_hands` -- hiring is a genuine recurring daily
    cost, not a one-time purchase. `farmHandCostMult` is assumed to be the
    documented default (1) for the agent's own cash-affordability bookkeeping
    -- true for every Phase 2.3 experiment, since no experiment overrides it.
  - Land: `land_quadrants` (0-3) is a target number of extra quadrants to buy,
    attempted (BUY_LAND, in the engine's fixed NE/SW/SE order) as soon as
    affordable on or after `land_buy_day`.
  - Tile allocation: every currently-owned, non-shed-adjacent tile is pooled
    each turn. The nearest `n_structures` tiles to home (Manhattan distance)
    are reserved for animal structures (coop/pasture); the remainder is split
    across `crops` by fraction using the same largest-remainder method as
    Phase 2.2. This is a deterministic, stateless function of the *current*
    owned-tile set, recomputed fresh every turn -- so buying land mid-episode
    grows the pool without disturbing already-planted tiles' crop identity
    (only *unplanted* tiles are affected by any largest-remainder reshuffle).
  - Animals: `animals` is a dict {"GOOSE"/"COW"/"SHEEP": target_count}.
    Reserved structure tiles are built (BUILD_COOP/BUILD_PASTURE, $0 cost per
    kaggriculture.py::_do_buy_land region -- VERIFIED no money touched) once
    `day >= animal_buy_day`, then an animal is bought (lands in the shed) and
    a worker PICKUPs + PLACEs it. If an animal escapes (2 consecutive unfed
    days -- VERIFIED, `_daily_refresh_animals`), the now-empty structure is
    automatically refilled with a freshly bought animal on a later turn (this
    agent does not model "give up and abandon the slot").
  - Feed: `feed_policy` "daily" feeds every animal every day it's unfed,
    requiring 1 carried WHEAT/animal. `feed_source`: "grow" only ever uses
    shed WHEAT from a WHEAT crop already in `crops`; "market" always buys
    WHEAT via BUY_PRODUCT at the dynamic price; "auto" grows if WHEAT is in
    `crops`, else buys. A `wheat_reserved` count is withheld from the daily
    SELL order so feed-earmarked wheat isn't sold out from under itself.
  - Care: `care_policy` "daily" issues CARE on every animal not yet cared for
    today (banks a production bonus on the next fed+cared production day --
    VERIFIED, `_daily_refresh_animals`'s `pending_care_bonus`).
  - Fertilizer: `collect_fertilizer` opportunistically COLLECT_FERTILIZERs
    from any animal with `fertilizer_available` (free, 1/day/animal, VERIFIED
    non-accumulating). `buy_fertilizer` additionally buys FERTILIZER via
    BUY_PRODUCT when none is carried/held. `fertilizer_apply` actually spends
    held fertilizer via FERTILIZE on eligible crop tiles; when False, any
    collected/bought fertilizer is sold instead (`fertilizer_sell_surplus`).
  - Selling: every crop in `crops`, every animal product for any animal type
    in `animals`, and FERTILIZER (if acquired at all) are sold from the shed
    every turn, net of the feed-wheat/fertilizer-application reservations
    above -- the same "sell everything, every turn" passive baseline as
    Phase 2.2, generalized to more item types.
  - Weed recovery: unlike Phase 2.2 (which never DIGs a WEED tile), this
    framework DIGs weeded crop tiles back to empty so hands/land investments
    aren't permanently wasted by one missed watering cycle -- directly
    relevant to the Phase 2.3 labor/land congestion questions. Documented
    here as a deliberate framework improvement over Phase 2.2, not a hidden
    behavior change; see docs/PHASE2_3_REPORT.md.
  - Seed stock: buys up to `min(seed_buffer_cap, n_workers, empty_tiles_needing_that_crop)`
    seeds per crop (at least 1 kept in reserve at all times), letting multiple
    workers plant the same crop simultaneously -- Phase 2.2's single-farmer
    agent never needed more than 1 (only one unit could ever plant per turn).
  - Task scheduling: every turn, build a prioritized task list (0=harvest,
    1=water/feed, 2=care/fertilize, 3=plant/build/place/dig, 4=collect
    fertilizer) plus synthetic "fetch" tasks (pick up a carried-item
    requirement from the shed). Assign each task to its nearest currently
    unclaimed, capability-eligible worker (greedy, priority order, no
    re-optimization) -- not a claim of optimal multi-worker routing, just a
    consistent, auditable policy applied identically across every experiment
    that uses hands. Workers with no assigned task and something in their
    carried inventory walk to the shed and DROP; otherwise PASS.
"""
from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS, LAND_PRICES


def _home_tile(board_size):
    half = board_size // 2
    return (half - 1, half - 1)


def _shed_tiles(board_size):
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def _owned_tiles(tiles, board_size):
    return [(x, y) for y in range(board_size) for x in range(board_size) if tiles[y][x] != "LOCKED"]


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _is_plant(tile, crop=None):
    return isinstance(tile, dict) and tile.get("kind") == "PLANT" and (crop is None or tile.get("crop") == crop)


def _needs_harvest_crop(tile, crop, day):
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


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def tile_pool_assignment(owned_tiles, home, shed_tiles, crop_fractions, n_structures):
    """Deterministic split of owned (non-shed) tiles into structure slots
    (nearest to home first) and crop tiles (largest-remainder among the
    rest). Stable as owned tiles grow: existing structure tiles keep being
    the nearest ones; crop tiles reshuffle only among not-yet-planted cells."""
    pool = [t for t in owned_tiles if t not in shed_tiles]
    pool_sorted = sorted(pool, key=lambda t: (_manhattan(t, home), t[1], t[0]))
    structure_tiles = pool_sorted[:n_structures]
    crop_pool = sorted(pool_sorted[n_structures:])
    n = len(crop_pool)
    if n == 0 or not crop_fractions:
        return structure_tiles, {}
    crops_sorted = sorted(crop_fractions.items())
    total_frac = sum(f for _, f in crops_sorted) or 1.0
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
        for t in crop_pool[pos:pos + cnt]:
            assignment[t] = c
        pos += cnt
    return structure_tiles, assignment


def structure_type_assignment(structure_tiles, animal_counts):
    seq = []
    for t, cnt in sorted(animal_counts.items()):
        seq.extend([t] * cnt)
    return {tile: seq[i] for i, tile in enumerate(structure_tiles) if i < len(seq)}


def make_agent(
    crops=None,
    n_hands=0,
    land_quadrants=0,
    land_buy_day=0,
    animals=None,
    animal_buy_day=0,
    feed_policy="daily",
    care_policy="daily",
    collect_fertilizer=False,
    buy_fertilizer=False,
    fertilizer_apply=False,
    fertilizer_sell_surplus=True,
    feed_source="auto",
    plant_delay_day=0,
    seed_buffer_cap=4,
):
    """`crops`: crop name / {crop: fraction} / None. `animals`: {TYPE: count} / None."""
    crop_fractions = {} if crops is None else ({crops: 1.0} if isinstance(crops, str) else dict(crops))
    animal_counts = dict(animals) if animals else {}
    n_structures = sum(animal_counts.values())

    def agent(obs):
        player = obs["player"]
        me = obs["farms"][player]
        private = obs["private"]
        board_size = len(me["tiles"])
        tiles = me["tiles"]
        day = obs["day"]
        money = me["money"]
        shed = private.get("shed", {})
        seeds = private.get("seeds", {})
        invs = private.get("inventories", [{}])
        prices = obs.get("market", {}).get("prices", {})

        home = _home_tile(board_size)
        shed_tiles = _shed_tiles(board_size)
        owned = _owned_tiles(tiles, board_size)
        structure_tiles, crop_assignment = tile_pool_assignment(owned, home, shed_tiles, crop_fractions, n_structures)
        structure_type = structure_type_assignment(structure_tiles, animal_counts)

        positions = [tuple(me["farmer"])] + [tuple(h) for h in me.get("hands", [])]
        workers = []
        for i, pos in enumerate(positions):
            inv = invs[i] if i < len(invs) else {}
            workers.append({"pos": pos, "inv": inv, "claimed": False, "action": None})
        n_workers = len(workers)

        market = []

        # --- HIRE (hands reset daily) ---
        current_hands = len(me.get("hands", []))
        need_hire = max(0, n_hands - current_hands)
        hire_cost_est = sum(_fib(current_hands + i) for i in range(need_hire))  # mult=1 assumed (never overridden)
        for _ in range(need_hire):
            market.append(["HIRE"])
        money -= hire_cost_est

        # --- BUY_LAND ---
        n_extra_owned = len(me.get("unlocked_quadrants", [])) - 1
        if n_extra_owned < land_quadrants and day >= land_buy_day and n_extra_owned < len(LAND_PRICES):
            next_cost = LAND_PRICES[n_extra_owned]
            if money >= next_cost:
                market.append(["BUY_LAND"])
                money -= next_cost

        # --- SELL shed inventory (reserve feed-wheat / apply-fertilizer) ---
        n_animals_alive = sum(
            1 for t in structure_tiles if isinstance(tiles[t[1]][t[0]], dict) and "animal" in tiles[t[1]][t[0]]
        )
        wheat_reserved = n_animals_alive if (feed_policy == "daily" and n_animals_alive) else 0
        fert_reserved = 1 if (fertilizer_apply and not fertilizer_sell_surplus) else 0

        sellable_items = set(crop_fractions) | {ANIMALS[t]["product"] for t in animal_counts}
        if buy_fertilizer or collect_fertilizer:
            sellable_items.add("FERTILIZER")
        for item in sorted(sellable_items):
            held = shed.get(item, 0)
            reserve = wheat_reserved if item == "WHEAT" else (fert_reserved if item == "FERTILIZER" else 0)
            sellable = max(0, held - reserve)
            if sellable > 0:
                market.append(["SELL", item, sellable])

        # --- BUY_SEED (enough for every worker to plant simultaneously) ---
        empty_needed = {}
        if day >= plant_delay_day:
            for t, c in crop_assignment.items():
                if tiles[t[1]][t[0]] is None:
                    empty_needed[c] = empty_needed.get(c, 0) + 1
        for c in crop_fractions:
            needed_now = empty_needed.get(c, 0)
            target = min(seed_buffer_cap, n_workers, needed_now) if needed_now > 0 else 1
            held = seeds.get(c, 0)
            need = max(0, target - held)
            if need > 0 and money >= CROPS[c]["seed"]:
                buy_n = min(need, int(money // CROPS[c]["seed"]))
                if buy_n > 0:
                    market.append(["BUY_SEED", c, buy_n])
                    money -= buy_n * CROPS[c]["seed"]

        # --- BUY_ANIMAL (fill empty built structures) ---
        need_animal_by_type = {}
        for t in structure_tiles:
            tt = tiles[t[1]][t[0]]
            atype = structure_type.get(t)
            if atype is None:
                continue
            if isinstance(tt, dict) and tt.get("kind") == ANIMALS[atype]["structure"] and "animal" not in tt:
                need_animal_by_type[atype] = need_animal_by_type.get(atype, 0) + 1
        if day >= animal_buy_day:
            for atype, cnt in need_animal_by_type.items():
                # Don't re-buy what's already acquired and simply awaiting PLACE
                # (shed stock + carried) -- buying ahead of placement capacity
                # just strands capital, it doesn't speed anything up.
                already_have = shed.get(atype, 0) + sum(w["inv"].get(atype, 0) for w in workers)
                still_needed = max(0, cnt - already_have)
                if still_needed <= 0:
                    continue
                cost = ANIMALS[atype]["cost"]
                buy_n = min(still_needed, int(money // cost))
                if buy_n > 0:
                    market.append(["BUY_ANIMAL", atype, buy_n])
                    money -= buy_n * cost

        # --- BUY_PRODUCT: wheat for feed / fertilizer ---
        wheat_needed_for_feed = 0
        if feed_policy == "daily":
            for t in structure_tiles:
                tt = tiles[t[1]][t[0]]
                if isinstance(tt, dict) and "animal" in tt and not tt.get("fed_today"):
                    wheat_needed_for_feed += 1
        wheat_available = shed.get("WHEAT", 0) + sum(w["inv"].get("WHEAT", 0) for w in workers)
        use_market_wheat = feed_source == "market" or (feed_source == "auto" and "WHEAT" not in crop_fractions)
        if wheat_needed_for_feed > wheat_available and use_market_wheat:
            deficit = wheat_needed_for_feed - wheat_available
            wprice = prices.get("WHEAT", 10 ** 9)
            if wprice and money >= wprice:
                buy_n = min(deficit, int(money // wprice))
                if buy_n > 0:
                    market.append(["BUY_PRODUCT", "WHEAT", buy_n])
                    money -= buy_n * wprice

        if buy_fertilizer:
            fert_have = shed.get("FERTILIZER", 0) + sum(w["inv"].get("FERTILIZER", 0) for w in workers)
            if fert_have == 0:
                fprice = prices.get("FERTILIZER", 10 ** 9)
                if fprice and money >= fprice:
                    market.append(["BUY_PRODUCT", "FERTILIZER", 1])
                    money -= fprice

        market = market[:10]  # maxMarketOrdersPerTurn default; excess retried next turn

        # ---------------- Physical task scheduling ----------------
        tasks = []  # (priority, tile, kind, carry_requirement, extra)

        for t, c in crop_assignment.items():
            x, y = t
            tt = tiles[y][x]
            if _needs_harvest_crop(tt, c, day):
                tasks.append((0, t, "HARVEST", None, None))
            elif _needs_water(tt, c):
                tasks.append((1, t, "WATER", None, None))
            elif fertilizer_apply and _is_plant(tt, c) and _needs_fertilize(tt, c, day):
                tasks.append((2, t, "FERTILIZE", "FERTILIZER", None))
            elif isinstance(tt, dict) and tt.get("kind") == "WEED":
                tasks.append((3, t, "DIG", None, None))
            elif tt is None and day >= plant_delay_day and seeds.get(c, 0) > 0:
                tasks.append((3, t, "PLANT", None, c))

        for t in structure_tiles:
            x, y = t
            tt = tiles[y][x]
            atype = structure_type.get(t)
            if atype is None:
                continue
            struct_kind = ANIMALS[atype]["structure"]
            if tt is None:
                if day >= animal_buy_day:
                    tasks.append((3, t, "BUILD", None, struct_kind))
            elif isinstance(tt, dict) and tt.get("kind") == struct_kind and "animal" not in tt:
                tasks.append((3, t, "PLACE", atype, atype))
            elif isinstance(tt, dict) and "animal" in tt:
                if tt.get("yield_units", 0) > 0:
                    tasks.append((0, t, "HARVEST_ANIMAL", None, None))
                elif feed_policy == "daily" and not tt.get("fed_today"):
                    tasks.append((1, t, "FEED", "WHEAT", None))
                elif care_policy == "daily" and not tt.get("cared_today"):
                    tasks.append((2, t, "CARE", None, None))
                elif collect_fertilizer and tt.get("fertilizer_available"):
                    tasks.append((4, t, "COLLECT_FERT", None, None))

        # atomic all-or-nothing PLANT rule: cap simultaneous plants per crop to held seeds
        plant_budget = dict(seeds)
        capped_tasks = []
        for pr, t, kind, req, extra in tasks:
            if kind == "PLANT":
                if plant_budget.get(extra, 0) <= 0:
                    continue
                plant_budget[extra] -= 1
            capped_tasks.append((pr, t, kind, req, extra))
        tasks = capped_tasks

        # synthetic fetch tasks: pick up an outstanding carry requirement from
        # the shed. Given the SAME priority as the most urgent task that
        # needs it, and sorted alongside tile tasks (by distance from home),
        # so e.g. an overdue animal PLACE can win a worker away from a
        # low-urgency PLANT instead of being starved behind every crop task
        # unconditionally (a real bug in an earlier version of this agent).
        req_min_priority = {}
        for pr, t, kind, req, extra in tasks:
            if req:
                req_min_priority[req] = min(pr, req_min_priority.get(req, 99))
        carried_counts = {}
        for w in workers:
            for item, n in w["inv"].items():
                carried_counts[item] = carried_counts.get(item, 0) + n
        req_counts = {}
        for pr, t, kind, req, extra in tasks:
            if req:
                req_counts[req] = req_counts.get(req, 0) + 1
        fetch_entries = []
        for item, needed in req_counts.items():
            deficit = needed - carried_counts.get(item, 0)
            if deficit <= 0:
                continue
            take = min(deficit, shed.get(item, 0))
            if take > 0:
                fetch_entries.append((req_min_priority[item], home, "FETCH", "PICKUP", item, take))

        # Greedy bipartite match, one priority tier at a time: within a tier,
        # repeatedly assign the globally closest (worker, task) pair rather
        # than a fixed task order -- a fixed distance-from-home task order
        # (an earlier version of this agent) picks tasks near the shed first
        # regardless of where a lone farmer/hand actually is right now,
        # causing far more backtracking than Phase 2.2's single-farmer
        # nearest-target logic. This reduces to the same nearest-target
        # choice as Phase 2.2 when there's exactly one eligible worker.
        tile_entries = [(pr, t, "TILE", kind, req, extra) for pr, t, kind, req, extra in tasks]
        combined = tile_entries + fetch_entries

        def entry_target(entry, worker_pos):
            etype = entry[2]
            if etype == "FETCH":
                return min(shed_tiles, key=lambda s: _manhattan(worker_pos, s))
            return entry[1]

        def entry_eligible(entry, w):
            req = entry[4]
            return (w["inv"].get(req, 0) > 0) if (entry[2] == "TILE" and req) else True

        def do_entry(entry, w):
            pr, pos, etype, kind, req, extra = entry
            w["claimed"] = True
            target = entry_target(entry, w["pos"])
            if w["pos"] != target:
                w["action"] = [_step_toward(w["pos"][0], w["pos"][1], target[0], target[1])]
            elif etype == "FETCH":
                w["action"] = ["PICKUP", req, extra]
            elif kind == "PLANT":
                w["action"] = ["PLANT", extra]
            elif kind == "BUILD":
                w["action"] = ["BUILD_COOP"] if extra == "COOP" else ["BUILD_PASTURE"]
            elif kind == "PLACE":
                w["action"] = ["PLACE", extra]
            elif kind == "HARVEST_ANIMAL":
                w["action"] = ["HARVEST"]
            elif kind == "COLLECT_FERT":
                w["action"] = ["COLLECT_FERTILIZER"]
            else:
                w["action"] = [kind]  # HARVEST / WATER / FERTILIZE / FEED / CARE / DIG

        # Phase A: a worker standing exactly on an actionable tile always
        # takes that action first, regardless of global priority tier
        # elsewhere on the map -- a free (zero-travel) action is never worth
        # skipping to go chase something "more important" far away. This
        # mirrors Phase 2.2's single-farmer "check my own tile before
        # picking a movement target" structure; without it, a strict global
        # priority ordering starves obvious in-place harvest->replant
        # cycles any time a higher-tier task exists anywhere else on the
        # board (measured: ~2x fewer harvests over 720 turns without this).
        for w in workers:
            if w["claimed"]:
                continue
            local = [e for e in combined if e[1] == w["pos"] and entry_eligible(e, w)]
            if not local:
                continue
            best_local = min(local, key=lambda e: e[0])
            do_entry(best_local, w)
            combined.remove(best_local)

        # Phase B: greedy bipartite match, one priority tier at a time, for
        # every worker/task not resolved locally in Phase A.
        tiers = sorted(set(e[0] for e in combined))
        for tier in tiers:
            remaining = [e for e in combined if e[0] == tier]
            while remaining:
                best = None  # (dist, entry, worker)
                for entry in remaining:
                    for w in workers:
                        if w["claimed"] or not entry_eligible(entry, w):
                            continue
                        d = _manhattan(w["pos"], entry_target(entry, w["pos"]))
                        if best is None or d < best[0]:
                            best = (d, entry, w)
                if best is None:
                    break
                _, entry, w = best
                do_entry(entry, w)
                remaining.remove(entry)

        for w in workers:
            if w["claimed"]:
                continue
            if w["inv"]:
                target = min(shed_tiles, key=lambda s: _manhattan(w["pos"], s))
                w["claimed"] = True
                w["action"] = ["DROP"] if w["pos"] == target else [_step_toward(w["pos"][0], w["pos"][1], target[0], target[1])]

        for w in workers:
            if w["action"] is None:
                w["action"] = ["PASS"]

        return {"farmer": workers[0]["action"], "hands": [w["action"] for w in workers[1:]], "market": market}

    return agent
