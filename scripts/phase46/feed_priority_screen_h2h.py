"""
Phase 46 Part B/C validation: head-to-head, Submission I shipped (baseline)
vs. Part B (FEED tier-0.5) vs. Part B+C (FEED tier-0.5 + capacity-aware
BUY_ANIMAL throttle), against all three required opponents (Submission G,
Submission C, the Phase 43 Jonaid archetype) -- same structure as
scripts/phase45/opponent_steering_screen.py, run first on the cheap 4-seed
dev set, then (mandatory per this project's own standing rule) on the full
15-seed set before any promotion recommendation.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402
from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from scripts.phase46.feed_priority_portfolio_agent import make_feed_priority_portfolio_agent  # noqa: E402
from scripts.phase46.feed_priority_throttled_portfolio_agent import make_feed_priority_throttled_portfolio_agent  # noqa: E402
from scripts.phase43.jonaid_archetype import make_jonaid_archetype  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from scripts.phase3_2_configs import SEED_SETS  # noqa: E402

STEPS = 720
DEV_SEEDS = SEED_SETS["development"]
ALL_SEEDS = SEED_SETS["development"] + SEED_SETS["validation"] + SEED_SETS["held_out"]
OUT_ROOT = "results/phase46"

OPPONENTS = {
    "submission_g": (make_macro_agent, {}),
    "submission_c": (make_competitive_v3_agent, {"trace_path": None, "liquidity_guard_enabled": False}),
    "jonaid": (make_jonaid_archetype, {}),
}
CANDIDATES = {
    "baseline": make_paced_portfolio_agent,
    "feed_priority": make_feed_priority_portfolio_agent,
    "feed_priority_throttled": make_feed_priority_throttled_portfolio_agent,
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


def main(seeds, seed_label):
    results = {}
    for cand_label, make_ours in CANDIDATES.items():
        results[cand_label] = {}
        for opp_label, (make_opponent, kwargs) in OPPONENTS.items():
            print(f"\n=== {cand_label} vs. {opp_label} ({seed_label}, n={len(seeds)}) ===")
            m = run_matchup(make_ours, opp_label, make_opponent, kwargs, seeds)
            results[cand_label][opp_label] = m
            print(f"  Record: {m['wins']}W-{m['losses']}L-{m['ties']}T ({m['wins']}/{m['n']})  mean_margin=${m['mean_margin']:,.2f}")

    os.makedirs(OUT_ROOT, exist_ok=True)
    out_path = os.path.join(OUT_ROOT, f"phase46_feed_priority_h2h_{seed_label}.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_path}")

    print(f"\n=== SUMMARY ({seed_label}) ===")
    for cand_label in CANDIDATES:
        row = results[cand_label]
        print(f"  {cand_label}: " + "  ".join(
            f"vs_{opp}={row[opp]['wins']}/{row[opp]['n']}(margin ${row[opp]['mean_margin']:,.0f})" for opp in OPPONENTS))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "dev"
    if stage == "dev":
        main(DEV_SEEDS, "4seed_dev")
    elif stage == "full":
        main(ALL_SEEDS, "15seed_full")
    else:
        raise SystemExit(f"unknown stage {stage!r}, expected 'dev' or 'full'")
