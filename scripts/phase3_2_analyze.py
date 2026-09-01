"""
Phase 3.2 analysis: consumes results/phase3_2/{features,experiments,
economic_analysis,market_analysis} produced by phase3_2_run_experiments.py
and produces:
  - Question A (economic distinctiveness): per-archetype economic trajectory
    stats (brief section 9).
  - Question B (observability/inferability): per-checkpoint classification
    accuracy using development+validation as TRAIN, held_out as TEST
    (brief section 8/13) -- both the supervised NearestCentroidClassifier
    and the unsupervised simple_kmeans (brief section 11).
  - Market-effect analysis (brief section 10) -- correlational only,
    explicitly labeled as such.
  - The final machine-readable phase3_2_summary.json (brief section 15).
Never mixes seed sets: TRAIN = development+validation, TEST = held_out,
used exactly once.
"""
import csv
import json
import os
import sys
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from agents.phase3.regime_classifier import (
    NearestCentroidClassifier, confusion_matrix, accuracy, balanced_accuracy,
    simple_kmeans, cluster_to_label_accuracy,
)
from scripts.phase3_2_configs import CHECKPOINTS, ARCHETYPES

ROOT = "results/phase3_2"


def load_metadata():
    rows = []
    with open(os.path.join(ROOT, "experiments", "episode_metadata.csv"), newline="") as f:
        for r in csv.DictReader(f):
            for k in ("seed", "protagonist_final_money", "opponent_final_money", "margin", "win", "n_transition_events"):
                r[k] = float(r[k]) if r[k] not in (None, "") else None
            rows.append(r)
    return rows


def load_features(archetype, seed):
    path = os.path.join(ROOT, "features", f"{archetype}_seed{int(seed)}.json")
    with open(path) as f:
        return json.load(f)["features_by_checkpoint"]


def economic_distinctiveness(rows):
    """Question A: does each regime produce a measurably different economic
    trajectory? Reports per-archetype stats on PROTAGONIST outcomes (the
    frozen Planner v1's own economic result when facing that archetype) --
    this measures whether facing different archetypes produces different
    protagonist trajectories, i.e. whether the regime has real economic
    consequence for the opponent it plays against."""
    out = {}
    for archetype in ARCHETYPES:
        subset = [r for r in rows if r["archetype"] == archetype]
        if not subset:
            continue
        moneys = [r["protagonist_final_money"] for r in subset]
        opp_moneys = [r["opponent_final_money"] for r in subset]
        margins = [r["margin"] for r in subset]
        out[archetype] = {
            "n_episodes": len(subset),
            "protagonist_money_mean": round(statistics.mean(moneys), 2),
            "protagonist_money_stdev": round(statistics.pstdev(moneys), 2) if len(moneys) > 1 else 0.0,
            "opponent_money_mean": round(statistics.mean(opp_moneys), 2),
            "margin_mean": round(statistics.mean(margins), 2),
            "win_rate": round(sum(r["win"] for r in subset) / len(subset), 3),
        }
    return out


def effect_size(a, b):
    """Cohen's d, pooled stdev -- a simple, interpretable effect size."""
    if len(a) < 2 or len(b) < 2:
        return None
    pooled_std = ((statistics.pstdev(a) ** 2 + statistics.pstdev(b) ** 2) / 2) ** 0.5
    if pooled_std == 0:
        return None
    return round((statistics.mean(a) - statistics.mean(b)) / pooled_std, 3)


def between_regime_separation(rows):
    """Question: which features differ between archetypes and the passive
    control, at the LAST checkpoint (600 turns, most information available)?
    Cohen's d per feature per archetype-vs-passive pair."""
    passive_rows = [r for r in rows if r["archetype"] == "passive"]
    passive_feats = [load_features(r["archetype"], r["seed"]).get("600", {}) for r in passive_rows]
    passive_feats = [f for f in passive_feats if f]

    out = {}
    for archetype in ARCHETYPES:
        if archetype == "passive":
            continue
        arch_rows = [r for r in rows if r["archetype"] == archetype]
        arch_feats = [load_features(r["archetype"], r["seed"]).get("600", {}) for r in arch_rows]
        arch_feats = [f for f in arch_feats if f]
        if not arch_feats or not passive_feats:
            continue
        common_keys = set(arch_feats[0]) & set(passive_feats[0])
        effects = {}
        for key in common_keys:
            a = [f[key] for f in arch_feats if key in f]
            b = [f[key] for f in passive_feats if key in f]
            d = effect_size(a, b)
            if d is not None:
                effects[key] = d
        top = sorted(effects.items(), key=lambda kv: -abs(kv[1]))[:8]
        out[archetype] = {"top_distinguishing_features_vs_passive": top}
    return out


def build_dataset(rows, checkpoint, seed_sets):
    """Returns (X, y, feature_names) for episodes in the given seed_sets at `checkpoint`."""
    X, y = [], []
    feature_names = None
    for r in rows:
        if r["seed_set"] not in seed_sets:
            continue
        feats = load_features(r["archetype"], r["seed"]).get(str(checkpoint))
        if not feats:
            continue
        if feature_names is None:
            feature_names = sorted(feats.keys())
        X.append([feats.get(k, 0.0) for k in feature_names])
        y.append(r["archetype"])
    return np.array(X, dtype=float), y, feature_names or []


