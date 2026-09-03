"""
Phase 29 Step 5c: re-confirm the win-rate result using the actual PACKAGED,
extracted Submission H artifact (not just the in-repo agents/phase21/
module) against the in-repo Submission G -- same cross-root technique
validated in Phase 18/20: import the packaged agent's dependency closure
from the isolated, extracted package directory FIRST (sys.path pointing
ONLY at the isolated dir, so Python's "agents" package resolves to the
packaged copy), build the agent closure, then clear sys.modules and
re-import Submission G fresh from the REPO root. Each agent closure captures
its own function's __globals__ at definition time, so which "agents" root
is cached afterward doesn't affect calling either agent.

Usage: python scripts/phase29/reconfirm_packaged_head_to_head.py <isolated_dir>
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEV_SEEDS = [700000, 700001, 700002, 700003]
STEPS = 720


def _clear_agent_modules():
    prefixes = ("agents", "vendor_kaggriculture", "economic_model")
    for name in list(sys.modules):
        if name in prefixes or any(name.startswith(p + ".") for p in prefixes):
            del sys.modules[name]


def build_packaged_agent_h(isolated_dir):
    sys.path.insert(0, isolated_dir)
    _clear_agent_modules()
    from agents.phase21.adapters.portfolio_agent import make_portfolio_agent
    agent = make_portfolio_agent()
    sys.path.remove(isolated_dir)
    return agent


def build_repo_agent_g():
    sys.path.insert(0, REPO_ROOT)
    _clear_agent_modules()
    from agents.phase15.adapters.macro_agent import make_macro_agent
    agent = make_macro_agent()
    return agent


def main():
    isolated_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/phase29_coldtest"
    isolated_dir = os.path.abspath(isolated_dir)

    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    from instrumentation.collector import run_episode

    print(f"Packaged Submission H (from {isolated_dir}) vs. in-repo Submission G, {len(DEV_SEEDS)} dev seeds:\n")
    results = []
    for seed in DEV_SEEDS:
        aH = build_packaged_agent_h(isolated_dir)
        aG = build_repo_agent_g()
        replay, meta = run_episode(aH, aG, STEPS, seed, None)
        ours, theirs = replay["rewards"][0], replay["rewards"][1]
        results.append((seed, ours, theirs))
        print(f"  seed={seed}: packaged-H=${ours:,.2f}  in-repo-G=${theirs:,.2f}  "
              f"{'H wins' if ours > theirs else 'G wins'}")

    wins = sum(1 for _, o, t in results if o > t)
    mean_ours = sum(o for _, o, t in results) / len(results)
    mean_theirs = sum(t for _, o, t in results) / len(results)
    print(f"\nWin rate: {wins}/{len(results)}")
    print(f"Mean: packaged-H=${mean_ours:,.2f}  in-repo-G=${mean_theirs:,.2f}")


if __name__ == "__main__":
    main()
