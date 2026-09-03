"""
Phase 29 submission packaging script -- Submission H (agents/phase21/'s
shared-market-durable portfolio agent, built Phase 21, tuned/fixed through
Phase 28: Phase 22's opening-ratio sweep (WHEAT 0.50/MELON 0.50), Phase 24's
crop-economics fix (STRAWBERRY-favoring day>=8, since it does not actually
glut at these agents' real combined selling pace), Phase 26's live-margin
risk-posture layer, and Phase 27's per-crop/per-tile liquidation timing --
see results/phase28/PHASE28_REMAINING_LOSS_DIAGNOSIS_REPORT.md for
confirmation that no code has changed since Phase 27's validated state (a
Phase 28 fix attempt was reverted after it was found to hurt more games than
it helped).

Promoted on results/phase27/PHASE27_PER_TILE_LIQUIDATION_REPORT.md and
Phase 28's re-confirmation: 9/15 (60.0%) head-to-head win rate against
Submission G (agents/phase15/, this project's previously-strongest live
submission) and 14/15 (93.3%) against Submission C, both on this project's
full development+validation+held-out seed set (n=15,
scripts/phase3_2_configs.py::SEED_SETS) -- the most rigorous validation any
agent in this project has cleared against BOTH prior live submissions
simultaneously.

This is a NEW, SEPARATE submission package. The repo root main.py is NOT
modified by this script and continues to build Submission C/E exactly as
before; the already-shipped kaggriculture_phase18_submission_F.tar.gz
(Submission F) and kaggriculture_phase20_submission_G.tar.gz (Submission G)
are also untouched -- this package's own main.py (written by this script,
embedded below, never the repo root's main.py) is the only entry point that
builds agents.phase21.adapters.portfolio_agent.make_portfolio_agent.

Same discipline as scripts/phase18_build_submission.py (Submission F) and
scripts/phase20_build_submission.py (Submission G): only the files verified
necessary for the package's own main.py to run standalone, dependency
closure traced by direct import reading (see results/phase29/
PHASE29_SUBMISSION_H_PACKAGING_REPORT.md Section 1).

Letter "H": A-G are taken (phase3_4 Variant D "A", phase3_5 competitive_v2
"B", phase3_8 "C", phase7 sell-safety fix "D", phase12 F-005 fix "E",
phase18 macro-controller "F", phase20 macro-controller + liquidity guard
"G") -- confirmed by listing every existing kaggriculture_*.tar.gz in the
repo root before choosing this letter.

Usage:
    python scripts/phase29_build_submission.py

Output:
    kaggriculture_phase29_submission_H.tar.gz  (repo root)
"""
import hashlib
import os
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
OUT_NAME = "kaggriculture_phase29_submission_H.tar.gz"

# Dependency closure for agents/phase21/adapters/portfolio_agent.py, traced by
# direct import reading (not assumed):
#   portfolio_agent.py  -> agents.phase3.opponent_observation
#                        -> agents.phase21.portfolio
#                             -> agents.phase21.execution
#                             -> agents.phase21.liquidation
#                        -> agents.phase21.execution
#                             -> vendor_kaggriculture.kaggriculture
#                             -> agents.phase21.risk_posture (stdlib only)
#                             -> agents.phase21.liquidation
#                             -> agents.phase2_3.common -> vendor_kaggriculture.kaggriculture
# Confirmed directly: agents/phase21/ does NOT import anything from
# agents/phase4/ or agents/phase6/ (those are used only by
# scripts/phase21/realistic_opponent.py and agents/phase21/sell_timing.py --
# neither of which portfolio_agent.py imports) -- so neither ships here.
# agents/phase2_3/ and vendor_kaggriculture/ are namespace packages (no
# __init__.py in either, confirmed directly, same as every prior submission's
# packaging) -- agents/phase3/ DOES have an (empty) __init__.py that must
# still ship for the import machinery to resolve the package.
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
    "agents/phase21/adapters/__init__.py",
    "agents/phase21/adapters/portfolio_agent.py",
]

# The package's OWN main.py -- NOT the repo root's main.py, never written back
# to it. Same root-resolution / Kaggle-loading-compatibility handling as the
# existing main.py and Submissions F/G's own package main.py (read directly
# from scripts/phase18_build_submission.py / scripts/phase20_build_submission.py,
# replicated verbatim, not reinvented).
MAIN_PY_CONTENT = '''"""
Kaggriculture competition submission entry point -- Submission H.

Canonical strategy: agents/phase21/'s macro-controller portfolio agent
(agents/phase21/adapters/portfolio_agent.py::make_portfolio_agent) -- a
clean, from-scratch agent (not built on the Submission C/D/E/F/G lineage)
designed around the shared-market glut mechanic (docs/FRESH_STRATEGY.md
Reframe 1): MELON is time-boxed to the opening only (it crashes hard under
two-producer competition -- confirmed directly through the real engine,
results/phase21/PHASE21_SHARED_MARKET_PORTFOLIO_REPORT.md), STRAWBERRY is
the durable bulk crop from day 8 onward (its own glut curve does not
actually bind at these agents' real combined selling pace -- confirmed by
financial-ledger read, results/phase24/PHASE24_LOSS_DIAGNOSIS_REPORT.md),
WHEAT rounds out the mix, land/hands/animal targets ramp from real
top-ladder replay data, a live-margin risk-posture layer adjusts cash
reserves by whether the game is currently being won or lost (results/
phase26/PHASE26_RISK_POSTURE_REPORT.md), and per-crop/per-tile liquidation
timing (not one fixed day for the whole farm) winds the season down
correctly (results/phase27/PHASE27_PER_TILE_LIQUIDATION_REPORT.md).

Promoted per results/phase27/PHASE27_PER_TILE_LIQUIDATION_REPORT.md and
Phase 28's re-confirmation (results/phase28/
PHASE28_REMAINING_LOSS_DIAGNOSIS_REPORT.md): 9/15 (60.0%) head-to-head win
rate against Submission G (this project's previously-strongest live
submission) and 14/15 (93.3%) against Submission C, both on this project's
full 15-seed development+validation+held-out set.

This file remains a packaging/entry-point wrapper ONLY -- see
agents/phase21/adapters/portfolio_agent.py for the actual architecture. The
root-resolution logic below is UNCHANGED from every prior submission's
main.py (same two verified Kaggle-loader defects it fixes: __file__ is
unavailable under Kaggle's exec()-based loading, and this project's
top-level `agents` package name collides with several unrelated `agents.py`
files bundled inside kaggle_environments itself).

Do not add strategy logic to this file. Any behavioral change belongs in
agents/phase21/'s own modules, or a new, separately-validated phase -- never
here.
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

from agents.phase21.adapters.portfolio_agent import make_portfolio_agent  # noqa: E402

_portfolio_agent = None


def _new_episode(obs):
    return obs.get("day") == 0 and obs.get("hour") == 0


def agent(obs):
    global _portfolio_agent
    if _portfolio_agent is None or _new_episode(obs):
        _portfolio_agent = make_portfolio_agent()
    return _portfolio_agent(obs)
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
