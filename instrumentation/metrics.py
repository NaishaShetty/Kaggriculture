"""
Derived metrics layer: action efficiency, crop-level and animal-level
economics, land utilization rates, daily summaries, episode summaries.
Pure aggregation over the raw + ledger layers -- no new state reconstruction,
no strategic ranking or optimization (Phase 2.1 scope boundary: measurement
only, e.g. "revenue per tile-day" is reported for every crop with no claim
about which crop is "best").
"""
import statistics

from vendor_kaggriculture.kaggriculture import FARMER_MOVES

MOVEMENT_OPS = set(FARMER_MOVES)


def _event_positions(production_events, turn):
    return {(ev["x"], ev["y"]) for ev in production_events if ev["turn"] == turn}


def action_efficiency(turns, production_events, board_size):
    events_by_turn = {}
    for ev in production_events:
        events_by_turn.setdefault(ev["turn"], set()).add((ev["x"], ev["y"]))

    counts = {
        "total_unit_actions": 0, "movement": 0, "movement_productive": 0,
        "crop": 0, "crop_productive": 0, "animal": 0, "animal_productive": 0,
        "farm": 0, "idle": 0, "unknown": 0,
        "n_hand_actions": 0, "n_farmer_actions": 0,
        "total_market_orders": 0, "market_by_category": {},
    }
    for t in turns:
        active_positions = events_by_turn.get(t["turn"], set())
        for u in t["unit_actions"]:
            counts["total_unit_actions"] += 1
            if u["unit"] == "farmer":
                counts["n_farmer_actions"] += 1
            else:
                counts["n_hand_actions"] += 1
            cat = u["category"]
            x, y = u["pos_before"]
            if cat == "MOVEMENT":
                counts["movement"] += 1
                dx, dy = FARMER_MOVES[u["op"]]
                nx, ny = x + dx, y + dy
                if 0 <= nx < board_size and 0 <= ny < board_size:
                    counts["movement_productive"] += 1
            elif cat == "CROP":
                counts["crop"] += 1
                if (x, y) in active_positions:
                    counts["crop_productive"] += 1
            elif cat == "ANIMAL":
                counts["animal"] += 1
                if (x, y) in active_positions:
                    counts["animal_productive"] += 1
            elif cat == "FARM":
                counts["farm"] += 1
            elif cat == "IDLE":
                counts["idle"] += 1
            else:
                counts["unknown"] += 1
        for m in t["market_orders"]:
            counts["total_market_orders"] += 1
            counts["market_by_category"][m["category"]] = counts["market_by_category"].get(m["category"], 0) + 1

    total = counts["total_unit_actions"] or 1
    productive = counts["movement_productive"] + counts["crop_productive"] + counts["animal_productive"] + counts["farm"]
    return {
        **counts,
        "productive_action_rate": round(productive / total, 4),
        "idle_fraction": round(counts["idle"] / total, 4),
        "movement_fraction": round(counts["movement"] / total, 4),
        "crop_fraction": round(counts["crop"] / total, 4),
        "animal_fraction": round(counts["animal"] / total, 4),
        "market_action_fraction": round(counts["total_market_orders"] / total, 4),
    }


def crop_level_metrics(crop_instances, financial_transactions, turns_per_day=24):
    by_crop = {}
    for inst in crop_instances:
        crop = inst["crop"]
        rec = by_crop.setdefault(crop, {
            "n_planted": 0, "n_harvested_instances": 0, "n_weeded": 0, "n_dug": 0,
            "total_harvested_units": 0, "total_harvest_events": 0, "total_watering_events": 0,
            "total_fertilize_events": 0,
        })
        rec["n_planted"] += 1
        if inst["harvests"]:
            rec["n_harvested_instances"] += 1
        if inst["removed_reason"] == "WEED_CONVERSION" or inst["weed_conversion_turn"] is not None:
            rec["n_weeded"] += 1
        if inst["removed_reason"] == "DIG":
            rec["n_dug"] += 1
        rec["total_harvested_units"] += inst["total_harvested_units"]
        rec["total_harvest_events"] += len(inst["harvests"])
        rec["total_watering_events"] += inst["watering_events"]
        rec["total_fertilize_events"] += inst["fertilize_events"]

    seeds_bought = {}
    revenue = {}
    for t in financial_transactions:
        if t["type"] == "BUY_SEED":
            seeds_bought[t["item"]] = seeds_bought.get(t["item"], 0) + t["quantity"]
        if t["type"] == "SELL" and t["total"] is not None:
            revenue[t["item"]] = revenue.get(t["item"], 0.0) + t["total"]

    for crop, rec in by_crop.items():
        rec["seeds_purchased"] = seeds_bought.get(crop, 0)
        rec["revenue"] = round(revenue.get(crop, 0.0), 4)
        rec["revenue_per_harvested_unit"] = round(rec["revenue"] / rec["total_harvested_units"], 4) \
            if rec["total_harvested_units"] else None
        rec["revenue_per_seed_purchased"] = round(rec["revenue"] / rec["seeds_purchased"], 4) \
            if rec["seeds_purchased"] else None
        n_actions = rec["total_watering_events"] + rec["total_harvest_events"] + rec["n_planted"] + rec["total_fertilize_events"]
        rec["revenue_per_action"] = round(rec["revenue"] / n_actions, 4) if n_actions else None
    return by_crop


