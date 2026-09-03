"""
Phase 31: test whether TOMATO and/or GOOSE/EGG are real, currently-unused
opportunities for agents/phase21/.

Step 1: isolated single-resource economics.
  - TOMATO: already measured by Phase 8 (results/phase8/
    phase8_calibration_probe_results.csv) -- reused directly, not re-derived.
  - GOOSE vs. COW vs. SHEEP: not previously measured at comparable scale by
    any phase -- built here, same isolated-no-opponent discipline Phase 8 used.

Step 2: the shared-market glut test, same design as Phase 21 Step 1 (two
competing agents at equal scale, through the real engine) -- does TOMATO
hold up better than STRAWBERRY, and does GOOSE hold up better than COW/SHEEP,
under real two-player competition?

Reuses agents/phase21/execution.py's make_execution_agent directly (single
crop or single animal type, fixed scale) -- same technique
scripts/phase21/market_glut_experiment.py used for the original MELON/WHEAT test.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.execution import make_execution_agent  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]

# Same scale as Phase 21 Step 1's own single-crop test.
N_HANDS = 8
LAND_QUADRANTS = 2
CROP_TILE_TARGET = 40
N_ANIMALS = 6  # per species, for the animal comparison -- matches COW6/SHEEP6 scale
# already used by scripts/phase21/market_glut_experiment.py's predecessor (Phase 11)


def make_single_crop_agent(crop):
    def targets(day, obs, opponent_history):
        return {
            "n_hands": N_HANDS, "land_quadrants": LAND_QUADRANTS, "animals": {},
            "crop_tile_target": CROP_TILE_TARGET, "crop_fractions": {crop: 1.0},
        }
    return make_execution_agent(targets)


def make_single_animal_agent(species):
    def targets(day, obs, opponent_history):
        return {
            "n_hands": N_HANDS, "land_quadrants": LAND_QUADRANTS,
            "animals": {species: N_ANIMALS},
            "crop_tile_target": 20, "crop_fractions": {"WHEAT": 1.0},  # small wheat patch to fund feed
        }
    return make_execution_agent(targets)


def isolated_animal_economics(species):
    rows = []
    for seed in DEV_SEEDS:
        agent = make_single_animal_agent(species)
        record, replay, extracted = run_and_analyze(agent, "pass", STEPS, seed, "phase31_isolated", species)
        fs = record["players"][0]["financial_summary"]
        txn = record["players"][0]["market_transaction_summary"]
        product = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}[species]
        sell = txn.get(f"SELL:{product}", {})
        rows.append({
            "seed": seed, "final_money": record["outcome"]["final_money"][0],
            "sell_revenue": sell.get("total_value", 0.0), "sell_qty": sell.get("total_quantity", 0),
            "avg_price": sell.get("avg_realized_price"),
        })
    return rows


def two_player_glut_test(item_a, item_b, is_animal):
    if is_animal:
        agent_a_fn = lambda: make_single_animal_agent(item_a)
        agent_b_fn = lambda: make_single_animal_agent(item_b)
        product_a = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}[item_a]
    else:
        agent_a_fn = lambda: make_single_crop_agent(item_a)
        agent_b_fn = lambda: make_single_crop_agent(item_b)
        product_a = item_a

    rows = []
    for seed in DEV_SEEDS:
        agent_a = agent_a_fn()
        agent_b = agent_b_fn()
        record, replay, extracted = run_and_analyze(agent_a, agent_b, STEPS, seed, "phase31_glut", f"{item_a}_vs_{item_b}")
        fs_a = record["players"][0]["financial_summary"]
        txn_a = record["players"][0]["market_transaction_summary"]
        sell_a = txn_a.get(f"SELL:{product_a}", {})
        rows.append({
            "seed": seed, "final_money_a": record["outcome"]["final_money"][0],
            "final_money_b": record["outcome"]["final_money"][1],
            "sell_revenue_a": sell_a.get("total_value", 0.0), "sell_qty_a": sell_a.get("total_quantity", 0),
            "avg_price_a": sell_a.get("avg_realized_price"),
        })
    return rows


def main():
    results = {}

    print("=== STEP 1b: isolated animal economics (GOOSE vs COW vs SHEEP) ===")
    for species in ["GOOSE", "COW", "SHEEP"]:
        rows = isolated_animal_economics(species)
        mean_final = sum(r["final_money"] for r in rows) / len(rows)
        mean_rev = sum(r["sell_revenue"] for r in rows) / len(rows)
        results[f"isolated_{species}"] = {"rows": rows, "mean_final": mean_final, "mean_sell_revenue": mean_rev}
        print(f"  {species}: mean_final=${mean_final:.0f}  mean_sell_rev=${mean_rev:.0f}")
        for r in rows:
            print(f"    seed={r['seed']}: final=${r['final_money']:.0f} rev=${r['sell_revenue']:.0f} "
                  f"qty={r['sell_qty']} avg_px={r['avg_price']}")

    print("\n=== STEP 2a: two-player glut test, TOMATO vs STRAWBERRY (crops) ===")
    conditions_crop = [
        ("TOMATO", "TOMATO", "two-seller TOMATO competition"),
        ("STRAWBERRY", "STRAWBERRY", "two-seller STRAWBERRY competition (Phase 21's own reference point)"),
        ("TOMATO", "STRAWBERRY", "TOMATO alone vs. a STRAWBERRY competitor (mixed control)"),
    ]
    for a, b, label in conditions_crop:
        rows = two_player_glut_test(a, b, is_animal=False)
        mean_final = sum(r["final_money_a"] for r in rows) / len(rows)
        mean_rev = sum(r["sell_revenue_a"] for r in rows) / len(rows)
        results[f"glut_{a}_vs_{b}"] = {"rows": rows, "mean_final_a": mean_final, "mean_sell_revenue_a": mean_rev}
        print(f"  {label}: A={a} mean_final=${mean_final:.0f} mean_sell_rev=${mean_rev:.0f}")

    print("\n=== STEP 2b: two-player glut test, GOOSE vs COW/SHEEP (animals) ===")
    conditions_animal = [
        ("GOOSE", "GOOSE", "two-seller GOOSE competition"),
        ("COW", "COW", "two-seller COW competition (reference)"),
        ("SHEEP", "SHEEP", "two-seller SHEEP competition (reference)"),
        ("GOOSE", "COW", "GOOSE alone vs. a COW competitor (mixed control)"),
    ]
    for a, b, label in conditions_animal:
        rows = two_player_glut_test(a, b, is_animal=True)
        mean_final = sum(r["final_money_a"] for r in rows) / len(rows)
        mean_rev = sum(r["sell_revenue_a"] for r in rows) / len(rows)
        results[f"glut_{a}_vs_{b}"] = {"rows": rows, "mean_final_a": mean_final, "mean_sell_revenue_a": mean_rev}
        print(f"  {label}: A={a} mean_final=${mean_final:.0f} mean_sell_rev=${mean_rev:.0f}")

    os.makedirs("results/phase31", exist_ok=True)
    with open("results/phase31/phase31_tomato_goose_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nWrote results/phase31/phase31_tomato_goose_results.json")


if __name__ == "__main__":
    main()
