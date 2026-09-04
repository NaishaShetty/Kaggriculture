"""
Phase 36 Stage 1, Step 4: isolated economy, 4 development seeds vs. "pass" --
does the adaptive pacer alone (SAME targets as shipped Submission H, only the
purchase TIMING differs) improve on the baseline?
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from agents.phase21.adapters.portfolio_agent import make_portfolio_agent  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase36.paced_execution import make_paced_execution_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase36"


def make_paced_agent():
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_paced_execution_agent(portfolio_targets)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    return agent


def run_condition(label, agent_factory):
    rows = []
    for seed in DEV_SEEDS:
        agent = agent_factory()
        replay, meta = run_episode(agent, "pass", STEPS, seed, None)
        record, extracted = analyze_replay(replay, meta, "phase36_isolated", f"{label}_seed{seed}")
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
    results["baseline"] = run_condition("baseline", make_portfolio_agent)

    print("=== Stage 1: adaptive pacer, SAME targets ===")
    results["paced"] = run_condition("paced", make_paced_agent)

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase36_isolated_economy_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase36_isolated_economy_results.json")

    b = results["baseline"]["mean_final_money"]
    p = results["paced"]["mean_final_money"]
    print(f"\nDelta: ${p - b:+.2f} ({(p - b) / b * 100:+.1f}%)")


if __name__ == "__main__":
    main()
