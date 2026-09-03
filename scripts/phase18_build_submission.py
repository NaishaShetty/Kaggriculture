"""
Phase 18 submission packaging script -- Submission F (agents/phase15/'s macro-
controller agent, built Phase 15, refined Phase 16, validated on this project's
full development+validation+held-out seed set (n=15) by Phase 17: 15/15 (100%)
head-to-head win rate against BOTH current live submissions C and E, +79% mean
margin -- see results/phase17/PHASE17_WHEAT_STARVATION_AND_WIDER_SAMPLE_REPORT.md.
Promoted on win-rate evidence per docs/LEADERBOARD_DIAGNOSTIC.md Section 1 (Kaggle's
live score is Elo-style win/loss, not isolated money), a deliberate, explicit
departure from Phase 15/16's money-bar framing made by the project owner directly.

This is a NEW, SEPARATE submission package. The repo root main.py is NOT
modified by this script and continues to build Submission C/E exactly as
before -- this package's own main.py (written by this script, embedded below,
never the repo root's main.py) is the only entry point that builds
agents.phase15.adapters.macro_agent.make_macro_agent instead.

Same discipline as scripts/phase7_build_submission.py (Submission D) and
scripts/phase12_build_submission.py (Submission E): only the files verified
necessary for the package's own main.py to run standalone, no frozen file
touched, dependency closure traced by direct import reading (see
results/phase18/PHASE18_SUBMISSION_F_PACKAGING_REPORT.md Section 1).

Letter "F": A, B, C, D, E are taken (phase3_4 Variant D "Submission A", phase3_5
competitive_v2 "Submission B", phase3_8 "Submission C", phase7 sell-safety fix
"Submission D", phase12 F-005 fix "Submission E") -- confirmed by listing every
existing kaggriculture_*.tar.gz in the repo root before choosing this letter.

Usage:
    python scripts/phase18_build_submission.py

Output:
    kaggriculture_phase18_submission_F.tar.gz  (repo root)
"""
import hashlib
import os
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
OUT_NAME = "kaggriculture_phase18_submission_F.tar.gz"

# Dependency closure for agents/phase15/adapters/macro_agent.py, traced by
# direct import reading (not assumed) -- see the Phase 18 report Section 1
# for the full transitive-import trace this list is built from:
#   macro_agent.py            -> agents.phase3.opponent_observation
#                              -> agents.phase15.macro_controller (no imports of its own)
#                              -> agents.phase15.execution
#                                   -> vendor_kaggriculture.kaggriculture
#                                   -> agents.phase2_3.common -> vendor_kaggriculture.kaggriculture
#                              -> agents.phase15.sell_timing
#                                   -> agents.phase4.market_model -> vendor_kaggriculture.kaggriculture
# agents/phase2_3/ and vendor_kaggriculture/ are namespace packages (no
# __init__.py in either, confirmed directly, same as every prior submission's
# packaging) -- agents/phase3/ and agents/phase4/ DO have (empty) __init__.py
# files that must still ship for the import machinery to resolve the package.
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
    "agents/phase15/adapters/__init__.py",
    "agents/phase15/adapters/macro_agent.py",
]

# The package's OWN main.py -- NOT the repo root's main.py, never written back
# to it. Same root-resolution / Kaggle-loading-compatibility handling as the
# existing main.py (read directly from it, replicated verbatim, not
# reinvented): __file__ is unavailable under Kaggle's exec()-based loading,
# and this project's top-level `agents` package name collides with several
# unrelated `agents.py` files bundled inside kaggle_environments itself.
MAIN_PY_CONTENT = '''"""
Kaggriculture competition submission entry point -- Submission F.

Canonical strategy: the Phase 15 macro-controller agent (agents/phase15/
adapters/macro_agent.py::make_macro_agent) -- a proportional, day-indexed
target ramp for land/hands/animals/crop-tile allocation grounded directly in
4 real opponents' own observed scale (results/phase6/), reusing Phase 11's
bounded multi-crop tile-pool execution and Phase 13's parallel-fetch fix,
with Phase 16's wheat-reserve cost fix applied and its sell-timing layer
disabled by default (measured net negative once re-tested on a wider sample).

Promoted per results/phase17/PHASE17_WHEAT_STARVATION_AND_WIDER_SAMPLE_REPORT.md:
15/15 (100%) head-to-head win rate against both Submission C and Submission E,
+79% mean margin, on this project's full development+validation+held-out seed
set (n=15) -- NOT on the isolated-money bar Phase 15/16 used (mean isolated
final money, ~$43,735, still falls short of that self-set $50,000-80,000+
target). Promoted instead on win-rate evidence, since Kaggle's own live
scoring is Elo-style win/loss, not isolated money (docs/LEADERBOARD_DIAGNOSTIC.md
Section 1) -- a deliberate choice made by the project owner directly, not
assumed by any single phase.

This file remains a packaging/entry-point wrapper ONLY -- see
agents/phase15/adapters/macro_agent.py for the actual architecture. The
root-resolution logic below is UNCHANGED from every prior submission's
main.py (same two verified Kaggle-loader defects it fixes: __file__ is
unavailable under Kaggle's exec()-based loading, and this project's
top-level `agents` package name collides with several unrelated `agents.py`
files bundled inside kaggle_environments itself).

Do not add strategy logic to this file. Any behavioral change belongs in
agents/phase15/'s own modules (all frozen after Phase 15-17's validation),
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
