"""
Phase 36 Stage 2: Stage 1's pacer cleared its own isolated-economy screen
(+6.0%, $59,144.50 vs. $55,785.00 baseline) AND the full 15-seed validation
(10/15 vs. Submission G, up from Submission H's shipped 9/15; 15/15 vs.
Submission C, up from 14/15) -- per this phase's own decision rule, Stage 2
is now warranted: reintroduce Phase 35's best-performing rebalance candidate
(A2 -- staggered SHEEP-heavy, Sundar-informed, crop_tile_target capped at 32,
COW9/SHEEP16 reached by day 20 instead of day 11) ON TOP of the working
pacer (scripts/phase36/paced_execution.py, unchanged from Stage 1), to test
Phase 35's own hypothesis directly: does a properly cash-paced purchase
schedule finally let the Sundar-style rebalance work?

Reuses scripts/phase35/rebalance_candidates.py::make_candidate_a2_targets
directly (not re-derived) as the target_fn, run through
scripts/phase36/paced_execution.py::make_paced_execution_agent (the SAME
pacer validated in Stage 1, unchanged).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase35.rebalance_candidates import make_candidate_a2_targets  # noqa: E402
from scripts.phase36.paced_execution import make_paced_execution_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase36"


def make_a2_on_pacer_agent():
    target_fn = make_candidate_a2_targets()
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_paced_execution_agent(target_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    return agent


def run_isolated():
    print("=== Stage 2: Candidate A2 (Sundar-informed rebalance) ON TOP of the paced execution layer ===")
    rows = []
    for seed in DEV_SEEDS:
        agent = make_a2_on_pacer_agent()
        replay, meta = run_episode(agent, "pass", STEPS, seed, None)
        record, extracted = analyze_replay(replay, meta, "phase36_stage2_isolated", f"a2_on_pacer_seed{seed}")
        final_money = record["outcome"]["final_money"][0]
        ae = record["players"][0]["action_efficiency"]
        rows.append({"seed": seed, "final_money": final_money, "idle_action_fraction": ae["idle_fraction"]})
        print(f"  seed={seed}: final_money=${final_money} idle_action_fraction={ae['idle_fraction']:.4f}", flush=True)
    mean_final = sum(r["final_money"] for r in rows) / len(rows)
    mean_idle = sum(r["idle_action_fraction"] for r in rows) / len(rows)
    print(f"  MEAN final_money=${mean_final:.2f}  MEAN idle_action_fraction={mean_idle:.4f}\n")
    return {"label": "a2_on_pacer", "rows": rows, "mean_final_money": mean_final, "mean_idle_action_fraction": mean_idle}


def main():
    result = run_isolated()
    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase36_stage2_isolated_results.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {OUT_ROOT}/phase36_stage2_isolated_results.json")

    baseline = 55785.00
    paced = 59144.50
    m = result["mean_final_money"]
    print(f"\nvs. unmodified Submission H baseline (${baseline:,.2f}): delta=${m - baseline:+.2f} ({(m - baseline)/baseline*100:+.1f}%)")
    print(f"vs. Stage 1 pacer alone (${paced:,.2f}): delta=${m - paced:+.2f} ({(m - paced)/paced*100:+.1f}%)")


if __name__ == "__main__":
    main()
