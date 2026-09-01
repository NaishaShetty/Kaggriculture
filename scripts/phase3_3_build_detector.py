"""
Phase 3.3 detector artifact builder. Fits the SAME NearestCentroidClassifier
machinery already used and validated in Phase 3.2
(agents/phase3/regime_classifier.py), at every Phase 3.2 checkpoint, on
Phase 3.2's development+validation feature data ONLY (the exact same split
Phase 3.2 itself used for training in its early-detection experiment --
never touches held_out data, and never touches any Phase 3.3 seed data
either, since none has been collected yet at this point in the phase).

Persists (mean, std, centroids, classes, feature_names) per checkpoint to
results/phase3_3/detector/artifact.json so an ONLINE agent can load a fitted
classifier without re-fitting at runtime (and without adding any new
dependency -- plain JSON, numpy arrays as lists).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from agents.phase3.regime_classifier import NearestCentroidClassifier
from scripts.phase3_2_configs import CHECKPOINTS
from scripts.phase3_2_analyze import load_metadata, build_dataset

OUT_PATH = "results/phase3_3/detector/artifact.json"


def main():
    rows = load_metadata()  # results/phase3_2/experiments/episode_metadata.csv
    artifact = {"trained_on": "phase3_2 development+validation seeds only", "checkpoints": {}}

    for cp in CHECKPOINTS:
        X, y, feat_names = build_dataset(rows, cp, {"development", "validation"})
        if len(X) == 0 or len(set(y)) < 2:
            continue
        clf = NearestCentroidClassifier().fit(X, y, feat_names)
        artifact["checkpoints"][str(cp)] = {
            "classes": clf.classes_, "feature_names": clf.feature_names_,
            "mean": clf.mean_.tolist(), "std": clf.std_.tolist(),
            "centroids": clf.centroids_.tolist(),
            "n_train_samples": len(X),
        }
        print(f"checkpoint {cp}: fit on {len(X)} samples, {len(clf.classes_)} classes")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
