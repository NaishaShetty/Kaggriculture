"""
Phase 9 shared harness.

DEVELOPMENT_SEEDS reuses this project's existing "development" seed bucket
(agents/phase5's TARGET_SEEDS["development"] = [700000..700003]) -- per
Phase 6 §17's instruction to use "development set, n=4" and this project's
convention of never inventing a fresh seed range where an established one
already fits.

Two agent families are provided:

1. `make_control_agent` -- a THIN WRAPPER around the UNMODIFIED
   `agents/phase2_3/common.py::make_agent` (Phase 2.3's own original
   function, reused not duplicated). Used for every CONTROL-arm cell in
   both experiments (small board / small hand-and-animal counts), where it
   reproduces the original a1_labor_sweep / a3_animal_lifecycle methodology
   exactly.

2. `make_high_scale_agent` -- a purpose-built probe agent for the
   VARIABLE arms (8-13 hands / 10-14 animals). See
   "WHY A CUSTOM AGENT" below for why the frozen function above cannot be
   reused unmodified at this scale.

WHY A CUSTOM AGENT FOR THE HIGH-SCALE ARMS:
Directly reusing `agents/phase2_3/common.py::make_agent` at n_hands>=8
produces a self-inflicted death spiral that has NOTHING to do with the
economic question being asked, for two compounding, VERIFIED reasons (found
by direct trace inspection while building this experiment, not assumed):

  (a) Hands reset to zero every in-game day (VERIFIED_MECHANIC, confirmed
      in Phase 6 §5); the frozen agent re-queues `["HIRE"]` orders
      unconditionally, with NO affordability check (unlike its own
      BUY_LAND/BUY_SEED logic, which DOES check `money >= cost` before
      queuing). At n_hands=13 this means up to 13 HIRE orders are queued
      every turn regardless of actual cash.
  (b) The market-action list is capped at 10 orders/turn
      (`market = market[:10]`, VERIFIED_MECHANIC, "maxMarketOrdersPerTurn
      default"). HIRE orders are constructed and appended to the list
      BEFORE the SELL block. When need_hire >= 10, the HIRE requests alone
      fill the ENTIRE 10-slot cap, and the SELL order for that turn's
      harvested inventory is silently truncated away -- confirmed directly:
      a raw reproduction of the frozen agent at n_hands=13/land_quadrants=3
      harvests real units from day 10 onward but shows `products_sold=0`
      for the ENTIRE 30-day episode, and ends at final_money=$0.

Both are genuine properties of the shared `make_agent` family this whole
project's tactical layer is built from (agents/phase2_3 AND agents/phase2_4
both have the same HIRE-before-SELL ordering and the same unconditional
HIRE queuing) -- not something introduced by this probe. They are disclosed,
reportable findings in their own right (see the Phase 9 report's
mechanism section), but they are execution-fidelity artifacts, not the
"is the Nth hand economically worth it" question this experiment needs to
answer, and per this project's explicit brief for this phase ("don't
under-fill the board... that would silently bias toward the FAIL
condition"), letting them stand would bias every high-hand-count cell
toward a floor of $0 regardless of true marginal value.

`make_high_scale_agent` is IDENTICAL in every other respect (same
`agents/phase2_3/common.py` helper primitives: `_home_tile`, `_shed_tiles`,
`_owned_tiles`, `tile_pool_assignment`, `_needs_harvest_crop`,
`_needs_water`, `_step_toward`, `_fib`, `_manhattan` -- imported, not
reimplemented) and makes exactly two changes, both disclosed and minimal:

  1. SELL orders are queued BEFORE HIRE orders (so realized harvest revenue
     is never crowded out of the 10-order cap by hire requests that may not
     even execute) -- a strictly more rational ordering, not a new
     mechanic.
  2. HIRE requests are capped to what's actually AFFORDABLE this turn
     (walking the same `_fib` cost curve the frozen agent already computes,
     stopping once cumulative cost would exceed current cash) -- applying
     the SAME affordability discipline the frozen agent's own
     BUY_LAND/BUY_SEED logic already uses, just extended to HIRE, which the
     original inconsistently omits.

Even with both fixes, reaching 8-13 hands from the default $3000 starting
capital on day 0 is still economically infeasible in isolation: 13 hands
costs `sum(fib(0..12)) = 609` in hire fees ALONE, EVERY SINGLE DAY (hands
reset nightly), before any MELON harvest revenue exists (first_yield_day=
10) -- a real, VERIFIED constraint, not an artifact, and consistent with
Phase 6's own observation (§4) that real strong opponents never committed
to 13 hands until AFTER their own day-10+ capital inflection, not from day
0. Testing "is the Nth hand worth it AT THIS SCALE" (Experiment 2/4's
actual question) is a different question from "can a single-crop farm
bootstrap into this scale from zero starting capital" (already a separate,
unresolved question per Phase 6 §5/§14.B.3 -- this phase does not attempt
to resolve it). To separate the two, the high-scale arm's episodes use
`extra_config={"startingMoney": 30000}` (the engine's own documented,
configurable `startingMoney` config key, VERIFIED via
`vendor_kaggriculture/kaggriculture.py` line 252 -- not a new mechanic) --
a fixed, disclosed capital cushion applied IDENTICALLY to every cell in the
high-scale arm (n_hands 4 through 13 alike), so it is a constant additive
offset that CANCELS OUT of the marginal (Δfinal_money) comparison between
adjacent hand counts. It answers "given a farm already at the scale strong
real opponents reach, is committing to hand N worth it" -- exactly Phase
6 Experiment 2/4's question -- without conflating it with the separate
bootstrapping question.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS, LAND_PRICES  # noqa: E402
from agents.phase2_3.common import (  # reuse, not duplicate -- noqa: E402
    make_agent as make_control_agent,
    _home_tile, _shed_tiles, _owned_tiles, tile_pool_assignment, structure_type_assignment,
    _needs_harvest_crop, _needs_water, _step_toward, _fib, _manhattan,
)
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEVELOPMENT_SEEDS = [700000, 700001, 700002, 700003]  # n=4, this project's existing "development" seed bucket
HIGH_SCALE_STARTING_MONEY = 30000  # disclosed capital cushion for high-scale arms only -- see module docstring


def make_high_scale_agent(crops=None, n_hands=0, land_quadrants=0, land_buy_day=0,
                           animals=None, animal_buy_day=0, feed_source="auto", seed_buffer_cap=6):
    """SELL-before-HIRE, affordability-capped-HIRE variant of
    agents/phase2_3/common.py::make_agent -- see module docstring for why."""
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

        # --- SELL FIRST (fix 1): never let HIRE spam crowd this out of the 10-order cap ---
        n_animals_alive = sum(
            1 for t in structure_tiles if isinstance(tiles[t[1]][t[0]], dict) and "animal" in tiles[t[1]][t[0]]
        )
        wheat_reserved = n_animals_alive if (feed_source != "market" and n_animals_alive) else 0
        sellable_items = set(crop_fractions) | {ANIMALS[t]["product"] for t in animal_counts}
        for item in sorted(sellable_items):
            held = shed.get(item, 0)
            reserve = wheat_reserved if item == "WHEAT" else 0
            sellable = max(0, held - reserve)
            if sellable > 0:
                market.append(["SELL", item, sellable])

        # --- HIRE (fix 2): cap to what's actually affordable this turn ---
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

        # --- BUY_LAND (unchanged from frozen logic) ---
        n_extra_owned = len(me.get("unlocked_quadrants", [])) - 1
        if n_extra_owned < land_quadrants and day >= land_buy_day and n_extra_owned < len(LAND_PRICES):
            next_cost = LAND_PRICES[n_extra_owned]
            if money >= next_cost:
                market.append(["BUY_LAND"])
                money -= next_cost

        # --- BUY_SEED (unchanged from frozen logic) ---
        empty_needed = {}
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

        # --- BUY_ANIMAL (unchanged from frozen logic) ---
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

        # --- BUY_PRODUCT: wheat for feed (unchanged from frozen logic) ---
        wheat_needed_for_feed = 0
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


def run_cell(experiment_id, cell_id, seed, agent, extra_config=None):
    replay, meta = run_episode(agent, "pass", STEPS, seed, extra_config)
    record, extracted = analyze_replay(replay, meta, experiment_id, f"{cell_id}_seed{seed}")
    final_money = record["outcome"]["final_money"][0]
    fin = record["players"][0]["financial_summary"]
    return {
        "final_money": final_money,
        "total_income": fin["total_income"],
        "total_expenditure": fin["total_expenditure"],
    }


def mean_by_value(rows, variable_name):
    by_value = {}
    for r in rows:
        by_value.setdefault(r[variable_name], []).append(r["final_money"])
    return {v: sum(vals) / len(vals) for v, vals in sorted(by_value.items())}


def marginal_values(means_by_value):
    """means_by_value: {value: mean_final_money}, sorted ascending. Returns
    {value: marginal $} for every value whose predecessor (value-1) is also
    present (marginal of value v = mean[v] - mean[v-1])."""
    out = {}
    for v in means_by_value:
        if (v - 1) in means_by_value:
            out[v] = round(means_by_value[v] - means_by_value[v - 1], 2)
    return out
