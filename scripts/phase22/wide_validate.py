"""
Phase 22 Step 4: widen validation of agents/phase21/'s portfolio controller
to this project's full 15-seed development+validation+held-out set
(scripts/phase3_2_configs.py::SEED_SETS -- same convention Phase 17/19/20
used), for BOTH isolated final money and head-to-head win rate against the
realistic-opponent benchmark (scripts/phase21/realistic_opponent.py, reused
unchanged). Reports full distributions, not single means, per Phase 17's
own hard-learned small-sample-luck lesson.
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.adapters.portfolio_agent import make_portfolio_agent  # noqa: E402
from scripts.phase21.realistic_opponent import make_realistic_opponent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from scripts.phase3_2_configs import SEED_SETS  # noqa: E402

ALL_SEEDS = SEED_SETS["development"] + SEED_SETS["validation"] + SEED_SETS["held_out"]
STEPS = 720
OUT_ROOT = "results/phase22"


def dist_stats(values):
    return {
        "n": len(values), "mean": round(sum(values) / len(values), 2),
        "median": round(statistics.median(values), 2), "min": round(min(values), 2),
        "max": round(max(values), 2), "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
    }


def main():
    print(f"Seed buckets: development(n={len(SEED_SETS['development'])}) + "
          f"validation(n={len(SEED_SETS['validation'])}) + held_out(n={len(SEED_SETS['held_out'])}) "
          f"= {len(ALL_SEEDS)} total\n")

    isolated = []
    for seed in ALL_SEEDS:
        agent = make_portfolio_agent()
        replay, _ = run_episode(agent, "pass", STEPS, seed, None)
        money = replay["rewards"][0]
        isolated.append(money)
        print(f"  isolated seed={seed}: ${money:,.2f}")

    ours, theirs = [], []
    for seed in ALL_SEEDS:
        agentP = make_portfolio_agent()
        agentR = make_realistic_opponent()
        replay, _ = run_episode(agentP, agentR, STEPS, seed, None)
        ours.append(replay["rewards"][0])
        theirs.append(replay["rewards"][1])
        print(f"  vs realistic-opponent seed={seed}: ours=${replay['rewards'][0]:,.2f} "
              f"theirs=${replay['rewards'][1]:,.2f}")

    isolated_stats = dist_stats(isolated)
    ours_stats, theirs_stats = dist_stats(ours), dist_stats(theirs)
    wins = sum(1 for o, t in zip(ours, theirs) if o > t)

    print("\n=== ISOLATED FINAL MONEY DISTRIBUTION (n=15) ===")
    print(json.dumps(isolated_stats, indent=2))

    print("\n=== HEAD-TO-HEAD vs REALISTIC-OPPONENT BENCHMARK (n=15) ===")
    print("ours:", json.dumps(ours_stats, indent=2))
    print("theirs:", json.dumps(theirs_stats, indent=2))
    print(f"Win rate: {wins}/{len(ALL_SEEDS)}")

    out = {
        "seeds": ALL_SEEDS,
        "isolated": {"values": isolated, "stats": isolated_stats},
        "head_to_head": {"ours": ours, "theirs": theirs, "ours_stats": ours_stats,
                          "theirs_stats": theirs_stats, "win_rate": f"{wins}/{len(ALL_SEEDS)}"},
    }
    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase22_wide_validation_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote results to {OUT_ROOT}/phase22_wide_validation_results.json")


if __name__ == "__main__":
    main()
