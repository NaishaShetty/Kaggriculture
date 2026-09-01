"""
Market + town-demand telemetry. Price/inventory history is already public raw
data captured per-turn by extractor.py (`market_history`, `town_history`);
this module adds derived statistics on top of it, plus deterministic town
CONSUMPTION reconstruction. Town consumption timing/quantities are computed
from `SHOPS`, `TOWN_CENTER_PRODUCTS`, and the shop/center sell intervals —
all public, fixed (or fixed-per-episode-config) constants imported read-only
from the frozen simulator module — not a re-simulation of gameplay, since
town consumption never depends on player actions, only on step number and
which shops are currently unlocked (both already recorded).
"""
import statistics

from vendor_kaggriculture.kaggriculture import SHOPS, TOWN_CENTER_PRODUCTS


def build_market_price_stats(market_history):
    by_item = {}
    for rec in market_history:
        for item, price in rec["prices"].items():
            by_item.setdefault(item, []).append(price)
    stats = {}
    for item, prices in by_item.items():
        changes = [abs(prices[i] - prices[i - 1]) for i in range(1, len(prices))]
        stats[item] = {
            "min_price": min(prices), "max_price": max(prices),
            "mean_price": round(statistics.mean(prices), 4),
            "price_volatility_stdev": round(statistics.pstdev(prices), 4) if len(prices) > 1 else 0.0,
            "mean_abs_change_per_turn": round(statistics.mean(changes), 4) if changes else 0.0,
        }
    return stats


def build_transaction_summary(financial_transactions):
    by_item = {}
    for t in financial_transactions:
        if t["type"] not in ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"):
            continue
        key = (t["type"], t["item"])
        by_item.setdefault(key, {"count": 0, "quantity": 0, "total": 0.0, "prices": [], "n_exact": 0})
        rec = by_item[key]
        rec["count"] += 1
        rec["quantity"] += t["quantity"] or 0
        if t["total"] is not None:
            rec["total"] += t["total"]
        if t["unit_price"] is not None:
            rec["prices"].append(t["unit_price"])
        if t["exact"]:
            rec["n_exact"] += 1

    out = {}
    for (op, item), rec in by_item.items():
        prices = rec["prices"]
        out[f"{op}:{item}"] = {
            "op": op, "item": item, "order_count": rec["count"], "total_quantity": rec["quantity"],
            "total_value": round(rec["total"], 4),
            "avg_realized_price": round(statistics.mean(prices), 4) if prices else None,
            "min_realized_price": min(prices) if prices else None,
            "max_realized_price": max(prices) if prices else None,
            "n_exact": rec["n_exact"], "n_total": rec["count"],
        }
    return out


def _town_consumption_at_step(unlocked_shops, step, shop_interval, center_interval):
    consumption = {}
    if step % shop_interval == 0:
        for shop_name in unlocked_shops:
            products = SHOPS[shop_name]
            multiplier = 2 if len(products) == 1 else 1
            for item in products:
                consumption[item] = consumption.get(item, 0) + multiplier
    if step % center_interval == 0:
        for item in TOWN_CENTER_PRODUCTS:
            consumption[item] = consumption.get(item, 0) + 1
    return consumption


def build_town_telemetry(town_history, configuration=None):
    cfg = configuration or {}
    shop_interval = max(1, int(cfg.get("townShopSellInterval", 4)))
    center_interval = max(1, int(cfg.get("townCenterSellInterval", 24)))

    unlock_events = []
    prev_shops = []
    for rec in town_history:
        shops = rec["unlocked_shops"]
        if len(shops) > len(prev_shops):
            new_shop = shops[len(prev_shops)]
            unlock_events.append({
                "turn": rec["turn"], "day": rec["day"], "shop": new_shop,
                "instance_index": shops[:len(prev_shops) + 1].count(new_shop),
                "total_shops_unlocked": len(shops),
            })
        prev_shops = shops

    consumption_events = []
    for rec in town_history:
        step = rec["turn"]
        consumption = _town_consumption_at_step(rec["unlocked_shops"], step, shop_interval, center_interval)
        if consumption:
            consumption_events.append({"turn": step, "day": rec["day"], "consumption": consumption})

    shop_instance_counts = {}
    if town_history:
        for shop in town_history[-1]["unlocked_shops"]:
            shop_instance_counts[shop] = shop_instance_counts.get(shop, 0) + 1

    return {
        "shop_unlock_events": unlock_events,
        "final_shop_instance_counts": shop_instance_counts,
        "total_shop_instances": len(town_history[-1]["unlocked_shops"]) if town_history else 0,
        "expected_consumption_events": consumption_events,
        "shop_sell_interval": shop_interval,
        "center_sell_interval": center_interval,
    }
