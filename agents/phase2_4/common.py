"""
Phase 2.4 market-aware agent framework.

Reuses the tested, unmodified tile-allocation and worker-task-scheduling
helpers from `agents/phase2_3/common.py` (import, not copy -- genuine reuse
of working machinery, per the Phase 2.4 brief's instruction). Writes its own
`make_agent`, structurally identical to Phase 2.3's, with exactly one
addition: the hardcoded "sell 100% of shed inventory every turn" block is
replaced by a pluggable `sell_policy`. Everything else (labor, land,
animals, feed/care, fertilizer, task scheduling) is byte-for-byte the same
policy as Phase 2.3 -- so any difference in outcome between a Phase 2.4 agent
and its Phase 2.3 ancestor at `sell_policy={"mode": "passive"}` is
attributable to this module's own logic, not a silent behavior drift, and
is a build-time regression check (see `scripts/phase2_4_smoke.py`).

Per `docs/03_control_contract_and_change_policy.md` rule 4 ("new agents are
separate experimental artifacts") and the precedent already set by
`agents/phase2_2/common.py` -> `agents/phase2_3/common.py`: this is a new,
separate module, never an in-place edit of the frozen `agents/phase2_3/`.

## Selling policy (`sell_policy` dict)

  - `mode="passive"` (default, reproduces Phase 2.3 exactly): sell every
    unit of every sellable item in the shed, every turn.
  - `mode="threshold"`: sell an item only when its CURRENT market price is
    >= `threshold_frac` (default 1.0) times that item's documented BASE
    price (`MARKET_PARAMS[item]["base"]`, VERIFIED against real episodes in
    Phase 2.4's Stage A market-formula check). Below threshold, held units
    accumulate in the shed instead of selling at a depressed price.
  - `mode="batch"`: sell an item only on days where
    `day % batch_interval_days == 0` (default 3); every other day, held
    units accumulate.
  - `mode="threshold_batch"`: sell whenever EITHER the threshold OR the
    batch-day condition is met (whichever comes first) -- avoids holding
    forever if a price never recovers to threshold.
  - `mode="tick_timed"`: sell only on turns aligned to the documented town
    consumption schedule (`tick_interval`, default 4 = townShopSellInterval),
    with `align="after"` (sell the turn right after a consumption tick, when
    that tick's price bump is freshest) or `align="before"` (sell the turn
    right before the next tick, i.e. the stalest price since the last one) --
    a deliberate contrast pair for Stage E's town-demand-timing question.
  - `overflow_safety` (default True): regardless of mode, force-sell an
    item's ENTIRE held quantity if shed occupancy (summed across all items)
    would otherwise exceed `overflow_safety_frac` (default 0.85) of
    `shedCapacity` (100, VERIFIED) after this turn's harvest/production --
    i.e. a rational agent doesn't let goods rot to shed-capacity overflow
    by policy accident. Set `overflow_safety=False` for Phase 2.4's Stage D
    cells that deliberately want to test whether holding CAN cause real
    overflow/waste (the brief's stated goal for that stage) -- with it off,
    `mode="threshold"`/`"batch"` can genuinely lose product to overflow
    discard, which is the point of that experiment.

Every selling decision above is a pure function of the CURRENT turn's public
market price and this player's own private shed state -- no path memory,
no opponent-specific behavior, consistent with the project's existing
stateless-agent convention (see agents/phase2_2/common.py, agents/phase2_3/common.py).
"""
from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS, LAND_PRICES, MARKET_PARAMS
from agents.phase2_3.common import (  # reuse, not duplicate
    _home_tile, _shed_tiles, _owned_tiles, tile_pool_assignment, structure_type_assignment,
    _is_plant, _needs_harvest_crop, _needs_water, _needs_fertilize, _step_toward, _fib,
)

SHED_CAPACITY = 100  # documented default (kaggriculture.json); never overridden by any Phase 2.4 experiment


def _sell_quantity(item, held, price, day, policy, turn=None):
    """How many of `held` units of `item` to SELL this turn, under `policy`."""
    if held <= 0:
        return 0
    mode = policy.get("mode", "passive")
    if mode == "passive":
        return held
    base = MARKET_PARAMS[item]["base"]
    if mode == "threshold":
        return held if price >= policy.get("threshold_frac", 1.0) * base else 0
    if mode == "batch":
        interval = max(1, policy.get("batch_interval_days", 3))
        return held if day % interval == 0 else 0
    if mode == "tick_timed":
        return held if _tick_should_sell(turn, policy) else 0
    if mode == "threshold_batch":
        interval = max(1, policy.get("batch_interval_days", 3))
        hit_threshold = price >= policy.get("threshold_frac", 1.0) * base
        hit_batch_day = day % interval == 0
        return held if (hit_threshold or hit_batch_day) else 0
    return held  # unknown mode -> fail safe to passive, never silently hold everything forever


