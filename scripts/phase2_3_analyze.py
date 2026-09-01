"""
Phase 2.3 analysis: loads every results/phase2_3/dataset_*.csv, produces
group/cell-level summary statistics (analysis_summary.json) plus a set of
explicit interaction-effect calculations for the Stage C cells (land x labor,
labor x crop, animal x crop sub-additivity, animal x fertilizer, capital x
horizon, inventory bottleneck). Read-only over the CSVs; never re-runs
episodes itself.
"""
import csv
import glob
import json
import os
import statistics

ROOT = "results/phase2_3"

NUMERIC_FIELDS = [
    "starting_money", "final_money", "profit", "revenue_total",
    "cost_seed", "cost_hire", "cost_land", "cost_animal", "cost_buy_wheat", "cost_buy_fertilizer", "cost_other",
    "animals_placed", "animals_escaped", "hands_hired_events", "land_quadrants_end",
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
        total_harvest = {}
        total_animal = {}
        for r in cell_rows:
            for c, u in r["harvest_units"].items():
                total_harvest[c] = total_harvest.get(c, 0) + u
            for a, u in r["animal_units"].items():
                total_animal[a] = total_animal.get(a, 0) + u
        out[f"{stage}::{group}::{cell_id}"] = {
            "stage": stage, "group": group, "cell_id": cell_id, "n_episodes": len(cell_rows),
            "config": cell_rows[0]["config"],
            "final_money": stats([r["final_money"] for r in cell_rows]),
            "profit": stats([r["profit"] for r in cell_rows]),
            "revenue_total": stats([r["revenue_total"] for r in cell_rows]),
            "cost_seed": stats([r["cost_seed"] for r in cell_rows]),
            "cost_hire": stats([r["cost_hire"] for r in cell_rows]),
            "cost_land": stats([r["cost_land"] for r in cell_rows]),
            "cost_animal": stats([r["cost_animal"] for r in cell_rows]),
            "cost_buy_wheat": stats([r["cost_buy_wheat"] for r in cell_rows]),
            "cost_buy_fertilizer": stats([r["cost_buy_fertilizer"] for r in cell_rows]),
            "win_rate": stats([r["win"] for r in cell_rows])["mean"],
            "money_margin": stats([r["money_margin"] for r in cell_rows]),
            "animals_placed": stats([r["animals_placed"] for r in cell_rows]),
            "animals_escaped": stats([r["animals_escaped"] for r in cell_rows]),
            "land_quadrants_end": stats([r["land_quadrants_end"] for r in cell_rows]),
            "productive_action_rate": stats([r["productive_action_rate"] for r in cell_rows]),
            "movement_fraction": stats([r["movement_fraction"] for r in cell_rows]),
            "inventory_overflow_rate": stats([r["inventory_overflow_flag"] for r in cell_rows])["mean"],
            "validation_pass_rate": sum(1 for r in cell_rows if r["validation_overall"] == "PASS") / len(cell_rows),
            "validation_partial_rate": sum(1 for r in cell_rows if r["validation_overall"] == "PARTIAL") / len(cell_rows),
            "validation_fail_rate": sum(1 for r in cell_rows if r["validation_overall"] == "FAIL") / len(cell_rows),
            "total_harvest_units": total_harvest,
            "total_animal_units": total_animal,
        }
    return out


def mean_money(summary, group, cell_id):
    key = None
    for k, v in summary.items():
        if v["group"] == group and v["cell_id"] == cell_id:
            key = k
            break
    if key is None:
        return None
    return summary[key]["final_money"]["mean"]


def interaction_effects(summary):
    """Explicit interaction-effect numbers for the Stage C cells -- computed
    here (plain arithmetic on group means), not asserted narratively without
    the underlying numbers alongside them."""
    out = {}

    # C1: land x labor interaction on MELON. Effect = [money(2q,4h)-money(2q,0h)]
    # - [money(0q,4h)-money(0q,0h)] -- positive means land and labor are
    # complements (adding labor is worth more when land is also added).
    def g(q, h):
        return mean_money(summary, "c1_land_x_labor", f"lxl_{q}q_{h}h")
    if all(g(q, h) is not None for q in (0, 2) for h in (0, 4)):
        out["c1_land_x_labor_interaction"] = {
            "money_0q_0h": g(0, 0), "money_0q_4h": g(0, 4), "money_2q_0h": g(2, 0), "money_2q_4h": g(2, 4),
            "labor_effect_at_0q": round(g(0, 4) - g(0, 0), 2),
            "labor_effect_at_2q": round(g(2, 4) - g(2, 0), 2),
            "interaction_term": round((g(2, 4) - g(2, 0)) - (g(0, 4) - g(0, 0)), 2),
        }

    # C2: labor x crop -- proportional final-money gain from 0->4 hands, per crop.
    out["c2_labor_x_crop_proportional_gain"] = {}
    for crop in ("WHEAT", "MELON", "STRAWBERRY"):
        m0 = mean_money(summary, "c2_labor_x_crop", f"lxc_{crop}_0h")
        m4 = mean_money(summary, "c2_labor_x_crop", f"lxc_{crop}_4h")
        if m0 and m4 is not None:
            out["c2_labor_x_crop_proportional_gain"][crop] = {
                "money_0h": m0, "money_4h": m4, "abs_gain": round(m4 - m0, 2),
                "pct_gain": round((m4 - m0) / m0 * 100, 2) if m0 else None,
            }

    # C3: animal x crop sub/super-additivity.
    m_crop = mean_money(summary, "c3_animal_x_crop", "axc_crop_only")
    m_animal = mean_money(summary, "c3_animal_x_crop", "axc_animal_only")
    m_both = mean_money(summary, "c3_animal_x_crop", "axc_crop_animal")
    m_both_fert = mean_money(summary, "c3_animal_x_crop", "axc_crop_animal_fert")
    if None not in (m_crop, m_animal, m_both):
        starting = 3000.0
        additive_prediction = m_crop + m_animal - starting
        out["c3_animal_x_crop_additivity"] = {
            "money_crop_only": m_crop, "money_animal_only": m_animal,
            "money_crop_and_animal": m_both, "money_crop_and_animal_with_fertilizer_use": m_both_fert,
            "additive_prediction": round(additive_prediction, 2),
            "actual_minus_additive_prediction": round(m_both - additive_prediction, 2),
            "fertilizer_use_effect": round(m_both_fert - m_both, 2) if m_both_fert is not None else None,
        }

    # C4: animal x fertilizer, by labor level.
    out["c4_animal_x_fertilizer_by_labor"] = {}
    for h in (1, 3):
        off = mean_money(summary, "c4_animal_x_fertilizer", f"axf_off_{h}h")
        on = mean_money(summary, "c4_animal_x_fertilizer", f"axf_on_{h}h")
        if off is not None and on is not None:
            out["c4_animal_x_fertilizer_by_labor"][f"{h}h"] = {
                "money_off": off, "money_on": on, "effect": round(on - off, 2),
            }

    # C5: capital x horizon.
    out["c5_capital_x_horizon"] = {}
    for kind in ("land", "animal"):
        pts = {}
        for d in (0, 150, 400):
            m = mean_money(summary, "c5_capital_x_horizon", f"cxh_{kind}_day{d}")
            if m is not None:
                pts[d] = m
        if pts:
            out["c5_capital_x_horizon"][kind] = pts

    # C6: inventory bottleneck.
    key_low = None
    key_high = None
    for k, v in summary.items():
        if v["group"] == "c6_inventory_bottleneck" and v["cell_id"] == "inv_low":
            key_low = k
        if v["group"] == "c6_inventory_bottleneck" and v["cell_id"] == "inv_high":
            key_high = k
    if key_low and key_high:
        out["c6_inventory_bottleneck"] = {
            "overflow_rate_low": summary[key_low]["inventory_overflow_rate"],
            "overflow_rate_high": summary[key_high]["inventory_overflow_rate"],
            "final_money_low": summary[key_low]["final_money"]["mean"],
            "final_money_high": summary[key_high]["final_money"]["mean"],
        }

    return out


def main():
    rows = load_rows()
    summary = cell_summary(rows)
    effects = interaction_effects(summary)
    out = {"n_total_episodes": len(rows), "cells": summary, "interaction_effects": effects}
    with open(os.path.join(ROOT, "analysis_summary.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"Loaded {len(rows)} episode rows across {len(summary)} cells.")
    print(f"Wrote {os.path.join(ROOT, 'analysis_summary.json')}")


if __name__ == "__main__":
    main()
