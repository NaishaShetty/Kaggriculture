"""
Phase 3.2 regime classifiers -- deliberately simple and interpretable per
the brief section 7/20 ("do NOT jump immediately to neural networks...
threshold rules, normalized distances, logistic regression, decision
trees... only use more complex models if simpler approaches fail"). No new
ML dependency was added to the frozen environment (`sklearn` is NOT
installed in `C:\\kagvenv` and this project does not add it) -- both
classifiers below are implemented directly over `numpy` (already present).

Two classifiers:
  1. NearestCentroidClassifier -- SUPERVISED (uses archetype labels at fit
     time only; brief section 7's "normalized distances" method). Used for
     the labeled offline analysis (sections 7-9) and the held-out
     evaluation (section 13).
  2. simple_kmeans -- UNSUPERVISED (never sees labels during clustering;
     labels are used ONLY afterward, to evaluate cluster-to-archetype
     alignment). This implements brief section 11's "detector receives
     only the observable trace" requirement honestly -- clustering, not a
     label-trained model evaluated on a held-out label-free run (which
     would still have "seen" labels at training time).
"""
import numpy as np


class NearestCentroidClassifier:
    """Standardizes features (z-score, fit on TRAIN data only), computes one
    centroid per class, predicts the nearest centroid by Euclidean distance.
    Confidence = 1 - (distance to nearest / distance to 2nd nearest), clipped
    to [0,1] -- a simple, interpretable margin-based confidence, not a
    calibrated probability."""

    def __init__(self):
        self.classes_ = []
        self.centroids_ = None
        self.mean_ = None
        self.std_ = None
        self.feature_names_ = []

    def fit(self, X: np.ndarray, y: list, feature_names: list):
        self.feature_names_ = feature_names
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0)
        self.std_[self.std_ == 0] = 1.0
        Xz = (X - self.mean_) / self.std_
        self.classes_ = sorted(set(y))
        self.centroids_ = np.array([Xz[[i for i, label in enumerate(y) if label == c]].mean(axis=0)
                                     for c in self.classes_])
        return self

    def _transform(self, X):
        return (X - self.mean_) / self.std_

    def predict(self, X: np.ndarray):
        Xz = self._transform(X)
        dists = np.linalg.norm(Xz[:, None, :] - self.centroids_[None, :, :], axis=2)  # (n_samples, n_classes)
        preds, confidences = [], []
        for row in dists:
            order = np.argsort(row)
            best, second = row[order[0]], row[order[1]] if len(order) > 1 else row[order[0]] + 1e-9
            conf = max(0.0, min(1.0, 1 - (best / (second + 1e-9))))
            preds.append(self.classes_[order[0]])
            confidences.append(round(float(conf), 4))
        return preds, confidences

    def feature_importance(self):
        """Crude interpretable 'importance': how spread out the class
        centroids are on each (standardized) feature dimension, relative to
        overall centroid spread -- a bigger value means that feature
        separates classes more (not a formal statistical test, documented
        as a heuristic, per the brief's 'simple interpretable methods first')."""
        spread = self.centroids_.std(axis=0)
        order = np.argsort(-spread)
        return [(self.feature_names_[i], round(float(spread[i]), 4)) for i in order]


def confusion_matrix(y_true, y_pred, classes):
    idx = {c: i for i, c in enumerate(classes)}
    m = np.zeros((len(classes), len(classes)), dtype=int)
    for t, p in zip(y_true, y_pred):
        m[idx[t], idx[p]] += 1
    return m.tolist()


def accuracy(y_true, y_pred):
    return sum(1 for t, p in zip(y_true, y_pred) if t == p) / max(1, len(y_true))


def balanced_accuracy(y_true, y_pred, classes):
    per_class = []
    for c in classes:
        idxs = [i for i, t in enumerate(y_true) if t == c]
        if not idxs:
            continue
        correct = sum(1 for i in idxs if y_pred[i] == c)
        per_class.append(correct / len(idxs))
    return sum(per_class) / len(per_class) if per_class else 0.0


def simple_kmeans(X: np.ndarray, k: int, n_iter=100, seed=42):
    """Lloyd's algorithm, numpy-only, deterministic given `seed` (uses a
    fixed-seed local RandomState, never the module-level global RNG, and
    never `random.Random()`/`np.random` unseeded -- reproducibility per the
    brief's seed-design requirement)."""
    rng = np.random.RandomState(seed)
    mean, std = X.mean(axis=0), X.std(axis=0)
    std[std == 0] = 1.0
    Xz = (X - mean) / std
    n = Xz.shape[0]
    centroid_idx = rng.choice(n, size=min(k, n), replace=False)
    centroids = Xz[centroid_idx].copy()
    assignments = np.zeros(n, dtype=int)
    for _ in range(n_iter):
        dists = np.linalg.norm(Xz[:, None, :] - centroids[None, :, :], axis=2)
        new_assignments = dists.argmin(axis=1)
        if np.array_equal(new_assignments, assignments) and _ > 0:
            break
        assignments = new_assignments
        for c in range(len(centroids)):
            members = Xz[assignments == c]
            if len(members):
                centroids[c] = members.mean(axis=0)
    return assignments.tolist(), centroids


def cluster_to_label_accuracy(cluster_assignments, true_labels):
    """Post-hoc ONLY: assigns each cluster the majority true label among its
    members, then reports accuracy under that mapping. Labels are used here
    for EVALUATION ONLY, never fed into simple_kmeans() itself."""
    from collections import Counter
    cluster_to_label = {}
    for cluster_id in set(cluster_assignments):
        members_labels = [true_labels[i] for i, c in enumerate(cluster_assignments) if c == cluster_id]
        cluster_to_label[cluster_id] = Counter(members_labels).most_common(1)[0][0]
    preds = [cluster_to_label[c] for c in cluster_assignments]
    return accuracy(true_labels, preds), cluster_to_label, preds
