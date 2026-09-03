"""
Phase 9 Experiment 2 (Phase 6 §17, Experiment 2): High-scale labor capacity
re-test.

HYPOTHESIS: marginal hand value at 8-13 hands, on a large (3-4 quadrant)
board, is positive -- unlike the negative marginal value Phase 2.3 found at
4 hands on a 1-quadrant board (results/phase2_3/dataset_a1_labor_sweep.csv,
CALIBRATION["marginal_hand_value"]["MELON"] in economic_model/model.py:
[5057, 477, -227, -29] -- already negative by the 4th hand).

CONTROL ARM: reproduces Phase 2.3's a1_labor_sweep methodology
(scripts/phase2_3_configs.py STAGE_A["a1_labor_sweep"]) as closely as
possible: MELON solo, 0 extra land quadrants, n_hands swept 0-4, isolated
(vs the engine's "pass" opponent), using the UNMODIFIED
agents/phase2_3/common.py::make_agent. The one disclosed methodology
difference: seeds. The original used 6 seeds (100000-100005); this phase
uses this project's established "development" bucket (700000-700003, n=4)
per Phase 6 §17's explicit instruction ("SEEDS: development set, n=4").

VARIABLE ARM: same MELON-solo methodology, n_hands swept 4-13, on a 3-extra-
quadrant (4 total) board -- matching the largest land count Phase 6's real
replay forensics observed (Lai Eu Wen, results/phase6/lai_eu_wen/,
land_quadrants=4 by day 10). Uses scripts/phase9/common.py::
make_high_scale_agent (see that module's docstring for exactly what differs
from the frozen agent and why it's necessary at this scale) with a
disclosed $30,000 starting-money cushion, identical across every cell in
this arm, so it cancels out of the marginal (Δfinal_money) comparison.

Board fill check: at land_quadrants=3, the full owned pool is ~96 tiles
(100 - 4 shed), all assigned to MELON (crops="MELON" -> 100% of the pool,
same as `tile_pool_assignment` behavior the frozen agent already uses) --
comfortably enough work to keep 13 hands watering/harvesting/replanting
without idling, avoiding the "under-filled board -> hands measured as
valueless" bias the brief warns against.

New code only. Does not modify agents/phase2_3/, agents/phase2_6/,
agents/phase3_3/, agents/phase3_5/, agents/phase3_8/, or main.py.
"""
import csv
import json
import os

from scripts.phase9.common import (
    DEVELOPMENT_SEEDS, HIGH_SCALE_STARTING_MONEY, STEPS,
    make_control_agent, make_high_scale_agent, run_cell, mean_by_value, marginal_values,
)

OUT_ROOT = "results/phase9"

CONTROL_HANDS = [0, 1, 2, 3, 4]
VARIABLE_HANDS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
VARIABLE_LAND_QUADRANTS = 3  # extra quadrants -> 4 total, matches Lai Eu Wen's observed max (Phase 6 §4)


def run_control():
    rows = []
    for h in CONTROL_HANDS:
        agent = make_control_agent(crops="MELON", n_hands=h, land_quadrants=0)
        for seed in DEVELOPMENT_SEEDS:
            result = run_cell("phase9_labor_control", f"h{h}", seed, agent)
            rows.append({"arm": "control", "n_hands": h, "seed": seed, **result})
            print(f"  [control h={h}] seed={seed} final_money=${result['final_money']}", flush=True)
    return rows


def run_variable():
    rows = []
    for h in VARIABLE_HANDS:
        agent = make_high_scale_agent(crops="MELON", n_hands=h, land_quadrants=VARIABLE_LAND_QUADRANTS, land_buy_day=0)
        for seed in DEVELOPMENT_SEEDS:
            result = run_cell(
                "phase9_labor_variable", f"h{h}", seed, agent,
                extra_config={"startingMoney": HIGH_SCALE_STARTING_MONEY},
            )
            rows.append({"arm": "variable", "n_hands": h, "seed": seed, **result})
            print(f"  [variable h={h} land={VARIABLE_LAND_QUADRANTS}] seed={seed} final_money=${result['final_money']}", flush=True)
    return rows


def main():
    print("=== CONTROL ARM (MELON solo, 0 extra land, hands 0-4, $3000 start) ===")
    control_rows = run_control()
    print("\n=== VARIABLE ARM (MELON solo, 3 extra land, hands 4-13, $30000 start) ===")
    variable_rows = run_variable()

    all_rows = control_rows + variable_rows
    os.makedirs(OUT_ROOT, exist_ok=True)
    out_csv = os.path.join(OUT_ROOT, "phase9_labor_capacity_results.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        for r in all_rows:
            w.writerow(r)
    print(f"\nWrote {len(all_rows)} rows to {out_csv}")

    control_means = mean_by_value(control_rows, "n_hands")
    variable_means = mean_by_value(variable_rows, "n_hands")
    control_marginal = marginal_values(control_means)
    variable_marginal = marginal_values(variable_means)

    summary = {
        "control_means_by_n_hands": control_means,
        "control_marginal_by_n_hands": control_marginal,
        "variable_means_by_n_hands": variable_means,
        "variable_marginal_by_n_hands": variable_marginal,
    }
    out_json = os.path.join(OUT_ROOT, "phase9_labor_capacity_summary.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to {out_json}")

    print("\nCONTROL marginal $/hand:", control_marginal)
    print("VARIABLE marginal $/hand:", variable_marginal)


if __name__ == "__main__":
    main()
