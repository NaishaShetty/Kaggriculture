"""
Phase 50: re-confirm the PACKAGED artifact's head-to-head behavior (not just
the in-repo modules) against Submission G, Submission C, and the Phase 43
Jonaid archetype, on the FULL 15-seed development+validation+held-out set --
same cross-root technique Phase 18/20/29/37/47 used, using Phase 47's own
reconfirmation script as a DIRECT TEMPLATE. `sys.path` is pointed ONLY at
the isolated extracted directory and `sys.modules` entries for
`agents`/`vendor_kaggriculture`/`scripts`/`instrumentation` are cleared
before importing the packaged agent fresh, forcing Python's import system to
resolve the entire dependency tree from the packaged copy, not the repo.
`sys.modules` is cleared again and `sys.path` repointed at the repo root
before importing the three opponents fresh from there.

Per this phase's own instruction, two specific pitfalls Phase 47 found and
fixed in ITS OWN version of this script are checked directly here, not
assumed to transfer automatically:

1. REPO_ROOT dirname()-count off-by-one: this script sits at
   scripts/phase50/reconfirm_packaged_head_to_head.py, the SAME directory
   depth below the repo root as Phase 47's own script
   (scripts/phase47/reconfirm_packaged_head_to_head.py -- both are exactly
   TWO directories below the repo root: scripts/<phaseN>/<file>.py). Phase
   47's fixed version uses three chained os.path.dirname() calls to walk
   scripts/phase47/reconfirm_...py -> scripts/phase47 -> scripts -> repo
   root. Confirmed directly below (see the assert in main()) that three
   dirname() calls from THIS file's __file__ also lands on the actual repo
   root (a directory containing main.py, agents/, scripts/, and
   vendor_kaggriculture/) -- not assumed just because the nesting depth
   looks the same.
2. Missing importlib.invalidate_caches() after repointing sys.path back to
   the repo root: included below, in the same place Phase 47's fixed version
   puts it (immediately after the sys.path repoint and _clear_modules call,
   before importing agents.phase15/agents.phase3_8/scripts.phase43 fresh
   from the repo) -- required because `agents` is a regular (non-namespace)
   package (has __init__.py) whose cached path-importer-cache entry
   otherwise survives the repoint and keeps resolving to the extracted
   directory even after sys.path no longer contains it.
"""
import importlib
import json
import os
import sys

EXTRACTED_ROOT = "C:/tmp/phase50_coldtest"
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
    # --- Pitfall 1 check: confirm REPO_ROOT actually resolves to the repo
    # root (contains main.py, agents/, scripts/, vendor_kaggriculture/), not
    # scripts/ or scripts/phase50/ -- directly verified, not assumed. ---
    for marker in ("main.py", "agents", "scripts", "vendor_kaggriculture"):
        assert os.path.exists(os.path.join(REPO_ROOT, marker)), (
            f"REPO_ROOT dirname()-count looks wrong: {REPO_ROOT!r} is missing "
            f"{marker!r} -- this is the exact off-by-one Phase 47 caught, "
            f"re-check the dirname() chain before trusting anything below."
        )
    print(f"REPO_ROOT resolved to: {REPO_ROOT} (verified: contains main.py, agents/, "
          f"scripts/, vendor_kaggriculture/ -- not scripts/ or scripts/phase50/)")

    # --- import the PACKAGED agent factory, resolved ONLY from the extracted dir ---
    sys.path.insert(0, EXTRACTED_ROOT)
    if REPO_ROOT in sys.path:
        sys.path.remove(REPO_ROOT)
    _clear_modules(["agents", "vendor_kaggriculture", "scripts", "instrumentation"])

    from scripts.phase48.capped_animal_portfolio_agent import make_capped_animal_portfolio_agent as packaged_make_agent  # noqa: E402

    print(f"packaged make_capped_animal_portfolio_agent resolved from: {packaged_make_agent.__module__} "
          f"({sys.modules[packaged_make_agent.__module__].__file__})")
    resolved_file = sys.modules[packaged_make_agent.__module__].__file__
    assert os.path.abspath(resolved_file).startswith(os.path.abspath(EXTRACTED_ROOT)), (
        f"packaged agent resolved from {resolved_file!r}, which is NOT under "
        f"{EXTRACTED_ROOT!r} -- the packaged-artifact re-confirmation would be "
        f"silently testing the repo copy instead of the packaged one."
    )

    # --- switch to the REPO for the three opponents and the game engine, resolved fresh ---
    sys.path.remove(EXTRACTED_ROOT)
    sys.path.insert(0, REPO_ROOT)
    _clear_modules(["agents", "vendor_kaggriculture", "scripts", "instrumentation"])
    importlib.invalidate_caches()  # Pitfall 2 fix: required -- without this, the 'agents'
    # regular-package (non-namespace, has __init__.py) finder stays cached to the
    # extracted dir's path-importer-cache entry even after sys.path is repointed --
    # this is the exact bug Phase 47 found via a standalone repro; included here
    # directly rather than assumed to be unnecessary this time.

    from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
    from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402
    from scripts.phase43.jonaid_archetype import make_jonaid_archetype  # noqa: E402
    from instrumentation.collector import run_episode  # noqa: E402

    # Confirm the opponents/engine resolved from the REPO, not the extracted dir
    # (the packaged tarball doesn't even contain these modules, so a successful
    # import here that resolved from EXTRACTED_ROOT would be impossible -- but
    # confirmed directly anyway, matching this phase's "verify, don't assume" rule).
    macro_agent_file = sys.modules[make_macro_agent.__module__].__file__
    assert os.path.abspath(macro_agent_file).startswith(os.path.abspath(REPO_ROOT)), (
        f"opponent make_macro_agent resolved from {macro_agent_file!r}, not under repo root {REPO_ROOT!r}"
    )
    print(f"opponents/engine resolved from repo root: {REPO_ROOT} (verified via make_macro_agent's module file)")

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

    os.makedirs(os.path.join(REPO_ROOT, "results/phase50"), exist_ok=True)
    out_path = os.path.join(REPO_ROOT, "results/phase50/phase50_reconfirm_packaged_h2h_15seed_full.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_path}")

    print("\n=== SUMMARY (packaged artifact, 15-seed full) ===")
    for opp_label, row in results.items():
        print(f"  vs_{opp_label}: {row['wins']}/{row['n']} (mean_margin=${row['mean_margin']:,.2f}, "
              f"packaged=${row['mean_packaged']:,.2f}, opp=${row['mean_opponent']:,.2f})")


if __name__ == "__main__":
    main()
