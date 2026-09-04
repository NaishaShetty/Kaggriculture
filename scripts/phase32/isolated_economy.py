"""
Phase 32 Steps 2-4: capacity-freeing fertilizer, isolated-economy screen.

Baseline (no fertilizer, agents/phase21/ as shipped): mean $55,785.00 across
the 4 development seeds vs. "pass" -- this is Phase 30's own number
(results/phase30/PHASE30_FERTILIZER_REPORT.md Section 4) and this script
reproduces it directly (not just cited) as row "baseline_no_fertilizer".

Approach A -- dedicated fertilizer hands: n_dedicated_fert_hands in {1, 2}
extra hands added ON TOP of agents/phase21/'s own portfolio_targets n_hands
rungs, reserved for FERTILIZE/COLLECT_FERTILIZER duty first (falls back to
normal tasks otherwise). See scripts/phase32/fert_execution.py.

Approach B -- traded crop-tile ceiling: crop_tile_target scaled by {0.90,
0.80} (a -10%/-20% reduction, per this phase's brief, informed by the ~7%
idle-capacity gap the Step 1 probe found), no dedicated hands, same
fertilizer tasks fit into the capacity freed by the smaller footprint.

agents/phase21/ itself is not modified -- both approaches wrap
agents/phase21/portfolio.py::portfolio_targets from the outside and run
through scripts/phase32/fert_execution.py's own from-scratch execution layer.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from agents.phase21.adapters.portfolio_agent import make_portfolio_agent  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase32.fert_execution import make_fert_execution_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase32"


def make_reduced_target_fn(factor):
    def targets(day, obs, opponent_history):
        t = dict(portfolio_targets(day, obs, opponent_history))
        t["crop_tile_target"] = max(1, round(t["crop_tile_target"] * factor))
        return t
    return targets


def make_agent_with_opponent_logging(execution_agent_factory):
    """Wires the same opponent-observation telemetry
    agents/phase21/adapters/portfolio_agent.py uses, around a fertilizer
    execution agent built with scripts/phase32/fert_execution.py."""
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
        record, extracted = analyze_replay(replay, meta, "phase32_isolated", f"{label}_seed{seed}")
        final_money = record["outcome"]["final_money"][0]
        ae = record["players"][0]["action_efficiency"]

        fert_counts = fertilized_tile_count_series(replay)
        peak_fert = max(fert_counts) if fert_counts else 0
        days_sustained_20plus = sum(1 for c in fert_counts if c >= 20)

        rows.append({
            "seed": seed, "final_money": final_money,
            "idle_action_fraction": ae["idle_fraction"],
            "peak_fertilized_tiles": peak_fert,
            "days_with_20plus_fertilized_tiles": days_sustained_20plus,
        })
        print(f"  [{label}] seed={seed}: final_money=${final_money} peak_fertilized={peak_fert} "
              f"idle_action_fraction={ae['idle_fraction']}", flush=True)

    mean_final = sum(r["final_money"] for r in rows) / len(rows)
    mean_peak = sum(r["peak_fertilized_tiles"] for r in rows) / len(rows)
    print(f"  [{label}] MEAN final_money=${mean_final:.2f}  MEAN peak_fertilized_tiles={mean_peak:.1f}\n")
    return {"label": label, "rows": rows, "mean_final_money": mean_final, "mean_peak_fertilized_tiles": mean_peak}


def fertilized_tile_count_series(replay):
    """Direct read of player 0's fertilized_tile_count over the episode, same
    field Phase 30 (Section 1) used from replay_forensics -- read here
    directly from the raw per-tile state at the last step of each day rather
    than via the forensics module (this is OUR OWN farm, not an opponent
    replay parse), counting tiles with fertilized_until_day >= day."""
    n_steps = len(replay["steps"])
    counts = []
    turns_per_day = 24
    for day in range(30):
        t = day * turns_per_day + (turns_per_day - 1)
        if t >= n_steps:
            break
        obs = replay["steps"][t][0]["observation"]
        farm = obs["farms"][0]
        tiles = farm["tiles"]
        n = 0
        for row in tiles:
            for tile in row:
                if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("fertilized_until_day", -1) >= day:
                    n += 1
        counts.append(n)
    return counts


def main():
    results = {}

    print("=== baseline: no fertilizer, agents/phase21/ as shipped ===")
    def baseline_factory():
        return make_fert_execution_agent(portfolio_targets, fertilize=False, n_dedicated_fert_hands=0)
    results["baseline_no_fertilizer"] = run_condition("baseline_no_fertilizer", baseline_factory)

    print("=== Phase 30 reproduction check: fertilizer, no capacity freeing ===")
    def phase30_repro_factory():
        return make_fert_execution_agent(portfolio_targets, fertilize=True, n_dedicated_fert_hands=0)
    results["phase30_repro_fertilizer_no_capacity"] = run_condition("phase30_repro", phase30_repro_factory)

    print("=== Approach A: dedicated fertilizer hands ===")
    for n_dedicated in [1, 2]:
        label = f"approachA_dedicated_hands_{n_dedicated}"
        def factory(n=n_dedicated):
            return make_fert_execution_agent(portfolio_targets, fertilize=True, n_dedicated_fert_hands=n)
        results[label] = run_condition(label, factory)

    print("=== Approach B: reduced crop-tile ceiling ===")
    for reduction_pct, factor in [(10, 0.90), (20, 0.80)]:
        label = f"approachB_reduced_ceiling_{reduction_pct}pct"
        def factory(f=factor):
            return make_fert_execution_agent(make_reduced_target_fn(f), fertilize=True, n_dedicated_fert_hands=0)
        results[label] = run_condition(label, factory)

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase32_isolated_economy_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase32_isolated_economy_results.json")

    print("\n=== SUMMARY (mean final money, mean peak fertilized tiles) ===")
    for label, r in results.items():
        print(f"  {label}: ${r['mean_final_money']:.2f}  peak_fert={r['mean_peak_fertilized_tiles']:.1f}")


if __name__ == "__main__":
    main()
