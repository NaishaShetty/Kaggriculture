"""
Phase 48 Part A, step 2: 4-seed isolated-economy screen for the opportunistic
fertilizer design recomposed on Phase 46's FEED-priority execution layer.
Mirrors scripts/phase33/isolated_economy_fertilizer.py's structure exactly
(same dev seeds, same "pass" opponent, same metrics) so the delta vs. that
phase's own baseline is directly comparable.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase48.fert_execution_feed_priority import make_fert_feed_priority_execution_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase48"


def make_agent_with_opponent_logging(fertilize):
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_fert_feed_priority_execution_agent(portfolio_targets, fertilize=fertilize)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    return agent


def fertilized_tile_count_series(replay):
    n_steps = len(replay["steps"])
    counts = []
    turns_per_day = 24
    for day in range(30):
        t = day * turns_per_day + (turns_per_day - 1)
        if t >= n_steps:
            break
        obs = replay["steps"][t][0]["observation"]
        tiles = obs["farms"][0]["tiles"]
        n = 0
        for row in tiles:
            for tile in row:
                if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("fertilized_until_day", -1) >= day:
                    n += 1
        counts.append(n)
    return counts


def run_condition(label, fertilize):
    rows = []
    for seed in DEV_SEEDS:
        agent = make_agent_with_opponent_logging(fertilize)
        replay, meta = run_episode(agent, "pass", STEPS, seed, None)
        record, extracted = analyze_replay(replay, meta, "phase48_isolated_fert", f"{label}_seed{seed}")
        final_money = record["outcome"]["final_money"][0]
        ae = record["players"][0]["action_efficiency"]
        fert_counts = fertilized_tile_count_series(replay)
        peak_fert = max(fert_counts) if fert_counts else 0
        rows.append({
            "seed": seed, "final_money": final_money,
            "idle_action_fraction": ae["idle_fraction"],
            "peak_fertilized_tiles": peak_fert,
        })
        print(f"  [{label}] seed={seed}: final_money=${final_money} peak_fertilized={peak_fert} "
              f"idle_action_fraction={ae['idle_fraction']}", flush=True)
    mean_final = sum(r["final_money"] for r in rows) / len(rows)
    mean_peak = sum(r["peak_fertilized_tiles"] for r in rows) / len(rows)
    mean_idle = sum(r["idle_action_fraction"] for r in rows) / len(rows)
    print(f"  [{label}] MEAN final_money=${mean_final:.2f}  MEAN peak_fertilized_tiles={mean_peak:.1f}  "
          f"MEAN idle_action_fraction={mean_idle:.4f}\n")
    return {"label": label, "rows": rows, "mean_final_money": mean_final,
            "mean_peak_fertilized_tiles": mean_peak, "mean_idle_action_fraction": mean_idle}


def main():
    results = {}
    print("=== baseline: FEED-priority execution layer, no fertilizer ===")
    results["baseline_no_fertilizer"] = run_condition("baseline_no_fertilizer", fertilize=False)

    print("=== opportunistic fertilizer (tier 4/5) on FEED-priority execution layer ===")
    results["opportunistic_fertilizer_feed_priority"] = run_condition("opportunistic_fertilizer_feed_priority", fertilize=True)

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase48_isolated_screen_fert_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase48_isolated_screen_fert_results.json")

    b = results["baseline_no_fertilizer"]["mean_final_money"]
    o = results["opportunistic_fertilizer_feed_priority"]["mean_final_money"]
    print(f"\nDelta: ${o - b:+.2f} ({(o - b) / b * 100:+.1f}%)")


if __name__ == "__main__":
    main()
