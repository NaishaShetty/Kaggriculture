"""
Phase 2.2 experiment runner. Every experiment group below states its
hypothesis in the corresponding entry of EXPERIMENTS (also echoed to
docs/PHASE2_2_REPORT.md). Uses only the Phase 2.1 instrumentation pipeline
(read-only) and the Phase 2.2 crop-agent framework (agents/phase2_2/common.py)
-- no simulator or frozen-baseline modification.

Usage:
    python scripts/phase2_2_run_experiments.py --group isolated
    python scripts/phase2_2_run_experiments.py --group fertilizer
    python scripts/phase2_2_run_experiments.py --group timing
    python scripts/phase2_2_run_experiments.py --group headtohead
    python scripts/phase2_2_run_experiments.py --group combo
    python scripts/phase2_2_run_experiments.py --group allocation

Each group writes results/phase2_2/dataset_<group>.csv (one row per episode,
per the brief section 31 schema) plus lightweight per-episode `episode` and
`validation` telemetry (not the full raw/daily layers, to control storage --
documented storage-conscious choice, consistent with the Phase 2.1 overhead
philosophy). A handful of representative episodes additionally get the full
raw layer for auditability (see --full-raw-sample).
"""
import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase2_2.common import make_agent  # noqa: E402
from instrumentation.pipeline import run_and_analyze, write_episode_outputs  # noqa: E402

CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
STEPS = 720
OUT_ROOT = "results/phase2_2"

FIELDNAMES = [
    "experiment_id", "episode_id", "seed", "opponent", "crop", "crop_allocation",
    "starting_money", "final_money", "profit", "revenue", "seed_cost", "other_direct_cost",
    "harvest_units", "harvest_events", "sold_units", "unsold_units", "avg_realized_price",
    "tile_days", "revenue_per_tile_day", "productive_actions", "movement_actions", "market_actions",
    "revenue_per_action", "first_harvest_day", "last_harvest_day", "capital_locked", "land_used",
    "win", "money_margin", "validation_overall", "condition",
]


def _tile_days_for_crop(land_daily, crop):
    total = 0
    days = sorted(land_daily.keys())
    for i, day in enumerate(days):
        n_next_boundary = days[i + 1] - day if i + 1 < len(days) else 1
        total += land_daily[day]["CROP"].get(crop, 0) * n_next_boundary
    return total


def episode_rows(record, extracted, experiment_id, opponent, crop_allocation, condition):
    rows = []
    for player in (0, 1):
        if player == 1:
            continue  # dataset rows are for the crop-agent seat (player 0) by convention
        fin = record["players"][player]["financial_summary"]
        eff = record["players"][player]["action_efficiency"]
        crop_metrics = record["players"][player]["crop_metrics"]
        land_daily = extracted["land_daily"][player]
        outcome = record["outcome"]
        win = 1 if outcome["winner"] == player else (0 if outcome["winner"] in (0, 1) else None)

        crops_here = list(crop_allocation.keys())
        for crop in crops_here:
            m = crop_metrics.get(crop, {})
            revenue = m.get("revenue", 0.0)
            seed_cost_total = m.get("seeds_purchased", 0) * __import__(
                "vendor_kaggriculture.kaggriculture", fromlist=["CROPS"]).CROPS[crop]["seed"]
            harvest_units = m.get("total_harvested_units", 0)
            tile_days = _tile_days_for_crop(land_daily, crop)
            harvests = m.get("total_harvest_events", 0)
            txns = [t for t in record["players"][player]["financial_transactions"]
                    if t["type"] == "SELL" and t["item"] == crop]
            sold_units = sum(t["quantity"] for t in txns)
            avg_price = (sum(t["total"] or 0 for t in txns) / sold_units) if sold_units else None
            harvest_days = []
            for pe in extracted["production_events"][player]:
                if pe["event"] == "HARVEST" and pe.get("crop") == crop:
                    harvest_days.append(pe["day"])

            rows.append({
                "experiment_id": experiment_id, "episode_id": record["episode_id"], "seed": record["meta"]["seed"],
                "opponent": opponent, "crop": crop, "crop_allocation": round(crop_allocation[crop], 4),
                "starting_money": fin["starting_money"], "final_money": fin["final_money"],
                "profit": round(fin["final_money"] - fin["starting_money"], 4),
                "revenue": revenue, "seed_cost": seed_cost_total, "other_direct_cost": None,
                "harvest_units": harvest_units, "harvest_events": harvests,
                "sold_units": sold_units, "unsold_units": harvest_units - sold_units,
                "avg_realized_price": round(avg_price, 4) if avg_price is not None else None,
                "tile_days": tile_days,
                "revenue_per_tile_day": round(revenue / tile_days, 4) if tile_days else None,
                "productive_actions": eff["crop_productive"], "movement_actions": eff["movement"],
                "market_actions": eff["total_market_orders"],
                "revenue_per_action": round(revenue / eff["total_unit_actions"], 4) if eff["total_unit_actions"] else None,
                "first_harvest_day": min(harvest_days) if harvest_days else None,
                "last_harvest_day": max(harvest_days) if harvest_days else None,
                "capital_locked": seed_cost_total,
                "land_used": len(crop_allocation),
                "win": win, "money_margin": round(outcome["margin"], 4) if outcome["margin"] is not None else None,
                "validation_overall": record["players"][player]["validation"]["overall"],
                "condition": condition,
            })
    return rows


