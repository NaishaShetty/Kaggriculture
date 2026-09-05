"""
Phase 47 submission packaging script -- Submission J (agents/phase21/'s
portfolio agent, UNCHANGED targets, running through Phase 46's validated
FEED tier-0.5 reprioritization execution layer instead of Submission I's
Phase 36 cash-pacer-only execution layer).

Phase 46 (results/phase46/PHASE46_SCHEDULING_CAPACITY_REPORT.md) precisely
characterized the worker-turn scheduling bottleneck behind four independent
prior rejections (Phases 30/33/42/45): FEED loses the tier-1 nearest-worker
race to WATER on 62.9%-65.9% of FEED-relevant turns (not outright worker
exhaustion, which only accounts for 24.1%-27.2%). Part B
(`scripts/phase46/feed_priority_execution.py`) fixed this by giving FEED its
own tier 0.5 -- strictly ahead of WATER (tier 1), but never contesting
HARVEST/HARVEST_ANIMAL's own tier 0 (a literal tier-0 merge, tried first, was
a decisive regression -- see that phase's report Section 2). Part C (a
further BUY_ANIMAL throttle) was ALSO built
(`scripts/phase46/feed_priority_throttled_execution.py`) but Phase 46's own
Section 4/6 recommendation is Part B ALONE: it strictly recovers 4 of
Submission I's 5 losses against Submission G with ZERO new losses anywhere
in the 15-seed sample (10/15->14/15, mean margin +82%), while Part B+C
reaches the same win count by trading one baseline win for one new loss --
a different, not strictly better, profile. Per this phase's (47) own
instruction, Part B alone is what is packaged here; Part B+C
(`feed_priority_throttled_execution.py` / `_portfolio_agent.py`) is
deliberately NOT shipped.

CONFIRMED DIRECTLY (this phase's own read of Phase 46's report and source,
not assumed): the recommended candidate's exact module/function chain is
`scripts/phase46/feed_priority_execution.py::make_feed_priority_execution_agent`
composed with `scripts/phase46/feed_priority_portfolio_agent.py::make_feed_priority_portfolio_agent`,
which itself imports `agents/phase21/portfolio.py::portfolio_targets`
UNMODIFIED (the same shipped targets Submission I already ships: 3 land / 11
hands / 58 crop tiles / current animal ratio) -- the identical composition
pattern Phase 37 used for Phase 36's pacer, just with Phase 46's new
execution-layer factory swapped in. `agents/phase21/`'s own files
(execution.py, portfolio.py, liquidation.py, risk_posture.py, adapters/,
__init__.py) are untouched by Phase 46 and remain untouched here.

This is a NEW, SEPARATE submission package. The repo root main.py is NOT
modified by this script and continues to build Submission C/E exactly as
before; every already-shipped kaggriculture_*.tar.gz (Submissions A through
I) is untouched -- this package's own main.py (written by this script,
embedded below, never the repo root's main.py) is the only entry point that
builds scripts.phase46.feed_priority_portfolio_agent.make_feed_priority_portfolio_agent.

Letter "J": A-I are taken (phase3_4 Variant D "A", phase3_5 competitive_v2
"B", phase3_8 "C", phase7 sell-safety fix "D", phase12 F-005 fix "E",
phase18 macro-controller "F", phase20 macro-controller + liquidity guard
"G", phase29 shared-market portfolio agent "H", phase37 cash-pacer "I") --
confirmed by listing every existing kaggriculture_*.tar.gz in the repo root
before choosing this letter.

Usage:
    python scripts/phase47_build_submission.py

Output:
    kaggriculture_phase47_submission_J.tar.gz  (repo root)
"""
import hashlib
import os
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
OUT_NAME = "kaggriculture_phase47_submission_J.tar.gz"

# Dependency closure for scripts/phase46/feed_priority_portfolio_agent.py,
# traced by direct import reading (not assumed -- see the Phase 47 report
# Section 2):
#   feed_priority_portfolio_agent.py -> agents.phase3.opponent_observation (dataclasses/typing only)
#                                     -> agents.phase21.portfolio
#                                          -> agents.phase21.execution
#                                          -> agents.phase21.liquidation
#                                     -> scripts.phase46.feed_priority_execution
#                                          -> vendor_kaggriculture.kaggriculture
#                                          -> agents.phase21.risk_posture (stdlib only)
#                                          -> agents.phase21.liquidation
#                                          -> agents.phase21.execution (bounded_multi_crop_tile_pool_assignment, reused)
#                                          -> agents.phase2_3.common -> vendor_kaggriculture.kaggriculture
# Identical closure shape to Phase 37's (scripts/phase36/paced_execution.py
# has the exact same import block as scripts/phase46/feed_priority_execution.py --
# the latter starts as a copy of the former, per Phase 46's own docstring).
# Confirmed directly: does NOT import agents/phase21/adapters/portfolio_agent.py
# (Submission H/I's own entry point) at all -- this is a separate, parallel
# entry point. agents/phase2_3/ and vendor_kaggriculture/ are namespace
# packages (no __init__.py in either, confirmed directly, same as every
# prior submission's packaging); scripts/, scripts/phase46/ are ALSO
# namespace packages (confirmed: neither has an __init__.py) -- Python 3's
# PEP 420 namespace-package resolution needs none, provided the directories
# exist under a sys.path entry -- the same mechanism agents/phase2_3/ and
# vendor_kaggriculture/ already rely on in every prior submission.
# agents/phase3/ DOES have an (empty) __init__.py that must still ship.
FILES = [
    "vendor_kaggriculture/kaggriculture.py",
    "vendor_kaggriculture/kaggriculture.json",
    "agents/__init__.py",
    "agents/phase2_3/common.py",
    "agents/phase3/__init__.py",
    "agents/phase3/opponent_observation.py",
    "agents/phase21/__init__.py",
    "agents/phase21/portfolio.py",
    "agents/phase21/execution.py",
    "agents/phase21/liquidation.py",
    "agents/phase21/risk_posture.py",
    "scripts/phase46/feed_priority_execution.py",
    "scripts/phase46/feed_priority_portfolio_agent.py",
]

