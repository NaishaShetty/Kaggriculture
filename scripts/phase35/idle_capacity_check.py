"""
Phase 35 Step 2: idle-capacity check BEFORE touching animal targets -- same
discipline Phase 30 used before attempting fertilizer (measure first, build
second). Question: does agents/phase21/'s current 11-hand allocation have
genuine spare worker-turn capacity if the crop-tile target were reduced
(fewer WATER/HARVEST/PLANT tasks), even before any animal target changes?

Reuses instrumentation/pipeline.py::analyze_replay's action_efficiency
(idle_fraction), the exact metric Phase 10/16/30 all used -- not
reimplemented. agents/phase21/portfolio.py::portfolio_targets is imported
unmodified; only a crop_tile_target CAP is applied on top via a thin wrapper
(land/hands/animals all untouched, isolating the crop-tile-target variable
alone, per this phase's step 2 instruction).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from agents.phase21.execution import make_execution_agent  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase35"


def make_capped_target_fn(cap):
    def targets(day, obs, opponent_history):
        t = dict(portfolio_targets(day, obs, opponent_history))
        if cap is not None:
            t["crop_tile_target"] = min(t["crop_tile_target"], cap)
        return t
    return targets


def make_agent(target_fn):
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_execution_agent(target_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    return agent


def run_condition(label, cap):
    rows = []
    for seed in DEV_SEEDS:
        agent = make_agent(make_capped_target_fn(cap))
        replay, meta = run_episode(agent, "pass", STEPS, seed, None)
        record, extracted = analyze_replay(replay, meta, "phase35_idle_check", f"{label}_seed{seed}")
        ae = record["players"][0]["action_efficiency"]
        final_money = record["outcome"]["final_money"][0]
        rows.append({"seed": seed, "final_money": final_money, "idle_action_fraction": ae["idle_fraction"]})
        print(f"  [{label}] seed={seed}: final_money=${final_money} idle_action_fraction={ae['idle_fraction']:.4f}", flush=True)
    mean_idle = sum(r["idle_action_fraction"] for r in rows) / len(rows)
    mean_final = sum(r["final_money"] for r in rows) / len(rows)
    print(f"  [{label}] MEAN idle_action_fraction={mean_idle:.4f}  MEAN final_money=${mean_final:.2f}\n")
    return {"label": label, "rows": rows, "mean_idle_action_fraction": mean_idle, "mean_final_money": mean_final}


def main():
    results = {}
    print("=== baseline: crop_tile_target uncapped (58 max, as shipped) ===")
    results["cap_none"] = run_condition("cap_none", None)

    print("=== crop_tile_target capped at 40 ===")
    results["cap_40"] = run_condition("cap_40", 40)

    print("=== crop_tile_target capped at 30 ===")
    results["cap_30"] = run_condition("cap_30", 30)

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase35_idle_capacity_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase35_idle_capacity_results.json")

    print("\n=== SUMMARY ===")
    for k, v in results.items():
        print(f"  {k}: idle={v['mean_idle_action_fraction']:.4f}  final=${v['mean_final_money']:.2f}")


if __name__ == "__main__":
    main()
