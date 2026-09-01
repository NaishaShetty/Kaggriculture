"""
Phase 3.3 threshold selection -- DEVELOPMENT SEEDS ONLY (brief section 6:
"Development set used for... threshold selection"). Never touches
validation or held_out data. Evaluates candidate thresholds against the
persisted per-checkpoint detector artifact and picks the smallest threshold
that produces ZERO false positives (activating on a non-expansion_oriented
opponent) on development data, breaking ties toward earlier mean detection
turn. This is a simple, interpretable, pre-registered selection rule -- not
optimized post-hoc against any later result.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3.opponent_observation import OpponentObservation
from agents.phase3_3.expansion_detector import ExpansionDetector
from scripts.phase3_2_configs import SEED_SETS, ARCHETYPES, CHECKPOINTS

FEATURES_ROOT = "results/phase3_2/features"
CANDIDATE_THRESHOLDS = [0.3, 0.5, 0.7, 0.9]


def load_dev_features(archetype, seed):
    path = os.path.join(FEATURES_ROOT, f"{archetype}_seed{seed}.json")
    with open(path) as f:
        return json.load(f)["features_by_checkpoint"]


def fake_history_from_features_at_checkpoint(features_at_cp):
    """The detector's .check() needs an OpponentObservation-like `history`
    ending in a snapshot whose features match `features_at_cp` -- since
    Phase 3.2 already extracted these features from a real history, we
    reconstruct a length-1 stand-in history is NOT possible (windowed
    features need real history). Instead, evaluate the detector directly
    against the precomputed feature dict via a small internal helper that
    mirrors ExpansionDetector.check()'s math but skips re-extraction --
    avoids needing to replay full episodes again for a threshold sweep."""
    return features_at_cp


def evaluate_threshold(threshold):
    detector = ExpansionDetector(threshold=threshold)
    false_positives = 0
    true_positives = 0
    detection_turns = []
    total_non_expansion = 0
    total_expansion = 0

    for archetype in ARCHETYPES:
        for seed in SEED_SETS["development"]:
            feats_by_cp = load_dev_features(archetype, seed)
            detected_this_episode = False
            first_detect_turn = None
            for cp in CHECKPOINTS:
                feats = feats_by_cp.get(str(cp))
                if not feats:
                    continue
                cp_data = detector.artifact["checkpoints"].get(str(cp))
                if not cp_data:
                    continue
                import numpy as np
                feature_names = cp_data["feature_names"]
                x = np.array([[feats.get(k, 0.0) for k in feature_names]], dtype=float)
                mean, std = np.array(cp_data["mean"]), np.array(cp_data["std"])
                centroids = np.array(cp_data["centroids"])
                classes = cp_data["classes"]
                xz = (x - mean) / std
                dists = np.linalg.norm(xz[:, None, :] - centroids[None, :, :], axis=2)[0]
                order = np.argsort(dists)
                best_class = classes[order[0]]
                best, second = dists[order[0]], dists[order[1]] if len(order) > 1 else dists[order[0]] + 1e-9
                confidence = max(0.0, min(1.0, 1 - (best / (second + 1e-9))))
                if best_class == "expansion_oriented" and confidence >= threshold and not detected_this_episode:
                    detected_this_episode = True
                    first_detect_turn = cp

            if archetype == "expansion_oriented":
                total_expansion += 1
                if detected_this_episode:
                    true_positives += 1
                    detection_turns.append(first_detect_turn)
            else:
                total_non_expansion += 1
                if detected_this_episode:
                    false_positives += 1

    return {
        "threshold": threshold, "true_positives": true_positives, "total_expansion_episodes": total_expansion,
        "false_positives": false_positives, "total_non_expansion_episodes": total_non_expansion,
        "mean_detection_turn": sum(detection_turns) / len(detection_turns) if detection_turns else None,
    }


def main():
    results = [evaluate_threshold(t) for t in CANDIDATE_THRESHOLDS]
    for r in results:
        print(r)

    zero_fp = [r for r in results if r["false_positives"] == 0 and r["true_positives"] == r["total_expansion_episodes"]]
    if zero_fp:
        chosen = min(zero_fp, key=lambda r: r["threshold"])
    else:
        chosen = min(results, key=lambda r: (r["false_positives"], -r["true_positives"]))

    out = {"candidate_results": results, "chosen_threshold": chosen["threshold"],
           "selection_rule": "smallest threshold with zero false positives AND 100% true-positive rate "
                              "on DEVELOPMENT seeds only; never evaluated against validation/held_out data",
           "chosen_result": chosen}
    with open("results/phase3_3/detector/threshold_selection.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nChosen threshold: {chosen['threshold']} (mean detection turn: {chosen['mean_detection_turn']})")


if __name__ == "__main__":
    main()
