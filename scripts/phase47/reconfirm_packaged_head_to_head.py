"""
Phase 47: re-confirm the PACKAGED artifact's head-to-head behavior (not just
the in-repo modules) against Submission G, Submission C, and the Phase 43
Jonaid archetype, on the FULL 15-seed development+validation+held-out set --
same cross-root technique Phase 18/20/29/37 used. `sys.path` is pointed
ONLY at the isolated extracted directory and `sys.modules` entries for
`agents`/`vendor_kaggriculture`/`scripts`/`instrumentation` are cleared
before importing the packaged agent fresh, forcing Python's import system to
resolve the entire dependency tree from the packaged copy, not the repo.
`sys.modules` is cleared again and `sys.path` repointed at the repo root
before importing the three opponents fresh from there.
"""
import importlib
import json
import os
import sys

EXTRACTED_ROOT = "C:/tmp/phase47_coldtest"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEV_SEEDS = [700000, 700001, 700002, 700003]
VAL_SEEDS = [701000, 701001, 701002, 701003, 701004]
HELD_OUT_SEEDS = [702000, 702001, 702002, 702003, 702004, 702005]
ALL_SEEDS = DEV_SEEDS + VAL_SEEDS + HELD_OUT_SEEDS
STEPS = 720


def _clear_modules(prefixes):
    for name in list(sys.modules):
        if any(name == p or name.startswith(p + ".") for p in prefixes):
            del sys.modules[name]


def main():
    # --- import the PACKAGED agent factory, resolved ONLY from the extracted dir ---
    sys.path.insert(0, EXTRACTED_ROOT)
    if REPO_ROOT in sys.path:
        sys.path.remove(REPO_ROOT)
    _clear_modules(["agents", "vendor_kaggriculture", "scripts", "instrumentation"])

    from scripts.phase46.feed_priority_portfolio_agent import make_feed_priority_portfolio_agent as packaged_make_agent  # noqa: E402

    print(f"packaged make_feed_priority_portfolio_agent resolved from: {packaged_make_agent.__module__} "
          f"({sys.modules[packaged_make_agent.__module__].__file__})")

    # --- switch to the REPO for the three opponents and the game engine, resolved fresh ---
    sys.path.remove(EXTRACTED_ROOT)
    sys.path.insert(0, REPO_ROOT)
    _clear_modules(["agents", "vendor_kaggriculture", "scripts", "instrumentation"])
    importlib.invalidate_caches()  # required: without this, the 'agents' regular-package
    # (non-namespace, has __init__.py) finder stays cached to the extracted dir's
    # path-importer-cache entry even after sys.path is repointed -- discovered directly
    # via a standalone repro during this phase's own validation, not assumed.

    from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
    from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402
    from scripts.phase43.jonaid_archetype import make_jonaid_archetype  # noqa: E402
    from instrumentation.collector import run_episode  # noqa: E402

    OPPONENTS = {
        "submission_g": (make_macro_agent, {}),
        "submission_c": (make_competitive_v3_agent, {"trace_path": None, "liquidity_guard_enabled": False}),
        "jonaid": (make_jonaid_archetype, {}),
    }

    results = {}
    for opp_label, (make_opponent, kwargs) in OPPONENTS.items():
        wins, losses, ties, per_seed = 0, 0, 0, []
        our_vals, their_vals = [], []
        print(f"\n=== packaged vs. {opp_label} (15seed_full, n={len(ALL_SEEDS)}) ===")
        for seed in ALL_SEEDS:
            ours = packaged_make_agent()
            theirs = make_opponent(**kwargs)
            replay, _ = run_episode(ours, theirs, STEPS, seed, None)
            o, t = replay["rewards"][0], replay["rewards"][1]
            our_vals.append(o)
            their_vals.append(t)
            winner = "packaged" if o > t else ("tie" if o == t else opp_label)
            if winner == "packaged":
                wins += 1
            elif winner == opp_label:
                losses += 1
            else:
                ties += 1
            per_seed.append({"seed": seed, "packaged": o, opp_label: t, "winner": winner})
            print(f"    seed={seed}: packaged=${o:,.2f} {opp_label}=${t:,.2f} winner={winner}", flush=True)
        mean_margin = sum(o - t for o, t in zip(our_vals, their_vals)) / len(ALL_SEEDS)
        results[opp_label] = {
            "wins": wins, "losses": losses, "ties": ties, "n": len(ALL_SEEDS),
            "mean_packaged": round(sum(our_vals) / len(ALL_SEEDS), 2),
            "mean_opponent": round(sum(their_vals) / len(ALL_SEEDS), 2),
            "mean_margin": round(mean_margin, 2), "per_seed": per_seed,
        }
        print(f"  Record: {wins}W-{losses}L-{ties}T ({wins}/{len(ALL_SEEDS)})  mean_margin=${mean_margin:,.2f}")

    os.makedirs("results/phase47", exist_ok=True)
    out_path = "results/phase47/phase47_reconfirm_packaged_h2h_15seed_full.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_path}")

    print("\n=== SUMMARY (packaged artifact, 15-seed full) ===")
    for opp_label, row in results.items():
        print(f"  vs_{opp_label}: {row['wins']}/{row['n']} (mean_margin=${row['mean_margin']:,.2f}, "
              f"packaged=${row['mean_packaged']:,.2f}, opp=${row['mean_opponent']:,.2f})")


if __name__ == "__main__":
    main()
