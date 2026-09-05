"""
Phase 42 Step 2: head-to-head vs. Submission G and Submission C, same
factories and kwargs scripts/phase23/vs_submission_g.py already established
as this project's standard. Runs BOTH Submission I as shipped (unmodified)
AND the delayed-start CARROT/TOMATO variant, so win-rate deltas are
measured against the same opponents in the same games' seeds -- not
inferred from isolated economy alone.

`n_seeds` lets this be run cheap (4 development seeds) first and, only if
that looks promising, re-run on the full 15-seed set
(scripts/phase3_2_configs.py::SEED_SETS) -- same two-stage discipline every
prior promotion in this project has used (Phase 17's own hard lesson: a
4-seed reading alone is not trustworthy for a promotion decision).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402
from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from scripts.phase42.carrot_tomato_portfolio import make_carrot_tomato_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from scripts.phase3_2_configs import SEED_SETS  # noqa: E402

STEPS = 720
DEV_SEEDS = SEED_SETS["development"]
ALL_SEEDS = SEED_SETS["development"] + SEED_SETS["validation"] + SEED_SETS["held_out"]
OUT_ROOT = "results/phase42"

OPPONENTS = {
    "submission_g": (make_macro_agent, {}),
    "submission_c": (make_competitive_v3_agent, {"trace_path": None, "liquidity_guard_enabled": False}),
}
CANDIDATES = {
    "baseline": make_paced_portfolio_agent,
    "variant": make_carrot_tomato_agent,
}


def run_matchup(make_ours, opp_label, make_opponent, opponent_kwargs, seeds):
    wins, losses, ties, per_seed = 0, 0, 0, []
    for seed in seeds:
        ours = make_ours()
        theirs = make_opponent(**opponent_kwargs)
        replay, _ = run_episode(ours, theirs, STEPS, seed, None)
        o, t = replay["rewards"][0], replay["rewards"][1]
        winner = "ours" if o > t else ("tie" if o == t else "opponent")
        if winner == "ours":
            wins += 1
        elif winner == "opponent":
            losses += 1
        else:
            ties += 1
        per_seed.append({"seed": seed, "ours": o, "opponent": t, "winner": winner})
        print(f"    seed={seed}: ours=${o:,.2f} {opp_label}=${t:,.2f} winner={winner}", flush=True)
    return {"wins": wins, "losses": losses, "ties": ties, "n": len(seeds), "per_seed": per_seed}


def main(seeds, seed_label):
    results = {}
    for cand_label, make_ours in CANDIDATES.items():
        results[cand_label] = {}
        for opp_label, (make_opponent, kwargs) in OPPONENTS.items():
            print(f"\n=== {cand_label} vs. {opp_label} ({seed_label}, n={len(seeds)}) ===")
            m = run_matchup(make_ours, opp_label, make_opponent, kwargs, seeds)
            results[cand_label][opp_label] = m
            print(f"  Record: {m['wins']}W-{m['losses']}L-{m['ties']}T ({m['wins']}/{m['n']})")

    os.makedirs(OUT_ROOT, exist_ok=True)
    out_path = os.path.join(OUT_ROOT, f"phase42_vs_g_and_c_{seed_label}.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_path}")

    print(f"\n=== SUMMARY ({seed_label}) ===")
    for cand_label in CANDIDATES:
        g, c = results[cand_label]["submission_g"], results[cand_label]["submission_c"]
        print(f"  {cand_label}: vs_G={g['wins']}/{g['n']}  vs_C={c['wins']}/{c['n']}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "dev"
    if stage == "dev":
        main(DEV_SEEDS, "4seed_dev")
    elif stage == "full":
        main(ALL_SEEDS, "15seed_full")
    else:
        raise SystemExit(f"unknown stage {stage!r}, expected 'dev' or 'full'")
