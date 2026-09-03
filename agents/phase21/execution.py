"""
Phase 21 execution layer -- a fresh, from-scratch worker/task-assignment
layer for this phase's new agent family (the realistic-opponent benchmark
AND the portfolio controller both use this, parameterized by a
`target_fn(day, obs, opponent_history) -> targets` callback).

Per this phase's explicit scope: does NOT import from agents/phase15/ (a
separate, shipped lineage) -- reuses only agents/phase2_3/common.py's
low-level tile/worker helpers (_home_tile, _shed_tiles, _owned_tiles,
structure_type_assignment, _needs_harvest_crop, _needs_water, _step_toward,
_fib, _manhattan -- the same primitives every phase since 9 has reused,
never copied), same as every prior phase's own execution layer. The
bounded multi-crop tile-pool assignment and worker-matching loop below are
freshly written for this phase (structurally similar to prior phases' own
versions, since it's the same standard greedy-bipartite-matching algorithm
this project has used since Phase 9 -- not a copy of any one file).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS, LAND_PRICES  # noqa: E402
from agents.phase21.risk_posture import posture_params  # noqa: E402
from agents.phase21.liquidation import planting_cutoff_day, tile_has_future_yield  # noqa: E402
from agents.phase2_3.common import (  # reuse, not duplicate -- noqa: E402
    _home_tile, _shed_tiles, _owned_tiles, structure_type_assignment,
    _needs_harvest_crop, _needs_water, _step_toward, _fib, _manhattan,
)


def bounded_multi_crop_tile_pool_assignment(owned_tiles, home, shed_tiles, crop_fractions,
                                             crop_tile_target, n_structures, tiles=None):
    """Splits the crop-tile pool among multiple crops by `crop_fractions`
    (dict crop -> fraction), bounded at `crop_tile_target` (extra tiles left
    fallow). STICKY: a tile that already holds a live crop keeps that crop
    regardless of the current schedule -- only vacant tiles are (re)assigned
    per the current fractions. Same STICKY-assignment discipline every
    multi-crop execution layer in this project has needed since it was first
    found necessary (a non-sticky version silently abandons growing crops
    the moment a schedule shifts, since agents/phase2_3/common.py's own
    `_needs_water`/`_needs_harvest_crop` gate on tile["crop"] == target)."""
    pool = [t for t in owned_tiles if t not in shed_tiles]
    pool_sorted = sorted(pool, key=lambda t: (_manhattan(t, home), t[1], t[0]))

    structure_kinds = {v["structure"] for v in ANIMALS.values()}

    def _is_existing_structure_tile(t):
        if tiles is None:
            return False
        tt = tiles[t[1]][t[0]]
        return isinstance(tt, dict) and (tt.get("kind") in structure_kinds or "animal" in tt)

    existing_structure_tiles = [t for t in pool_sorted if _is_existing_structure_tile(t)]
    rest_pool = [t for t in pool_sorted if t not in set(existing_structure_tiles)]
    n_new_structures_needed = max(0, n_structures - len(existing_structure_tiles))
    new_structure_tiles = rest_pool[:n_new_structures_needed]
    structure_tiles = existing_structure_tiles + new_structure_tiles

    crop_pool = sorted(t for t in rest_pool if t not in set(new_structure_tiles))

    crop_assignment = {}
    vacant_tiles = []
    existing_crop_tiles = []
    for t in crop_pool:
        existing_crop = None
        if tiles is not None:
            tt = tiles[t[1]][t[0]]
            if isinstance(tt, dict) and tt.get("kind") == "PLANT":
                existing_crop = tt.get("crop")
        if existing_crop is not None:
            crop_assignment[t] = existing_crop
            existing_crop_tiles.append(t)
        else:
            vacant_tiles.append(t)

    remaining_budget = max(0, crop_tile_target - len(existing_crop_tiles))
    vacant_tiles = vacant_tiles[:remaining_budget]

    idx = 0
    crops_sorted = sorted(crop_fractions.items(), key=lambda kv: -kv[1])
    remaining = len(vacant_tiles)
    for i, (crop, frac) in enumerate(crops_sorted):
        n = remaining if i == len(crops_sorted) - 1 else min(round(len(vacant_tiles) * frac), remaining)
        for _ in range(n):
            if idx >= len(vacant_tiles):
                break
            crop_assignment[vacant_tiles[idx]] = crop
            idx += 1
        remaining -= n
    return structure_tiles, crop_assignment


def make_execution_agent(target_fn, seed_buffer_cap=6):
    """`target_fn(day, obs, opponent_history) -> dict` with keys n_hands,
    land_quadrants, animals (dict), crop_tile_target, crop_fractions.
    Called once per turn -- everything below reacts to DYNAMIC targets."""
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

        # Minimal cash-safety throttle (same principle Phase 20 validated for
        # agents/phase15/ -- an independent, freshly-written version here, not
        # imported, per this phase's explicit scope of not building on
        # agents/phase15/): a day-0-style aggressive ramp with zero cash
        # discipline reliably produces a chronic near-$0 collapse (confirmed
        # directly while validating this module's own realistic-opponent
        # benchmark, results/phase21/PHASE21_SHARED_MARKET_PORTFOLIO_REPORT.md
        # Section 1). Freezes further hiring/land growth below a small
        # operating floor when cash is critical; never raises a target above
        # what target_fn proposed.
        #
        # PHASE 26: the reserve thresholds below are no longer fixed -- they
        # come from agents/phase21/risk_posture.py's live, fully-public
        # margin classifier (own money - opponent's, obs["farms"] is the same
        # shared list object for both players -- see that module's docstring).
        # BEHIND accepts more risk (smaller reserves); AHEAD protects the lead
        # (larger reserves); CLOSE uses the original fixed $150 both ways.
        opponent_money = obs["farms"][1 - player]["money"]
        posture, posture_p = posture_params(money, opponent_money)
        cash_danger_threshold = posture_p["cash_danger_threshold"]
        land_purchase_reserve = posture_p["land_purchase_reserve"]

        current_hands_now = len(me.get("hands", []))
        current_land_now = len(me.get("unlocked_quadrants", ["NW"]))
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

        # --- SELL FIRST (never let HIRE spam crowd the 10-order cap) ---
        # PHASE 28 NOTE: a wheat-reserve-for-feed fix (mirroring Phase 16's fix
        # for agents/phase15/) was diagnosed, attempted, and REVERTED here --
        # see results/phase28/PHASE28_REMAINING_LOSS_DIAGNOSIS_REPORT.md
        # Section 4 for the full account. The underlying inefficiency is real
        # (BUY_PRODUCT spend roughly double Submission G's in a traced seed),
        # but every gating attempt tried (unconditional, cash-threshold-gated,
        # day-and-cash-gated) made MORE seeds worse than it fixed on the full
        # 15-seed set -- reserving WHEAT removes exactly the small trickle of
        # SELL cash this agent's own ramp timing depends on at unpredictable
        # points across the game, not just the early window. Reported
        # honestly as a diagnosed-but-not-cheaply-fixable inefficiency, per
        # this phase's own explicit instruction not to force a change that
        # helps one seed at real risk to others.
        sellable_items = set(crops_in_play) | {ANIMALS[t]["product"] for t in animal_counts}
        for item in sorted(sellable_items):
            held = shed.get(item, 0)
            if held > 0:
                market.append(["SELL", item, held])

        # --- HIRE, affordability-capped ---
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

        # --- BUY_LAND -- pre-emptive reserve check (same principle as the cash-
        # safety throttle above): a raw affordability check let land purchases
        # drain cash from comfortable levels straight to $0 in one shot. ---
        n_extra_owned = len(me.get("unlocked_quadrants", [])) - 1
        target_extra = max(0, land_quadrants - 1)
        if n_extra_owned < target_extra and n_extra_owned < len(LAND_PRICES):
            next_cost = LAND_PRICES[n_extra_owned]
            if money >= next_cost + land_purchase_reserve:
                market.append(["BUY_LAND"])
                money -= next_cost

        # --- BUY_SEED (per crop in play) ---
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

        # --- BUY_ANIMAL ---
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

        # --- BUY_PRODUCT: wheat for feed (market-sourced, simple) ---
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

        # ---------------- Task scheduling: standard priority order ----------------
        tasks = []
        for t, c in crop_assignment.items():
            x, y = t
            tt = tiles[y][x]
            if _needs_harvest_crop(tt, c, day):
                tasks.append((0, t, "HARVEST", None, None))
            elif (isinstance(tt, dict) and tt.get("kind") == "PLANT" and CROPS[c]["ongoing"]
                  and not tile_has_future_yield(tt.get("planted_day", day), c, day)):
                # PHASE 27 per-tile endgame wind-down (replaces Phase 24/26's
                # blanket day-threshold DIG): an "ongoing" crop (STRAWBERRY/
                # TOMATO) never auto-clears on harvest -- explicitly DIG THIS
                # TILE only once ITS OWN remaining scheduled yields (computed
                # from ITS planted_day, per agents/phase21/liquidation.py) can
                # no longer land by day 29. A tile with real production left
                # keeps growing regardless of what day it is.
                tasks.append((3, t, "DIG", None, None))
            elif _needs_water(tt, c):
                tasks.append((1, t, "WATER", None, None))
            elif isinstance(tt, dict) and tt.get("kind") == "WEED":
                tasks.append((3, t, "DIG", None, None))
            elif tt is None and seeds.get(c, 0) > 0 and day <= planting_cutoff_day(c):
                # PHASE 27 per-crop planting cutoff (replaces Phase 24/26's
                # blanket LIQUIDATION_START_DAY): each crop gets its OWN last
                # plantable day (agents/phase21/liquidation.py), derived from
                # that crop's own first_yield_day -- WHEAT can keep being
                # planted much later than STRAWBERRY, since it matures faster.
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

        # Parallel-fetch (Phase 13's verified fix -- split fetch deficit across
        # up to n_workers separate entries so multiple free workers can each
        # become independently eligible in the same turn, not funneled through one).
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
