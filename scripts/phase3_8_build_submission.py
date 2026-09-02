"""
Phase 3.8 submission packaging script -- Submission C (animal-specific
scaling response layered on Submission B's frozen stack). Builds the exact
tar.gz Kaggle submission artifact, containing ONLY the files verified to
be necessary for main.py to run standalone (same discipline as Phase 3.5's
scripts/phase3_5_build_submission.py, which built Submission B).

Usage:
    python scripts/phase3_8_build_submission.py

Output:
    kaggriculture_phase3_8_submission_C.tar.gz  (repo root)
"""
import os
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_NAME = "kaggriculture_phase3_8_submission_C.tar.gz"

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
    print(f"Wrote {out_path} ({size} bytes, {size / 1024:.1f} KB, {len(FILES)} files)")
    with tarfile.open(out_path, "r:gz") as tar:
        names = sorted(tar.getnames())
    print("\nContents:")
    for n in names:
        print(" ", n)


if __name__ == "__main__":
    main()
