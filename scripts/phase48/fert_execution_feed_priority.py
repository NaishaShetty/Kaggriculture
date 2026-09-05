"""
Phase 48 Part A: Phase 33 Part B's strictly-opportunistic (non-preempting)
fertilizer design, recomposed on top of Phase 46's FEED-priority execution
layer (scripts/phase46/feed_priority_execution.py) INSTEAD of the plain
execution shape Phase 33 originally used.

WHAT PHASE 33 ORIGINALLY COMPOSED WITH (confirmed by direct read before
building this file): scripts/phase33/fert_execution_opportunistic.py is a
freestanding reconstruction of agents/phase21/execution.py's own task-
scheduling loop -- it does NOT include Phase 36's BUY_ANIMAL cash pacer
(BUY_ANIMAL there is the original unthrottled, zero-reserve form: `buy_n =
min(still_needed, int(money // cost))`) and it does NOT include Phase 46's
FEED tier-0.5 reprioritization (FEED sits at tier 1, tied with WATER, same
as agents/phase21/execution.py before Phase 46). So "whatever execution
layer Phase 33 originally used" is the PRE-Phase-36, PRE-Phase-46 execution
shape -- this file's base is instead an exact copy of
scripts/phase46/feed_priority_execution.py (which already composes Phase
36's pacer + Phase 46's FEED tier 0.5), with Phase 33's own fertilizer
task additions layered on top, UNCHANGED from Phase 33's own design:

  FERTILIZE          tier 4 (strictly below every tier feed_priority_execution
                      uses -- HARVEST/HARVEST_ANIMAL=0, FEED=0.5, WATER=1,
                      CARE=2, DIG/PLANT/BUILD/PLACE=3)
  COLLECT_FERTILIZER  tier 5 (strictly below FERTILIZE, same relative order
                      Phase 30/33 used)

The same structural non-preemption argument Phase 33 Section 4 made still
holds unchanged here: the tiered greedy-assignment loop processes tiers in
strictly increasing order and cannot terminate while any unclaimed worker
remains eligible for any unmatched same-tier entry, so a worker reaching
tier 4/5 unclaimed is, by construction, one tier 0-3 (now including FEED's
own tier 0.5) had no eligible use for that turn. Fertilizer competes with
"passing" for idle worker-turns, never with a higher-priority task,
regardless of which lower-tier fix (Phase 36's pacer, Phase 46's FEED
reorder) sits underneath it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS, LAND_PRICES  # noqa: E402
from agents.phase21.risk_posture import posture_params  # noqa: E402
from agents.phase21.liquidation import planting_cutoff_day, tile_has_future_yield  # noqa: E402
from agents.phase21.execution import bounded_multi_crop_tile_pool_assignment  # noqa: E402
from agents.phase2_3.common import (  # reuse, not duplicate -- noqa: E402
    _home_tile, _shed_tiles, _owned_tiles, structure_type_assignment,
    _needs_harvest_crop, _needs_water, _step_toward, _fib, _manhattan,
)

FEED_BUFFER_DAYS = 2  # matches Phase 46's own FEED-priority pacer, unchanged
WHEAT_PRICE_ESTIMATE = 30
MAX_ANIMAL_PURCHASES_PER_TURN = 1

FERTILIZE_TIER = 4
COLLECT_FERT_TIER = 5


def _needs_fertilize(tile, crop, day):
    return isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == crop \
        and tile.get("fertilized_until_day", -1) < day


def make_fert_feed_priority_execution_agent(target_fn, fertilize=True, seed_buffer_cap=6):
    state = {"opponent_history": []}

    def set_opponent_history(history):
        state["opponent_history"] = history

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

        targets = target_fn(day, obs, state["opponent_history"])

        opponent_money = obs["farms"][1 - player]["money"]
        posture, posture_p = posture_params(money, opponent_money)
        cash_danger_threshold = posture_p["cash_danger_threshold"]
        land_purchase_reserve = posture_p["land_purchase_reserve"]

        current_hands_now = len(me.get("hands", []))
        if money < cash_danger_threshold:
            targets = dict(targets)
            targets["n_hands"] = max(current_hands_now, min(targets["n_hands"], 5))

        n_hands = targets["n_hands"]
        land_quadrants = targets["land_quadrants"]
        animal_counts = dict(targets["animals"])
        crop_tile_target = targets["crop_tile_target"]
        crop_fractions = targets["crop_fractions"]
        n_structures = sum(animal_counts.values())

        home = _home_tile(board_size)
        shed_tiles = _shed_tiles(board_size)
        owned = _owned_tiles(tiles, board_size)
        structure_tiles, crop_assignment = bounded_multi_crop_tile_pool_assignment(
            owned, home, shed_tiles, crop_fractions, crop_tile_target, n_structures, tiles=tiles,
        )
        structure_type = structure_type_assignment(structure_tiles, animal_counts)
        crops_in_play = sorted(set(crop_assignment.values()))

        positions = [tuple(me["farmer"])] + [tuple(h) for h in me.get("hands", [])]
        workers = []
        for i, pos in enumerate(positions):
            inv = invs[i] if i < len(invs) else {}
            workers.append({"pos": pos, "inv": inv, "claimed": False, "action": None})
        n_workers = len(workers)

        market = []

        sellable_items = set(crops_in_play) | {ANIMALS[t]["product"] for t in animal_counts}
        for item in sorted(sellable_items):
            held = shed.get(item, 0)
            if held > 0:
                market.append(["SELL", item, held])

        owned_animal_count = 0
        for row in tiles:
            for tt in row:
                if isinstance(tt, dict) and "animal" in tt:
                    owned_animal_count += 1

        def animal_reserve_now():
            return land_purchase_reserve + FEED_BUFFER_DAYS * owned_animal_count * WHEAT_PRICE_ESTIMATE

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

        n_extra_owned = len(me.get("unlocked_quadrants", [])) - 1
        target_extra = max(0, land_quadrants - 1)
        if n_extra_owned < target_extra and n_extra_owned < len(LAND_PRICES):
            next_cost = LAND_PRICES[n_extra_owned]
            if money >= next_cost + land_purchase_reserve:
                market.append(["BUY_LAND"])
                money -= next_cost

        empty_by_crop = {}
        for t, c in crop_assignment.items():
            if tiles[t[1]][t[0]] is None:
                empty_by_crop[c] = empty_by_crop.get(c, 0) + 1
        for crop, empty_needed in empty_by_crop.items():
            if empty_needed <= 0 or day > planting_cutoff_day(crop):
                continue
            target = min(seed_buffer_cap, n_workers, empty_needed)
            held = seeds.get(crop, 0)
            need = max(0, target - held)
            if need > 0 and money >= CROPS[crop]["seed"]:
                buy_n = min(need, int(money // CROPS[crop]["seed"]))
                if buy_n > 0:
                    market.append(["BUY_SEED", crop, buy_n])
                    money -= buy_n * CROPS[crop]["seed"]

        need_animal_by_type = {}
        for t in structure_tiles:
            tt = tiles[t[1]][t[0]]
            atype = structure_type.get(t)
            if atype is None:
                continue
            if isinstance(tt, dict) and tt.get("kind") == ANIMALS[atype]["structure"] and "animal" not in tt:
                need_animal_by_type[atype] = need_animal_by_type.get(atype, 0) + 1
        for atype, cnt in need_animal_by_type.items():
            already_have = shed.get(atype, 0) + sum(w["inv"].get(atype, 0) for w in workers)
            still_needed = max(0, cnt - already_have)
            if still_needed <= 0:
                continue
            cost = ANIMALS[atype]["cost"]
            r = animal_reserve_now()
            affordable_units = int((money - r) // cost) if money > r else 0
            buy_n = min(still_needed, MAX_ANIMAL_PURCHASES_PER_TURN, affordable_units)
            if buy_n > 0:
                market.append(["BUY_ANIMAL", atype, buy_n])
                money -= buy_n * cost
                owned_animal_count += buy_n

        wheat_needed_for_feed = 0
        for t in structure_tiles:
            tt = tiles[t[1]][t[0]]
            if isinstance(tt, dict) and "animal" in tt and not tt.get("fed_today"):
                wheat_needed_for_feed += 1
        wheat_available = shed.get("WHEAT", 0) + sum(w["inv"].get("WHEAT", 0) for w in workers)
        if wheat_needed_for_feed > wheat_available:
            deficit = wheat_needed_for_feed - wheat_available
            wprice = prices.get("WHEAT", 10 ** 9)
            if wprice and money >= wprice:
                buy_n = min(deficit, int(money // wprice))
                if buy_n > 0:
                    market.append(["BUY_PRODUCT", "WHEAT", buy_n])
                    money -= buy_n * wprice

        market = market[:10]

        # ---------------- Task scheduling ----------------
        tasks = []
        for t, c in crop_assignment.items():
            x, y = t
            tt = tiles[y][x]
            if _needs_harvest_crop(tt, c, day):
                tasks.append((0, t, "HARVEST", None, None))
            elif (isinstance(tt, dict) and tt.get("kind") == "PLANT" and CROPS[c]["ongoing"]
                  and not tile_has_future_yield(tt.get("planted_day", day), c, day)):
                tasks.append((3, t, "DIG", None, None))
            elif _needs_water(tt, c):
                tasks.append((1, t, "WATER", None, None))
            elif isinstance(tt, dict) and tt.get("kind") == "WEED":
                tasks.append((3, t, "DIG", None, None))
            elif tt is None and seeds.get(c, 0) > 0 and day <= planting_cutoff_day(c):
                tasks.append((3, t, "PLANT", None, c))
            elif fertilize and _needs_fertilize(tt, c, day):
                tasks.append((FERTILIZE_TIER, t, "FERTILIZE", "FERTILIZER", None))

        for t in structure_tiles:
            x, y = t
            tt = tiles[y][x]
            atype = structure_type.get(t)
            if atype is None:
                continue
            struct_kind = ANIMALS[atype]["structure"]
            if tt is None:
                tasks.append((3, t, "BUILD", None, struct_kind))
            elif isinstance(tt, dict) and tt.get("kind") == struct_kind and "animal" not in tt:
                tasks.append((3, t, "PLACE", atype, atype))
            elif isinstance(tt, dict) and "animal" in tt:
                if tt.get("yield_units", 0) > 0:
                    tasks.append((0, t, "HARVEST_ANIMAL", None, None))
                elif not tt.get("fed_today"):
                    tasks.append((0.5, t, "FEED", "WHEAT", None))
                elif not tt.get("cared_today"):
                    tasks.append((2, t, "CARE", None, None))
                elif fertilize and tt.get("fertilizer_available"):
                    tasks.append((COLLECT_FERT_TIER, t, "COLLECT_FERT", None, None))

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
            available = min(deficit, shed.get(item, 0))
            if available <= 0:
                continue
            n_entries = min(available, n_workers)
            base = available // n_entries
            remainder = available % n_entries
            for i in range(n_entries):
                qty = base + (1 if i < remainder else 0)
                if qty > 0:
                    fetch_entries.append((req_min_priority[item], home, "FETCH", "PICKUP", item, qty))

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

    agent.set_opponent_history = set_opponent_history
    return agent
