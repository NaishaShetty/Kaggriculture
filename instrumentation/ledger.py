"""
Derived economic ledgers, built entirely from the RAW layer produced by
extractor.py. Nothing here re-runs or re-simulates the game; dollar amounts
for BUY_SEED / BUY_ANIMAL / BUY_LAND / HIRE are computed from PUBLIC, fixed
pricing constants imported read-only from the frozen simulator module (seed
cost, animal cost, land price ladder, hire-cost Fibonacci schedule) — these
are lookup tables, not gameplay logic, and importing them does not execute or
alter any simulator behavior. SELL / BUY_PRODUCT dollar amounts use the
dynamic market-clearing price, which is NOT independently recomputed here
(that would require replicating the per-unit, dual-player lockstep algorithm
in kaggriculture.py's `_process_market`, out of scope for Phase 2.1); instead
the realized price is derived exactly from the ground-truth money delta divided
by the ground-truth quantity delta, which is exact whenever a turn's shed
activity is unambiguous (see `exact` flags below) and only estimated/pooled
when multiple order types collide on the same item in the same turn.
"""
from vendor_kaggriculture.kaggriculture import (
    CROPS, ANIMALS, PRODUCTS, LAND_PRICES, FARM_HAND_COST_MULT, _fib, _hire_cost,
)

_PRODUCT_OF_ANIMAL = {a: spec["product"] for a, spec in ANIMALS.items()}


def _harvested_by_item_per_turn(production_events):
    """turn -> {item: units harvested that turn}, crops and animal products alike."""
    out = {}
    for ev in production_events:
        if ev["event"] != "HARVEST":
            continue
        item = ev.get("crop") or _PRODUCT_OF_ANIMAL.get(ev.get("animal"))
        if item is None:
            continue
        out.setdefault(ev["turn"], {})
        out[ev["turn"]][item] = out[ev["turn"]].get(item, 0) + ev["units"]
    return out


def _fertilize_count_per_turn(production_events):
    out = {}
    for ev in production_events:
        if ev["event"] == "FERTILIZE":
            out[ev["turn"]] = out.get(ev["turn"], 0) + 1
    return out