def run_group(rows_out, experiment_id, p0_spec, p1, crop_allocation, seeds, opponent, condition, full_raw_sample=0):
    for i, seed in enumerate(seeds):
        episode_id = f"{experiment_id}_seed{seed}"
        t0 = time.time()
        record, replay, extracted = run_and_analyze(p0_spec, p1, STEPS, seed, experiment_id, episode_id)
        rows_out.extend(episode_rows(record, extracted, experiment_id, opponent, crop_allocation, condition))
        if i < full_raw_sample:
            write_episode_outputs(OUT_ROOT, experiment_id, i, record)
        else:
            for sub in ("episode", "validation"):
                d = os.path.join(OUT_ROOT, sub, experiment_id)
                os.makedirs(d, exist_ok=True)
            import json
            with open(os.path.join(OUT_ROOT, "episode", experiment_id, f"ep{i:03d}.json"), "w") as f:
                json.dump({"meta": record["meta"], "outcome": record["outcome"],
                           "players": {p: record["players"][p]["episode_summary"] for p in (0, 1)}}, f, default=str)
            with open(os.path.join(OUT_ROOT, "validation", experiment_id, f"ep{i:03d}.json"), "w") as f:
                json.dump({p: record["players"][p]["validation"] for p in (0, 1)}, f, default=str)
        print(f"  [{experiment_id}] seed={seed} ({i+1}/{len(seeds)}) money={record['outcome']['final_money']} "
              f"winner={record['outcome']['winner']} valid={record['players'][0]['validation']['overall']} "
              f"({time.time()-t0:.2f}s)", flush=True)


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file_exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def group_isolated(n=15):
    # Same fixed seed range per opponent, shared identically across every
    # crop (brief sections 22/24: "identical seed sets across crop agents") --
    # a paired design, not independent samples per crop.
    rows = []
    seed_ranges = {"pass": range(10_000, 10_000 + n), "starter": range(20_000, 20_000 + n)}
    for crop in CROPS:
        agent = make_agent(crop)
        for opponent, seeds in seed_ranges.items():
            exp_id = f"isolated_{crop}_vs_{opponent}"
            run_group(rows, exp_id, agent, opponent, {crop: 1.0}, list(seeds), opponent, "no_fertilizer_no_delay",
                      full_raw_sample=1)
    write_csv(os.path.join(OUT_ROOT, "dataset_isolated.csv"), rows)


def group_fertilizer(n=8):
    rows = []
    seeds = list(range(30_000, 30_000 + n))
    for crop in CROPS:
        agent = make_agent(crop, fertilizer=True)
        exp_id = f"fertilizer_{crop}_vs_pass"
        run_group(rows, exp_id, agent, "pass", {crop: 1.0}, seeds, "pass", "fertilizer_on")
    write_csv(os.path.join(OUT_ROOT, "dataset_fertilizer.csv"), rows)


def group_timing(n=6):
    rows = []
    timing_seeds = {"early": range(40_000, 40_000 + n), "mid": range(41_000, 41_000 + n),
                     "late": range(42_000, 42_000 + n)}
    for crop in CROPS:
        for label, delay in (("early", 0), ("mid", 10), ("late", 20)):
            agent = make_agent(crop, plant_delay_day=delay)
            exp_id = f"timing_{crop}_{label}_vs_pass"
            run_group(rows, exp_id, agent, "pass", {crop: 1.0}, list(timing_seeds[label]), "pass",
                      f"plant_delay_day={delay}")
    write_csv(os.path.join(OUT_ROOT, "dataset_timing.csv"), rows)


def group_headtohead(n=15):
    rows = []
    seeds = list(range(50_000, 50_000 + n))
    for crop in CROPS:
        agent = make_agent(crop)
        exp_id = f"h2h_{crop}_vs_baseline"
        run_group(rows, exp_id, agent, "agents/baseline_agent.py", {crop: 1.0}, seeds, "baseline_agent",
                  "no_fertilizer_no_delay", full_raw_sample=1)
    write_csv(os.path.join(OUT_ROOT, "dataset_headtohead.csv"), rows)


def group_combo(n=10):
    rows = []
    seeds = list(range(60_000, 60_000 + n))
    pairs = [("WHEAT", "CARROT"), ("WHEAT", "TOMATO"), ("WHEAT", "STRAWBERRY"), ("WHEAT", "MELON")]
    for a, b in pairs:
        alloc = {a: 0.5, b: 0.5}
        agent = make_agent(alloc)
        exp_id = f"combo_{a}_{b}_50_50_vs_pass"
        run_group(rows, exp_id, agent, "pass", alloc, seeds, "pass", "combo_50_50", full_raw_sample=1)
    write_csv(os.path.join(OUT_ROOT, "dataset_combo.csv"), rows)


def group_allocation(pair=("WHEAT", "MELON"), n=8):
    rows = []
    seeds = list(range(70_000, 70_000 + n))
    a, b = pair
    for fa, fb in ((0.25, 0.75), (0.75, 0.25)):
        alloc = {a: fa, b: fb}
        agent = make_agent(alloc)
        exp_id = f"allocation_{a}_{int(fa*100)}_{b}_{int(fb*100)}_vs_pass"
        run_group(rows, exp_id, agent, "pass", alloc, seeds, "pass", f"allocation_{fa}_{fb}")
    write_csv(os.path.join(OUT_ROOT, "dataset_allocation.csv"), rows)


GROUPS = {
    "isolated": group_isolated, "fertilizer": group_fertilizer, "timing": group_timing,
    "headtohead": group_headtohead, "combo": group_combo, "allocation": group_allocation,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", required=True, choices=list(GROUPS))
    args = ap.parse_args()
    os.makedirs(OUT_ROOT, exist_ok=True)
    GROUPS[args.group]()


if __name__ == "__main__":
    main()
