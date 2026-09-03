"""
Phase 18 Step 4c: re-confirm the win-rate result using the actual PACKAGED,
extracted artifact (not just the in-repo agents/phase15/ module) -- the one
thing Phase 15-17 never explicitly tested.

Technique: import the packaged agent's dependency closure from the isolated,
extracted package directory FIRST (sys.path pointing ONLY at the isolated
dir, so Python's "agents" package resolves to the packaged copy), build the
agent closure, then clear sys.modules and re-import Submission C fresh from
the REPO root (sys.path pointing at the repo). Each agent closure captures
its own function's __globals__ at the time it was defined, so once both
closures exist, which "agents" package is currently cached in sys.modules no
longer matters for calling them -- this gives genuine cross-root validation
in a single process, rather than risking a same-process import collision
silently reusing one root's copy for both agents (Python does not merge two
same-named regular packages from different sys.path roots).

Usage: python scripts/phase18/reconfirm_packaged_head_to_head.py <isolated_dir>
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEV_SEEDS = [700000, 700001, 700002, 700003]
STEPS = 720


def _clear_agents_modules():
    prefixes = ("agents", "vendor_kaggriculture", "economic_model")
    for name in list(sys.modules):
        if name in prefixes or any(name.startswith(p + ".") for p in prefixes):
            del sys.modules[name]


def build_packaged_agent_f(isolated_dir):
    sys.path.insert(0, isolated_dir)
    _clear_agents_modules()
    from agents.phase15.adapters.macro_agent import make_macro_agent
    agent = make_macro_agent()
    sys.path.remove(isolated_dir)
    return agent


def build_repo_agent_c():
    sys.path.insert(0, REPO_ROOT)
    _clear_agents_modules()
    from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent
    agent = make_competitive_v3_agent(trace_path=None, liquidity_guard_enabled=False)
    return agent


def main():
    isolated_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/phase18_coldtest"
    isolated_dir = os.path.abspath(isolated_dir)

    agentF = build_packaged_agent_f(isolated_dir)
    agentC = build_repo_agent_c()  # leaves REPO_ROOT on sys.path, needed by instrumentation below

    from instrumentation.collector import run_episode

    print(f"Packaged Submission F (from {isolated_dir}) vs. in-repo Submission C, {len(DEV_SEEDS)} dev seeds:\n")
    results = []
    for seed in DEV_SEEDS:
        # Fresh agent instances per episode (matches every prior phase's per-episode agent construction discipline)
        aF = build_packaged_agent_f(isolated_dir)
        aC = build_repo_agent_c()
        replay, meta = run_episode(aF, aC, STEPS, seed, None)
        ours, theirs = replay["rewards"][0], replay["rewards"][1]
        results.append((seed, ours, theirs))
        print(f"  seed={seed}: packaged-F=${ours:,.2f}  in-repo-C=${theirs:,.2f}  "
              f"{'F wins' if ours > theirs else 'C wins'}")

    wins = sum(1 for _, o, t in results if o > t)
    mean_ours = sum(o for _, o, t in results) / len(results)
    mean_theirs = sum(t for _, o, t in results) / len(results)
    print(f"\nWin rate: {wins}/{len(results)}")
    print(f"Mean: packaged-F=${mean_ours:,.2f}  in-repo-C=${mean_theirs:,.2f}")


if __name__ == "__main__":
    main()