def build_financial_ledger(turns, configuration=None, production_events=None, market_prices_by_turn=None):
    """`production_events` (this player's) is used to correctly separate the
    daily automatic carried-inventory -> shed drop (and explicit
    DROP/PICKUP/PLACE/FEED/FERTILIZE carried-inventory movements) from actual
    market SELL/BUY_PRODUCT activity touching the shed in the same turn --
    without this, a turn that both sells product AND coincides with the
    end-of-day auto-drop would misattribute the freshly-dropped (unsold)
    harvest as market activity. See docs/PHASE2_1_ARCHITECTURE.md."""
    hire_mult = int((configuration or {}).get("farmHandCostMult", FARM_HAND_COST_MULT))
    production_events = production_events or []
    market_prices_by_turn = market_prices_by_turn or {}
    harvested_by_turn = _harvested_by_item_per_turn(production_events)
    fertilize_by_turn = _fertilize_count_per_turn(production_events)
    transactions = []

    for t in turns:
        if t["money_after"] is None or t["private_after"] is None:
            continue
        money_delta = t["money_after"] - t["money_before"]
        orders = t["market_orders"]
        priv_b, priv_a = t["private_before"], t["private_after"]
        known_cost = 0.0
        has_shed_side_channel = any(u["op"] in ("DROP", "PICKUP", "PLACE") for u in t["unit_actions"])
        base = {"turn": t["turn"], "day": t["day"], "hour": t["hour"], "player": t["player"]}

        # --- BUY_LAND: exact, fixed price ladder ---
        n_land_orders = sum(1 for o in orders if o["op"] == "BUY_LAND")
        land_before = len(t["unlocked_quadrants_before"])
        land_after = len(t["unlocked_quadrants_after"]) if t["unlocked_quadrants_after"] is not None else land_before
        land_gained = max(0, land_after - land_before)
        for k in range(min(n_land_orders, land_gained)):
            idx = land_before - 1 + k
            if 0 <= idx < len(LAND_PRICES):
                cost = LAND_PRICES[idx]
                known_cost += cost
                transactions.append({**base, "category": "EXPENDITURE", "type": "BUY_LAND", "item": "LAND",
                                      "quantity": 1, "unit_price": cost, "total": cost, "exact": True})

        # --- HIRE: exact, fixed Fibonacci schedule ---
        n_hire_orders = sum(1 for o in orders if o["op"] == "HIRE")
        hands_gained = max(0, (t["n_hands_after"] - t["n_hands_before"]) if t["n_hands_after"] is not None else 0)
        hires_today_before = t["hires_today_before"]
        for k in range(min(n_hire_orders, hands_gained)):
            cost = _hire_cost(hires_today_before + k, hire_mult)
            known_cost += cost
            transactions.append({**base, "category": "EXPENDITURE", "type": "HIRE", "item": "FARM_HAND",
                                  "quantity": 1, "unit_price": cost, "total": cost, "exact": True})

        # --- BUY_SEED: exact, fixed price per crop ---
        for crop in CROPS:
            seed_before = priv_b["seeds"].get(crop, 0)
            seed_after = priv_a["seeds"].get(crop, 0)
            seed_delta = seed_after - seed_before
            planted_consumed = sum(
                1 for u in t["unit_actions"]
                if u["op"] == "PLANT" and u["args"] and u["args"][0] == crop and u["tile_before_kind"] == "EMPTY"
            )
            planted_consumed = min(planted_consumed, seed_before)
            fulfilled_buy = seed_delta + planted_consumed
            requested = sum(
                (int(o["args"][1]) if len(o["args"]) > 1 else 1)
                for o in orders if o["op"] == "BUY_SEED" and o["args"] and o["args"][0] == crop
            )
            if requested > 0 and fulfilled_buy > 0:
                qty = min(requested, fulfilled_buy)
                cost = CROPS[crop]["seed"] * qty
                known_cost += cost
                transactions.append({**base, "category": "EXPENDITURE", "type": "BUY_SEED", "item": crop,
                                      "quantity": qty, "unit_price": CROPS[crop]["seed"], "total": cost,
                                      "exact": fulfilled_buy == requested})

        # --- BUY_ANIMAL: exact, fixed price per animal (lands directly in shed) ---
        for animal in ANIMALS:
            requested = sum(
                (int(o["args"][1]) if len(o["args"]) > 1 else 1)
                for o in orders if o["op"] == "BUY_ANIMAL" and o["args"] and o["args"][0] == animal
            )
            if requested <= 0:
                continue
            gained = priv_a["shed"].get(animal, 0) - priv_b["shed"].get(animal, 0)
            qty = min(requested, max(gained, 0))
            if qty > 0:
                cost = ANIMALS[animal]["cost"] * qty
                known_cost += cost
                transactions.append({**base, "category": "EXPENDITURE", "type": "BUY_ANIMAL", "item": animal,
                                      "quantity": qty, "unit_price": ANIMALS[animal]["cost"], "total": cost,
                                      "exact": gained == requested})

        # --- SELL / BUY_PRODUCT: dynamic-price remainder, split by MARKET-
        # attributable shed delta (raw shed delta minus the carried-inventory
        # -> shed movement this turn: end-of-day auto-drop, explicit DROP/
        # PLACE, PICKUP, and carried-inventory consumption via FEED/FERTILIZE).
        remainder = money_delta + known_cost
        harvested_this_turn = harvested_by_turn.get(t["turn"], {})
        n_fertilize_this_turn = fertilize_by_turn.get(t["turn"], 0)
        n_feed_this_turn = sum(1 for u in t["unit_actions"] if u["op"] == "FEED")
        moved_items = []
        for item in PRODUCTS:
            raw_delta = priv_a["shed"].get(item, 0) - priv_b["shed"].get(item, 0)
            carried_before = sum(inv.get(item, 0) for inv in priv_b["inventories"])
            carried_after = sum(inv.get(item, 0) for inv in priv_a["inventories"])
            consumed = (n_feed_this_turn if item == "WHEAT" else 0) + \
                (n_fertilize_this_turn if item == "FERTILIZER" else 0)
            drop_minus_pickup = carried_before + harvested_this_turn.get(item, 0) - carried_after - consumed
            market_delta = raw_delta - drop_minus_pickup
            if market_delta != 0:
                moved_items.append((item, market_delta))

        if len(moved_items) == 1:
            item, delta = moved_items[0]
            qty = abs(delta)
            exact = not has_shed_side_channel
            total = round(abs(remainder), 4)
            unit_price = round(total / qty, 4) if qty else None
            op_type = "SELL" if delta < 0 else "BUY_PRODUCT"
            category = "INCOME" if delta < 0 else "EXPENDITURE"
            transactions.append({**base, "category": category, "type": op_type, "item": item,
                                  "quantity": qty, "unit_price": unit_price, "total": total,
                                  "exact": exact})
        elif len(moved_items) > 1:
            # Multiple items' shed contents moved the same turn (e.g. a
            # multi-crop agent selling two products at once): the pooled
            # dollar remainder is exact in aggregate, but not directly
            # separable by item from money-delta alone. Estimate each item's
            # share using that turn's PRE-transaction public market price
            # (already recorded in market_history -- a real, observed price,
            # not invented), then rescale every estimate by a single common
            # factor so the estimates sum EXACTLY to the true pooled
            # remainder (conservation is never broken by this estimate).
            # Flagged `exact: False`.
            prices = market_prices_by_turn.get(t["turn"], {})
            signed_estimates = {}
            for item, delta in moved_items:
                price = prices.get(item, 1) or 1
                qty = abs(delta)
                signed_estimates[item] = (qty * price) if delta < 0 else -(qty * price)
            total_estimate = sum(signed_estimates.values())
            scale = (remainder / total_estimate) if total_estimate else 1.0
            for item, delta in moved_items:
                qty = abs(delta)
                signed_value = signed_estimates[item] * scale
                op_type = "SELL" if delta < 0 else "BUY_PRODUCT"
                category = "INCOME" if delta < 0 else "EXPENDITURE"
                transactions.append({**base, "category": category, "type": op_type, "item": item,
                                      "quantity": qty, "unit_price": round(abs(signed_value) / qty, 4) if qty else None,
                                      "total": round(abs(signed_value), 4), "exact": False,
                                      "note": "multi-item turn; value estimated from pre-turn market price, "
                                              "rescaled to match the exact pooled remainder"})

    return transactions


