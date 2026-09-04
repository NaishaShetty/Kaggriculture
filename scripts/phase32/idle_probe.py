"""
Phase 32 Step 1: re-run Phase 30's exact idle-capacity measurement on the
CURRENT (no-fertilizer) agents/phase21/ baseline, to confirm the 7.0% figure
(results/phase30/PHASE30_FERTILIZER_REPORT.md Section 2) still holds before
building anything on top of it. Same methodology: agents/phase21/'s shipped
portfolio agent (agents/phase21/adapters/portfolio_agent.py::make_portfolio_agent,
Submission H's own target_fn), isolated vs. "pass", seed 700000, full
30-day/720-step episode, action_efficiency read from the existing
instrumentation pipeline (instrumentation/pipeline.py::analyze_replay) --
not reimplemented.

agents/phase21/ is not modified.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.adapters.portfolio_agent import make_portfolio_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase32"


def main():
    rows = []
    for seed in DEV_SEEDS:
        agent = make_portfolio_agent()
        replay, meta = run_episode(agent, "pass", STEPS, seed, None)
        record, extracted = analyze_replay(replay, meta, "phase32_idle_probe", f"seed{seed}")
        ae = record["players"][0]["action_efficiency"]
        row = {
            "seed": seed,
            "final_money": record["outcome"]["final_money"][0],
            "idle_action_fraction": ae["idle_fraction"],
            "productive_action_rate": ae["productive_action_rate"],
            "movement_fraction": ae["movement_fraction"],
            "crop_fraction": ae["crop_fraction"],
            "n_farmer_actions": ae["n_farmer_actions"],
            "n_hand_actions": ae["n_hand_actions"],
        }
        rows.append(row)
        print(f"  seed={seed}: final_money=${row['final_money']} idle_action_fraction={row['idle_action_fraction']} "
              f"productive_rate={row['productive_action_rate']}", flush=True)

    mean_idle = sum(r["idle_action_fraction"] for r in rows) / len(rows)
    mean_productive = sum(r["productive_action_rate"] for r in rows) / len(rows)
    seed700000 = next(r for r in rows if r["seed"] == 700000)

    print(f"\nMean idle_action_fraction across {len(DEV_SEEDS)} dev seeds: {mean_idle:.4f}")
    print(f"Mean productive_action_rate: {mean_productive:.4f}")
    print(f"seed=700000 alone (Phase 30's exact single-seed measurement point): "
          f"idle_action_fraction={seed700000['idle_action_fraction']:.4f}")

    os.makedirs(OUT_ROOT, exist_ok=True)
    out = {"rows": rows, "mean_idle_action_fraction": mean_idle, "mean_productive_action_rate": mean_productive,
           "seed_700000_idle_action_fraction": seed700000["idle_action_fraction"]}
    with open(os.path.join(OUT_ROOT, "phase32_idle_probe_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase32_idle_probe_results.json")


if __name__ == "__main__":
    main()
