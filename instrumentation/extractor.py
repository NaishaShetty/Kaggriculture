"""
Extractor: turns a replay (env.toJSON()) into the RAW telemetry layer —
per-turn per-player action/state records, a distilled production-event
stream (from a full board diff pass, not stored as raw per-turn boards), a
once-per-day land snapshot, and public market/town history.

Index alignment (verified empirically against the vendored simulator, see
docs/PHASE2_1_ARCHITECTURE.md "Replay indexing"): `replay["steps"][t]`
stores the action an agent chose USING the observation at index `t-1` (or
the true pre-game initial state for t==0), together with the RESULTING
observation after that action was applied. i.e. `steps[t].observation`
already reflects `steps[t].action`'s effect (confirmed directly: money and
`private.seeds` at the same index already show a BUY_SEED order's effect).
So for turn t: before-state = steps[t-1].observation (or the synthetic
initial state for t==0), action = steps[t].action, after-state =
steps[t].observation. The synthetic initial state is built with the
vendored simulator's own `_new_farm`/`_new_private`/`_new_market`/`_new_town`
constructors (imported read-only) so it is guaranteed identical to what the
simulator itself would report, not independently re-derived.

Everything here reads only fields already present in the replay. It performs
no simulation of its own beyond simple, documented diff/classification logic
(e.g. disambiguating HARVEST vs DIG using inventory deltas as corroborating
evidence) needed to turn raw state diffs into named events.
"""
from vendor_kaggriculture.kaggriculture import _new_farm, _new_private, _new_market, _new_town

from .schema import classify_unit_op, classify_market_op


def _tile_kind(tile):
    if tile is None:
        return "EMPTY"
    if tile == "LOCKED":
        return "LOCKED"
    if isinstance(tile, dict):
        kind = tile.get("kind")
        if kind == "PLANT":
            return f"PLANT:{tile.get('crop')}"
        if "animal" in tile:
            return f"{kind}:{tile.get('animal')}"
        return kind
    return "UNKNOWN"


def _copy_private(private):
    if private is None:
        return None
    return {
        "shed": dict(private.get("shed", {})),
        "seeds": dict(private.get("seeds", {})),
        "inventories": [dict(inv) for inv in private.get("inventories", [])],
    }


def _quadrant_of(x, y, board_size):
    half = board_size // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


def _initial_state(configuration):
    """Synthetic pre-game state (turn -1), built from the vendored
    simulator's own constructors -- not re-derived independently."""
    board_size = int(configuration.get("boardSize", 10))
    starting_money = int(configuration.get("startingMoney", 3000))
    farm0 = _new_farm(board_size, starting_money)
    farm1 = _new_farm(board_size, starting_money)
    private0 = _new_private()
    private1 = _new_private()
    market = _new_market()
    town = _new_town()
    public = {"day": 0, "hour": 0, "step": -1, "farms": [farm0, farm1], "market": market, "town": town}
    return public, [private0, private1]


def _summarize_board(tiles, board_size, unlocked_quadrants):
    counts = {"LOCKED": 0, "EMPTY": 0, "WEED": 0, "CROP": {}, "STRUCTURE_EMPTY": {}, "STRUCTURE_ANIMAL": {}}
    by_quadrant = {}
    for y in range(board_size):
        for x in range(board_size):
            tile = tiles[y][x]
            q = _quadrant_of(x, y, board_size)
            by_quadrant.setdefault(q, {"LOCKED": 0, "EMPTY": 0, "WEED": 0, "CROP": 0, "STRUCTURE": 0})
            if tile == "LOCKED":
                counts["LOCKED"] += 1
                by_quadrant[q]["LOCKED"] += 1
            elif tile is None:
                counts["EMPTY"] += 1
                by_quadrant[q]["EMPTY"] += 1
            elif isinstance(tile, dict):
                kind = tile.get("kind")
                if kind == "WEED":
                    counts["WEED"] += 1
                    by_quadrant[q]["WEED"] += 1
                elif kind == "PLANT":
                    crop = tile.get("crop")
                    counts["CROP"][crop] = counts["CROP"].get(crop, 0) + 1
                    by_quadrant[q]["CROP"] += 1
                elif kind in ("COOP", "PASTURE"):
                    if "animal" in tile:
                        a = tile["animal"]
                        counts["STRUCTURE_ANIMAL"][a] = counts["STRUCTURE_ANIMAL"].get(a, 0) + 1
                    else:
                        counts["STRUCTURE_EMPTY"][kind] = counts["STRUCTURE_EMPTY"].get(kind, 0) + 1
                    by_quadrant[q]["STRUCTURE"] += 1
    counts["unlocked_tiles"] = counts["EMPTY"] + counts["WEED"] + sum(counts["CROP"].values()) + \
        sum(counts["STRUCTURE_EMPTY"].values()) + sum(counts["STRUCTURE_ANIMAL"].values())
    counts["unlocked_quadrants"] = list(unlocked_quadrants)
    counts["by_quadrant"] = by_quadrant
    return counts


