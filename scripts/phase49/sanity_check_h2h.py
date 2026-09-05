"""
Phase 49 Step 1, part 2: 4-seed head-to-head screen, Submission I shipped
(baseline) vs. the combined-execution-layer candidate (Submission I's
EXISTING crop fractions, no CARROT/TOMATO slice), against all three required
opponents (Submission G, Submission C, the Phase 43 Jonaid archetype). Same
two-stage discipline as Phase 42/45's own screens -- run cheap first, before
committing to anything further.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402
from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from scripts.phase49.combined_portfolio_agent import make_combined_portfolio_agent  # noqa: E402
from scripts.phase43.jonaid_archetype import make_jonaid_archetype  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from scripts.phase3_2_configs import SEED_SETS  # noqa: E402

STEPS = 720
DEV_SEEDS = SEED_SETS["development"]
OUT_ROOT = "results/phase49"

OPPONENTS = {
    "submission_g": (make_macro_agent, {}),
    "submission_c": (make_competitive_v3_agent, {"trace_path": None, "liquidity_guard_enabled": False}),
    "jonaid": (make_jonaid_archetype, {}),
}
CANDIDATES = {
    "shipped": make_paced_portfolio_agent,
    "combined": make_combined_portfolio_agent,
}


def run_matchup(make_ours, opp_label, make_opponent, opponent_kwargs, seeds):
    wins, losses, ties, per_seed = 0, 0, 0, []
    our_vals, their_vals = [], []
    for seed in seeds:
        ours = make_ours()
        theirs = make_opponent(**opponent_kwargs)
        replay, _ = run_episode(ours, theirs, STEPS, seed, None)
        o, t = replay["rewards"][0], replay["rewards"][1]
        our_vals.append(o)
        their_vals.append(t)
        winner = "ours" if o > t else ("tie" if o == t else "opponent")
        if winner == "ours":
            wins += 1
        elif winner == "opponent":
            losses += 1
        else:
            ties += 1
        per_seed.append({"seed": seed, "ours": o, "opponent": t, "winner": winner})
        print(f"    seed={seed}: ours=${o:,.2f} {opp_label}=${t:,.2f} winner={winner}", flush=True)
    mean_margin = sum(o - t for o, t in zip(our_vals, their_vals)) / len(seeds)
    return {"wins": wins, "losses": losses, "ties": ties, "n": len(seeds),
            "mean_ours": round(sum(our_vals) / len(seeds), 2), "mean_theirs": round(sum(their_vals) / len(seeds), 2),
            "mean_margin": round(mean_margin, 2), "per_seed": per_seed}


def main():
    results = {}
    for cand_label, make_ours in CANDIDATES.items():
        results[cand_label] = {}
        for opp_label, (make_opponent, kwargs) in OPPONENTS.items():
            print(f"\n=== {cand_label} vs. {opp_label} (4seed_dev) ===")
            m = run_matchup(make_ours, opp_label, make_opponent, kwargs, DEV_SEEDS)
            results[cand_label][opp_label] = m
            print(f"  Record: {m['wins']}W-{m['losses']}L-{m['ties']}T ({m['wins']}/{m['n']})  mean_margin=${m['mean_margin']:,.2f}")

    os.makedirs(OUT_ROOT, exist_ok=True)
    out_path = os.path.join(OUT_ROOT, "phase49_sanity_h2h_4seed_dev.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_path}")

    print("\n=== SUMMARY (4seed_dev) ===")
    for cand_label in CANDIDATES:
        row = results[cand_label]
        print(f"  {cand_label}: " + "  ".join(
            f"vs_{opp}={row[opp]['wins']}/{row[opp]['n']}(margin ${row[opp]['mean_margin']:,.0f})" for opp in OPPONENTS))


if __name__ == "__main__":
    main()