def summarize_financial_ledger(transactions, starting_money, final_money):
    income = sum(t["total"] for t in transactions if t["category"] == "INCOME" and t["total"] is not None)
    expenditure = sum(t["total"] for t in transactions if t["category"] == "EXPENDITURE" and t["total"] is not None)
    unresolved = sum(1 for t in transactions if not t.get("exact", True))
    by_type = {}
    for t in transactions:
        if t["total"] is None:
            continue
        by_type.setdefault(t["type"], {"count": 0, "total": 0.0, "quantity": 0})
        by_type[t["type"]]["count"] += 1
        by_type[t["type"]]["total"] += t["total"]
        by_type[t["type"]]["quantity"] += t["quantity"] or 0
    return {
        "starting_money": starting_money,
        "final_money": final_money,
        "total_income": round(income, 4),
        "total_expenditure": round(expenditure, 4),
        "reconstructed_final_money": round(starting_money + income - expenditure, 4),
        "discrepancy": round((starting_money + income - expenditure) - final_money, 4),
        "n_unresolved_transactions": unresolved,
        "by_type": by_type,
    }


# ---------------------------------------------------------------------------
# Production ledger: stitches production_events into per-instance crop/animal
# lifecycle records, keyed by (x, y, planted_day) -- the strongest justified
# identity available since the simulator exposes no stable object IDs.
# ---------------------------------------------------------------------------

