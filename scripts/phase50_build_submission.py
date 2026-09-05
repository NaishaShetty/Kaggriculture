"""
Phase 50 submission packaging script -- Submission K (Phase 48 Part C's
validated capped-animal-target fix: agents/phase21/'s macro-controller
portfolio, running through Phase 46's FEED-priority execution layer -- the
same as Submission J -- but with the "animals" field of
agents/phase21/portfolio.py::portfolio_targets' own output capped at a
realistic sustainable total instead of the uncapped target rung ladder
reaching 17 by day 11).

CONFIRMED DIRECTLY (this phase's own read of Phase 48's report and source,
not assumed): the recommended candidate's exact module/function chain is
`scripts/phase48/capped_animal_portfolio_agent.py::make_capped_animal_portfolio_agent`,
which composes `scripts/phase48/capped_animal_portfolio.py::make_capped_animal_target_fn`
(cap_total=8, the default, confirmed directly in that module's own source --
grounded in scripts/phase48/animal_ceiling_probe.py's own steady-state
measurement of a real 6-9-animal equilibrium; NOT packaged with any other
value) -- itself wrapping `agents/phase21/portfolio.py::portfolio_targets`
UNMODIFIED, only touching the "animals" field of its output -- with
`scripts/phase46/feed_priority_execution.py::make_feed_priority_execution_agent`
(byte-for-byte the SAME execution layer Submission J already ships,
confirmed unchanged: FEED tier 0.5, Phase 36's BUY_ANIMAL cash pacer, HIRE/
BUY_LAND/BUY_SEED all untouched). `agents/phase21/`'s own files (execution.py,
portfolio.py, liquidation.py, risk_posture.py, adapters/, __init__.py) are
untouched by Phase 48 and remain untouched here, exactly as Phase 46/47 left
them for Submission J.

This is a NEW, SEPARATE submission package. The repo root main.py is NOT
modified by this script and continues to build Submission C/E exactly as
before; every already-shipped kaggriculture_*.tar.gz (Submissions A through
J) is untouched -- this package's own main.py (written by this script,
embedded below, never the repo root's main.py) is the only entry point that
builds scripts.phase48.capped_animal_portfolio_agent.make_capped_animal_portfolio_agent.

Letter "K": A-J are taken (phase3_4 Variant D "A", phase3_5 competitive_v2
"B", phase3_8 "C", phase7 sell-safety fix "D", phase12 F-005 fix "E",
phase18 macro-controller "F", phase20 macro-controller + liquidity guard
"G", phase29 shared-market portfolio agent "H", phase37 cash-pacer "I",
phase47 FEED tier-0.5 fix "J") -- confirmed by listing every existing
kaggriculture_*.tar.gz in the repo root before choosing this letter (see
results/phase50/PHASE50_SUBMISSION_K_PACKAGING_REPORT.md Section 2).

Usage:
    python scripts/phase50_build_submission.py

Output:
    kaggriculture_phase50_submission_K.tar.gz  (repo root)
"""
import hashlib
import os
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
OUT_NAME = "kaggriculture_phase50_submission_K.tar.gz"

# Dependency closure for scripts/phase48/capped_animal_portfolio_agent.py,
# traced by direct import reading (not assumed -- Phase 47's own closure plus
# the two new Phase 48 files):
#   capped_animal_portfolio_agent.py -> agents.phase3.opponent_observation (dataclasses/typing only)
#                                     -> scripts.phase46.feed_priority_execution
#                                          -> vendor_kaggriculture.kaggriculture
#                                          -> agents.phase21.risk_posture (stdlib only)
#                                          -> agents.phase21.liquidation
#                                          -> agents.phase21.execution (bounded_multi_crop_tile_pool_assignment, reused)
#                                          -> agents.phase2_3.common -> vendor_kaggriculture.kaggriculture
#                                     -> scripts.phase48.capped_animal_portfolio
#                                          -> agents.phase21.portfolio
#                                               -> agents.phase21.execution
#                                               -> agents.phase21.liquidation
# Identical closure shape to Phase 47's, plus the two new Phase 48 wrapper
# files. Confirmed directly: does NOT import agents/phase21/adapters/
# portfolio_agent.py (Submission H/I's own entry point), nor
# scripts/phase46/feed_priority_portfolio_agent.py (Submission J's own
# adapter, byte-identical in structure but not itself imported here -- the
# capped-animal adapter reimplements that same thin wiring directly, per
# Phase 48's own source). agents/phase2_3/ and vendor_kaggriculture/ are
# namespace packages (no __init__.py in either, confirmed directly, same as
# every prior submission's packaging); scripts/, scripts/phase46/, and
# scripts/phase48/ are ALSO namespace packages (confirmed: none has an
# __init__.py) -- Python 3's PEP 420 namespace-package resolution needs
# none, provided the directories exist under a sys.path entry. agents/phase3/
# DOES have an (empty) __init__.py that must still ship.
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
    "scripts/phase48/capped_animal_portfolio.py",
    "scripts/phase48/capped_animal_portfolio_agent.py",
]

