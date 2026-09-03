"""
Phase 12 submission packaging script -- Submission E (Submission D's exact
frozen stack -- Planner v1 with the Phase 7 sell-safety fix already baked
into agents/phase2_6/common.py, plus Submission C's Phase 3.8 animal
response -- with ONE addition: agents/phase3_7/f005_liquidity_guard.py's
widened early cash-trajectory guard, wired in as a new layer 4 in
agents/phase3_8/adapters/competitive_v3_agent.py. See
results/phase12/PHASE12_F005_LIQUIDITY_GUARD_FIX_REPORT.md for the full
diagnosis and validation record. Same discipline as
scripts/phase7_build_submission.py: only the files verified necessary for
main.py to run standalone.

Usage:
    python scripts/phase12_build_submission.py

Output:
    kaggriculture_phase12_submission_E.tar.gz  (repo root)
"""
import hashlib
import os
import tarfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
OUT_NAME = "kaggriculture_phase12_submission_E.tar.gz"

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
    "agents/phase2_5/common.py",
    "agents/phase2_6/__init__.py",
    "agents/phase2_6/common.py",
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
    "agents/phase3_7/__init__.py",
    "agents/phase3_7/f005_liquidity_guard.py",  # NEW vs. Submission D: the Phase 12 fix
    "agents/phase3_8/__init__.py",
    "agents/phase3_8/animal_response.py",
    "agents/phase3_8/adapters/__init__.py",
    "agents/phase3_8/adapters/competitive_v3_agent.py",  # CHANGED vs. Submission D: new layer 4
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