def _tick_should_sell(turn, policy):
    """Stage E: sell only on turns aligned to the documented town-consumption
    schedule (VERIFIED, Phase 2.4 Stage A part 2 -- town consumption strictly
    REDUCES market inventory, which raises price when inventory is already
    >= I0 post-sale, i.e. every tick nudges price back toward/above base).
    align='after' sells the turn immediately following a tick (price already
    bumped up); align='before' sells the turn immediately preceding one
    (price still at its pre-tick low) -- a deliberate contrast pair."""
    interval = policy.get("tick_interval", 4)  # townShopSellInterval default
    align = policy.get("align", "after")
    phase = (turn - 1) % interval  # -1: the Stage A off-by-one, town consumption lands on turn t
    # after: sell on the turn right after a consumption tick (phase == 1)
    # before: sell on the turn right before the next tick (phase == interval-1)
    return phase == 1 if align == "after" else phase == interval - 1


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
    sell_policy=None,
):
    """Identical signature to agents/phase2_3/common.py::make_agent plus `sell_policy`."""
    crop_fractions = {} if crops is None else ({crops: 1.0} if isinstance(crops, str) else dict(crops))
    animal_counts = dict(animals) if animals else {}
    n_structures = sum(animal_counts.values())
    policy = dict(sell_policy) if sell_policy else {"mode": "passive"}
    overflow_safety = policy.get("overflow_safety", True)
    overflow_frac = policy.get("overflow_safety_frac", 0.85)

    def agent(obs):
        player = obs["player"]
        me = obs["farms"][player]
        private = obs["private"]
        board_size = len(me["tiles"])
        tiles = me["tiles"]
        day = obs["day"]
        turn = day * 24 + obs.get("hour", 0)  # turnsPerDay=24 default, never overridden in this project
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

        # --- HIRE (hands reset daily) --- identical to Phase 2.3
        current_hands = len(me.get("hands", []))
        need_hire = max(0, n_hands - current_hands)
        hire_cost_est = sum(_fib(current_hands + i) for i in range(need_hire))
        for _ in range(need_hire):
            market.append(["HIRE"])
        money -= hire_cost_est

        # --- BUY_LAND --- identical to Phase 2.3
        n_extra_owned = len(me.get("unlocked_quadrants", [])) - 1
        if n_extra_owned < land_quadrants and day >= land_buy_day and n_extra_owned < len(LAND_PRICES):
            next_cost = LAND_PRICES[n_extra_owned]
            if money >= next_cost:
                market.append(["BUY_LAND"])
                money -= next_cost

        # --- SELL: Phase 2.4's actual contribution (pluggable policy) ---
        n_animals_alive = sum(
            1 for t in structure_tiles if isinstance(tiles[t[1]][t[0]], dict) and "animal" in tiles[t[1]][t[0]]
        )
        wheat_reserved = n_animals_alive if (feed_policy == "daily" and n_animals_alive) else 0
        fert_reserved = 1 if (fertilizer_apply and not fertilizer_sell_surplus) else 0

        sellable_items = set(crop_fractions) | {ANIMALS[t]["product"] for t in animal_counts}
        if buy_fertilizer or collect_fertilizer:
            sellable_items.add("FERTILIZER")

        shed_total = sum(shed.values())
        for item in sorted(sellable_items):
            held = shed.get(item, 0)
            reserve = wheat_reserved if item == "WHEAT" else (fert_reserved if item == "FERTILIZER" else 0)
            sellable_held = max(0, held - reserve)
            if sellable_held <= 0:
                continue
            price = prices.get(item, MARKET_PARAMS[item]["base"])
            qty = _sell_quantity(item, sellable_held, price, day, policy, turn=turn)
            if overflow_safety and shed_total > overflow_frac * SHED_CAPACITY and qty < sellable_held:
                qty = sellable_held  # safety valve: don't let policy-driven holding rot in an overfull shed
            if qty > 0:
                market.append(["SELL", item, qty])

        # --- BUY_SEED --- identical to Phase 2.3
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

        # --- BUY_ANIMAL --- identical to Phase 2.3
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

        # --- BUY_PRODUCT: wheat for feed / fertilizer --- identical to Phase 2.3
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

        market = market[:10]

        # ---------------- Physical task scheduling (identical to Phase 2.3) ----------------
        tasks = []

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

        def manhattan(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        def nearest_free_worker(pos, predicate):
            best, best_d = None, None
            for w in workers:
                if w["claimed"] or not predicate(w):
                    continue
                d = manhattan(w["pos"], pos)
                if best is None or d < best_d:
                    best, best_d = w, d
            return best

        tile_entries = [(pr, t, "TILE", kind, req, extra) for pr, t, kind, req, extra in tasks]
        combined = tile_entries + fetch_entries

        def entry_target(entry, worker_pos):
            etype = entry[2]
            if etype == "FETCH":
                return min(shed_tiles, key=lambda s: manhattan(worker_pos, s))
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
                        d = manhattan(w["pos"], entry_target(entry, w["pos"]))
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
                target = min(shed_tiles, key=lambda s: manhattan(w["pos"], s))
                w["claimed"] = True
                w["action"] = ["DROP"] if w["pos"] == target else [_step_toward(w["pos"][0], w["pos"][1], target[0], target[1])]

        for w in workers:
            if w["action"] is None:
                w["action"] = ["PASS"]

        return {"farmer": workers[0]["action"], "hands": [w["action"] for w in workers[1:]], "market": market}

    return agent
