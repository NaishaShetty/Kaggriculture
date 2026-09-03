"""
Phase 17 Step 4: widen the promotion-decision seed sample. Reuses this
project's EXISTING seed-bucket convention (scripts/phase3_2_configs.py::SEED_SETS,
already used by every phase since Phase 3.2 -- not invented new seeds):
  development: 700000-700003 (n=4) -- what Phase 15/16 used
  validation:  701000-701004 (n=5)
  held_out:    702000-702005 (n=6) -- "final evaluation, used exactly once";
               this promotion decision is exactly that use.
Total n=15, exceeding the brief's "at least 12" floor while staying inside
this project's own established bucket semantics rather than picking new,
unaccountable seed numbers.

Runs Phase 15/16's exact Tier B/C methodology (isolated vs. "pass", head-to-head
vs. Submission C and Submission E) on agents/phase15/'s CURRENT code (Phase 16's
wheat-reserve fix + sell-timing disabled; Phase 17 found no further scheduling
fix was needed -- see the Phase 17 report Section 1-2). Reports the full
distribution (mean, median, min, max, count clearing $50,000), not just a mean.
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from scripts.phase3_2_configs import SEED_SETS  # noqa: E402

ALL_SEEDS = SEED_SETS["development"] + SEED_SETS["validation"] + SEED_SETS["held_out"]
STEPS = 720
OUT_ROOT = "results/phase17"

REAL_OPPONENT_FINAL_MONEY = {
    "moushun_chen": 63798.0, "lai_eu_wen": 104569.0, "achille_gohin": 76076.0, "zach_locke": 83904.0,
}


def dist_stats(values):
    return {
        "n": len(values), "mean": round(sum(values) / len(values), 2),
        "median": round(statistics.median(values), 2), "min": round(min(values), 2),
        "max": round(max(values), 2), "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
        "n_clearing_50k": sum(1 for v in values if v >= 50000),
    }


def main():
    print(f"Seed buckets: development(n={len(SEED_SETS['development'])}) + "
          f"validation(n={len(SEED_SETS['validation'])}) + held_out(n={len(SEED_SETS['held_out'])}) "
          f"= {len(ALL_SEEDS)} total\n")

    isolated = []
    vs_c_ours, vs_c_theirs = [], []
    vs_e_ours, vs_e_theirs = [], []

    for seed in ALL_SEEDS:
        agent = make_macro_agent()
        replay, _ = run_episode(agent, "pass", STEPS, seed, None)
        money = replay["rewards"][0]
        isolated.append(money)
        print(f"  isolated seed={seed}: ${money:,.2f}")

    for seed in ALL_SEEDS:
        agent15 = make_macro_agent()
        agentC = make_competitive_v3_agent(trace_path=None, liquidity_guard_enabled=False)
        replay, _ = run_episode(agent15, agentC, STEPS, seed, None)
        vs_c_ours.append(replay["rewards"][0])
        vs_c_theirs.append(replay["rewards"][1])
        print(f"  vs Submission C seed={seed}: ours=${replay['rewards'][0]:,.2f} theirs=${replay['rewards'][1]:,.2f}")

    for seed in ALL_SEEDS:
        agent15 = make_macro_agent()
        agentE = make_competitive_v3_agent(trace_path=None)
        replay, _ = run_episode(agent15, agentE, STEPS, seed, None)
        vs_e_ours.append(replay["rewards"][0])
        vs_e_theirs.append(replay["rewards"][1])
        print(f"  vs Submission E seed={seed}: ours=${replay['rewards'][0]:,.2f} theirs=${replay['rewards'][1]:,.2f}")

    isolated_stats = dist_stats(isolated)
    vs_c_ours_stats, vs_c_theirs_stats = dist_stats(vs_c_ours), dist_stats(vs_c_theirs)
    vs_e_ours_stats, vs_e_theirs_stats = dist_stats(vs_e_ours), dist_stats(vs_e_theirs)

    print("\n=== ISOLATED FINAL MONEY DISTRIBUTION ===")
    print(json.dumps(isolated_stats, indent=2))
    print(f"Bar ($50,000-80,000+): mean {'CLEARS' if isolated_stats['mean'] >= 50000 else 'DOES NOT CLEAR'} "
          f"the $50,000 floor. {isolated_stats['n_clearing_50k']}/{isolated_stats['n']} individual seeds clear it.")

    print("\n=== HEAD-TO-HEAD vs SUBMISSION C ===")
    print("ours:", json.dumps(vs_c_ours_stats, indent=2))
    print("theirs:", json.dumps(vs_c_theirs_stats, indent=2))
    wins_c = sum(1 for o, t in zip(vs_c_ours, vs_c_theirs) if o > t)
    print(f"Win rate vs Submission C: {wins_c}/{len(ALL_SEEDS)}")

    print("\n=== HEAD-TO-HEAD vs SUBMISSION E ===")
    print("ours:", json.dumps(vs_e_ours_stats, indent=2))
    print("theirs:", json.dumps(vs_e_theirs_stats, indent=2))
    wins_e = sum(1 for o, t in zip(vs_e_ours, vs_e_theirs) if o > t)
    print(f"Win rate vs Submission E: {wins_e}/{len(ALL_SEEDS)}")

    print("\n=== vs REAL OPPONENTS (Phase 6) ===")
    for name, m in REAL_OPPONENT_FINAL_MONEY.items():
        print(f"  {name}: ${m:,.2f} ({'above' if isolated_stats['mean'] > m else 'below'} our mean)")

    out = {
        "seeds": ALL_SEEDS,
        "isolated": {"values": isolated, "stats": isolated_stats},
        "vs_submission_c": {"ours": vs_c_ours, "theirs": vs_c_theirs, "ours_stats": vs_c_ours_stats,
                             "theirs_stats": vs_c_theirs_stats, "win_rate": f"{wins_c}/{len(ALL_SEEDS)}"},
        "vs_submission_e": {"ours": vs_e_ours, "theirs": vs_e_theirs, "ours_stats": vs_e_ours_stats,
                             "theirs_stats": vs_e_theirs_stats, "win_rate": f"{wins_e}/{len(ALL_SEEDS)}"},
        "real_opponent_final_money": REAL_OPPONENT_FINAL_MONEY,
    }
    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase17_wide_validation_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote results to {OUT_ROOT}/phase17_wide_validation_results.json")


if __name__ == "__main__":
    main()