# The package's OWN main.py -- NOT the repo root's main.py, never written back
# to it. Same root-resolution / Kaggle-loading-compatibility handling as
# every prior submission's package main.py (read directly from
# scripts/phase37_build_submission.py, replicated verbatim, not reinvented).
MAIN_PY_CONTENT = '''"""
Kaggriculture competition submission entry point -- Submission J.

Canonical strategy: agents/phase21/'s macro-controller portfolio agent
(agents/phase21/portfolio.py::portfolio_targets -- UNCHANGED from Submission
I: MELON time-boxed to the opening, STRAWBERRY the durable bulk crop from
day 8, WHEAT rounds out the mix, land/hands/animal targets ramped from real
top-ladder replay data, a live-margin risk-posture layer, per-crop/per-tile
liquidation timing), run through Phase 46's FEED-priority execution layer
(scripts/phase46/feed_priority_execution.py::make_feed_priority_execution_agent)
instead of Submission I's own Phase-36-pacer-only execution layer: FEED
tasks now get their own priority tier (0.5, strictly ahead of WATER's tier
1, but never contesting HARVEST/HARVEST_ANIMAL's own tier 0) instead of
sharing WATER's tier and losing the nearest-worker race to it on the large
majority (62.9%-65.9%) of FEED-relevant turns. Phase 36's BUY_ANIMAL cash
pacer (composed, not reimplemented) and everything else (HIRE, BUY_LAND,
BUY_SEED, the rest of the task-priority scheme, the greedy nearest-worker
matching algorithm itself) is unchanged from Submission I.

Promoted per results/phase46/PHASE46_SCHEDULING_CAPACITY_REPORT.md: 14/15
(93.3%) head-to-head win rate against Submission G (up from Submission I's
own shipped 10/15, mean margin +82%), 15/15 (100%) against Submission C
(margin +36.8%), and 15/15 (100%) against the Phase 43 Jonaid archetype
(margin +23.8%), all on this project's full 15-seed
development+validation+held-out set -- re-confirmed against the packaged
artifact itself, not just the in-repo code, per
results/phase47/PHASE47_SUBMISSION_J_PACKAGING_REPORT.md.

This file remains a packaging/entry-point wrapper ONLY -- see
scripts/phase46/feed_priority_portfolio_agent.py for the actual wiring and
agents/phase21/portfolio.py / scripts/phase46/feed_priority_execution.py for
the architecture. The root-resolution logic below is UNCHANGED from every
prior submission's main.py (same two verified Kaggle-loader defects it
fixes: __file__ is unavailable under Kaggle's exec()-based loading, and this
project's top-level `agents` package name collides with several unrelated
`agents.py` files bundled inside kaggle_environments itself).

Do not add strategy logic to this file. Any behavioral change belongs in
agents/phase21/'s own modules or scripts/phase46/feed_priority_execution.py,
or a new, separately-validated phase -- never here.
"""
import os
import sys


def _resolve_submission_root():
    if sys.path and os.path.isfile(os.path.join(sys.path[-1], "main.py")):
        return os.path.abspath(sys.path[-1])
    return os.path.dirname(os.path.abspath(__file__))


_ROOT = _resolve_submission_root()
if sys.path[:1] != [_ROOT]:
    sys.path.insert(0, _ROOT)

from scripts.phase46.feed_priority_portfolio_agent import make_feed_priority_portfolio_agent  # noqa: E402

_feed_priority_portfolio_agent = None


def _new_episode(obs):
    return obs.get("day") == 0 and obs.get("hour") == 0


def agent(obs):
    global _feed_priority_portfolio_agent
    if _feed_priority_portfolio_agent is None or _new_episode(obs):
        _feed_priority_portfolio_agent = make_feed_priority_portfolio_agent()
    return _feed_priority_portfolio_agent(obs)
'''


def main():
    out_path = os.path.join(ROOT, OUT_NAME)
    with tempfile.TemporaryDirectory() as tmpdir:
        main_py_path = os.path.join(tmpdir, "main.py")
        with open(main_py_path, "w") as f:
            f.write(MAIN_PY_CONTENT)

        with tarfile.open(out_path, "w:gz") as tar:
            tar.add(main_py_path, arcname="main.py")
            for rel_path in FILES:
                abs_path = os.path.join(ROOT, rel_path)
                if not os.path.isfile(abs_path):
                    raise FileNotFoundError(f"required submission file missing: {rel_path}")
                tar.add(abs_path, arcname=rel_path)

    size = os.path.getsize(out_path)
    sha256 = hashlib.sha256()
    with open(out_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    print(f"Wrote {out_path} ({size} bytes, {size / 1024:.1f} KB, {len(FILES) + 1} files)")
    print(f"SHA-256: {sha256.hexdigest()}")
    with tarfile.open(out_path, "r:gz") as tar:
        names = sorted(tar.getnames())
    print("\nContents:")
    for n in names:
        print(" ", n)


if __name__ == "__main__":
    main()