# The package's OWN main.py -- NOT the repo root's main.py, never written back
# to it. Same root-resolution / Kaggle-loading-compatibility handling as
# every prior submission's package main.py (read directly from
# scripts/phase47_build_submission.py, replicated verbatim, not reinvented).
MAIN_PY_CONTENT = '''"""
Kaggriculture competition submission entry point -- Submission K.

Canonical strategy: agents/phase21/'s macro-controller portfolio agent
(agents/phase21/portfolio.py::portfolio_targets -- UNCHANGED from Submission
I/J: MELON time-boxed to the opening, STRAWBERRY the durable bulk crop from
day 8, WHEAT rounds out the mix, land/hands/crop-tile targets ramped from
real top-ladder replay data, a live-margin risk-posture layer, per-crop/
per-tile liquidation timing), wrapped so ONLY the "animals" field of its
output is capped at a realistic sustainable total (cap_total=8, proportionally
scaling COW:SHEEP to preserve the existing ratio -- Phase 48's own
capped_animal_portfolio.py::make_capped_animal_target_fn) instead of letting
the uncapped rung ladder escalate to 17 by day 11 -- a target this execution
layer's realistic play was never able to sustain anyway (Phase 48's own
steady-state instrumentation found owned-animal count actually EQUILIBRATES
around 6-9 regardless of the 17 target, because purchases and chronic
feed-related escapes roughly balance out well below it). Everything else
(land, hands, crop_tile_target, crop_fractions) passes through byte-for-byte
unchanged. Run through Phase 46's FEED-priority execution layer
(scripts/phase46/feed_priority_execution.py::make_feed_priority_execution_agent)
-- BYTE-IDENTICAL to Submission J's own shipped execution layer, unmodified
by this phase: FEED tasks keep their own priority tier 0.5 (strictly ahead of
WATER's tier 1, never contesting HARVEST/HARVEST_ANIMAL's own tier 0), and
Phase 36's BUY_ANIMAL cash pacer, HIRE, BUY_LAND, BUY_SEED, and the greedy
nearest-worker matching algorithm are all unchanged from Submission J.

Promoted per results/phase48/PHASE48_FERTILIZER_LAND_ANIMAL_TARGET_RETEST_REPORT.md
Section 4: on the full 15-seed development+validation+held-out set, strictly
dominant over Submission J's own shipped baseline -- vs. Submission G, 14/15
->15/15 (mean margin $7,345.47->$14,842.73, +102%, recovering baseline's one
remaining loss); vs. Submission C, 15/15 held (margin $35,483.40->$43,501.13,
+22.6%); vs. the Phase 43 Jonaid archetype, 15/15 held (margin
$27,808.07->$36,256.73, +30.4%) -- zero new losses anywhere in the sample.
Re-confirmed against the packaged artifact itself, not just the in-repo code,
per results/phase50/PHASE50_SUBMISSION_K_PACKAGING_REPORT.md.

This file remains a packaging/entry-point wrapper ONLY -- see
scripts/phase48/capped_animal_portfolio_agent.py for the actual wiring,
scripts/phase48/capped_animal_portfolio.py for the capping wrapper itself,
and agents/phase21/portfolio.py / scripts/phase46/feed_priority_execution.py
for the underlying architecture. The root-resolution logic below is
UNCHANGED from every prior submission's main.py (same two verified Kaggle-
loader defects it fixes: __file__ is unavailable under Kaggle's exec()-based
loading, and this project's top-level `agents` package name collides with
several unrelated `agents.py` files bundled inside kaggle_environments
itself).

Do not add strategy logic to this file. Any behavioral change belongs in
agents/phase21/'s own modules, scripts/phase46/feed_priority_execution.py, or
scripts/phase48/capped_animal_portfolio.py, or a new, separately-validated
phase -- never here.
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

from scripts.phase48.capped_animal_portfolio_agent import make_capped_animal_portfolio_agent  # noqa: E402

_capped_animal_portfolio_agent = None


def _new_episode(obs):
    return obs.get("day") == 0 and obs.get("hour") == 0


def agent(obs):
    global _capped_animal_portfolio_agent
    if _capped_animal_portfolio_agent is None or _new_episode(obs):
        _capped_animal_portfolio_agent = make_capped_animal_portfolio_agent()
    return _capped_animal_portfolio_agent(obs)
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
