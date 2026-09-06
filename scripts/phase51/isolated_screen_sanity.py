"""
Phase 51, MANDATORY FIRST STEP (per this phase's own brief -- run BEFORE
touching the 4th-quadrant idea at all): 4-seed isolated-economy sanity check
comparing Submission K's own shipped, unmodified portfolio
(scripts/phase48/capped_animal_portfolio_agent.py, cap_total=8, composed with
Phase 46's FEED-priority execution) against the SAME portfolio run through
the new HIRE pacer instead
(scripts/phase51/hire_paced_capped_animal_portfolio_agent.py). No 4th
quadrant, no new crop -- this isolates the HIRE pacer's own effect. Mirrors
scripts/phase48/isolated_screen_animal_cap.py's structure exactly.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase48.capped_animal_portfolio_agent import make_capped_animal_portfolio_agent  # noqa: E402
from scripts.phase51.hire_paced_capped_animal_portfolio_agent import make_hire_paced_capped_animal_portfolio_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase51"


def owned_animal_count(obs):
    tiles = obs["farms"][0]["tiles"]
    return sum(1 for row in tiles for tt in row if isinstance(tt, dict) and "animal" in tt)


def run_condition(label, agent_factory):
    rows = []
    for seed in DEV_SEEDS:
        agent = agent_factory()
        replay, meta = run_episode(agent, "pass", STEPS, seed, None)
        record, extracted = analyze_replay(replay, meta, "phase51_sanity", f"{label}_seed{seed}")
        final_money = record["outcome"]["final_money"][0]
        ae = record["players"][0]["action_efficiency"]
        final_owned = owned_animal_count(replay["steps"][-1][0]["observation"])
        rows.append({
            "seed": seed, "final_money": final_money,
            "idle_action_fraction": ae["idle_fraction"], "final_owned": final_owned,
        })
        print(f"  [{label}] seed={seed}: final_money=${final_money} idle_fraction={ae['idle_fraction']:.4f} "
              f"final_owned={final_owned}", flush=True)
    mean_final = sum(r["final_money"] for r in rows) / len(rows)
    print(f"  [{label}] MEAN final_money=${mean_final:.2f}\n")
    return {"label": label, "rows": rows, "mean_final_money": mean_final}


def main():
    results = {}
    print("=== baseline: Submission K shipped, unmodified (capped-animal target + FEED-priority execution) ===")
    results["submission_k_baseline"] = run_condition("submission_k_baseline", make_capped_animal_portfolio_agent)

    print("=== candidate: Submission K's SAME portfolio, HIRE pacer added to execution layer ===")
    results["hire_paced"] = run_condition("hire_paced", make_hire_paced_capped_animal_portfolio_agent)

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase51_isolated_screen_sanity_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase51_isolated_screen_sanity_results.json")

    b = results["submission_k_baseline"]["mean_final_money"]
    m = results["hire_paced"]["mean_final_money"]
    print("\n=== SUMMARY vs. Submission K baseline ===")
    print(f"  hire_paced: ${m:.2f}  delta=${m - b:+.2f} ({(m - b) / b * 100:+.1f}%)")
    per_seed_deltas = [
        (br["seed"], hr["final_money"] - br["final_money"])
        for br, hr in zip(results["submission_k_baseline"]["rows"], results["hire_paced"]["rows"])
    ]
    print("  per-seed deltas: " + ", ".join(f"seed{s}:{d:+.2f}" for s, d in per_seed_deltas))
    n_regressed = sum(1 for _, d in per_seed_deltas if d < 0)
    print(f"  seeds regressed: {n_regressed}/4")


if __name__ == "__main__":
    main()
