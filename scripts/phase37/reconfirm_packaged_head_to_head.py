"""
Phase 37, Step 5c: re-confirm the PACKAGED artifact's head-to-head behavior
(not just the in-repo modules) against the in-repo Submission G, on the 4
development seeds -- same cross-root technique Phase 18/20/29 used.
`sys.path` is pointed ONLY at the isolated extracted directory and
`sys.modules` entries for `agents`/`vendor_kaggriculture`/`scripts` are
cleared before importing the packaged agent fresh, forcing Python's import
system to resolve the entire dependency tree from the packaged copy, not the
repo. `sys.modules` is cleared again and `sys.path` repointed at the repo
root before importing Submission G fresh from there.
"""
import json
import os
import sys

EXTRACTED_ROOT = "C:/tmp/phase37_coldtest"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEV_SEEDS = [700000, 700001, 700002, 700003]
STEPS = 720


def _clear_modules(prefixes):
    for name in list(sys.modules):
        if any(name == p or name.startswith(p + ".") for p in prefixes):
            del sys.modules[name]


def main():
    # --- import the PACKAGED agent, resolved ONLY from the extracted dir ---
    sys.path.insert(0, EXTRACTED_ROOT)
    if REPO_ROOT in sys.path:
        sys.path.remove(REPO_ROOT)
    _clear_modules(["agents", "vendor_kaggriculture", "scripts", "instrumentation"])

    from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent as packaged_make_agent  # noqa: E402

    print(f"packaged make_paced_portfolio_agent resolved from: {packaged_make_agent.__module__} "
          f"({sys.modules[packaged_make_agent.__module__].__file__})")

    # --- switch to the REPO for Submission G and the game engine, resolved fresh ---
    sys.path.remove(EXTRACTED_ROOT)
    sys.path.insert(0, REPO_ROOT)
    _clear_modules(["agents", "vendor_kaggriculture", "scripts", "instrumentation"])

    from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
    from instrumentation.collector import run_episode  # noqa: E402

    rows = []
    for seed in DEV_SEEDS:
        agent_packaged = packaged_make_agent()
        agent_g = make_macro_agent()
        replay, meta = run_episode(agent_packaged, agent_g, STEPS, seed, None)
        o, t = replay["rewards"][0], replay["rewards"][1]
        winner = "packaged" if o > t else ("tie" if o == t else "submission_g")
        rows.append({"seed": seed, "packaged": o, "submission_g": t, "winner": winner})
        print(f"  seed={seed}: packaged=${o:,.2f}  submission_g=${t:,.2f}  winner={winner}")

    mean_p = sum(r["packaged"] for r in rows) / len(rows)
    mean_g = sum(r["submission_g"] for r in rows) / len(rows)
    print(f"\nMean: packaged=${mean_p:,.2f}  submission_g=${mean_g:,.2f}")

    os.makedirs("results/phase37", exist_ok=True)
    with open("results/phase37/phase37_reconfirm_packaged_results.json", "w") as f:
        json.dump({"rows": rows, "mean_packaged": mean_p, "mean_submission_g": mean_g}, f, indent=2)
    print("Wrote results/phase37/phase37_reconfirm_packaged_results.json")


if __name__ == "__main__":
    main()
