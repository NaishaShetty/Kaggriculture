"""
Phase 2.4 experiment runner (Stages B-F; Stage A is handled by
scripts/phase2_4_stage_a_verify.py). Same instrumentation pipeline and
per-cell-flush resilience pattern as scripts/phase2_3_run_experiments.py.

Usage:
    python scripts/phase2_4_run_experiments.py --stage B
    python scripts/phase2_4_run_experiments.py --stage C
    python scripts/phase2_4_run_experiments.py --stage D
    python scripts/phase2_4_run_experiments.py --stage E
    python scripts/phase2_4_run_experiments.py --stage F --validate-cells-json <path> --headtohead-cells-json <path>
"""
import argparse
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase2_4.common import make_agent  # noqa: E402
from instrumentation.pipeline import run_and_analyze, write_episode_outputs  # noqa: E402
from scripts.phase2_4_configs import STAGE_B, STAGE_C, STAGE_D, STAGE_E, STAGE_F_VALIDATE_SEEDS, STAGE_F_H2H_SEEDS, STEPS  # noqa: E402

OUT_ROOT = "results/phase2_4"

FIELDNAMES = [
    "stage", "group", "cell_id", "episode_id", "seed", "opponent", "config_json",
    "starting_money", "final_money", "profit", "revenue_total",
    "cost_seed", "cost_hire", "cost_land", "cost_animal", "cost_buy_wheat", "cost_buy_fertilizer", "cost_other",
    "harvest_units_json", "animal_units_json",
    "sold_units_total", "avg_realized_price_overall",
    "hands_hired_events", "land_quadrants_end",
    "productive_action_rate", "movement_fraction", "market_action_fraction",
    "win", "money_margin", "validation_overall", "inventory_overflow_flag",
]


def episode_row(record, stage, group, cell_id, config_kwargs, opponent):
    p0 = record["players"][0]
    fin = p0["financial_summary"]
    eff = p0["action_efficiency"]
    outcome = record["outcome"]
    val = p0["validation"]
    txns = p0["financial_transactions"]

    def cost(pred):
        return round(sum(t["total"] or 0 for t in txns if pred(t)), 4)

    cost_seed = cost(lambda t: t["type"] == "BUY_SEED")
    cost_hire = cost(lambda t: t["type"] == "HIRE")
    cost_land = cost(lambda t: t["type"] == "BUY_LAND")
    cost_animal = cost(lambda t: t["type"] == "BUY_ANIMAL")
    cost_buy_wheat = cost(lambda t: t["type"] == "BUY_PRODUCT" and t["item"] == "WHEAT")
    cost_buy_fertilizer = cost(lambda t: t["type"] == "BUY_PRODUCT" and t["item"] == "FERTILIZER")
    total_expenditure = fin["total_expenditure"]
    cost_other = round(total_expenditure - (cost_seed + cost_hire + cost_land + cost_animal +
                                             cost_buy_wheat + cost_buy_fertilizer), 4)

    sell_txns = [t for t in txns if t["type"] == "SELL"]
    sold_units_total = sum(t["quantity"] for t in sell_txns)
    sell_revenue_total = sum(t["total"] or 0 for t in sell_txns)
    avg_realized_price = round(sell_revenue_total / sold_units_total, 4) if sold_units_total else None

    harvest_units = {c: m.get("total_harvested_units", 0) for c, m in p0["crop_metrics"].items()}
    animal_units = {a: m.get("total_product_units", 0) for a, m in p0["animal_metrics"].items()}
    hire_txn_count = sum(1 for t in txns if t["type"] == "HIRE")

    inventory_overflow_flag = 0
    for row in val.get("inventory", []):
        if row.get("discrepancy", 0) > 0:
            inventory_overflow_flag = 1
            break

    win = 1 if outcome["winner"] == 0 else (0 if outcome["winner"] in (0, 1) else None)

    return {
        "stage": stage, "group": group, "cell_id": cell_id, "episode_id": record["episode_id"],
        "seed": record["meta"]["seed"], "opponent": opponent,
        "config_json": json.dumps(config_kwargs, sort_keys=True, default=str),
        "starting_money": fin["starting_money"], "final_money": fin["final_money"],
        "profit": round(fin["final_money"] - fin["starting_money"], 4),
        "revenue_total": fin["total_income"],
        "cost_seed": cost_seed, "cost_hire": cost_hire, "cost_land": cost_land, "cost_animal": cost_animal,
        "cost_buy_wheat": cost_buy_wheat, "cost_buy_fertilizer": cost_buy_fertilizer, "cost_other": cost_other,
        "harvest_units_json": json.dumps(harvest_units), "animal_units_json": json.dumps(animal_units),
        "sold_units_total": sold_units_total, "avg_realized_price_overall": avg_realized_price,
        "hands_hired_events": hire_txn_count, "land_quadrants_end": val["land"]["actual_ending_unlocked_quadrants"],
        "productive_action_rate": eff["productive_action_rate"], "movement_fraction": eff["movement_fraction"],
        "market_action_fraction": eff["market_action_fraction"],
        "win": win, "money_margin": round(outcome["margin"], 4) if outcome["margin"] is not None else None,
        "validation_overall": val["overall"], "inventory_overflow_flag": inventory_overflow_flag,
    }


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file_exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def run_cell(rows_out, stage, group, cell, seeds, opponent, full_raw_sample=0):
    cell_id, kwargs = cell["cell_id"], cell["kwargs"]
    agent = make_agent(**kwargs)
    for i, seed in enumerate(seeds):
        episode_id = f"{cell_id}_seed{seed}"
        t0 = time.time()
        record, replay, extracted = run_and_analyze(agent, opponent, STEPS, seed, f"{group}__{cell_id}", episode_id)
        rows_out.append(episode_row(record, stage, group, cell_id, kwargs, opponent))
        if i < full_raw_sample:
            write_episode_outputs(OUT_ROOT, f"{group}__{cell_id}", i, record)
        print(f"  [{group}/{cell_id}] seed={seed} ({i+1}/{len(seeds)}) money={record['outcome']['final_money']} "
              f"valid={record['players'][0]['validation']['overall']} ({time.time()-t0:.2f}s)", flush=True)


