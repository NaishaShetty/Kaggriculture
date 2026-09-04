"""
Phase 33 Part A: CARROT in real two-player competition.

Reuses Phase 21 Step 1 / Phase 31 Step 2's exact glut-experiment design
(scripts/phase21/market_glut_experiment.py, scripts/phase31/test_tomato_goose.py)
unchanged -- single-crop agents built directly from
agents/phase21/execution.py::make_execution_agent (imported, not modified),
same scale (8 hands, 2 land quadrants, 40 crop-tile target), same 4
development seeds, through the real engine (kaggle_environments via
instrumentation/collector.py), not the standalone market simulator.

CARROT's own glut-curve constants (vendor_kaggriculture/kaggriculture.py,
read directly, not trusted from any paraphrase): base=$35, T=450,
above_func="sqrt", above_target=0.70 -- a materially softer above-target
curve than STRAWBERRY's (above_func="linear", above_target=1.60) or MELON's
(above_func="sq", above_target=3.60), and CARROT's T=450 (inventory units
before the above-target curve engages at all) is 4.5x STRAWBERRY's T=100 --
CARROT should be structurally harder to glut than STRAWBERRY on paper. This
phase checks whether that translates into a real two-player result, the same
way Phase 31 checked (and rejected) the same reasoning for TOMATO and GOOSE.

Conditions:
  1. A=CARROT, B=CARROT   (two-seller CARROT competition -- contested)
  2. A=CARROT, B=STRAWBERRY (CARROT alone in its own pool -- uncontested)
  3. A=STRAWBERRY, B=STRAWBERRY (reference point, reproduced fresh here for a
     directly self-contained, apples-to-apples comparison rather than only
     citing Phase 21/31's own number)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.execution import make_execution_agent  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]

N_HANDS = 8
LAND_QUADRANTS = 2
CROP_TILE_TARGET = 40

OUT_ROOT = "results/phase33"


def make_single_crop_agent(crop):
    def targets(day, obs, opponent_history):
        return {
            "n_hands": N_HANDS, "land_quadrants": LAND_QUADRANTS, "animals": {},
            "crop_tile_target": CROP_TILE_TARGET, "crop_fractions": {crop: 1.0},
        }
    return make_execution_agent(targets)


def run_condition(crop_a, crop_b, seed):
    agent_a = make_single_crop_agent(crop_a)
    agent_b = make_single_crop_agent(crop_b)
    record, replay, extracted = run_and_analyze(agent_a, agent_b, STEPS, seed, "phase33_carrot_glut", f"{crop_a}_vs_{crop_b}")
    txn_a = record["players"][0]["market_transaction_summary"]
    sell_a = txn_a.get(f"SELL:{crop_a}", {})
    return {
        "seed": seed,
        "final_money_a": record["outcome"]["final_money"][0],
        "final_money_b": record["outcome"]["final_money"][1],
        "sell_revenue_a": sell_a.get("total_value", 0.0),
        "sell_quantity_a": sell_a.get("total_quantity", 0),
        "avg_price_a": sell_a.get("avg_realized_price"),
    }


def main():
    conditions = [
        ("CARROT", "CARROT", "two-seller CARROT competition (contested)"),
        ("CARROT", "STRAWBERRY", "A=CARROT alone in its pool, competitor grows STRAWBERRY (CARROT uncontested)"),
        ("STRAWBERRY", "STRAWBERRY", "two-seller STRAWBERRY competition (reference, reproduced fresh)"),
    ]
    results = {}
    for crop_a, crop_b, label in conditions:
        print(f"\n=== {label}: A={crop_a}, B={crop_b} ===")
        rows = []
        for seed in DEV_SEEDS:
            r = run_condition(crop_a, crop_b, seed)
            rows.append(r)
            print(f"  seed={seed}: A final=${r['final_money_a']:.0f} A sell_rev=${r['sell_revenue_a']:.0f} "
                  f"(qty={r['sell_quantity_a']}, avg_price={r['avg_price_a']})")
        mean_final = sum(r["final_money_a"] for r in rows) / len(rows)
        mean_sell_rev = sum(r["sell_revenue_a"] for r in rows) / len(rows)
        mean_qty = sum(r["sell_quantity_a"] for r in rows) / len(rows)
        key = f"{crop_a}_vs_{crop_b}"
        results[key] = {"label": label, "mean_final_money_a": mean_final, "mean_sell_revenue_a": mean_sell_rev,
                        "mean_sell_quantity_a": mean_qty, "rows": rows}
        print(f"  MEAN: A final=${mean_final:.0f}  A sell_rev=${mean_sell_rev:.0f}  A qty={mean_qty:.0f}")

    print("\n\n=== SUMMARY ===")
    for k, v in results.items():
        print(f"  {k}: mean A final=${v['mean_final_money_a']:.0f}, mean A sell_rev=${v['mean_sell_revenue_a']:.0f}")

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase33_carrot_glut_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nWrote {OUT_ROOT}/phase33_carrot_glut_results.json")


if __name__ == "__main__":
    main()
