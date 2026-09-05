"""
Phase 43 Part A, Steps 1-2, 4: head-to-head Submission I (as shipped,
unmodified -- scripts/phase37/paced_portfolio_agent.py::
make_paced_portfolio_agent, confirmed by Phase 37/39's own reports as the
actual packaged factory) against the 4th-quadrant, whole-portfolio-scale-up
archetype, on the full 15-seed set (scripts/phase3_2_configs.py::SEED_SETS)
-- a benchmark-validation phase, so no 4-seed-only screen is needed for
THIS measurement (the archetype itself is what needs validating cheaply,
which Step 1 below does separately, in isolation, before this runs).

Two archetypes are available:
  - `scripts.phase34.sundar_archetype.make_sundar_archetype` (Phase 34,
    reused unchanged) -- Step 1 below re-confirms it, per this phase's own
    instruction not to trust it blindly, and finds it STILL fails its own
    isolation sanity check (chronic cash collapse to $0, hands down to 0
    workers mid-game) -- the exact same failure Phase 34's own report
    already documented ("failed its own prerequisite isolation sanity
    check on every attempt (3 rounds)"). NOT a regression -- confirmed
    still true, not newly broken. Included in the output for completeness
    and honesty, but NOT relied on as valid evidence.
  - `scripts.phase43.jonaid_archetype.make_jonaid_archetype` (this phase,
    new) -- a second, independent reconstruction from real episode
    105405216 (Jonaid), which DOES pass its own isolation sanity check
    (Step 1 below: $38,548-$45,914 across the 4 development seeds, no
    collapse) -- this is the archetype Part A's benchmark result and
    adoption recommendation actually rest on.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from scripts.phase34.sundar_archetype import make_sundar_archetype  # noqa: E402
from scripts.phase43.jonaid_archetype import make_jonaid_archetype  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from scripts.phase3_2_configs import SEED_SETS  # noqa: E402

STEPS = 720
DEV_SEEDS = SEED_SETS["development"]
ALL_SEEDS = SEED_SETS["development"] + SEED_SETS["validation"] + SEED_SETS["held_out"]
OUT_ROOT = "results/phase43"

ARCHETYPES = {
    "sundar": make_sundar_archetype,
    "jonaid": make_jonaid_archetype,
}


def isolation_sanity_check():
    print("=== Step 1: isolation sanity check (vs. 'pass', 4 dev seeds) ===")
    results = {}
    for label, make_archetype in ARCHETYPES.items():
        rows = []
        for seed in DEV_SEEDS:
            agent = make_archetype()
            replay, meta = run_episode(agent, "pass", STEPS, seed, None)
            fm = replay["rewards"][0]
            rows.append({"seed": seed, "final_money": fm})
            print(f"  [{label}] seed={seed}: final_money=${fm:,.2f}")
        results[label] = rows
    return results


def head_to_head(seeds, seed_label):
    print(f"\n=== Submission I vs. 4th-quadrant archetypes ({seed_label}, n={len(seeds)}) ===")
    results = {}
    for label, make_archetype in ARCHETYPES.items():
        wins, losses, ties, per_seed = 0, 0, 0, []
        our_vals, their_vals = [], []
        for seed in seeds:
            ours = make_paced_portfolio_agent()
            theirs = make_archetype()
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
            print(f"  [vs {label}] seed={seed}: ours=${o:,.2f} {label}=${t:,.2f} winner={winner}", flush=True)
        mean_margin = sum(o - t for o, t in zip(our_vals, their_vals)) / len(seeds)
        results[label] = {
            "wins": wins, "losses": losses, "ties": ties, "n": len(seeds),
            "mean_ours": round(sum(our_vals) / len(seeds), 2), "mean_theirs": round(sum(their_vals) / len(seeds), 2),
            "mean_margin": round(mean_margin, 2), "per_seed": per_seed,
        }
        print(f"  [vs {label}] Record: {wins}W-{losses}L-{ties}T ({wins}/{len(seeds)})  "
              f"mean_margin=${mean_margin:,.2f}\n")
    return results


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    sanity = isolation_sanity_check()

    h2h_full = head_to_head(ALL_SEEDS, "15seed_full")

    out = {"isolation_sanity_check": sanity, "head_to_head_15seed": h2h_full}
    with open(os.path.join(OUT_ROOT, "phase43_vs_fourth_quadrant_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase43_vs_fourth_quadrant_results.json")

    print("\n=== SUMMARY (15-seed full set) ===")
    for label, m in h2h_full.items():
        print(f"  vs {label}: {m['wins']}/{m['n']} ({100*m['wins']/m['n']:.1f}%)  mean_margin=${m['mean_margin']:,.2f}")


if __name__ == "__main__":
    main()