def _diff_tile(tb, ta, turn, day, player, x, y, priv_before, priv_after):
    events = []

    def crop_gain(item):
        # CARRIED-inventory delta only (never shed) for `item` this turn. A
        # HARVEST exclusively lands in the acting unit's carried inventory
        # (`_apply_unit_action`'s HARVEST branch calls `_inv_add(inv, ...)`
        # where `inv` is the per-unit carried inventory, never the shed
        # directly) -- so this is an unconfounded signal even when a SELL of
        # the SAME item (which only touches the shed) happens the same turn.
        # An earlier version aggregated shed+carried together, which a same-
        # turn SELL (shed -1) + HARVEST (carried +1) cancels to a net of
        # zero, misclassifying the harvest as a DIG -- caught via a $25
        # money-conservation discrepancy while building Phase 2.2's crop
        # agents (see docs/PHASE2_1_TELEMETRY_SCHEMA.md changelog).
        b = sum(inv.get(item, 0) for inv in priv_before["inventories"])
        a = sum(inv.get(item, 0) for inv in priv_after["inventories"])
        return a - b

    tb_is_plant = isinstance(tb, dict) and tb.get("kind") == "PLANT"
    ta_is_plant = isinstance(ta, dict) and ta.get("kind") == "PLANT"
    tb_is_animal = isinstance(tb, dict) and "animal" in tb
    ta_is_animal = isinstance(ta, dict) and "animal" in ta

    def emit(ev):
        ev.update({"turn": turn, "day": day, "player": player, "x": x, "y": y})
        events.append(ev)

    if tb is None and ta_is_plant:
        emit({"event": "PLANT", "crop": ta["crop"]})
        return events
    if tb is None and isinstance(ta, dict) and ta.get("kind") in ("COOP", "PASTURE") and "animal" not in ta:
        emit({"event": "BUILD", "structure": ta["kind"]})
        return events
    if tb is None and isinstance(ta, dict) and ta.get("kind") == "WEED":
        emit({"event": "WEED_SPAWN"})
        return events

    if tb_is_plant and ta_is_plant:
        if not tb["watered_today"] and ta["watered_today"]:
            emit({"event": "WATER", "crop": tb["crop"]})
        if ta.get("fertilized_until_day", -1) > tb.get("fertilized_until_day", -1):
            emit({"event": "FERTILIZE", "crop": tb["crop"]})
        if tb["yield_units"] > 0 and ta["yield_units"] == 0:
            emit({"event": "HARVEST", "crop": tb["crop"], "units": tb["yield_units"], "ongoing": True})
        elif ta["yield_units"] > tb["yield_units"]:
            emit({"event": "GROWTH", "crop": tb["crop"], "delta": ta["yield_units"] - tb["yield_units"]})
        return events

    if tb_is_plant and ta is None:
        gained = crop_gain(tb["crop"])
        if tb.get("yield_units", 0) > 0 and gained > 0:
            emit({"event": "HARVEST", "crop": tb["crop"], "units": tb["yield_units"], "ongoing": False})
        else:
            emit({"event": "DIG", "removed": "PLANT", "crop": tb["crop"]})
        return events

    if tb_is_plant and isinstance(ta, dict) and ta.get("kind") == "WEED":
        emit({"event": "WEED_CONVERSION", "crop": tb["crop"]})
        return events

    if isinstance(tb, dict) and tb.get("kind") == "WEED" and ta is None:
        emit({"event": "DIG", "removed": "WEED"})
        return events

    if isinstance(tb, dict) and tb.get("kind") in ("COOP", "PASTURE") and "animal" not in tb and ta_is_animal:
        emit({"event": "PLACE_ANIMAL", "animal": ta["animal"], "structure": tb["kind"]})
        return events

    if tb_is_animal and ta_is_animal:
        if not tb["fed_today"] and ta["fed_today"]:
            emit({"event": "FEED", "animal": tb["animal"]})
        if not tb["cared_today"] and ta["cared_today"]:
            emit({"event": "CARE", "animal": tb["animal"]})
        if not tb["fertilizer_available"] and ta["fertilizer_available"]:
            emit({"event": "FERTILIZER_READY", "animal": tb["animal"]})
        if tb["fertilizer_available"] and not ta["fertilizer_available"]:
            emit({"event": "COLLECT_FERTILIZER", "animal": tb["animal"]})
        if tb["yield_units"] > 0 and ta["yield_units"] == 0:
            emit({"event": "HARVEST", "animal": tb["animal"], "units": tb["yield_units"]})
        elif ta["yield_units"] > tb["yield_units"]:
            emit({"event": "GROWTH", "animal": tb["animal"], "delta": ta["yield_units"] - tb["yield_units"]})
        return events

    if tb_is_animal and isinstance(ta, dict) and "animal" not in ta and ta.get("kind") == tb.get("kind"):
        emit({"event": "ANIMAL_ESCAPE", "animal": tb["animal"]})
        return events

    if isinstance(tb, dict) and tb.get("kind") == "WEED" and isinstance(ta, dict) and ta.get("kind") == "WEED":
        return events

    emit({"event": "UNCLASSIFIED", "tile_before": tb, "tile_after": ta})
    return events


