"""
Phase 7 submission packaging script -- Submission D (Submission C's exact
frozen stack, with ONE change: agents/phase2_6/common.py now imports
`make_agent` from agents.phase2_5.common instead of agents.phase2_4.common,
restoring the already-designed, already-tested horizon_aware sell-safety
net that was previously set but never wired in -- see
results/phase7/PHASE7_SELL_SAFETY_FIX_REPORT.md for the full diagnosis and
validation). Same discipline as scripts/phase3_8_build_submission.py (which
built Submission C): only the files verified necessary for main.py to run
standalone.

The letter "D" is used because Phase 4 explored a candidate under that name
and explicitly rejected it without ever packaging a submission (see
results/phase4's own report) -- the letter was never consumed. This is an
unrelated, much narrower change (a one-import bug fix, not a new
architecture) that happens to be the next submission in sequence.

Usage:
    python scripts/phase7_build_submission.py

Output:
    kaggriculture_phase7_submission_D.tar.gz  (repo root)
"""
import hashlib
import os
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_NAME = "kaggriculture_phase7_submission_D.tar.gz"

FILES = [
    "main.py",
    "results/phase3_3/detector/artifact.json",
    "vendor_kaggriculture/kaggriculture.py",
    "vendor_kaggriculture/kaggriculture.json",
    "economic_model/model.py",
    "agents/__init__.py",
    "agents/phase2_2/common.py",
    "agents/phase2_3/common.py",
    "agents/phase2_4/common.py",
    "agents/phase2_5/common.py",  # NEW vs. Submission C's file list: the fix's target module
    "agents/phase2_6/__init__.py",
    "agents/phase2_6/common.py",  # CHANGED vs. Submission C: one import line (Phase 7 fix)
    "agents/phase2_6/state.py",
    "agents/phase2_6/opportunities.py",
    "agents/phase2_6/evaluator.py",
    "agents/phase2_6/constraints.py",
    "agents/phase2_6/decisions.py",
    "agents/phase2_6/trace.py",
    "agents/phase3/__init__.py",
    "agents/phase3/opponent_observation.py",
    "agents/phase3/feature_extractor.py",
    "agents/phase3_3/__init__.py",
    "agents/phase3_3/expansion_detector.py",
    "agents/phase3_3/interventions.py",
    "agents/phase3_3/adapters/__init__.py",
    "agents/phase3_3/adapters/intervention_agent.py",
    "agents/phase3_5/__init__.py",
    "agents/phase3_5/opponent_scaling_detector.py",
    "agents/phase3_5/response_policy.py",
    "agents/phase3_5/adapters/__init__.py",
    "agents/phase3_5/adapters/competitive_v2_agent.py",
    "agents/phase3_8/__init__.py",
    "agents/phase3_8/animal_response.py",
    "agents/phase3_8/adapters/__init__.py",
    "agents/phase3_8/adapters/competitive_v3_agent.py",
]


def main():
    out_path = os.path.join(ROOT, OUT_NAME)
    with tarfile.open(out_path, "w:gz") as tar:
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
    print(f"Wrote {out_path} ({size} bytes, {size / 1024:.1f} KB, {len(FILES)} files)")
    print(f"SHA-256: {sha256.hexdigest()}")
    with tarfile.open(out_path, "r:gz") as tar:
        names = sorted(tar.getnames())
    print("\nContents:")
    for n in names:
        print(" ", n)


if __name__ == "__main__":
    main()
