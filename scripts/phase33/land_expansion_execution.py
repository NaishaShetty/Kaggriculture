"""
Phase 33 Part C: TOMATO/GOOSE as a PURE ADDITION on the 4th land quadrant
(SE -- LAND_ORDER=["NE","SW","SE"], the most expensive at $4,000, currently
never bought by agents/phase21/'s shipped rungs, which cap land_quadrants at
3 -- confirmed by direct read of agents/phase21/portfolio.py's
_LAND_RUNGS = [(0,1),(6,2),(11,3)]).

New code, isolated from agents/phase21/ (not modified). Reuses
agents/phase21/execution.py's own primitives (bounded_multi_crop_tile_pool_
assignment, the unmodified tiered task-scheduling loop) unchanged -- the only
new logic here is TILE-POOL SPLITTING: the owned tile pool is partitioned by
quadrant (vendor_kaggriculture.kaggriculture._quadrant_of, read-only, not
modified) into a CORE pool (everything agents/phase21/'s own portfolio_targets
would normally use -- NW/NE/SW) and an EXTENSION pool (SE only, once bought).
bounded_multi_crop_tile_pool_assignment is called ONCE on the core pool with
portfolio_targets' own UNCHANGED crop_tile_target/crop_fractions/animals (so
STRAWBERRY/WHEAT/COW/SHEEP are byte-for-byte what Submission H would already
plan, never reduced), and independently on the extension pool with a 100%
TOMATO crop_fraction (TOMATO condition) or a fixed GOOSE structure count
(GOOSE condition) -- the two pools can never compete for the same tile or the
same fraction of the same tile-pool, by construction, which is what makes
this a genuine ADDITION rather than a reallocation.

n_hands is portfolio_targets' own value PLUS n_dedicated_hands (added on top,
never substituted) -- same "dedicated hands" convention Phase 32's Approach A
used, this time paired with genuinely new, non-competing work (a physically
separate tile pool), unlike Phase 32 where the new hands competed with
existing tiers on the SAME pool.

land_quadrants is forced to 4 once `day >= extension_trigger_day` (else left
at portfolio_targets' own value) -- agents/phase21/execution.py's existing
BUY_LAND logic (reused unchanged) purchases quadrants strictly in LAND_ORDER,
so requesting land_quadrants=4 buys NE/SW/SE in the normal order and the SE
purchase (the 4th, $4,000) only lands once the first three are already owned
-- no new land-purchase logic was needed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS, LAND_PRICES, _quadrant_of  # noqa: E402
from agents.phase21.risk_posture import posture_params  # noqa: E402
from agents.phase21.liquidation import planting_cutoff_day, tile_has_future_yield  # noqa: E402
from agents.phase21.execution import bounded_multi_crop_tile_pool_assignment  # noqa: E402
from agents.phase2_3.common import (  # reuse, not duplicate -- noqa: E402
    _home_tile, _shed_tiles, _owned_tiles, structure_type_assignment,
    _needs_harvest_crop, _needs_water, _step_toward, _fib, _manhattan,
)

EXTENSION_QUADRANT = "SE"  # LAND_ORDER[2] -- the 4th, never-bought quadrant
GOOSE_EXTENSION_COUNT = 6  # matches Phase 31's own isolated-GOOSE test scale


def make_extension_agent(target_fn, extension_type, n_dedicated_hands=2, extension_trigger_day=12):
    """extension_type: "TOMATO" (extension pool -> 100% TOMATO crop) or
    "GOOSE" (extension pool -> up to GOOSE_EXTENSION_COUNT COOPs)."""
    assert extension_type in ("TOMATO", "GOOSE")
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

        base_targets = target_fn(day, obs, state["opponent_history"])

        targets = dict(base_targets)
        targets["n_hands"] = base_targets["n_hands"] + n_dedicated_hands
        if day >= extension_trigger_day:
            targets["land_quadrants"] = max(base_targets["land_quadrants"], 4)

        opponent_money = obs["farms"][1 - player]["money"]
        posture, posture_p = posture_params(money, opponent_money)
        cash_danger_threshold = posture_p["cash_danger_threshold"]
        land_purchase_reserve = posture_p["land_purchase_reserve"]

        current_hands_now = len(me.get("hands", []))
        if money < cash_danger_threshold:
            targets = dict(targets)
            targets["n_hands"] = max(current_hands_now, min(targets["n_hands"], 5 + n_dedicated_hands))

        n_hands = targets["n_hands"]
        land_quadrants = targets["land_quadrants"]
        core_animal_counts = dict(base_targets["animals"])  # UNCHANGED from target_fn -- COW/SHEEP untouched
        core_crop_tile_target = base_targets["crop_tile_target"]  # UNCHANGED
        core_crop_fractions = base_targets["crop_fractions"]  # UNCHANGED

        home = _home_tile(board_size)
        shed_tiles = _shed_tiles(board_size)
        owned = _owned_tiles(tiles, board_size)
        core_owned = [t for t in owned if _quadrant_of(t[0], t[1], board_size) != EXTENSION_QUADRANT]
        ext_owned = [t for t in owned if _quadrant_of(t[0], t[1], board_size) == EXTENSION_QUADRANT]

        # --- CORE pool: byte-for-byte what target_fn's own plan would do ---
        core_n_structures = sum(core_animal_counts.values())
        core_structure_tiles, core_crop_assignment = bounded_multi_crop_tile_pool_assignment(
            core_owned, home, shed_tiles, core_crop_fractions, core_crop_tile_target, core_n_structures, tiles=tiles,
        )
        core_structure_type = structure_type_assignment(core_structure_tiles, core_animal_counts)

        # --- EXTENSION pool: SE quadrant only, never overlaps core ---
        ext_structure_tiles, ext_crop_assignment, ext_animal_counts = [], {}, {}
        if extension_type == "TOMATO":
            ext_structure_tiles, ext_crop_assignment = bounded_multi_crop_tile_pool_assignment(
                ext_owned, home, shed_tiles, {"TOMATO": 1.0}, len(ext_owned), 0, tiles=tiles,
            )
            ext_structure_type = {}
        else:  # GOOSE
            ext_animal_counts = {"GOOSE": GOOSE_EXTENSION_COUNT}
            ext_pool_sorted = sorted(ext_owned, key=lambda t: (_manhattan(t, home), t[1], t[0]))
            structure_kinds = {v["structure"] for v in ANIMALS.values()}

            def _is_existing_structure_tile(t):
                tt = tiles[t[1]][t[0]]
                return isinstance(tt, dict) and (tt.get("kind") in structure_kinds or "animal" in tt)

            existing = [t for t in ext_pool_sorted if _is_existing_structure_tile(t)]
            rest = [t for t in ext_pool_sorted if t not in set(existing)]
            n_needed = max(0, GOOSE_EXTENSION_COUNT - len(existing))
            ext_structure_tiles = existing + rest[:n_needed]
            ext_structure_type = structure_type_assignment(ext_structure_tiles, ext_animal_counts)

        # --- combine (disjoint by construction -- core/ext pools never share a tile) ---
        structure_tiles = core_structure_tiles + ext_structure_tiles
        structure_type = dict(core_structure_type)
        structure_type.update(ext_structure_type)
        crop_assignment = dict(core_crop_assignment)
        crop_assignment.update(ext_crop_assignment)
        animal_counts = dict(core_animal_counts)
        for k, v in ext_animal_counts.items():
            animal_counts[k] = animal_counts.get(k, 0) + v
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
            target = min(6, n_workers, empty_needed)
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
            buy_n = min(still_needed, int(money // cost))
            if buy_n > 0:
                market.append(["BUY_ANIMAL", atype, buy_n])
                money -= buy_n * cost

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

        # ---------------- Task scheduling: UNCHANGED from agents/phase21/execution.py ----------------
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
