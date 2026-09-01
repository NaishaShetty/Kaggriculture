"""
Phase 2.2 analysis: reads results/phase2_2/dataset_*.csv, computes the
multiple economic views required by brief section 26 (absolute, production,
land, capital, action, time, competitive), and writes
results/phase2_2/analysis_summary.json for the report to quote from.
Pure aggregation -- no strategic ranking baked in beyond descriptive stats;
any "regime" labeling is done in the report text with the numbers cited.
"""
import csv
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT_ROOT = "results/phase2_2"


def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _f(row, key):
    v = row.get(key)
    if v is None or v == "":
        return None
    return float(v)


def _stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return {
        "n": len(vals), "mean": round(statistics.mean(vals), 4),
        "median": round(statistics.median(vals), 4),
        "stdev": round(statistics.pstdev(vals), 4) if len(vals) > 1 else 0.0,
        "min": round(min(vals), 4), "max": round(max(vals), 4),
    }


def summarize_by(rows, group_keys, value_keys):
    groups = {}
    for r in rows:
        key = tuple(r[k] for k in group_keys)
        groups.setdefault(key, []).append(r)
    out = {}
    for key, grp in groups.items():
        label = "|".join(key)
        entry = {"n_episodes": len(grp)}
        for vk in value_keys:
            entry[vk] = _stats([_f(r, vk) for r in grp])
        wins = [_f(r, "win") for r in grp if r.get("win") not in (None, "")]
        entry["win_rate"] = round(sum(wins) / len(wins), 4) if wins else None
        valids = [r["validation_overall"] for r in grp]
        entry["validation_pass_rate"] = round(sum(1 for v in valids if v == "PASS") / len(valids), 4)
        out[label] = entry
    return out


VALUE_KEYS = [
    "final_money", "profit", "revenue", "harvest_units", "tile_days", "revenue_per_tile_day",
    "revenue_per_action", "capital_locked", "first_harvest_day", "unsold_units", "money_margin",
]


def main():
    isolated = _read(os.path.join(OUT_ROOT, "dataset_isolated.csv"))
    fertilizer = _read(os.path.join(OUT_ROOT, "dataset_fertilizer.csv"))
    timing = _read(os.path.join(OUT_ROOT, "dataset_timing.csv"))
    headtohead = _read(os.path.join(OUT_ROOT, "dataset_headtohead.csv"))
    combo = _read(os.path.join(OUT_ROOT, "dataset_combo.csv"))
    allocation = _read(os.path.join(OUT_ROOT, "dataset_allocation.csv"))

    summary = {
        "isolated_by_crop_opponent": summarize_by(isolated, ["crop", "opponent"], VALUE_KEYS),
        "isolated_by_crop_pooled": summarize_by(isolated, ["crop"], VALUE_KEYS),
        "fertilizer_by_crop": summarize_by(fertilizer, ["crop"], VALUE_KEYS),
        "fertilizer_baseline_no_fert_by_crop": summarize_by(
            [r for r in isolated if r["opponent"] == "pass"], ["crop"], VALUE_KEYS),
        "timing_by_crop_condition": summarize_by(timing, ["crop", "condition"], VALUE_KEYS),
        "headtohead_by_crop": summarize_by(headtohead, ["crop"], VALUE_KEYS),
        "combo_by_experiment": summarize_by(combo, ["experiment_id", "crop"], VALUE_KEYS),
        "allocation_by_experiment": summarize_by(allocation, ["experiment_id", "crop"], VALUE_KEYS),
        "counts": {
            "isolated": len(isolated), "fertilizer": len(fertilizer), "timing": len(timing),
            "headtohead": len(headtohead), "combo": len(combo), "allocation": len(allocation),
            "total_episode_rows": len(isolated) + len(fertilizer) + len(timing) + len(headtohead) +
            len(combo) + len(allocation),
        },
    }

    with open(os.path.join(OUT_ROOT, "analysis_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(json.dumps(summary["counts"], indent=2))
    print("\n=== isolated_by_crop_pooled (revenue_per_tile_day) ===")
    for crop, e in summary["isolated_by_crop_pooled"].items():
        rptd = e["revenue_per_tile_day"]
        print(crop, "n=", e["n_episodes"], "revenue_per_tile_day mean=", rptd["mean"] if rptd else None,
              "final_money mean=", e["final_money"]["mean"] if e["final_money"] else None,
              "first_harvest_day mean=", e["first_harvest_day"]["mean"] if e["first_harvest_day"] else None)


if __name__ == "__main__":
    main()
