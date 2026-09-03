"""
Phase 11: does marginal hand/animal value turn positive on a combined
crop+animal portfolio matching real opponent moushun_chen's actual
day-15/day-20 shape (results/phase6/moushun_chen/days_opponent.csv:
hands=10, land_quadrants=3 (4 total), STRAWBERRY tiles 20->28,
COW=6, SHEEP=5->8), where Phase 9 found it decisively negative on a
single-crop (MELON-solo) portfolio?

Two sweeps, isolated (vs the engine's "pass" opponent), 4 development
seeds (700000-700003), 4 land quadrants, $30,000 starting cushion (same
value Phase 9 used for its variable arms -- confirmed sufficient here by
direct smoke-test at every boundary cell before committing to the full
sweep; applied identically to every cell in both sweeps so it cancels out
of the marginal comparison exactly as Phase 9 §5b established):

  (a) LABOR sweep: animals fixed at COW=6/SHEEP=6 (12 total, the midpoint
      of moushun_chen's observed 11-14 range), STRAWBERRY tile target
      fixed at 24 (midpoint of the observed 20-28 range), hands swept
      4-13 -- directly comparable to Phase 9 Experiment 2's variable arm.
  (b) ANIMAL sweep: hands fixed at 10 (moushun_chen's own observed
      constant across both snapshots), STRAWBERRY tile target fixed at
      24, animals swept 6-14 (COW/SHEEP split evenly, matching
      moushun_chen's roughly-even COW/SHEEP composition) -- directly
      comparable to Phase 9 Experiment 4's variable arm.

Uses scripts/phase11/multi_resource_agent.py::make_multi_resource_agent --
see that module's docstring for exactly why a new (not frozen-modifying)
tile-pool-assignment step was needed to match moushun_chen's BOUNDED
(20-28 tile, not full-board) crop footprint, and why everything else is
unchanged from Phase 9's own execution layer.

New code only. Does not modify agents/phase2_3/common.py,
agents/phase2_4/common.py, agents/phase2_6/, agents/phase3_3/,
agents/phase3_5/, agents/phase3_8/, or main.py.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402
from scripts.phase9.common import DEVELOPMENT_SEEDS, HIGH_SCALE_STARTING_MONEY  # noqa: E402
from scripts.phase11.multi_resource_agent import make_multi_resource_agent  # noqa: E402

STEPS = 720
OUT_ROOT = "results/phase11"
LAND_QUADRANTS = 3
CROP = "STRAWBERRY"
CROP_TILE_TARGET = 24  # midpoint of moushun_chen's observed 20 (day15) - 28 (day20)

LABOR_SWEEP_HANDS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
LABOR_SWEEP_ANIMALS = {"COW": 6, "SHEEP": 6}  # 12 total, midpoint of observed 11-14

ANIMAL_SWEEP_COUNTS = [6, 7, 8, 9, 10, 11, 12, 13, 14]
ANIMAL_SWEEP_HANDS = 10  # moushun_chen's own observed constant, both snapshots


def split_cow_sheep(n):
    n_cow = (n + 1) // 2
    n_sheep = n - n_cow
    return {"COW": n_cow, "SHEEP": n_sheep}


def run_cell(experiment_id, cell_id, seed, agent):
    replay, meta = run_episode(agent, "pass", STEPS, seed, extra_config={"startingMoney": HIGH_SCALE_STARTING_MONEY})
    record, extracted = analyze_replay(replay, meta, experiment_id, f"{cell_id}_seed{seed}")
    final_money = record["outcome"]["final_money"][0]
    fin = record["players"][0]["financial_summary"]
    return {
        "final_money": final_money,
        "total_income": fin["total_income"],
        "total_expenditure": fin["total_expenditure"],
    }


def run_labor_sweep():
    rows = []
    for h in LABOR_SWEEP_HANDS:
        agent = make_multi_resource_agent(
            crop=CROP, crop_tile_target=CROP_TILE_TARGET, n_hands=h,
            land_quadrants=LAND_QUADRANTS, land_buy_day=0,
            animals=LABOR_SWEEP_ANIMALS, animal_buy_day=0, feed_source="market",
        )
        for seed in DEVELOPMENT_SEEDS:
            result = run_cell("phase11_labor", f"h{h}", seed, agent)
            rows.append({"n_hands": h, "seed": seed, **result})
            print(f"  [labor h={h}] seed={seed} final_money=${result['final_money']}", flush=True)
    return rows


def run_animal_sweep():
    rows = []
    for n in ANIMAL_SWEEP_COUNTS:
        agent = make_multi_resource_agent(
            crop=CROP, crop_tile_target=CROP_TILE_TARGET, n_hands=ANIMAL_SWEEP_HANDS,
            land_quadrants=LAND_QUADRANTS, land_buy_day=0,
            animals=split_cow_sheep(n), animal_buy_day=0, feed_source="market",
        )
        for seed in DEVELOPMENT_SEEDS:
            result = run_cell("phase11_animal", f"n{n}", seed, agent)
            rows.append({"n_animals": n, "seed": seed, **result})
            print(f"  [animal n={n}] seed={seed} final_money=${result['final_money']}", flush=True)
    return rows


def mean_by_value(rows, key):
    by_value = {}
    for r in rows:
        by_value.setdefault(r[key], []).append(r["final_money"])
    return {v: sum(vals) / len(vals) for v, vals in sorted(by_value.items())}


def marginal_values(means_by_value):
    out = {}
    for v in means_by_value:
        if (v - 1) in means_by_value:
            out[v] = round(means_by_value[v] - means_by_value[v - 1], 2)
    return out


def main():
    print(f"=== LABOR SWEEP (STRAWBERRY x{CROP_TILE_TARGET} + COW6/SHEEP6, {LAND_QUADRANTS} extra land, hands 4-13) ===")
    labor_rows = run_labor_sweep()
    print(f"\n=== ANIMAL SWEEP (STRAWBERRY x{CROP_TILE_TARGET} + 10 hands, {LAND_QUADRANTS} extra land, animals 6-14) ===")
    animal_rows = run_animal_sweep()

    os.makedirs(OUT_ROOT, exist_ok=True)
    for name, rows in (("labor", labor_rows), ("animal", animal_rows)):
        out_csv = os.path.join(OUT_ROOT, f"phase11_{name}_sweep_results.csv")
        with open(out_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"Wrote {len(rows)} rows to {out_csv}")

    labor_means = mean_by_value(labor_rows, "n_hands")
    labor_marginal = marginal_values(labor_means)
    animal_means = mean_by_value(animal_rows, "n_animals")
    animal_marginal = marginal_values(animal_means)

    summary = {
        "labor_means_by_n_hands": labor_means,
        "labor_marginal_by_n_hands": labor_marginal,
        "animal_means_by_n_animals": animal_means,
        "animal_marginal_by_n_animals": animal_marginal,
    }
    out_json = os.path.join(OUT_ROOT, "phase11_multi_resource_summary.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to {out_json}")
    print("\nLABOR marginal $/hand:", labor_marginal)
    print("ANIMAL marginal $/animal:", animal_marginal)


if __name__ == "__main__":
    main()
