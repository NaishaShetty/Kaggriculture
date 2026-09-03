"""
Phase 20 submission packaging script -- Submission G (Phase 19's ladder-
recalibrated macro-controller agent + Phase 20's liquidity guard: a per-turn,
re-armable hiring/land-purchase throttle plus a pre-emptive land-purchase
cash-reserve check, both in agents/phase15/liquidity_guard.py, closing the
head-to-head win-rate regression Phase 19's recalibration caused (100% -> 53.3%)
while keeping nearly all of its isolated-money gain -- see
results/phase20/PHASE20_LIQUIDITY_GUARD_REPORT.md for the full diagnosis and
validation record. Same discipline as scripts/phase18_build_submission.py
(Submission F): only the files verified necessary for the package's own
main.py to run standalone.

This is a NEW, SEPARATE submission package. The repo root main.py is NOT
modified by this script and continues to build Submission C/E exactly as
before; the already-shipped kaggriculture_phase18_submission_F.tar.gz
(Submission F) is also untouched -- this package's own main.py (written by
this script, embedded below) is the only entry point that builds Phase 20's
current agents.phase15.adapters.macro_agent.make_macro_agent.

Letter "G": A-F are taken (phase3_4 Variant D "A", phase3_5 competitive_v2
"B", phase3_8 "C", phase7 sell-safety fix "D", phase12 F-005 fix "E", phase18
macro-controller "F") -- confirmed by listing every existing
kaggriculture_*.tar.gz in the repo root before choosing this letter.

Usage:
    python scripts/phase20_build_submission.py

Output:
    kaggriculture_phase20_submission_G.tar.gz  (repo root)
"""
import hashlib
import os
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
OUT_NAME = "kaggriculture_phase20_submission_G.tar.gz"

# Dependency closure for agents/phase15/adapters/macro_agent.py, traced by
# direct import reading (unchanged from Phase 18's own trace, plus the two
# new self-contained modules -- agents/phase15/endgame.py and
# agents/phase15/liquidity_guard.py -- neither of which imports anything
# outside the Python standard library):
#   macro_agent.py            -> agents.phase3.opponent_observation
#                              -> agents.phase15.macro_controller (no imports of its own)
#                              -> agents.phase15.execution
#                                   -> vendor_kaggriculture.kaggriculture
#                                   -> agents.phase2_3.common -> vendor_kaggriculture.kaggriculture
#                                   -> agents.phase15.endgame (stdlib only)
#                                   -> agents.phase15.liquidity_guard (stdlib only)
#                              -> agents.phase15.sell_timing
#                                   -> agents.phase4.market_model -> vendor_kaggriculture.kaggriculture
FILES = [
    "vendor_kaggriculture/kaggriculture.py",
    "vendor_kaggriculture/kaggriculture.json",
    "agents/__init__.py",
    "agents/phase2_3/common.py",
    "agents/phase3/__init__.py",
    "agents/phase3/opponent_observation.py",
    "agents/phase4/__init__.py",
    "agents/phase4/market_model.py",
    "agents/phase15/__init__.py",
    "agents/phase15/macro_controller.py",
    "agents/phase15/execution.py",
    "agents/phase15/sell_timing.py",
    "agents/phase15/endgame.py",
    "agents/phase15/liquidity_guard.py",
    "agents/phase15/adapters/__init__.py",
    "agents/phase15/adapters/macro_agent.py",
]

# The package's OWN main.py -- NOT the repo root's main.py, never written back
# to it. Same root-resolution / Kaggle-loading-compatibility handling as the
# existing main.py and Submission F's own package main.py (read directly,
# replicated verbatim, not reinvented).
MAIN_PY_CONTENT = '''"""
Kaggriculture competition submission entry point -- Submission G.

Canonical strategy: the Phase 15 macro-controller agent (agents/phase15/
adapters/macro_agent.py::make_macro_agent), as of Phase 20 --
  + Phase 19's ladder recalibration (land target 3, hands target 11, animal
    range 12-17, crop-tile ceiling 62, a MELON-start/STRAWBERRY-mid/WHEAT-late
    crop schedule, and an explicit endgame-liquidation mechanic --
    agents/phase15/endgame.py), grounded in fresh top-ladder replay data
    (results/phase19/fresh_ladder/).
  + Phase 20's liquidity guard (agents/phase15/liquidity_guard.py): a
    per-turn, re-armable hiring/land-purchase throttle once cash drops below
    $300, plus a pre-emptive reserve check before any land purchase -- closes
    the head-to-head win-rate regression Phase 19's recalibration alone
    caused (100% -> 53.3% against Submission C/E) while keeping nearly all of
    its isolated-money gain.

Promoted per results/phase20/PHASE20_LIQUIDITY_GUARD_REPORT.md: mean isolated
final money $56,664.93 (14/15 of this project's development+validation+
held-out seed set clear $50,000) AND a 13/15 (86.7%) head-to-head win rate
against both Submission C and Submission E, recovered from Phase 19's 53.3%
-- both bars this project set for itself are cleared together, not one
traded for the other.

This file remains a packaging/entry-point wrapper ONLY -- see
agents/phase15/adapters/macro_agent.py for the actual architecture. The
root-resolution logic below is UNCHANGED from every prior submission's
main.py (same two verified Kaggle-loader defects it fixes: __file__ is
unavailable under Kaggle's exec()-based loading, and this project's
top-level `agents` package name collides with several unrelated `agents.py`
files bundled inside kaggle_environments itself).

Do not add strategy logic to this file. Any behavioral change belongs in
agents/phase15/'s own modules, or a new, separately-validated phase -- never
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

from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402

_macro_agent = None


def _new_episode(obs):
    return obs.get("day") == 0 and obs.get("hour") == 0


def agent(obs):
    global _macro_agent
    if _macro_agent is None or _new_episode(obs):
        _macro_agent = make_macro_agent()
    return _macro_agent(obs)
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