def build_crop_instances(production_events):
    instances = {}
    order = []
    for ev in production_events:
        if ev["event"] == "PLANT":
            key = (ev["x"], ev["y"], ev["day"])
            instances[key] = {
                "crop": ev["crop"], "x": ev["x"], "y": ev["y"],
                "planted_turn": ev["turn"], "planted_day": ev["day"],
                "watering_events": 0, "fertilize_events": 0,
                "harvests": [], "removed_turn": None, "removed_reason": None,
                "weed_conversion_turn": None,
            }
            order.append(key)

    def _find_open_instance(x, y, turn):
        # Most recent PLANT at (x,y) not yet closed (removed/weeded), as of `turn`.
        best = None
        for key in order:
            kx, ky, kday = key
            if kx != x or ky != y:
                continue
            inst = instances[key]
            if inst["planted_turn"] > turn:
                continue
            if inst["removed_turn"] is not None and inst["removed_turn"] <= turn:
                continue
            if inst["weed_conversion_turn"] is not None and inst["weed_conversion_turn"] <= turn:
                continue
            if best is None or inst["planted_turn"] > instances[best]["planted_turn"]:
                best = key
        return best

    for ev in production_events:
        if ev["event"] in ("WATER", "FERTILIZE", "HARVEST", "WEED_CONVERSION") and "crop" in ev:
            key = _find_open_instance(ev["x"], ev["y"], ev["turn"])
            if key is None:
                continue
            inst = instances[key]
            if ev["event"] == "WATER":
                inst["watering_events"] += 1
            elif ev["event"] == "FERTILIZE":
                inst["fertilize_events"] += 1
            elif ev["event"] == "HARVEST":
                inst["harvests"].append({"turn": ev["turn"], "day": ev["day"], "units": ev["units"]})
                if not ev.get("ongoing", True):
                    inst["removed_turn"] = ev["turn"]
                    inst["removed_reason"] = "HARVEST"
            elif ev["event"] == "WEED_CONVERSION":
                inst["weed_conversion_turn"] = ev["turn"]
                inst["removed_reason"] = "WEED_CONVERSION"
        if ev["event"] == "DIG" and ev.get("crop"):
            key = _find_open_instance(ev["x"], ev["y"], ev["turn"])
            if key:
                instances[key]["removed_turn"] = ev["turn"]
                instances[key]["removed_reason"] = "DIG"

    for key, inst in instances.items():
        end_turn = inst["removed_turn"] if inst["removed_turn"] is not None else (
            inst["weed_conversion_turn"] if inst["weed_conversion_turn"] is not None else None)
        inst["tile_days_occupied"] = None if end_turn is None else None  # filled by caller with turns_per_day context
        inst["total_harvested_units"] = sum(h["units"] for h in inst["harvests"])

    return list(instances.values())


