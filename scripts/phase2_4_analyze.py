"""
Phase 2.4 analysis: loads every results/phase2_4/dataset_*.csv (Stages B-F)
plus results/phase2_4/stage_a_verification.json, produces group/cell-level
summary statistics (analysis_summary.json) and explicit paired-comparison
numbers for each stage's headline question. Read-only; never re-runs episodes.
"""
import csv
import glob
import json
import os
import statistics

ROOT = "results/phase2_4"

NUMERIC_FIELDS = [
    "starting_money", "final_money", "profit", "revenue_total",
    "cost_seed", "cost_hire", "cost_land", "cost_animal", "cost_buy_wheat", "cost_buy_fertilizer", "cost_other",
    "sold_units_total", "avg_realized_price_overall", "hands_hired_events", "land_quadrants_end",
    "productive_action_rate", "movement_fraction", "market_action_fraction",
    "win", "money_margin", "inventory_overflow_flag",
]


def load_rows():
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "dataset_*.csv"))):
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                for k in NUMERIC_FIELDS:
                    v = r.get(k)
                    if v in (None, ""):
                        r[k] = None
                    else:
                        try:
                            r[k] = float(v)
                        except ValueError:
                            pass
                r["harvest_units"] = json.loads(r["harvest_units_json"]) if r.get("harvest_units_json") else {}
                r["animal_units"] = json.loads(r["animal_units_json"]) if r.get("animal_units_json") else {}
                r["config"] = json.loads(r["config_json"]) if r.get("config_json") else {}
                rows.append(r)
    return rows


def stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"n": 0, "mean": None, "median": None, "stdev": None, "min": None, "max": None}
    return {
        "n": len(vals), "mean": round(statistics.mean(vals), 3), "median": round(statistics.median(vals), 3),
        "stdev": round(statistics.pstdev(vals), 3) if len(vals) > 1 else 0.0,
        "min": round(min(vals), 3), "max": round(max(vals), 3),
    }


def cell_summary(rows):
    by_cell = {}
    for r in rows:
        key = (r["stage"], r["group"], r["cell_id"])
        by_cell.setdefault(key, []).append(r)
    out = {}
    for (stage, group, cell_id), cell_rows in by_cell.items():
        out[f"{stage}::{group}::{cell_id}"] = {
            "stage": stage, "group": group, "cell_id": cell_id, "n_episodes": len(cell_rows),
            "config": cell_rows[0]["config"],
            "final_money": stats([r["final_money"] for r in cell_rows]),
            "profit": stats([r["profit"] for r in cell_rows]),
            "revenue_total": stats([r["revenue_total"] for r in cell_rows]),
            "avg_realized_price_overall": stats([r["avg_realized_price_overall"] for r in cell_rows]),
            "sold_units_total": stats([r["sold_units_total"] for r in cell_rows]),
            "win_rate": stats([r["win"] for r in cell_rows])["mean"],
            "money_margin": stats([r["money_margin"] for r in cell_rows]),
            "inventory_overflow_rate": stats([r["inventory_overflow_flag"] for r in cell_rows])["mean"],
            "validation_pass_rate": sum(1 for r in cell_rows if r["validation_overall"] == "PASS") / len(cell_rows),
            "validation_partial_rate": sum(1 for r in cell_rows if r["validation_overall"] == "PARTIAL") / len(cell_rows),
            "validation_fail_rate": sum(1 for r in cell_rows if r["validation_overall"] == "FAIL") / len(cell_rows),
            "seeds": sorted(set(r["seed"] for r in cell_rows)),
            "per_seed_final_money": {r["seed"]: r["final_money"] for r in cell_rows},
        }
    return out


def mean_money(summary, group, cell_id):
    for v in summary.values():
        if v["group"] == group and v["cell_id"] == cell_id:
            return v["final_money"]["mean"]
    return None


def paired_win_rate(summary, group, cell_a, cell_b):
    """Fraction of SHARED seeds where cell_a's final_money > cell_b's (paired, same-seed comparison)."""
    a = b = None
    for v in summary.values():
        if v["group"] == group and v["cell_id"] == cell_a:
            a = v["per_seed_final_money"]
        if v["group"] == group and v["cell_id"] == cell_b:
            b = v["per_seed_final_money"]
    if a is None or b is None:
        return None
    shared = sorted(set(a) & set(b))
    if not shared:
        return None
    wins = sum(1 for s in shared if a[s] > b[s])
    return {"n_shared_seeds": len(shared), "a_wins": wins, "a_win_rate": round(wins / len(shared), 3),
            "mean_diff_a_minus_b": round(statistics.mean(a[s] - b[s] for s in shared), 2)}


