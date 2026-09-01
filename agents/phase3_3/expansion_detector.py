"""
Phase 3.3 online expansion-oriented detector. Loads the persisted
per-checkpoint NearestCentroidClassifier artifact (fit on Phase 3.2's
development+validation data ONLY -- see scripts/phase3_3_build_detector.py)
and, given an OpponentObservationLogger.history up to the current turn,
reports whether the observable evidence currently indicates an
`expansion_oriented` opponent, using the SAME feature extractor and
classifier machinery already validated in Phase 3.2 -- no new detection
mechanism was invented for this phase.

Detection activates only once BOTH conditions hold:
  1. the nearest-checkpoint classifier's predicted class is "expansion_oriented"
  2. its confidence (Phase 3.2's margin-based confidence metric) is >= THRESHOLD

THRESHOLD is chosen on DEVELOPMENT DATA ONLY (see
scripts/phase3_3_choose_threshold.py) -- never tuned against held-out
results, per the brief's explicit anti-overfitting instruction.
"""
import json
import os

import numpy as np

from agents.phase3.feature_extractor import extract, WINDOWS

ARTIFACT_PATH = "results/phase3_3/detector/artifact.json"
DEFAULT_THRESHOLD = 0.5  # overridden by scripts/phase3_3_choose_threshold.py's dev-set-selected value, see artifact metadata


class ExpansionDetector:
    def __init__(self, threshold=DEFAULT_THRESHOLD, artifact_path=ARTIFACT_PATH):
        with open(artifact_path) as f:
            self.artifact = json.load(f)
        self.threshold = threshold
        self.checkpoints = sorted(int(k) for k in self.artifact["checkpoints"])

    def _nearest_checkpoint(self, turn):
        eligible = [c for c in self.checkpoints if c <= turn]
        return max(eligible) if eligible else None

    def check(self, history, turn):
        """Returns dict: {active, predicted_class, confidence, checkpoint_used}.
        `history`: OpponentObservationLogger.history up to and including `turn`
        (never anything beyond it -- the caller is responsible for that
        temporal boundary, enforced identically to Phase 3.2's feature
        extractor, which itself clamps to len(history)-1)."""
        cp = self._nearest_checkpoint(turn)
        if cp is None:
            return {"active": False, "predicted_class": None, "confidence": 0.0, "checkpoint_used": None}

        cp_data = self.artifact["checkpoints"][str(cp)]
        idx = len(history) - 1
        feats = extract(history, idx, WINDOWS)
        feature_names = cp_data["feature_names"]
        x = np.array([[feats.get(k, 0.0) for k in feature_names]], dtype=float)

        mean = np.array(cp_data["mean"])
        std = np.array(cp_data["std"])
        centroids = np.array(cp_data["centroids"])
        classes = cp_data["classes"]

        xz = (x - mean) / std
        dists = np.linalg.norm(xz[:, None, :] - centroids[None, :, :], axis=2)[0]
        order = np.argsort(dists)
        best_class = classes[order[0]]
        best, second = dists[order[0]], dists[order[1]] if len(order) > 1 else dists[order[0]] + 1e-9
        confidence = max(0.0, min(1.0, 1 - (best / (second + 1e-9))))

        active = (best_class == "expansion_oriented") and (confidence >= self.threshold)
        return {"active": active, "predicted_class": best_class, "confidence": round(float(confidence), 4),
                "checkpoint_used": cp}
