"""
Phase 11 execution layer: a combined crop+animal, BOUNDED-tile-footprint
agent, matching real opponent moushun_chen's actual day-15/day-20 shape
(results/phase6/moushun_chen/days_opponent.csv: hands=10, land_quadrants=3
(4 total), STRAWBERRY tiles=20 (day15) -> 28 (day20), animals COW=6,
SHEEP=5 (day15) -> SHEEP=8 (day20)) rather than an invented allocation.

WHY THIS IS NEW CODE, NOT A REUSE OF scripts/phase9/common.py UNCHANGED:
`agents/phase2_3/common.py::tile_pool_assignment` (imported unchanged by
Phase 9's `make_high_scale_agent`) always allocates 100% of the non-
structure owned tile pool among whatever crops are listed in
`crop_fractions` -- there is no way to express "commit only N tiles to
this crop and leave the rest of the land fallow." moushun_chen's real
shape deliberately does NOT fill the whole 4-quadrant board with
STRAWBERRY (only 20-28 of the ~96 available tiles) -- confirmed directly
from the replay CSV, not assumed. Reusing the unbounded frozen helper here
would silently replace "match the real portfolio shape" with "max out the
board with STRAWBERRY," a materially different (and invented) config the
brief explicitly says not to build. Per this phase's own brief ("if you
can't build a working combined config within the existing additive
helpers... describe exactly what minimal new code would be needed rather
than forcing something"): the minimal fix is a bounded pool-assignment
function, used here, imported and reused for everything ELSE (worker/task
scheduling, hire/land/sell/buy logic) exactly as
`scripts/phase9/common.py::make_high_scale_agent` already established --
this file duplicates that agent's structure with exactly one change (the
tile-pool step), not a rewrite of task-assignment logic. All the
SELL-before-HIRE / affordability-capped-HIRE fixes Phase 9 required are
carried over unchanged.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS, LAND_PRICES  # noqa: E402
from agents.phase2_3.common import (  # reuse, not duplicate -- noqa: E402
    _home_tile, _shed_tiles, _owned_tiles, structure_type_assignment,
    _needs_harvest_crop, _needs_water, _step_toward, _fib, _manhattan,
)


def bounded_tile_pool_assignment(owned_tiles, home, shed_tiles, crop, crop_tile_target, n_structures):
    """Like `agents/phase2_3/common.py::tile_pool_assignment`, but commits
    at most `crop_tile_target` tiles to `crop` (nearest-to-home first,
    after structure tiles are carved out, same ordering the frozen helper
    already uses) and leaves everything beyond that FALLOW (unassigned --
    never planted) instead of filling the entire remaining pool. Single
    crop only (this phase's config never needs multi-crop fractions)."""
    pool = [t for t in owned_tiles if t not in shed_tiles]
    pool_sorted = sorted(pool, key=lambda t: (_manhattan(t, home), t[1], t[0]))
    structure_tiles = pool_sorted[:n_structures]
    crop_pool = sorted(pool_sorted[n_structures:])
    crop_tiles = crop_pool[:crop_tile_target]
    crop_assignment = {t: crop for t in crop_tiles}
    return structure_tiles, crop_assignment


def make_multi_resource_agent(crop="STRAWBERRY", crop_tile_target=24, n_hands=0,
                               land_quadrants=0, land_buy_day=0,
                               animals=None, animal_buy_day=0, feed_source="auto", seed_buffer_cap=6):
    """SELL-before-HIRE, affordability-capped-HIRE (same fixes as Phase 9's
    make_high_scale_agent), BOUNDED crop-tile-footprint variant. Everything
    else (buying, selling, task scheduling, worker assignment) is
    unchanged from Phase 9's agent, which itself is unchanged from the
    frozen agent's own logic except for those two disclosed fixes."""
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
        structure_tiles, crop_assignment = bounded_tile_pool_assignment(
            owned, home, shed_tiles, crop, crop_tile_target, n_structures,
        )
        structure_type = structure_type_assignment(structure_tiles, animal_counts)

        positions = [tuple(me["farmer"])] + [tuple(h) for h in me.get("hands", [])]
        workers = []
        for i, pos in enumerate(positions):
            inv = invs[i] if i < len(invs) else {}
            workers.append({"pos": pos, "inv": inv, "claimed": False, "action": None})
        n_workers = len(workers)

        market = []

        # --- SELL FIRST (Phase 9 fix 1): never let HIRE spam crowd the 10-order cap ---
        n_animals_alive = sum(
            1 for t in structure_tiles if isinstance(tiles[t[1]][t[0]], dict) and "animal" in tiles[t[1]][t[0]]
        )
        wheat_reserved = n_animals_alive if (feed_source != "market" and n_animals_alive) else 0
        sellable_items = {crop} | {ANIMALS[t]["product"] for t in animal_counts}
        for item in sorted(sellable_items):
            held = shed.get(item, 0)
            reserve = wheat_reserved if item == "WHEAT" else 0
            sellable = max(0, held - reserve)
            if sellable > 0:
                market.append(["SELL", item, sellable])

        # --- HIRE (Phase 9 fix 2): cap to what's actually affordable this turn ---
        current_hands = len(me.get("hands", []))
        need_hire_target = max(0, n_hands - current_hands)
        affordable, cum = 0, 0.0
        for i in range(need_hire_target):
            c = _fib(current_hands + i)
            if cum + c > money:
                break
            cum += c
            affordable += 1
        for _ in range(affordable):
            market.append(["HIRE"])
        money -= cum

        # --- BUY_LAND (unchanged) ---
        n_extra_owned = len(me.get("unlocked_quadrants", [])) - 1
        if n_extra_owned < land_quadrants and day >= land_buy_day and n_extra_owned < len(LAND_PRICES):
            next_cost = LAND_PRICES[n_extra_owned]
            if money >= next_cost:
                market.append(["BUY_LAND"])
                money -= next_cost

        # --- BUY_SEED (unchanged) ---
        empty_needed = sum(1 for t in crop_assignment if tiles[t[1]][t[0]] is None)
        if empty_needed > 0:
            target = min(seed_buffer_cap, n_workers, empty_needed)
            held = seeds.get(crop, 0)
            need = max(0, target - held)
            if need > 0 and money >= CROPS[crop]["seed"]:
                buy_n = min(need, int(money // CROPS[crop]["seed"]))
                if buy_n > 0:
                    market.append(["BUY_SEED", crop, buy_n])
                    money -= buy_n * CROPS[crop]["seed"]

        # --- BUY_ANIMAL (unchanged) ---
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
                already_have = shed.get(atype, 0) + sum(w["inv"].get(atype, 0) for w in workers)
                still_needed = max(0, cnt - already_have)
                if still_needed <= 0:
                    continue
                cost = ANIMALS[atype]["cost"]
                buy_n = min(still_needed, int(money // cost))
                if buy_n > 0:
                    market.append(["BUY_ANIMAL", atype, buy_n])
                    money -= buy_n * cost

        # --- BUY_PRODUCT: wheat for feed (unchanged) ---
        wheat_needed_for_feed = 0
        for t in structure_tiles:
            tt = tiles[t[1]][t[0]]
            if isinstance(tt, dict) and "animal" in tt and not tt.get("fed_today"):
                wheat_needed_for_feed += 1
        wheat_available = shed.get("WHEAT", 0) + sum(w["inv"].get("WHEAT", 0) for w in workers)
        use_market_wheat = feed_source == "market" or (feed_source == "auto" and crop != "WHEAT")
        if wheat_needed_for_feed > wheat_available and use_market_wheat:
            deficit = wheat_needed_for_feed - wheat_available
            wprice = prices.get("WHEAT", 10 ** 9)
            if wprice and money >= wprice:
                buy_n = min(deficit, int(money // wprice))
                if buy_n > 0:
                    market.append(["BUY_PRODUCT", "WHEAT", buy_n])
                    money -= buy_n * wprice

        market = market[:10]

        # ---------------- Task scheduling: identical priority order to the frozen agent ----------------
        tasks = []
        for t, c in crop_assignment.items():
            x, y = t
            tt = tiles[y][x]
            if _needs_harvest_crop(tt, c, day):
                tasks.append((0, t, "HARVEST", None, None))
            elif _needs_water(tt, c):
                tasks.append((1, t, "WATER", None, None))
            elif isinstance(tt, dict) and tt.get("kind") == "WEED":
                tasks.append((3, t, "DIG", None, None))
            elif tt is None and seeds.get(c, 0) > 0:
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
                elif not tt.get("fed_today"):
                    tasks.append((1, t, "FEED", "WHEAT", None))
                elif not tt.get("cared_today"):
                    tasks.append((2, t, "CARE", None, None))

        plant_budget = dict(seeds)
        capped_tasks = []
        for pr, t, kind, req, extra in tasks:
            if kind == "PLANT":
                if plant_budget.get(extra, 0) <= 0:
                    continue
                plant_budget[extra] -= 1
            capped_tasks.append((pr, t, kind, req, extra))
        tasks = capped_tasks

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
            else:
                w["action"] = [kind]

        for w in workers:
            if w["claimed"]:
                continue
            local = [e for e in combined if e[1] == w["pos"] and entry_eligible(e, w)]
            if not local:
                continue
            best_local = min(local, key=lambda e: e[0])
            do_entry(best_local, w)
            combined.remove(best_local)

        tiers = sorted(set(e[0] for e in combined))
        for tier in tiers:
            remaining = [e for e in combined if e[0] == tier]
            while remaining:
                best = None
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
