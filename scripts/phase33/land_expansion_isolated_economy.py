"""
Phase 33 Part C, Steps 7-8: isolated economy for the 4th-quadrant TOMATO/GOOSE
pure-addition test, 4 development seeds vs. "pass". The bar is explicit per
this phase's own instruction: does buying the 4th quadrant + dedicated hands
earn MORE than not buying it at all (net positive over the current baseline),
not whether TOMATO/GOOSE beats STRAWBERRY/COW on the same land.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase33.land_expansion_execution import make_extension_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase33"


def make_agent_with_opponent_logging(execution_agent_factory):
    opponent_logger = OpponentObservationLogger()
    execution_agent = execution_agent_factory()

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    return agent


def run_condition(label, execution_agent_factory):
    rows = []
    for seed in DEV_SEEDS:
        agent = make_agent_with_opponent_logging(execution_agent_factory)
        replay, meta = run_episode(agent, "pass", STEPS, seed, None)
        record, extracted = analyze_replay(replay, meta, "phase33_land_expansion", f"{label}_seed{seed}")
        final_money = record["outcome"]["final_money"][0]
        txn = record["players"][0]["market_transaction_summary"]
        n_extra_quadrants = None
        replay_last_obs = replay["steps"][-1][0]["observation"]
        n_extra_quadrants = len(replay_last_obs["farms"][0]["unlocked_quadrants"]) - 1
        rows.append({
            "seed": seed, "final_money": final_money, "n_extra_quadrants_owned_at_end": n_extra_quadrants,
            "sell_tomato_rev": txn.get("SELL:TOMATO", {}).get("total_value", 0.0),
            "sell_egg_rev": txn.get("SELL:EGG", {}).get("total_value", 0.0),
        })
        print(f"  [{label}] seed={seed}: final_money=${final_money} extra_quadrants={n_extra_quadrants} "
              f"tomato_rev=${rows[-1]['sell_tomato_rev']:.0f} egg_rev=${rows[-1]['sell_egg_rev']:.0f}", flush=True)
    mean_final = sum(r["final_money"] for r in rows) / len(rows)
    print(f"  [{label}] MEAN final_money=${mean_final:.2f}\n")
    return {"label": label, "rows": rows, "mean_final_money": mean_final}


def main():
    results = {}

    print("=== baseline: agents/phase21/ portfolio agent, as shipped ===")
    def baseline_factory():
        return make_extension_agent(portfolio_targets, extension_type="TOMATO", n_dedicated_hands=0,
                                     extension_trigger_day=99999)  # trigger never fires -> pure baseline
    results["baseline"] = run_condition("baseline", baseline_factory)

    print("=== TOMATO on 4th quadrant (pure addition, dedicated hands) ===")
    def tomato_factory():
        return make_extension_agent(portfolio_targets, extension_type="TOMATO", n_dedicated_hands=2,
                                     extension_trigger_day=12)
    results["tomato_extension"] = run_condition("tomato_extension", tomato_factory)

    print("=== GOOSE on 4th quadrant (pure addition, dedicated hands) ===")
    def goose_factory():
        return make_extension_agent(portfolio_targets, extension_type="GOOSE", n_dedicated_hands=2,
                                     extension_trigger_day=12)
    results["goose_extension"] = run_condition("goose_extension", goose_factory)

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase33_land_expansion_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase33_land_expansion_results.json")

    b = results["baseline"]["mean_final_money"]
    print("\n=== SUMMARY vs. baseline ===")
    for label in ["tomato_extension", "goose_extension"]:
        m = results[label]["mean_final_money"]
        print(f"  {label}: ${m:.2f}  delta=${m - b:+.2f} ({(m - b) / b * 100:+.1f}%)")


if __name__ == "__main__":
    main()
