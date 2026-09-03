"""
Phase 21 Step 1: the load-bearing empirical test for the whole "shared-market
durability" reframe (docs/FRESH_STRATEGY.md) -- BEFORE building any portfolio
logic around it.

Hypothesis: two real competing sellers producing the SAME glut-prone crop
(MELON: `sq` above-curve, above_target=3.60, the harshest in the game) crash
that crop's revenue materially more than two sellers each producing a crop
with a flat glut curve (WHEAT: `log`, above_target=0.20), at comparable
production scale -- because the market inventory is ONE SHARED POOL per
resource (confirmed directly by reading vendor_kaggriculture/kaggriculture.py's
`_process_market`: both players' SELL orders for the same item are quoted and
committed in the same per-unit lockstep loop against the same
`market["inventory"][item]`).

This MUST run through the real engine (kaggle_environments), not just
agents/phase4/market_model.py's simulator -- the whole point is two
INDEPENDENT agents' orders interacting through the shared pool in real time,
which the simulator (single-seller-in-isolation) cannot represent.

Design: two single-crop agents (A commits fully to MELON or WHEAT; B commits
fully to MELON or WHEAT), same hands/land/tile-footprint scale for both, same
seed. Three conditions:
  1. A=MELON, B=MELON  (two-seller MELON competition)
  2. A=WHEAT, B=WHEAT  (two-seller WHEAT competition, the control)
  3. A=MELON, B=WHEAT  (A alone in the MELON pool, mixed control)
Compare A's own MELON/WHEAT sell revenue and final money across conditions.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.execution import make_execution_agent  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]

# Same scale for every single-crop agent in this experiment -- large enough to
# generate real combined-volume pressure on the shared pool, held constant
# across conditions so only the CROP CHOICE differs.
N_HANDS = 8
LAND_QUADRANTS = 2
CROP_TILE_TARGET = 40


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
    record, replay, extracted = run_and_analyze(agent_a, agent_b, STEPS, seed, "phase21_glut", f"{crop_a}_vs_{crop_b}")
    fs_a = record["players"][0]["financial_summary"]
    txn_a = record["players"][0]["market_transaction_summary"]
    sell_key = f"SELL:{crop_a}"
    sell_a = txn_a.get(sell_key, {})
    return {
        "final_money_a": record["outcome"]["final_money"][0],
        "final_money_b": record["outcome"]["final_money"][1],
        "sell_revenue_a": sell_a.get("total_value", 0.0),
        "sell_quantity_a": sell_a.get("total_quantity", 0),
        "avg_price_a": sell_a.get("avg_realized_price"),
    }


def main():
    conditions = [
        ("MELON", "MELON", "two-seller MELON competition"),
        ("WHEAT", "WHEAT", "two-seller WHEAT competition (control)"),
        ("MELON", "WHEAT", "A alone in MELON pool (mixed control)"),
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
        results[f"{crop_a}_vs_{crop_b}"] = {"mean_final_money_a": mean_final, "mean_sell_revenue_a": mean_sell_rev,
                                             "mean_sell_quantity_a": mean_qty, "rows": rows}
        print(f"  MEAN: A final=${mean_final:.0f}  A sell_rev=${mean_sell_rev:.0f}  A qty={mean_qty:.0f}")

    print("\n\n=== SUMMARY ===")
    for k, v in results.items():
        print(f"  {k}: mean A final=${v['mean_final_money_a']:.0f}, mean A sell_rev=${v['mean_sell_revenue_a']:.0f}")

    import json
    os.makedirs("results/phase21", exist_ok=True)
    with open("results/phase21/phase21_market_glut_experiment.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nWrote results/phase21/phase21_market_glut_experiment.json")


if __name__ == "__main__":
    main()
