"""
Phase 15 execution layer: generalizes `scripts/phase11/multi_resource_agent.py`
(bounded single-crop tile-pool assignment, SELL-before-HIRE, affordability-
capped HIRE -- all reused, not rewritten) to (a) a MULTI-crop tile pool
driven by the macro controller's day-indexed crop_fractions, (b) DYNAMIC
targets recomputed every turn from `agents.phase15.macro_controller
.compute_targets` instead of fixed values baked in at construction time, and
(c) Phase 13's verified PARALLEL FETCH fix
(`scripts/phase13/fixed_agent.py`'s fetch_entries block, reused import-only
per this phase's brief) -- needed here because this controller operates at
real animal scale (10-14), exactly where Phase 13 proved the single-fetch-
entry-per-item cap becomes a binding bottleneck (Phase 14 already confirmed
it does NOT matter at Submission C's actual 6-animal ceiling, but this agent
targets 10-14, squarely inside the range where Phase 13's fix produced a
clean, monotonic +6.6 to +26.6-point improvement).

Everything not explicitly called out above (worker/task priority order,
greedy nearest-worker-to-nearest-entry matching, buy/build/place logic) is
copied from `scripts/phase11/multi_resource_agent.py` /
`scripts/phase13/fixed_agent.py` unchanged in structure.

New code only. Does not edit scripts/phase11/, scripts/phase13/,
agents/phase2_3/common.py, or agents/phase2_4/common.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS, LAND_PRICES  # noqa: E402
from agents.phase2_3.common import (  # reuse, not duplicate -- noqa: E402
    _home_tile, _shed_tiles, _owned_tiles, structure_type_assignment,
    _needs_harvest_crop, _needs_water, _step_toward, _fib, _manhattan,
)
from agents.phase15.endgame import is_liquidating, should_dig_ongoing_crop  # noqa: E402
from agents.phase15.liquidity_guard import apply_liquidity_guard, land_purchase_affordable  # noqa: E402


def bounded_multi_crop_tile_pool_assignment(owned_tiles, home, shed_tiles, crop_fractions,
                                             crop_tile_target, n_structures, tiles=None):
    """Like `scripts/phase11/multi_resource_agent.py::bounded_tile_pool_assignment`,
    generalized to split the crop-tile pool among MULTIPLE crops by
    `crop_fractions` (a dict crop -> fraction, summing to ~1.0), instead of a
    single crop. Same ordering discipline (nearest-to-home first, structure
    tiles carved out first) -- tiles beyond `crop_tile_target` are left
    FALLOW (never planted), matching the bounded-footprint real-data shape
    Phase 11 established, not an unbounded fill.

    STICKY ASSIGNMENT (critical fix found during this phase's own validation,
    documented here rather than silently patched): the macro controller's
    crop_fractions change day-to-day (Step 1's schedule ramps WHEAT/MELON ->
    STRAWBERRY over time). An early version of this function re-derived
    EVERY tile's target crop from the CURRENT schedule on every call -- which
    silently reassigned tiles that already had a real, growing crop planted
    on them to a DIFFERENT target crop the moment the schedule shifted.
    `agents/phase2_3/common.py::_needs_water`/`_needs_harvest_crop` both
    gate on `tile["crop"] == crop`, so a tile whose target crop no longer
    matches what's ACTUALLY planted on it silently stops being watered or
    harvested -- it just decays to WEED and gets replanted, burning cash on
    redundant seed purchases with zero production benefit. First smoke test
    (`scripts/phase15/smoke_test.py`) surfaced this directly: STRAWBERRY seed
    spend was $5,300 for only ~30 STRAWBERRY tiles (should be roughly
    one-time per tile for an "ongoing" crop), and final money came out
    LOWER than Submission C's baseline despite $21,996 gross sell revenue.
    THE FIX: a tile that already holds an actual, live crop (`tiles[y][x]
    .get("crop")`) keeps that crop as its assignment regardless of what the
    current schedule's fractions say -- the schedule only governs which crop
    gets planted on tiles that are EMPTY (or in the process of dying to WEED,
    at which point they re-enter the assignable pool naturally once cleared).
    """
    pool = [t for t in owned_tiles if t not in shed_tiles]
    pool_sorted = sorted(pool, key=lambda t: (_manhattan(t, home), t[1], t[0]))

    # STICKY STRUCTURE TILES too, same reasoning as crop stickiness above: a
    # tile already committed to an animal structure (COOP/PASTURE kind, or
    # already holding a live animal) must stay a structure tile even if
    # `n_structures` later shrinks the schedule's target below the current
    # committed count -- otherwise it silently falls into the crop pool,
    # a growing/living animal investment gets abandoned, and BUILD tasks
    # never fire for it again. Structure kinds are read directly from
    # ANIMALS[*]["structure"] (COOP, PASTURE), not hardcoded.
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
    crop_tiles_candidate = crop_pool

    crop_assignment = {}
    vacant_tiles = []
    existing_crop_tiles = []
    for t in crop_tiles_candidate:
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

    # Existing planted tiles always count toward (and can exceed) the target --
    # already-planted tiles are never un-planted (same non-regression discipline
    # as everywhere else in this project). Only fill vacant tiles up to whatever
    # budget remains under crop_tile_target.
    remaining_budget = max(0, crop_tile_target - len(existing_crop_tiles))
    vacant_tiles = vacant_tiles[:remaining_budget]

    idx = 0
    crops_sorted = sorted(crop_fractions.items(), key=lambda kv: -kv[1])
    remaining = len(vacant_tiles)
    for i, (crop, frac) in enumerate(crops_sorted):
        if i == len(crops_sorted) - 1:
            n = remaining
        else:
            n = round(len(vacant_tiles) * frac)
            n = min(n, remaining)
        for _ in range(n):
            if idx >= len(vacant_tiles):
                break
            crop_assignment[vacant_tiles[idx]] = crop
            idx += 1
        remaining -= n
    return structure_tiles, crop_assignment


def make_execution_agent(target_fn, seed_buffer_cap=6):
    """`target_fn(day, opponent_history) -> dict` (macro_controller.compute_targets
    or a drop-in) is called ONCE PER TURN to get the current day's proportional
    targets -- everything below reacts to those DYNAMIC targets instead of
    fixed construction-time values. `opponent_history` must be supplied by the
    caller via the returned agent's `set_opponent_history` hook (the adapter
    wires this to its own agents.phase3.opponent_observation.OpponentObservationLogger)."""
    state = {"opponent_history": [], "liquidity_guard_activations": 0}

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

        targets = target_fn(day, state["opponent_history"])

        # --- Phase 20 liquidity guard (agents/phase15/liquidity_guard.py): re-checked
        # every turn, freezes further hiring/land-buying this turn if cash is
        # critically low -- see that module's docstring for why this is a per-turn,
        # re-armable throttle rather than a one-time F-005-style halving. ---
        current_hands_now = len(me.get("hands", []))
        current_land_now = len(me.get("unlocked_quadrants", ["NW"]))
        targets, _liquidity_guard_triggered = apply_liquidity_guard(
            targets, money, current_hands_now, current_land_now)
        if _liquidity_guard_triggered:
            state["liquidity_guard_activations"] += 1

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

        # --- HOME-GROWN WHEAT FEED RESERVE (fix found during this phase's own
        # diagnostic, see agents/phase15/PHASE16 notes in the module docstring
        # below): the pre-fix version always sold 100% of harvested WHEAT
        # immediately (the pre-fix "feed_source='market'" mode meant wheat was
        # never reserved), then separately BOUGHT wheat back from the market
        # for every single
        # feed need -- Phase 16's financial-ledger read found this was the
        # single largest cost line in the whole agent ($17,015 of $46,949 total
        # spend on one seed, at ~$42/unit bought back, having just sold the
        # same item moments earlier). THE FIX: reserve enough already-held
        # WHEAT to cover TODAY's actual feed need (computed once, up front)
        # before generating any SELL order for it; only the genuine surplus
        # beyond that gets sold. The market top-up below still covers any
        # remaining deficit unconditionally -- this is a strict improvement,
        # never a source of new starvation risk (a shortfall is still made up
        # from the market exactly as before, it's just no longer double-paid).
        wheat_needed_for_feed = sum(
            1 for t in structure_tiles
            if isinstance(tiles[t[1]][t[0]], dict) and "animal" in tiles[t[1]][t[0]]
            and not tiles[t[1]][t[0]].get("fed_today")
        )
        held_wheat = shed.get("WHEAT", 0)
        wheat_kept_for_feed = min(held_wheat, wheat_needed_for_feed)

        # --- SELL FIRST (Phase 9 fix, reused): never let HIRE spam crowd the 10-order cap ---
        sellable_items = set(crops_in_play) | {ANIMALS[t]["product"] for t in animal_counts}
        for item in sorted(sellable_items):
            held = shed.get(item, 0)
            reserve = wheat_kept_for_feed if item == "WHEAT" else 0
            sellable = max(0, held - reserve)
            if sellable > 0:
                market.append(["SELL", item, sellable])

        # --- HIRE (Phase 9 fix, reused): cap to what's actually affordable this turn ---
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

        # --- BUY_LAND -- gated by a pre-emptive reserve check (Phase 20 liquidity
        # guard, agents/phase15/liquidity_guard.py::land_purchase_affordable):
        # a raw "can we technically afford it" check let past land purchases
        # drain cash from comfortable levels straight to $0 in one shot, which
        # then stalled hiring entirely (hands reset to [] daily; a $0-cash day
        # can't afford even the cheapest possible hire). Requiring a reserve to
        # remain afterward defers the purchase a few turns instead. ---
        n_extra_owned = len(me.get("unlocked_quadrants", [])) - 1
        target_extra = max(0, land_quadrants - 1)
        if n_extra_owned < target_extra and n_extra_owned < len(LAND_PRICES):
            next_cost = LAND_PRICES[n_extra_owned]
            if land_purchase_affordable(money, next_cost):
                market.append(["BUY_LAND"])
                money -= next_cost

        # --- BUY_SEED (per crop in play) -- suppressed once liquidating (Phase 19
        # endgame mechanic, agents/phase15/endgame.py): no point buying more seed
        # for tiles that won't be replanted from here on. ---
        empty_by_crop = {}
        if not is_liquidating(day):
            for t, c in crop_assignment.items():
                if tiles[t[1]][t[0]] is None:
                    empty_by_crop[c] = empty_by_crop.get(c, 0) + 1
        for crop, empty_needed in empty_by_crop.items():
            if empty_needed <= 0:
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

        # --- BUY_PRODUCT: wheat for feed, topping up the home-grown reserve above.
        # Always covers any remaining deficit from the market -- reserving
        # home-grown wheat first (above) and topping up the gap here are
        # complementary, not alternative, strategies; there is no longer a
        # mode where a shortfall goes unfed because market buying was disabled
        # (that all-or-nothing framing was itself part of the pre-fix design
        # and is not reused here). ---
        wheat_available = wheat_kept_for_feed + sum(w["inv"].get("WHEAT", 0) for w in workers)
        if wheat_needed_for_feed > wheat_available:
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
            elif (isinstance(tt, dict) and tt.get("kind") == "PLANT" and CROPS[c]["ongoing"]
                  and should_dig_ongoing_crop(day)):
                # Phase 19 endgame mechanic: an "ongoing" crop (STRAWBERRY/TOMATO)
                # never auto-clears itself (see agents/phase15/endgame.py's
                # module docstring) -- explicitly clear it once there's no time
                # left in the season for it to matter, matching the observed
                # 0-2-tile day-29 shape in the fresh ladder data instead of
                # leaving it standing, unharvested-from-here-on, forever.
                tasks.append((3, t, "DIG", None, None))
            elif _needs_water(tt, c):
                tasks.append((1, t, "WATER", None, None))
            elif isinstance(tt, dict) and tt.get("kind") == "WEED":
                tasks.append((3, t, "DIG", None, None))
            elif tt is None and seeds.get(c, 0) > 0 and not is_liquidating(day):
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

        # ===================== PARALLEL FETCH FIX (Phase 13, reused) =====================
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
        # ===================== END PARALLEL FETCH FIX =====================

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
    agent._state = state
    return agent
