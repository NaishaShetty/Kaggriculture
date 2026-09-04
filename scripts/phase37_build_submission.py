"""
Phase 37 submission packaging script -- Submission I (agents/phase21/'s
portfolio agent, UNCHANGED targets, running through Phase 36's validated
cash-flow-adaptive purchase pacer instead of agents/phase21/execution.py's
own unpaced BUY_ANIMAL logic).

Phase 36 (results/phase36/PHASE36_ADAPTIVE_PACING_REPORT.md) found that
agents/phase21/execution.py's BUY_ANIMAL purchases held back NO cash reserve
at all -- Phase 35 had already traced this as the mechanism behind its own
rebalance candidates' collapse. Phase 36 built a fix
(scripts/phase36/paced_execution.py::make_paced_execution_agent) that gates
BUY_ANIMAL against a reserve (posture-aware land_purchase_reserve + 2 days'
feed buffer per owned animal, grounded directly in the vendor engine's own
"2 consecutive unfed days -> animal escapes" mechanic), leaving HIRE and
BUY_LAND untouched (an earlier, more aggressive version that also paced HIRE
was found, by direct trace, to cause a self-defeating feedback loop -- see
that phase's own report Section 3) -- and validated it, on the SAME targets
Submission H already ships (3 land / 11 hands / 58 crop tiles / current
animal ratio, agents/phase21/portfolio.py::portfolio_targets unmodified):
10/15 (66.7%) vs. Submission G (up from Submission H's shipped 9/15) and
15/15 (100%) vs. Submission C (up from 14/15), on this project's full
15-seed development+validation+held-out set.

CONFIRMED DIRECTLY (this phase's own Step 1, not assumed): agents/phase21/'s
own files (execution.py, portfolio.py, liquidation.py, risk_posture.py,
adapters/portfolio_agent.py, __init__.py) are BYTE-IDENTICAL to Submission
H's packaged state -- Phase 36's fix was built and validated entirely as new,
separate code (scripts/phase36/paced_execution.py), never merged back into
agents/phase21/ itself. Per this phase's own explicit constraint ("do not
modify agents/phase21/'s own files in this phase"), that fix is packaged
here EXACTLY where Phase 36 left it (scripts/phase36/paced_execution.py,
shipped unchanged, not copied or rewritten into agents/phase21/), wired to
agents/phase21/portfolio.py's own unmodified targets via a new, additive-only
adapter (scripts/phase37/paced_portfolio_agent.py) that mirrors
agents/phase21/adapters/portfolio_agent.py's own structure exactly (see
results/phase37/PHASE37_SUBMISSION_I_PACKAGING_REPORT.md Section 1-2 for the
full direct-read confirmation and dependency-closure trace).

This is a NEW, SEPARATE submission package. The repo root main.py is NOT
modified by this script and continues to build Submission C/E exactly as
before; every already-shipped kaggriculture_*.tar.gz (Submissions A through
H) is untouched -- this package's own main.py (written by this script,
embedded below, never the repo root's main.py) is the only entry point that
builds scripts.phase37.paced_portfolio_agent.make_paced_portfolio_agent.

Letter "I": A-H are taken (phase3_4 Variant D "A", phase3_5 competitive_v2
"B", phase3_8 "C", phase7 sell-safety fix "D", phase12 F-005 fix "E", phase18
macro-controller "F", phase20 macro-controller + liquidity guard "G", phase29
shared-market portfolio agent "H") -- confirmed by listing every existing
kaggriculture_*.tar.gz in the repo root before choosing this letter.

Usage:
    python scripts/phase37_build_submission.py

Output:
    kaggriculture_phase37_submission_I.tar.gz  (repo root)
"""
import hashlib
import os
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
OUT_NAME = "kaggriculture_phase37_submission_I.tar.gz"

