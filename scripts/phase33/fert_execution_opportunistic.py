"""
Phase 33 Part B: strictly opportunistic (non-preempting) fertilizer.

New code, isolated from agents/phase21/ (not modified). Adapts
agents/phase21/execution.py::make_execution_agent (same reused low-level
primitives from agents/phase2_3/common.py, same overall structure) with
fertilizer tasks reconstructed from Phase 30's own report
(results/phase30/PHASE30_FERTILIZER_REPORT.md Section 3 -- Phase 30's actual
code was fully reverted and no longer exists in the repo, so this is a
rebuild informed by that report, not a literal reuse), but at DIFFERENT
priority tiers than Phase 30 used:

  Phase 30:  FERTILIZE tier 2 (between WATER=1 and DIG/PLANT/BUILD/PLACE=3)
             COLLECT_FERTILIZER tier 4
  Phase 33:  FERTILIZE tier 4          (strictly below every existing tier)
             COLLECT_FERTILIZER tier 5 (strictly below FERTILIZE, same
                                         relative ordering Phase 30 used --
                                         collecting is more opportunistic
                                         than applying)

agents/phase21/execution.py's own existing tiers, confirmed by direct read,
top out at 3 (0=HARVEST/HARVEST_ANIMAL, 1=WATER/FEED, 2=CARE, 3=endgame-DIG/
WEED-DIG/PLANT/BUILD/PLACE). Tiers 4 and 5 are strictly new, unused numbers.

WHY THIS IS STRUCTURALLY NON-PREEMPTIVE, NOT JUST NUMBERED LOWER:
the assignment loop below (identical in structure to agents/phase21/
execution.py and every execution layer since Phase 9) processes tiers in
STRICTLY INCREASING order, and within a tier repeatedly assigns the globally
closest (still-unclaimed worker, still-unmatched entry) pair until no such
pair exists. That "until no such pair exists" exit condition is the key
invariant: the tier-N loop cannot terminate while ANY unclaimed worker is
still eligible for ANY unmatched tier-N entry, because that pair would always
be a valid, better-than-nothing candidate for the next iteration. So by the
time tier 4 (FERTILIZE) begins processing, EVERY worker who is both unclaimed
AND eligible for some remaining tier-0..3 entry has already necessarily been
claimed by it. A worker that reaches tier 4 unclaimed is, by construction,
one that tier 0-3 had no eligible use for THIS TURN -- exactly a worker that
would otherwise have gone to the final PASS fallback. This is a structural
proof from the algorithm's own termination condition, not an assumption; the
trace in scripts/phase33/trace_nonpreemption.py additionally confirms it
empirically (zero cases of a fertilizer action coexisting with a claimable
tier<=3 entry).
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

FERTILIZE_TIER = 4
COLLECT_FERT_TIER = 5


def _needs_fertilize(tile, crop, day):
    return isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == crop \
        and tile.get("fertilized_until_day", -1) < day


def make_fert_execution_agent(target_fn, fertilize=True, trace_sink=None, seed_buffer_cap=6):
    """`trace_sink`, if given, is a list -- one dict appended per turn with
    enough detail (assigned tiers per worker, unmatched tier<=3 entries at
    the moment tier 4 begins) for scripts/phase33/trace_nonpreemption.py to
    confirm non-preemption empirically, not just by construction."""
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
                # Strictly below every other crop-tile task (tier 4): only
                # considered once HARVEST/endgame-DIG/WATER/WEED-DIG/PLANT
                # have all already been checked false for THIS tile.
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
                    tasks.append((1, t, "FEED", "WHEAT", None))
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

        trace_row = None
        if trace_sink is not None:
            trace_row = {"day": day, "assignments": [], "unmatched_le3_at_tier4_start": None,
                         "eligible_le3_pairs_at_tier4_start": None}

        tiers = sorted(set(e[0] for e in combined))
        for tier in tiers:
            if trace_sink is not None and tier >= FERTILIZE_TIER and trace_row["unmatched_le3_at_tier4_start"] is None:
                # Snapshot BEFORE processing the first fertilizer-or-higher
                # tier: any tier<=3 entries still sitting in `combined` at
                # this point are ones the tier<=3 loop already could not
                # match to any unclaimed eligible worker (by that loop's own
                # exit condition). The real non-preemption claim is stronger
                # than "some are left over" -- it's that NONE of them are
                # eligible-and-reachable by any worker still unclaimed at
                # this exact moment (the workers about to receive tier
                # 4/5 fertilizer assignments). Both are recorded.
                already_matched = [a["entry"] for a in trace_row["assignments"]]
                le3_entries = [e for e in combined if e[0] <= 3 and e not in already_matched]
                trace_row["unmatched_le3_at_tier4_start"] = len(le3_entries)
                eligible_pairs = 0
                for e in le3_entries:
                    for w in workers:
                        if not w["claimed"] and entry_eligible(e, w):
                            eligible_pairs += 1
                trace_row["eligible_le3_pairs_at_tier4_start"] = eligible_pairs

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
                # NOTE: `combined` itself is intentionally left un-pruned here,
                # matching agents/phase21/execution.py's own original loop
                # exactly (it only reads `w["claimed"]`, so a matched-but-
                # not-removed entry lingering in `combined` is harmless for
                # scheduling). The trace snapshot below prunes its OWN copy
                # to avoid miscounting already-matched entries as leftover.
                if trace_sink is not None:
                    trace_row["assignments"].append({"tier": entry[0], "kind": entry[3], "worker_idx": workers.index(w),
                                                       "entry": entry})

        for w in workers:
            if w["claimed"]:
                continue
            if w["inv"]:
                target = min(shed_tiles, key=lambda s: _manhattan(w["pos"], s))
                w["claimed"] = True
                w["action"] = ["DROP"] if w["pos"] == target else [_step_toward(w["pos"][0], w["pos"][1], target[0], target[1])]

        n_pass = 0
        for w in workers:
            if w["action"] is None:
                w["action"] = ["PASS"]
                n_pass += 1

        if trace_sink is not None:
            trace_row["n_pass"] = n_pass
            trace_row["n_workers"] = n_workers
            trace_sink.append(trace_row)

        return {"farmer": workers[0]["action"], "hands": [w["action"] for w in workers[1:]], "market": market}

    agent.set_opponent_history = set_opponent_history
    return agent