def run_stage(stage_letter, stage_dict, opponent_override=None):
    for group, spec in stage_dict.items():
        path = os.path.join(OUT_ROOT, f"dataset_{group}.csv")
        for cell in spec["cells"]:
            rows = []
            opponent = opponent_override or spec["opponent"]
            run_cell(rows, stage_letter, group, cell, spec["seeds"], opponent, full_raw_sample=1)
            write_csv(path, rows)


def run_stage_f_validate(cell_specs):
    path = os.path.join(OUT_ROOT, "dataset_f_validation.csv")
    for cell in cell_specs:
        rows = []
        run_cell(rows, "F", f"validate_{cell['source_group']}", cell, STAGE_F_VALIDATE_SEEDS, "pass", full_raw_sample=1)
        write_csv(path, rows)


def run_stage_f_headtohead(cell_specs):
    path = os.path.join(OUT_ROOT, "dataset_f_headtohead.csv")
    for cell in cell_specs:
        rows = []
        run_cell(rows, "F", f"h2h_{cell['source_group']}", cell, STAGE_F_H2H_SEEDS,
                  "agents/baseline_agent.py", full_raw_sample=1)
        write_csv(path, rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["B", "C", "D", "E", "F"])
    ap.add_argument("--validate-cells-json", default=None)
    ap.add_argument("--headtohead-cells-json", default=None)
    args = ap.parse_args()
    os.makedirs(OUT_ROOT, exist_ok=True)

    if args.stage == "B":
        run_stage("B", STAGE_B)
    elif args.stage == "C":
        run_stage("C", STAGE_C)
    elif args.stage == "D":
        run_stage("D", STAGE_D)
    elif args.stage == "E":
        run_stage("E", STAGE_E)
    elif args.stage == "F":
        if args.validate_cells_json:
            with open(args.validate_cells_json) as f:
                run_stage_f_validate(json.load(f))
        if args.headtohead_cells_json:
            with open(args.headtohead_cells_json) as f:
                run_stage_f_headtohead(json.load(f))


if __name__ == "__main__":
    main()