def _public_at(replay, index, initial_public):
    return initial_public if index < 0 else replay["steps"][index][0]["observation"]


def _private_at(replay, player, index, initial_privates):
    return initial_privates[player] if index < 0 else replay["steps"][index][player]["observation"]["private"]


def _scan_board_events(replay, player, initial_public, initial_privates):
    steps = replay["steps"]
    n = len(steps)
    events = []
    land_daily = {}
    board_size = len(initial_public["farms"][player]["tiles"])
    last_day = None

    for t in range(n):
        pub_before = _public_at(replay, t - 1, initial_public)
        pub_after = _public_at(replay, t, initial_public)
        priv_before = _private_at(replay, player, t - 1, initial_privates)
        priv_after = _private_at(replay, player, t, initial_privates)

        farm_before = pub_before["farms"][player]
        farm_after = pub_after["farms"][player]
        day = pub_after["day"]

        if day != last_day:
            land_daily[day] = _summarize_board(farm_before["tiles"], board_size, farm_before["unlocked_quadrants"])
            last_day = day

        tiles_b, tiles_a = farm_before["tiles"], farm_after["tiles"]
        for y in range(board_size):
            row_b, row_a = tiles_b[y], tiles_a[y]
            for x in range(board_size):
                tb, ta = row_b[x], row_a[x]
                if tb == ta:
                    continue
                events.extend(_diff_tile(tb, ta, t, day, player, x, y, priv_before, priv_after))

    # Final day's land snapshot (state after the last recorded turn).
    final_farm = initial_public["farms"][player] if n == 0 else _public_at(replay, n - 1, initial_public)["farms"][player]
    final_day = 0 if n == 0 else _public_at(replay, n - 1, initial_public)["day"]
    land_daily[final_day] = _summarize_board(final_farm["tiles"], board_size, final_farm["unlocked_quadrants"])

    return events, land_daily


