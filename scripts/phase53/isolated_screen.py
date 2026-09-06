"""
Phase 53 Step 3: 4-seed isolated-economy screen comparing Submission K's own
shipped candidate (scripts/phase48/capped_animal_portfolio_agent.py, 3 land
quadrants) against this phase's 4th-quadrant extension
(scripts/phase53/fourth_quadrant_portfolio_agent.py), both run through the
SAME unmodified execution layer. Mirrors scripts/phase48/
isolated_screen_animal_cap.py's own structure -- also reports idle-action
fraction (Phase 30/46's own capacity metric) and final land-quadrant/hand/
crop-tile counts so the mechanism, not just the headline economy number, is
visible directly from this screen.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase48.capped_animal_portfolio_agent import make_capped_animal_portfolio_agent  # noqa: E402
from scripts.phase53.fourth_quadrant_portfolio_agent import make_fourth_quadrant_portfolio_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase53"


def farm_snapshot(obs):
    farm = obs["farms"][0]
    tiles = farm["tiles"]
    crop_tiles = sum(1 for row in tiles for tt in row if isinstance(tt, dict) and tt.get("kind") == "PLANT")
    animals = sum(1 for row in tiles for tt in row if isinstance(tt, dict) and "animal" in tt)
    return {
        "land_quadrants": len(farm.get("unlocked_quadrants", ["NW"])),
        "hands_count": len(farm.get("hands", [])),
        "crop_tiles": crop_tiles, "animals": animals,
    }


def run_condition(label, make_agent):
    rows = []
    for seed in DEV_SEEDS:
        agent = make_agent()
        replay, meta = run_episode(agent, "pass", STEPS, seed, None)
        record, extracted = analyze_replay(replay, meta, "phase53_fourth_quadrant", f"{label}_seed{seed}")
        final_money = record["outcome"]["final_money"][0]
        ae = record["players"][0]["action_efficiency"]
        final_obs = replay["steps"][-1][0]["observation"]
        snap = farm_snapshot(final_obs)
        rows.append({
            "seed": seed, "final_money": final_money, "idle_action_fraction": ae["idle_fraction"],
            **snap,
        })
        print(f"  [{label}] seed={seed}: final_money=${final_money:,.2f} idle_fraction={ae['idle_fraction']:.3f} "
              f"land={snap['land_quadrants']} hands={snap['hands_count']} "
              f"crop_tiles={snap['crop_tiles']} animals={snap['animals']}", flush=True)
    mean_final = sum(r["final_money"] for r in rows) / len(rows)
    mean_idle = sum(r["idle_action_fraction"] for r in rows) / len(rows)
    print(f"  [{label}] MEAN final_money=${mean_final:,.2f}  MEAN idle_fraction={mean_idle:.3f}\n")
    return {"label": label, "rows": rows, "mean_final_money": mean_final, "mean_idle_fraction": mean_idle}


def main():
    results = {}
    print("=== baseline: Submission K shipped (capped-animal, 3 land quadrants) ===")
    results["baseline_k"] = run_condition("baseline_k", make_capped_animal_portfolio_agent)

    print("=== candidate: 4th-quadrant extension (same crops, same execution) ===")
    results["fourth_quadrant"] = run_condition("fourth_quadrant", make_fourth_quadrant_portfolio_agent)

    os.makedirs(OUT_ROOT, exist_ok=True)
    out_path = os.path.join(OUT_ROOT, "phase53_isolated_screen_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_path}")

    b = results["baseline_k"]["mean_final_money"]
    c = results["fourth_quadrant"]["mean_final_money"]
    print("\n=== SUMMARY vs. baseline ===")
    print(f"  fourth_quadrant: ${c:,.2f}  delta=${c - b:+,.2f} ({(c - b) / b * 100:+.1f}%)")
    print(f"  idle_fraction: baseline={results['baseline_k']['mean_idle_fraction']:.3f} "
          f"fourth_quadrant={results['fourth_quadrant']['mean_idle_fraction']:.3f}")


if __name__ == "__main__":
    main()
