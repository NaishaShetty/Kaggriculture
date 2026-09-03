"""
Phase 23: validation-only. Runs agents/phase21/'s portfolio controller
(Phase 22's tuned opening ratio) head-to-head against agents/phase15/'s
macro-controller agent AS SHIPPED (Submission G -- make_macro_agent()'s own
defaults: sell_timing_enabled=False, Phase 20's liquidity guard baked in
unconditionally in agents/phase15/execution.py), on this project's full
15-seed development+validation+held-out set
(scripts/phase3_2_configs.py::SEED_SETS) -- the same seeds and methodology
Phase 17/19/20/22 all used.

Secondary: also runs agents/phase21/ against Submission C
(agents/phase3_8/adapters/competitive_v3_agent.py, liquidity_guard_enabled=False,
matching every prior phase's "Submission C" convention) as extra context.

Neither agents/phase15/ nor agents/phase21/ is modified by this script or
this phase.
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from agents.phase21.adapters.portfolio_agent import make_portfolio_agent  # noqa: E402
from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from scripts.phase3_2_configs import SEED_SETS  # noqa: E402

ALL_SEEDS = SEED_SETS["development"] + SEED_SETS["validation"] + SEED_SETS["held_out"]
STEPS = 720
OUT_ROOT = "results/phase23"


def dist_stats(values):
    return {
        "n": len(values), "mean": round(sum(values) / len(values), 2),
        "median": round(statistics.median(values), 2), "min": round(min(values), 2),
        "max": round(max(values), 2), "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
    }


def run_matchup(label, make_opponent, opponent_kwargs=None):
    opponent_kwargs = opponent_kwargs or {}
    print(f"\n=== agents/phase21/ vs. {label} ({len(ALL_SEEDS)} seeds) ===")
    ours, theirs, per_seed = [], [], []
    for seed in ALL_SEEDS:
        agent21 = make_portfolio_agent()
        agent_opp = make_opponent(**opponent_kwargs)
        replay, _ = run_episode(agent21, agent_opp, STEPS, seed, None)
        o, t = replay["rewards"][0], replay["rewards"][1]
        ours.append(o)
        theirs.append(t)
        winner = "phase21" if o > t else ("tie" if o == t else label)
        per_seed.append({"seed": seed, "phase21": o, "opponent": t, "winner": winner})
        print(f"  seed={seed}: phase21=${o:,.2f}  {label}=${t:,.2f}  winner={winner}")

    wins = sum(1 for r in per_seed if r["winner"] == "phase21")
    losses = sum(1 for r in per_seed if r["winner"] == label)
    ties = sum(1 for r in per_seed if r["winner"] == "tie")
    ours_stats, theirs_stats = dist_stats(ours), dist_stats(theirs)
    print(f"\n  phase21 stats: {json.dumps(ours_stats)}")
    print(f"  {label} stats: {json.dumps(theirs_stats)}")
    print(f"  Record: {wins}W-{losses}L-{ties}T  (win rate {wins}/{len(ALL_SEEDS)})")

    return {
        "label": label, "per_seed": per_seed, "phase21_stats": ours_stats, "opponent_stats": theirs_stats,
        "wins": wins, "losses": losses, "ties": ties, "win_rate": f"{wins}/{len(ALL_SEEDS)}",
    }


def main():
    print(f"Seed set: development(n={len(SEED_SETS['development'])}) + "
          f"validation(n={len(SEED_SETS['validation'])}) + held_out(n={len(SEED_SETS['held_out'])}) "
          f"= {len(ALL_SEEDS)} total")

    results = {}
    # Primary: vs Submission G exactly as shipped (default kwargs).
    results["vs_submission_g"] = run_matchup("Submission_G", make_macro_agent)

    # Secondary: vs Submission C (liquidity_guard_enabled=False, matching every
    # prior phase's "Submission C" convention -- Phase 12's guard disabled).
    results["vs_submission_c"] = run_matchup(
        "Submission_C", make_competitive_v3_agent,
        {"trace_path": None, "liquidity_guard_enabled": False},
    )

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase23_vs_submission_g_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote results to {OUT_ROOT}/phase23_vs_submission_g_results.json")


if __name__ == "__main__":
    main()