# Dependency closure for scripts/phase37/paced_portfolio_agent.py, traced by
# direct import reading (not assumed -- see the Phase 37 report Section 2):
#   paced_portfolio_agent.py -> agents.phase3.opponent_observation (dataclasses/typing only)
#                             -> agents.phase21.portfolio
#                                  -> agents.phase21.execution
#                                  -> agents.phase21.liquidation
#                             -> scripts.phase36.paced_execution
#                                  -> vendor_kaggriculture.kaggriculture
#                                  -> agents.phase21.risk_posture (stdlib only)
#                                  -> agents.phase21.liquidation
#                                  -> agents.phase21.execution (bounded_multi_crop_tile_pool_assignment, reused)
#                                  -> agents.phase2_3.common -> vendor_kaggriculture.kaggriculture
# Confirmed directly: does NOT import agents/phase21/adapters/portfolio_agent.py
# (Submission H's own entry point) at all -- the paced adapter is a separate,
# parallel entry point. agents/phase2_3/ and vendor_kaggriculture/ are
# namespace packages (no __init__.py in either, confirmed directly, same as
# every prior submission's packaging); scripts/, scripts/phase36/, and
# scripts/phase37/ are ALSO namespace packages (confirmed: none of the three
# has an __init__.py either, and Python 3's PEP 420 namespace-package
# resolution needs none, provided the directories exist under a sys.path
# entry -- the same mechanism agents/phase2_3/ and vendor_kaggriculture/
# already rely on in every prior submission). agents/phase3/ DOES have an
# (empty) __init__.py that must still ship for that package to resolve.
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
    "scripts/phase36/paced_execution.py",
    "scripts/phase37/paced_portfolio_agent.py",
]

# The package's OWN main.py -- NOT the repo root's main.py, never written back
# to it. Same root-resolution / Kaggle-loading-compatibility handling as
# every prior submission's package main.py (read directly from
# scripts/phase29_build_submission.py, replicated verbatim, not reinvented).
MAIN_PY_CONTENT = '''"""
Kaggriculture competition submission entry point -- Submission I.

Canonical strategy: agents/phase21/'s macro-controller portfolio agent
(agents/phase21/portfolio.py::portfolio_targets -- UNCHANGED from Submission
H: MELON time-boxed to the opening, STRAWBERRY the durable bulk crop from
day 8, WHEAT rounds out the mix, land/hands/animal targets ramped from real
top-ladder replay data, a live-margin risk-posture layer, per-crop/per-tile
liquidation timing), run through Phase 36's cash-flow-adaptive purchase
pacer (scripts/phase36/paced_execution.py::make_paced_execution_agent)
instead of Submission H's own unpaced execution layer: BUY_ANIMAL purchases
now hold back a cash reserve (posture-aware land-purchase reserve + 2 days'
feed cost per owned animal, grounded in the vendor engine's own
"2-consecutive-unfed-days" animal-escape mechanic) before firing, instead of
spending every affordable dollar in one lump sum the instant an animal
becomes affordable. HIRE and BUY_LAND are unchanged from Submission H.

Promoted per results/phase36/PHASE36_ADAPTIVE_PACING_REPORT.md: 10/15
(66.7%) head-to-head win rate against Submission G (up from Submission H's
own shipped 9/15) and 15/15 (100%) against Submission C (up from 14/15),
both on this project's full 15-seed development+validation+held-out set --
re-confirmed against the packaged artifact itself, not just the in-repo
code, per results/phase37/PHASE37_SUBMISSION_I_PACKAGING_REPORT.md.

This file remains a packaging/entry-point wrapper ONLY -- see
scripts/phase37/paced_portfolio_agent.py for the actual wiring and
agents/phase21/portfolio.py / scripts/phase36/paced_execution.py for the
architecture. The root-resolution logic below is UNCHANGED from every prior
submission's main.py (same two verified Kaggle-loader defects it fixes:
__file__ is unavailable under Kaggle's exec()-based loading, and this
project's top-level `agents` package name collides with several unrelated
`agents.py` files bundled inside kaggle_environments itself).

Do not add strategy logic to this file. Any behavioral change belongs in
agents/phase21/'s own modules or scripts/phase36/paced_execution.py, or a
new, separately-validated phase -- never here.
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

from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402

_paced_portfolio_agent = None


def _new_episode(obs):
    return obs.get("day") == 0 and obs.get("hour") == 0


def agent(obs):
    global _paced_portfolio_agent
    if _paced_portfolio_agent is None or _new_episode(obs):
        _paced_portfolio_agent = make_paced_portfolio_agent()
    return _paced_portfolio_agent(obs)
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
