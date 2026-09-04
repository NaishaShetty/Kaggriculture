"""
Phase 35 Step 4: isolated economy for candidates A/B/C, 4 development seeds
vs. "pass" -- the cheap screen before anything expensive, per this project's
standing discipline. Any candidate that doesn't clear the baseline here is
rejected without a full 15-seed validation.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from agents.phase21.execution import make_execution_agent  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase35.rebalance_candidates import (  # noqa: E402
    make_candidate_a_targets, make_candidate_b_targets, make_candidate_c_targets,
)
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase35"


def make_agent(target_fn):
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_execution_agent(target_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    return agent


def run_condition(label, target_fn):
    rows = []
    for seed in DEV_SEEDS:
        agent = make_agent(target_fn)
        replay, meta = run_episode(agent, "pass", STEPS, seed, None)
        record, extracted = analyze_replay(replay, meta, "phase35_isolated", f"{label}_seed{seed}")
        final_money = record["outcome"]["final_money"][0]
        ae = record["players"][0]["action_efficiency"]
        rows.append({"seed": seed, "final_money": final_money, "idle_action_fraction": ae["idle_fraction"]})
        print(f"  [{label}] seed={seed}: final_money=${final_money} idle_action_fraction={ae['idle_fraction']:.4f}", flush=True)
    mean_final = sum(r["final_money"] for r in rows) / len(rows)
    mean_idle = sum(r["idle_action_fraction"] for r in rows) / len(rows)
    print(f"  [{label}] MEAN final_money=${mean_final:.2f}  MEAN idle_action_fraction={mean_idle:.4f}\n")
    return {"label": label, "rows": rows, "mean_final_money": mean_final, "mean_idle_action_fraction": mean_idle}


def main():
    results = {}
    print("=== baseline: agents/phase21/ as shipped (Submission H) ===")
    results["baseline"] = run_condition("baseline", portfolio_targets)

    print("=== Candidate A: SHEEP-heavy, reduced crop tiles, land 3 / hands 11 (unchanged) ===")
    results["candidate_a"] = run_condition("candidate_a", make_candidate_a_targets())

    print("=== Candidate B: A + 4th land quadrant, hands unchanged ===")
    results["candidate_b"] = run_condition("candidate_b", make_candidate_b_targets())

    print("=== Candidate C: COW-heavy (Crop Dusta-informed), same crop reduction as A ===")
    results["candidate_c"] = run_condition("candidate_c", make_candidate_c_targets())

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase35_isolated_economy_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase35_isolated_economy_results.json")

    b = results["baseline"]["mean_final_money"]
    print("\n=== SUMMARY vs. baseline ===")
    for label in ["candidate_a", "candidate_b", "candidate_c"]:
        m = results[label]["mean_final_money"]
        print(f"  {label}: ${m:.2f}  delta=${m - b:+.2f} ({(m - b) / b * 100:+.1f}%)  "
              f"idle={results[label]['mean_idle_action_fraction']:.4f}")


if __name__ == "__main__":
    main()