def early_detection_experiment(rows):
    """Brief section 8: train on development+validation, evaluate on
    held_out, at every checkpoint -- report accuracy/balanced accuracy/
    confusion matrix per checkpoint."""
    results = {}
    for cp in CHECKPOINTS:
        X_train, y_train, feat_names = build_dataset(rows, cp, {"development", "validation"})
        X_test, y_test, _ = build_dataset(rows, cp, {"held_out"})
        if len(X_train) == 0 or len(X_test) == 0 or len(set(y_train)) < 2:
            results[cp] = {"status": "insufficient_data"}
            continue
        clf = NearestCentroidClassifier().fit(X_train, y_train, feat_names)
        preds, confidences = clf.predict(X_test)
        classes = sorted(set(y_train) | set(y_test))
        results[cp] = {
            "n_train": len(X_train), "n_test": len(X_test),
            "accuracy": round(accuracy(y_test, preds), 3),
            "balanced_accuracy": round(balanced_accuracy(y_test, preds, classes), 3),
            "mean_confidence": round(statistics.mean(confidences), 3),
            "confusion_matrix": confusion_matrix(y_test, preds, classes),
            "classes": classes,
            "top_features": clf.feature_importance()[:5],
        }
    return results


def unsupervised_regime_discovery(rows):
    """Brief section 11: clustering with NO label access at all during
    clustering -- labels used only for post-hoc alignment accuracy."""
    results = {}
    for cp in (24, 120, 360, 600):
        X, y, feat_names = build_dataset(rows, cp, {"development", "validation", "held_out"})
        if len(X) == 0 or len(set(y)) < 2:
            results[cp] = {"status": "insufficient_data"}
            continue
        assignments, _ = simple_kmeans(X, k=len(ARCHETYPES), seed=42)
        acc, cluster_to_label, preds = cluster_to_label_accuracy(assignments, y)
        results[cp] = {"n_samples": len(X), "post_hoc_alignment_accuracy": round(acc, 3),
                        "cluster_to_majority_label": cluster_to_label}
    return results


def market_effect_analysis(rows):
    """Brief section 10: CORRELATIONAL ONLY. Compares protagonist revenue
    against archetype identity -- flags this explicitly as correlational,
    not causal, per the brief's requirement."""
    out = {}
    for archetype in ARCHETYPES:
        subset = [r for r in rows if r["archetype"] == archetype]
        if not subset:
            continue
        econ_files = [os.path.join(ROOT, "economic_analysis", f"{archetype}_seed{int(r['seed'])}_econ.json")
                      for r in subset]
        revenues = []
        for path in econ_files:
            if os.path.exists(path):
                with open(path) as f:
                    revenues.append(json.load(f)["total_revenue"])
        if revenues:
            out[archetype] = {"protagonist_mean_revenue": round(statistics.mean(revenues), 2),
                               "classification": "correlated", "n": len(revenues)}
    out["_classification_note"] = ("All figures above are CORRELATIONAL (regime identity vs. protagonist "
                                    "revenue in the SAME episode) -- no causal mechanism was tested "
                                    "(e.g. an intervention holding the archetype's production constant "
                                    "while varying only its selling behavior). Do not read a revenue "
                                    "difference here as proof the archetype's market activity CAUSED it.")
    return out


def main():
    rows = load_metadata()
    print(f"Loaded {len(rows)} episode metadata rows.")

    econ = economic_distinctiveness(rows)
    separation = between_regime_separation(rows)
    detection = early_detection_experiment(rows)
    clustering = unsupervised_regime_discovery(rows)
    market = market_effect_analysis(rows)

    out = {
        "n_episodes": len(rows), "economic_distinctiveness": econ,
        "between_regime_separation_vs_passive": separation,
        "early_detection_by_checkpoint": detection,
        "unsupervised_clustering": clustering,
        "market_effect_analysis": market,
    }
    with open(os.path.join(ROOT, "tables", "phase3_2_analysis.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)

    print("\nEconomic distinctiveness (protagonist outcome by opponent archetype):")
    for a, v in econ.items():
        print(f"  {a:22s} n={v['n_episodes']} protagonist_mean=${v['protagonist_money_mean']} "
              f"win_rate={v['win_rate']}")

    print("\nEarly detection (held-out accuracy by checkpoint):")
    for cp, v in detection.items():
        if v.get("status") == "insufficient_data":
            print(f"  turn={cp}: insufficient data")
        else:
            print(f"  turn={cp}: accuracy={v['accuracy']} balanced_accuracy={v['balanced_accuracy']} "
                  f"mean_confidence={v['mean_confidence']}")

    print("\nUnsupervised clustering (post-hoc alignment accuracy):")
    for cp, v in clustering.items():
        if v.get("status") == "insufficient_data":
            print(f"  turn={cp}: insufficient data")
        else:
            print(f"  turn={cp}: alignment_accuracy={v['post_hoc_alignment_accuracy']}")

    print(f"\nWrote {os.path.join(ROOT, 'tables', 'phase3_2_analysis.json')}")


if __name__ == "__main__":
    main()
