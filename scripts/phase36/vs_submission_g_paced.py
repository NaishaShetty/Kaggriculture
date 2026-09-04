"""
Phase 36 Stage 1, Step 4 (continued): full 15-seed head-to-head validation
for the adaptive pacer (SAME targets as Submission H, only BUY_ANIMAL's
purchase timing differs), against Submission G and Submission C -- same
methodology as scripts/phase23/vs_submission_g.py, reused directly.
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402
from scripts.phase36.paced_execution import make_paced_execution_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from scripts.phase3_2_configs import SEED_SETS  # noqa: E402

ALL_SEEDS = SEED_SETS["development"] + SEED_SETS["validation"] + SEED_SETS["held_out"]
STEPS = 720
OUT_ROOT = "results/phase36"


def make_paced_agent():
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_paced_execution_agent(portfolio_targets)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    return agent


def dist_stats(values):
    return {
        "n": len(values), "mean": round(sum(values) / len(values), 2),
        "median": round(statistics.median(values), 2), "min": round(min(values), 2),
        "max": round(max(values), 2), "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
    }


def run_matchup(label, make_opponent, opponent_kwargs=None):
    opponent_kwargs = opponent_kwargs or {}
    print(f"\n=== paced agents/phase21/ vs. {label} ({len(ALL_SEEDS)} seeds) ===")
    ours, theirs, per_seed = [], [], []
    for seed in ALL_SEEDS:
        agent_paced = make_paced_agent()
        agent_opp = make_opponent(**opponent_kwargs)
        replay, _ = run_episode(agent_paced, agent_opp, STEPS, seed, None)
        o, t = replay["rewards"][0], replay["rewards"][1]
        ours.append(o)
        theirs.append(t)
        winner = "paced" if o > t else ("tie" if o == t else label)
        per_seed.append({"seed": seed, "paced": o, "opponent": t, "winner": winner})
        print(f"  seed={seed}: paced=${o:,.2f}  {label}=${t:,.2f}  winner={winner}")

    wins = sum(1 for r in per_seed if r["winner"] == "paced")
    losses = sum(1 for r in per_seed if r["winner"] == label)
    ties = sum(1 for r in per_seed if r["winner"] == "tie")
    print(f"\n  Record: {wins}W-{losses}L-{ties}T  (win rate {wins}/{len(ALL_SEEDS)})")

    return {
        "label": label, "per_seed": per_seed, "paced_stats": dist_stats(ours), "opponent_stats": dist_stats(theirs),
        "wins": wins, "losses": losses, "ties": ties, "win_rate": f"{wins}/{len(ALL_SEEDS)}",
    }


def main():
    print(f"Seed set: development(n={len(SEED_SETS['development'])}) + "
          f"validation(n={len(SEED_SETS['validation'])}) + held_out(n={len(SEED_SETS['held_out'])}) "
          f"= {len(ALL_SEEDS)} total")

    results = {}
    results["vs_submission_g"] = run_matchup("Submission_G", make_macro_agent)
    results["vs_submission_c"] = run_matchup(
        "Submission_C", make_competitive_v3_agent,
        {"trace_path": None, "liquidity_guard_enabled": False},
    )

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase36_vs_submission_g_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase36_vs_submission_g_results.json")


if __name__ == "__main__":
    main()
