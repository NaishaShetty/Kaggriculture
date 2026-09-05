"""
Phase 48 Part C, step 9: 4-seed isolated-economy screen comparing Submission
J's shipped (uncapped) animal targets against the capacity-aware capped
variant (scripts/phase48/capped_animal_portfolio.py), both run through
Submission J's own unmodified execution layer
(scripts/phase46/feed_priority_execution.py). Also reports final/steady-state
owned-animal counts so the trade-off (money vs. animal-count) is visible
directly, not just the headline economy number.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase46.feed_priority_execution import make_feed_priority_execution_agent  # noqa: E402
from scripts.phase48.capped_animal_portfolio import make_capped_animal_target_fn  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase48"


def make_agent_with_opponent_logging(target_fn):
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_feed_priority_execution_agent(target_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    return agent


def owned_animal_count(obs):
    tiles = obs["farms"][0]["tiles"]
    return sum(1 for row in tiles for tt in row if isinstance(tt, dict) and "animal" in tt)


def run_condition(label, target_fn):
    rows = []
    for seed in DEV_SEEDS:
        agent = make_agent_with_opponent_logging(target_fn)
        replay, meta = run_episode(agent, "pass", STEPS, seed, None)
        record, extracted = analyze_replay(replay, meta, "phase48_animal_cap", f"{label}_seed{seed}")
        final_money = record["outcome"]["final_money"][0]
        ae = record["players"][0]["action_efficiency"]
        turns_per_day = 24
        owned_series = []
        for day in range(30):
            t = day * turns_per_day + (turns_per_day - 1)
            if t >= len(replay["steps"]):
                break
            owned_series.append(owned_animal_count(replay["steps"][t][0]["observation"]))
        final_owned = owned_series[-1] if owned_series else 0
        steady = owned_series[20:30]
        steady_mean = sum(steady) / len(steady) if steady else 0.0
        rows.append({
            "seed": seed, "final_money": final_money, "idle_action_fraction": ae["idle_fraction"],
            "final_owned": final_owned, "steady_state_mean_owned": round(steady_mean, 2),
        })
        print(f"  [{label}] seed={seed}: final_money=${final_money} final_owned={final_owned} "
              f"steady_state={steady_mean:.2f}", flush=True)
    mean_final = sum(r["final_money"] for r in rows) / len(rows)
    mean_owned = sum(r["final_owned"] for r in rows) / len(rows)
    mean_steady = sum(r["steady_state_mean_owned"] for r in rows) / len(rows)
    print(f"  [{label}] MEAN final_money=${mean_final:.2f}  MEAN final_owned={mean_owned:.2f}  "
          f"MEAN steady_state={mean_steady:.2f}\n")
    return {"label": label, "rows": rows, "mean_final_money": mean_final,
            "mean_final_owned": mean_owned, "mean_steady_state_owned": mean_steady}


def main():
    results = {}
    print("=== baseline: Submission J shipped, uncapped animal targets (17 by day 11) ===")
    results["baseline_uncapped"] = run_condition("baseline_uncapped", portfolio_targets)

    for cap in (8, 9):
        label = f"capped_{cap}"
        print(f"=== capped animal target (cap_total={cap}) ===")
        results[label] = run_condition(label, make_capped_animal_target_fn(cap_total=cap))

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase48_isolated_screen_animal_cap_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase48_isolated_screen_animal_cap_results.json")

    b = results["baseline_uncapped"]["mean_final_money"]
    print("\n=== SUMMARY vs. baseline ===")
    for cap in (8, 9):
        label = f"capped_{cap}"
        m = results[label]["mean_final_money"]
        print(f"  {label}: ${m:.2f}  delta=${m - b:+.2f} ({(m - b) / b * 100:+.1f}%)")


if __name__ == "__main__":
    main()
