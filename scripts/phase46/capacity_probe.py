"""
Phase 46 Part A: an instrumented copy of Submission I's shipped execution
layer (scripts/phase36/paced_execution.py::make_paced_execution_agent,
itself a validated wrapper around agents/phase21/execution.py's own
primitives -- imported unchanged, never modified) that records, every
single turn, the exact worker-turn supply/demand split at the FEED/WATER
priority tier (tier 1) -- distinguishing the two failure modes the Phase 46
brief calls out as needing separate diagnosis:

  1. WORKER EXHAUSTION: zero workers remain unclaimed by the time tier 1 is
     reached (tier 0 -- HARVEST/HARVEST_ANIMAL -- already claimed every
     worker this turn). FEED (and WATER) are not even attempted.
  2. ASSIGNMENT-RACE LOSS: at least one worker is free entering tier 1, but
     by the end of tier 1's greedy nearest-worker matching, one or more
     FEED entries remain unassigned while one or more WATER entries in the
     SAME tier got a worker instead (or a FEED entry simply lost the
     nearest-worker comparison to a WATER entry that was closer).

This is a pure MEASUREMENT script -- it does not change scheduling
behavior at all; the task list, tier processing order, and greedy
nearest-worker matching are byte-identical to
scripts/phase36/paced_execution.py (which is itself byte-identical to
agents/phase21/execution.py's own logic for these sections, only
BUY_ANIMAL differs, and BUY_ANIMAL pacing has no bearing on the FEED/WATER
tier-1 assignment race being measured here).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS, LAND_PRICES  # noqa: E402
from agents.phase21.risk_posture import posture_params  # noqa: E402
from agents.phase21.liquidation import planting_cutoff_day, tile_has_future_yield  # noqa: E402
from agents.phase21.execution import bounded_multi_crop_tile_pool_assignment  # noqa: E402
from agents.phase2_3.common import (  # noqa: E402
    _home_tile, _shed_tiles, _owned_tiles, structure_type_assignment,
    _needs_harvest_crop, _needs_water, _step_toward, _fib, _manhattan,
)

FEED_BUFFER_DAYS = 2
WHEAT_PRICE_ESTIMATE = 30
MAX_ANIMAL_PURCHASES_PER_TURN = 1


def make_capacity_probe_agent(target_fn, seed_buffer_cap=6):
    """Same shape as scripts/phase36/paced_execution.py's
    make_paced_execution_agent, with a `log` list attached to the returned
    agent function (`agent.turn_log`) recording per-turn tier-1 diagnostics.
    """
    state = {"opponent_history": []}
    turn_log = []

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

        # ---- Instrumentation: tally tier-1 (FEED/WATER) task kinds BEFORE any assignment ----
        n_feed_entries = sum(1 for e in combined if e[0] == 1 and e[2] == "TILE" and e[3] == "FEED")
        n_water_entries = sum(1 for e in combined if e[0] == 1 and e[2] == "TILE" and e[3] == "WATER")
        n_tier0_entries = sum(1 for e in combined if e[0] == 0)

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

        # ---- Instrumentation: workers still free right as tier processing begins ----
        n_free_pre_tiers = sum(1 for w in workers if not w["claimed"])

        tiers = sorted(set(e[0] for e in combined))
        n_free_entering_tier1 = None
        n_feed_assigned = 0
        n_water_assigned = 0
        for tier in tiers:
            if tier == 1:
                n_free_entering_tier1 = sum(1 for w in workers if not w["claimed"])
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
                if tier == 1 and entry[2] == "TILE":
                    if entry[3] == "FEED":
                        n_feed_assigned += 1
                    elif entry[3] == "WATER":
                        n_water_assigned += 1
                do_entry(entry, w)
                remaining.remove(entry)

        if n_free_entering_tier1 is None:
            # tier 1 had zero combined entries this turn (no FEED/WATER tasks existed at all)
            n_free_entering_tier1 = sum(1 for w in workers if not w["claimed"])

        n_feed_unassigned = n_feed_entries - n_feed_assigned

        # Classify this turn's FEED outcome (only meaningful when FEED entries existed):
        #   "no_feed_needed"      -- n_feed_entries == 0
        #   "worker_exhaustion"   -- FEED entries existed, but ALL workers were already
        #                            claimed by tier 0 (HARVEST/HARVEST_ANIMAL) before
        #                            tier 1 was even reached -- FEED wasn't attempted at all
        #   "assignment_race_loss"-- FEED entries existed, at least one worker was free
        #                            entering tier 1, but some FEED entries still ended
        #                            the turn unassigned (WATER/other FEED entries won
        #                            the nearest-worker comparison instead)
        #   "fully_served"        -- FEED entries existed and all were assigned
        if n_feed_entries == 0:
            feed_outcome = "no_feed_needed"
        elif n_feed_unassigned == 0:
            feed_outcome = "fully_served"
        elif n_free_entering_tier1 == 0:
            feed_outcome = "worker_exhaustion"
        else:
            feed_outcome = "assignment_race_loss"

        for w in workers:
            if w["claimed"]:
                continue
            if w["inv"]:
                target = min(shed_tiles, key=lambda s: _manhattan(w["pos"], s))
                w["claimed"] = True
                w["action"] = ["DROP"] if w["pos"] == target else [_step_toward(w["pos"][0], w["pos"][1], target[0], target[1])]

        n_idle_end_of_turn = sum(1 for w in workers if w["action"] is None)

        for w in workers:
            if w["action"] is None:
                w["action"] = ["PASS"]

        turn_log.append({
            "day": day,
            "n_workers": n_workers,
            "n_tier0_entries": n_tier0_entries,
            "n_free_pre_tiers": n_free_pre_tiers,
            "n_free_entering_tier1": n_free_entering_tier1,
            "n_feed_entries": n_feed_entries,
            "n_water_entries": n_water_entries,
            "n_feed_assigned": n_feed_assigned,
            "n_water_assigned": n_water_assigned,
            "n_feed_unassigned": n_feed_unassigned,
            "feed_outcome": feed_outcome,
            "n_idle_end_of_turn": n_idle_end_of_turn,
            "owned_animal_count": owned_animal_count,
        })

        return {"farmer": workers[0]["action"], "hands": [w["action"] for w in workers[1:]], "market": market}

    agent.set_opponent_history = set_opponent_history
    agent.turn_log = turn_log
    return agent


def summarize(turn_log):
    n_turns = len(turn_log)
    total_idle = sum(t["n_idle_end_of_turn"] for t in turn_log)
    total_worker_turns = sum(t["n_workers"] for t in turn_log)
    outcome_counts = {}
    for t in turn_log:
        outcome_counts[t["feed_outcome"]] = outcome_counts.get(t["feed_outcome"], 0) + 1
    feed_turns = n_turns - outcome_counts.get("no_feed_needed", 0)
    total_feed_entries = sum(t["n_feed_entries"] for t in turn_log)
    total_feed_assigned = sum(t["n_feed_assigned"] for t in turn_log)
    total_feed_unassigned = sum(t["n_feed_unassigned"] for t in turn_log)
    return {
        "n_turns": n_turns,
        "idle_action_fraction": round(total_idle / total_worker_turns, 4) if total_worker_turns else None,
        "feed_relevant_turns": feed_turns,
        "outcome_counts": outcome_counts,
        "outcome_fractions_of_feed_relevant_turns": {
            k: round(v / feed_turns, 4) for k, v in outcome_counts.items() if k != "no_feed_needed" and feed_turns
        },
        "total_feed_entries": total_feed_entries,
        "total_feed_assigned": total_feed_assigned,
        "total_feed_unassigned": total_feed_unassigned,
        "feed_service_rate": round(total_feed_assigned / total_feed_entries, 4) if total_feed_entries else None,
        "max_owned_animal_count": max((t["owned_animal_count"] for t in turn_log), default=0),
    }


if __name__ == "__main__":
    import json as _json
    from agents.phase3.opponent_observation import OpponentObservationLogger
    from agents.phase21.portfolio import portfolio_targets
    from agents.phase15.adapters.macro_agent import make_macro_agent
    from instrumentation.collector import run_episode

    STEPS = 720
    SEEDS = {"isolated_700000": (700000, "pass"), "vs_g_701002": (701002, "submission_g")}
    OUT_ROOT = "results/phase46"
    os.makedirs(OUT_ROOT, exist_ok=True)

    all_summaries = {}
    for label, (seed, opp) in SEEDS.items():
        opponent_logger = OpponentObservationLogger()
        exec_agent = make_capacity_probe_agent(portfolio_targets)

        def agent(obs):
            opponent_logger.observe(obs)
            exec_agent.set_opponent_history(opponent_logger.history)
            return exec_agent(obs)

        opponent = "pass" if opp == "pass" else make_macro_agent()
        replay, meta = run_episode(agent, opponent, STEPS, seed, None)
        summary = summarize(exec_agent.turn_log)
        all_summaries[label] = summary
        print(f"=== {label} (seed={seed}, opponent={opp}) ===")
        print(_json.dumps(summary, indent=2))
        with open(os.path.join(OUT_ROOT, f"phase46_capacity_probe_{label}_turnlog.json"), "w") as f:
            _json.dump(exec_agent.turn_log, f)

    with open(os.path.join(OUT_ROOT, "phase46_capacity_probe_summary.json"), "w") as f:
        _json.dump(all_summaries, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase46_capacity_probe_summary.json")