def _build_unit_records(farm_before, action):
    farmer_action = action.get("farmer", ["PASS"]) if isinstance(action, dict) else ["PASS"]
    hands_actions = action.get("hands", []) if isinstance(action, dict) else []
    if not isinstance(hands_actions, list):
        hands_actions = []

    fx, fy = farm_before["farmer"]
    units = [{"role": "farmer", "pos": (fx, fy), "tile_before": farm_before["tiles"][fy][fx], "op_list": farmer_action}]
    for hi, hpos in enumerate(farm_before["hands"]):
        hx, hy = hpos
        op_list = hands_actions[hi] if hi < len(hands_actions) else ["PASS"]
        units.append({"role": f"hand{hi}", "pos": (hx, hy), "tile_before": farm_before["tiles"][hy][hx], "op_list": op_list})

    records = []
    for u in units:
        op_list = u["op_list"] if isinstance(u["op_list"], list) and u["op_list"] else ["PASS"]
        op = op_list[0]
        args = op_list[1:]
        records.append({
            "unit": u["role"],
            "pos_before": [u["pos"][0], u["pos"][1]],
            "tile_before_kind": _tile_kind(u["tile_before"]),
            "op": op,
            "args": args,
            "category": classify_unit_op(op, u["tile_before"]),
        })
    return records


def _build_market_records(action):
    orders = action.get("market", []) if isinstance(action, dict) else []
    if not isinstance(orders, list):
        return []
    records = []
    for order in orders:
        if not isinstance(order, list) or not order:
            continue
        op = order[0]
        records.append({"op": op, "args": order[1:], "category": classify_market_op(op)})
    return records


def _build_outcome(replay, meta):
    final = replay["steps"][-1]
    rewards = [s["reward"] for s in final]
    statuses = [s["status"] for s in final]
    if rewards[0] is None or rewards[1] is None:
        winner = None
    elif rewards[0] > rewards[1]:
        winner = 0
    elif rewards[1] > rewards[0]:
        winner = 1
    else:
        winner = "tie"
    return {
        "final_money": rewards,
        "statuses": statuses,
        "winner": winner,
        "margin": (rewards[0] - rewards[1]) if (rewards[0] is not None and rewards[1] is not None) else None,
        "n_steps_recorded": len(replay["steps"]),
        "runtime_s": meta["runtime_s"],
    }


def extract_episode(replay, meta):
    steps = replay["steps"]
    n = len(steps)
    configuration = replay.get("configuration", {}) or {}
    initial_public, initial_privates = _initial_state(configuration)

    turns = {0: [], 1: []}
    market_history = []
    town_history = []

    for t in range(n):
        pub_after = _public_at(replay, t, initial_public)
        day, hour = pub_after["day"], pub_after["hour"]
        market, town, farms_after = pub_after["market"], pub_after["town"], pub_after["farms"]
        farms_before = _public_at(replay, t - 1, initial_public)["farms"]

        market_history.append({
            "turn": t, "day": day, "hour": hour,
            "inventory": dict(market["inventory"]), "prices": dict(market["prices"]),
        })
        town_history.append({"turn": t, "day": day, "hour": hour, "unlocked_shops": list(town["unlocked_shops"])})

        for player in (0, 1):
            entry = steps[t][player]
            action = entry["action"] if isinstance(entry["action"], dict) else {}
            farm_before = farms_before[player]
            farm_after = farms_after[player]
            private_before = _private_at(replay, player, t - 1, initial_privates)
            private_after = _private_at(replay, player, t, initial_privates)

            turns[player].append({
                "turn": t, "day": day, "hour": hour, "player": player,
                "reward": entry["reward"], "status": entry["status"],
                "money_before": farm_before["money"],
                "money_after": farm_after["money"],
                "unlocked_quadrants_before": list(farm_before["unlocked_quadrants"]),
                "unlocked_quadrants_after": list(farm_after["unlocked_quadrants"]),
                "hires_today_before": farm_before["hires_today"],
                "n_hands_before": len(farm_before["hands"]),
                "n_hands_after": len(farm_after["hands"]),
                "private_before": _copy_private(private_before),
                "private_after": _copy_private(private_after),
                "unit_actions": _build_unit_records(farm_before, action),
                "market_orders": _build_market_records(action),
            })

    production_events = {}
    land_daily = {}
    for player in (0, 1):
        production_events[player], land_daily[player] = _scan_board_events(replay, player, initial_public, initial_privates)

    return {
        "meta": meta,
        "outcome": _build_outcome(replay, meta),
        "turns": turns,
        "production_events": production_events,
        "land_daily": land_daily,
        "market_history": market_history,
        "town_history": town_history,
    }