def build_effects(summary):
    out = {}

    # Stage B: best non-passive policy per crop vs passive.
    out["b1_best_policy_vs_passive"] = {}
    for crop in ("WHEAT", "MELON"):
        passive = mean_money(summary, "b1_sale_timing_by_crop", f"b1_{crop}_passive")
        candidates = [(cid.split(f"b1_{crop}_", 1)[1], v["final_money"]["mean"])
                      for cid, v in ((k.split("::")[-1], v) for k, v in summary.items())
                      if v["group"] == "b1_sale_timing_by_crop" and v["cell_id"].startswith(f"b1_{crop}_")
                      and not v["cell_id"].endswith("passive")]
        if candidates and passive is not None:
            best_name, best_money = max(candidates, key=lambda x: x[1])
            out["b1_best_policy_vs_passive"][crop] = {
                "passive": passive, "best_non_passive_policy": best_name, "best_non_passive_money": best_money,
                "improvement": round(best_money - passive, 2),
                "paired": paired_win_rate(summary, "b1_sale_timing_by_crop", f"b1_{crop}_{best_name}", f"b1_{crop}_passive"),
            }

    # Stage C: does market awareness change the production ranking?
    simple_passive = mean_money(summary, "c1_production_x_market", "c1_simple_melon_2h_passive")
    integrated_passive = mean_money(summary, "c1_production_x_market", "c1_integrated_inv_high_passive")
    best_simple = max((v["final_money"]["mean"] for v in summary.values()
                        if v["group"] == "c1_production_x_market" and v["cell_id"].startswith("c1_simple_melon_2h_")),
                       default=None)
    best_integrated = max((v["final_money"]["mean"] for v in summary.values()
                            if v["group"] == "c1_production_x_market" and v["cell_id"].startswith("c1_integrated_inv_high_")),
                           default=None)
    if None not in (simple_passive, integrated_passive, best_simple, best_integrated):
        out["c1_production_ranking"] = {
            "simple_passive": simple_passive, "integrated_passive": integrated_passive,
            "integrated_lead_under_passive": round(integrated_passive - simple_passive, 2),
            "simple_best_market_aware": best_simple, "integrated_best_market_aware": best_integrated,
            "integrated_lead_under_best_market_aware": round(best_integrated - best_simple, 2),
        }

    # Stage D: overflow-safety paired comparisons.
    out["d1_overflow_safety_pairs"] = {}
    for name in ("threshold_1.0", "threshold_1.3", "batch_10d"):
        on = mean_money(summary, "d1_inventory_holding", f"d1_{name}_safetyon")
        off = mean_money(summary, "d1_inventory_holding", f"d1_{name}_safetyoff")
        overflow_off = None
        for v in summary.values():
            if v["group"] == "d1_inventory_holding" and v["cell_id"] == f"d1_{name}_safetyoff":
                overflow_off = v["inventory_overflow_rate"]
        if on is not None and off is not None:
            out["d1_overflow_safety_pairs"][name] = {
                "safety_on_money": on, "safety_off_money": off, "cost_of_removing_safety": round(on - off, 2),
                "safety_off_overflow_rate": overflow_off,
            }

    # Stage E: tick-timing realized price comparison.
    e_after = e_before = None
    for v in summary.values():
        if v["group"] == "e1_town_demand_timing" and v["cell_id"] == "e1_tick_after":
            e_after = v["avg_realized_price_overall"]["mean"]
        if v["group"] == "e1_town_demand_timing" and v["cell_id"] == "e1_tick_before":
            e_before = v["avg_realized_price_overall"]["mean"]
    if e_after is not None and e_before is not None:
        out["e1_tick_timing"] = {
            "avg_realized_price_after_tick": e_after, "avg_realized_price_before_tick": e_before,
            "diff": round(e_after - e_before, 4),
            "paired": paired_win_rate(summary, "e1_town_demand_timing", "e1_tick_after", "e1_tick_before"),
        }

    return out


def main():
    rows = load_rows()
    summary = cell_summary(rows)
    effects = build_effects(summary)
    stage_a_path = os.path.join(ROOT, "stage_a_verification.json")
    stage_a = json.load(open(stage_a_path)) if os.path.exists(stage_a_path) else None
    out = {"n_total_episodes": len(rows), "cells": summary, "effects": effects, "stage_a_verification": stage_a}
    with open(os.path.join(ROOT, "analysis_summary.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"Loaded {len(rows)} episode rows across {len(summary)} cells.")
    print(f"Wrote {os.path.join(ROOT, 'analysis_summary.json')}")


if __name__ == "__main__":
    main()