def animal_level_metrics(animal_instances, financial_transactions):
    by_animal = {}
    for inst in animal_instances:
        animal = inst["animal"]
        rec = by_animal.setdefault(animal, {
            "n_placed": 0, "n_escaped": 0, "total_product_units": 0,
            "total_feed_events": 0, "total_care_events": 0, "total_fertilizer_collected": 0,
        })
        rec["n_placed"] += 1
        if inst["escaped_turn"] is not None:
            rec["n_escaped"] += 1
        rec["total_product_units"] += inst["total_product_units"]
        rec["total_feed_events"] += inst["feed_events"]
        rec["total_care_events"] += inst["care_events"]
        rec["total_fertilizer_collected"] += inst["fertilizer_collected"]

    purchased = {}
    for t in financial_transactions:
        if t["type"] == "BUY_ANIMAL":
            purchased[t["item"]] = purchased.get(t["item"], 0) + t["quantity"]
            by_animal.setdefault(t["item"], {"n_placed": 0, "n_escaped": 0, "total_product_units": 0,
                                              "total_feed_events": 0, "total_care_events": 0,
                                              "total_fertilizer_collected": 0})

    for animal, rec in by_animal.items():
        rec["purchased"] = purchased.get(animal, 0)
    return by_animal


def land_utilization_from_daily_snapshot(day_snapshot):
    unlocked = day_snapshot["unlocked_tiles"]
    empty = day_snapshot["EMPTY"]
    weed = day_snapshot["WEED"]
    crop = sum(day_snapshot["CROP"].values())
    structure = sum(day_snapshot["STRUCTURE_EMPTY"].values()) + sum(day_snapshot["STRUCTURE_ANIMAL"].values())
    productive = crop + structure
    return {
        "unlocked_tiles": unlocked,
        "land_utilization_rate": round(productive / unlocked, 4) if unlocked else None,
        "productive_tile_rate": round(productive / unlocked, 4) if unlocked else None,
        "idle_tile_rate": round(empty / unlocked, 4) if unlocked else None,
        "weed_rate": round(weed / unlocked, 4) if unlocked else None,
    }


def daily_summary(player, turns, financial_transactions, land_daily, production_events):
    days = sorted(set(t["day"] for t in turns))
    out = []
    for day in days:
        day_turns = [t for t in turns if t["day"] == day]
        day_txns = [t for t in financial_transactions if t["day"] == day]
        day_events = [e for e in production_events if e["day"] == day]
        start_money = day_turns[0]["money_before"]
        end_money = day_turns[-1]["money_after"] if day_turns[-1]["money_after"] is not None else start_money
        income = round(sum(t["total"] for t in day_txns if t["category"] == "INCOME" and t["total"] is not None), 4)
        expenditure = round(sum(t["total"] for t in day_txns if t["category"] == "EXPENDITURE" and t["total"] is not None), 4)
        land_snap = land_daily.get(day)
        out.append({
            "player": player, "day": day,
            "starting_money": start_money, "ending_money": end_money,
            "revenue": income, "expenditure": expenditure, "net": round(income - expenditure, 4),
            "seeds_purchased": sum(t["quantity"] for t in day_txns if t["type"] == "BUY_SEED"),
            "crops_planted": sum(1 for e in day_events if e["event"] == "PLANT"),
            "crops_harvested": sum(1 for e in day_events if e["event"] == "HARVEST" and "crop" in e),
            "products_sold": sum(t["quantity"] for t in day_txns if t["type"] == "SELL"),
            "animals_purchased": sum(t["quantity"] for t in day_txns if t["type"] == "BUY_ANIMAL"),
            "animal_products_harvested": sum(1 for e in day_events if e["event"] == "HARVEST" and "animal" in e),
            "fertilizer_purchased": sum(t["quantity"] for t in day_txns if t["type"] == "BUY_PRODUCT" and t["item"] == "FERTILIZER"),
            "fertilizer_used": sum(1 for tt in day_turns for u in tt["unit_actions"] if u["op"] == "FERTILIZE"),
            "fertilizer_sold": sum(t["quantity"] for t in day_txns if t["type"] == "SELL" and t["item"] == "FERTILIZER"),
            "workers_hired": sum(t["quantity"] for t in day_txns if t["type"] == "HIRE"),
            "land_purchased": sum(t["quantity"] for t in day_txns if t["type"] == "BUY_LAND"),
            "land_utilization": land_utilization_from_daily_snapshot(land_snap) if land_snap else None,
        })
    return out


def episode_summary(player, outcome, financial_summary, action_eff, crop_metrics, animal_metrics,
                     market_stats, town_telemetry, opponent_final_money):
    total_actions = action_eff["total_unit_actions"] or 1
    net_profit = financial_summary["final_money"] - financial_summary["starting_money"]
    return {
        "player": player,
        "financial": {
            "final_money": financial_summary["final_money"],
            "net_profit": round(net_profit, 4),
            "revenue": financial_summary["total_income"],
            "expenditure": financial_summary["total_expenditure"],
        },
        "production": {
            "total_crop_harvest_events": sum(c["total_harvest_events"] for c in crop_metrics.values()),
            "total_crop_units_harvested": sum(c["total_harvested_units"] for c in crop_metrics.values()),
            "total_animal_product_units": sum(a["total_product_units"] for a in animal_metrics.values()),
        },
        "efficiency": {
            "profit_per_action": round(net_profit / total_actions, 4),
            "productive_action_rate": action_eff["productive_action_rate"],
            "idle_fraction": action_eff["idle_fraction"],
            "movement_fraction": action_eff["movement_fraction"],
        },
        "market": {"price_stats": market_stats},
        "town": {
            "shops_unlocked": town_telemetry["total_shop_instances"],
            "shop_instance_counts": town_telemetry["final_shop_instance_counts"],
        },
        "outcome": {
            "winner": outcome["winner"], "final_money": outcome["final_money"][player],
            "opponent_final_money": opponent_final_money,
            "margin": outcome["margin"] if player == 0 else (
                -outcome["margin"] if outcome["margin"] is not None else None),
        },
    }