def build_animal_instances(production_events):
    instances = {}
    order = []
    for ev in production_events:
        if ev["event"] == "PLACE_ANIMAL":
            key = (ev["x"], ev["y"], ev["day"])
            instances[key] = {
                "animal": ev["animal"], "structure": ev["structure"], "x": ev["x"], "y": ev["y"],
                "placed_turn": ev["turn"], "placed_day": ev["day"],
                "feed_events": 0, "care_events": 0, "harvests": [],
                "fertilizer_collected": 0, "escaped_turn": None,
            }
            order.append(key)

    def _find_open_instance(x, y, turn):
        best = None
        for key in order:
            kx, ky, kday = key
            if kx != x or ky != y:
                continue
            inst = instances[key]
            if inst["placed_turn"] > turn:
                continue
            if inst["escaped_turn"] is not None and inst["escaped_turn"] <= turn:
                continue
            if best is None or inst["placed_turn"] > instances[best]["placed_turn"]:
                best = key
        return best

    for ev in production_events:
        if ev["event"] in ("FEED", "CARE", "HARVEST", "COLLECT_FERTILIZER", "ANIMAL_ESCAPE") and "animal" in ev:
            key = _find_open_instance(ev["x"], ev["y"], ev["turn"])
            if key is None:
                continue
            inst = instances[key]
            if ev["event"] == "FEED":
                inst["feed_events"] += 1
            elif ev["event"] == "CARE":
                inst["care_events"] += 1
            elif ev["event"] == "HARVEST":
                inst["harvests"].append({"turn": ev["turn"], "day": ev["day"], "units": ev["units"]})
            elif ev["event"] == "COLLECT_FERTILIZER":
                inst["fertilizer_collected"] += 1
            elif ev["event"] == "ANIMAL_ESCAPE":
                inst["escaped_turn"] = ev["turn"]

    for inst in instances.values():
        inst["total_product_units"] = sum(h["units"] for h in inst["harvests"])

    return list(instances.values())


# ---------------------------------------------------------------------------
# Fertilizer ledger: sources (BUY_PRODUCT/animal collection), uses (FERTILIZE),
# sales (SELL). Aggregate (shed + all carried inventories), since per-unit
# attribution when multiple hands act simultaneously is not preserved.
# ---------------------------------------------------------------------------

def build_fertilizer_ledger(turns, financial_transactions, production_events):
    purchased = sum(t["quantity"] for t in financial_transactions
                     if t["type"] == "BUY_PRODUCT" and t["item"] == "FERTILIZER")
    sold = sum(t["quantity"] for t in financial_transactions
               if t["type"] == "SELL" and t["item"] == "FERTILIZER")
    collected = sum(1 for ev in production_events if ev["event"] == "COLLECT_FERTILIZER")
    used = sum(1 for t in turns for u in t["unit_actions"] if u["op"] == "FERTILIZE")

    starting = 0
    if turns:
        p0 = turns[0]["private_before"]
        starting = p0["shed"].get("FERTILIZER", 0) + sum(inv.get("FERTILIZER", 0) for inv in p0["inventories"])
    ending = starting
    for t in turns:
        if t["private_after"] is None:
            continue
        ending = t["private_after"]["shed"].get("FERTILIZER", 0) + \
            sum(inv.get("FERTILIZER", 0) for inv in t["private_after"]["inventories"])

    acquired = purchased + collected
    reconstructed_ending = starting + acquired - used - sold
    return {
        "starting_inventory": starting,
        "purchased": purchased,
        "collected_from_animals": collected,
        "total_acquired": acquired,
        "used_on_fertilize": used,
        "sold": sold,
        "ending_inventory": ending,
        "reconstructed_ending_inventory": reconstructed_ending,
        "discrepancy": reconstructed_ending - ending,
    }


# ---------------------------------------------------------------------------
# Land ledger
# ---------------------------------------------------------------------------

def build_land_ledger(turns, financial_transactions):
    purchases = [t for t in financial_transactions if t["type"] == "BUY_LAND"]
    starting = len(turns[0]["unlocked_quadrants_before"]) if turns else 1
    ending = starting
    for t in turns:
        if t["unlocked_quadrants_after"] is not None:
            ending = len(t["unlocked_quadrants_after"])
    return {
        "starting_unlocked_quadrants": starting,
        "purchases": [{"turn": p["turn"], "day": p["day"], "cost": p["total"]} for p in purchases],
        "ending_unlocked_quadrants": ending,
        "reconstructed_ending_unlocked_quadrants": starting + len(purchases),
        "discrepancy": (starting + len(purchases)) - ending,
    }
