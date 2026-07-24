"""Module 3 -- Adaptive Multimodal Niching.

Clusters the population in (normalised) decision space to discover how many
equivalent decision-space modes currently exist, without a fixed niche radius.
The number of modes is chosen adaptively by silhouette score over a small range
of k; an adaptive niche radius is derived from the average nearest-neighbour
distance. Mode occupancy and its entropy feed the cross-mode mating controller
(Module 4) and the equivalence-aware fitness (Module 1).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    _HAVE_SK = True
except Exception:  # pragma: no cover
    _HAVE_SK = False


@dataclass
class NicheInfo:
    labels: np.ndarray         # cluster id per individual
    n_modes: int
    centers: np.ndarray        # (n_modes, n_var) in normalised space
    radius: float              # adaptive niche radius (normalised space)
    occupancy: np.ndarray      # count per mode
    entropy: float             # normalised entropy of occupancy in [0,1]


def _normalize(X, xl, xu):
    rng = np.asarray(xu) - np.asarray(xl)
    rng = np.where(rng < 1e-12, 1.0, rng)
    return (X - xl) / rng


def occupancy_entropy(counts: np.ndarray) -> float:
    p = counts / counts.sum()
    p = p[p > 0]
    h = -(p * np.log(p)).sum()
    hmax = np.log(len(counts)) if len(counts) > 1 else 1.0
    return float(h / hmax) if hmax > 0 else 0.0


def adaptive_niching(X: np.ndarray, xl, xu, *, min_modes=2, max_modes=20,
                     rng: np.random.Generator | None = None) -> NicheInfo:
    """Cluster X in decision space; pick k by silhouette; derive niche radius."""
    X = np.asarray(X, dtype=float)
    n = X.shape[0]
    Xn = _normalize(X, xl, xu)
    seed = int(rng.integers(0, 2**31 - 1)) if rng is not None else 0

    if n < 4 or not _HAVE_SK:
        labels = np.zeros(n, dtype=int)
        centers = Xn.mean(axis=0, keepdims=True)
        radius = _avg_nn_distance(Xn)
        return NicheInfo(labels, 1, centers, radius, np.array([n]), 0.0)

    kmax = int(min(max_modes, n // 2))
    kmin = int(min(min_modes, kmax))
    best_k, best_score, best_labels, best_centers = 1, -1.0, None, None
    for k in range(max(kmin, 2), kmax + 1):
        km = KMeans(n_clusters=k, n_init=3, random_state=seed)
        lab = km.fit_predict(Xn)
        if len(np.unique(lab)) < 2:
            continue
        try:
            score = silhouette_score(Xn, lab)
        except Exception:
            continue
        if score > best_score:
            best_k, best_score, best_labels, best_centers = k, score, lab, km.cluster_centers_

    if best_labels is None:
        labels = np.zeros(n, dtype=int)
        centers = Xn.mean(axis=0, keepdims=True)
        return NicheInfo(labels, 1, centers, _avg_nn_distance(Xn), np.array([n]), 0.0)

    counts = np.bincount(best_labels, minlength=best_k)
    radius = _avg_nn_distance(Xn)
    return NicheInfo(best_labels, best_k, best_centers, radius, counts,
                     occupancy_entropy(counts))


def assign_to_centers(X: np.ndarray, xl, xu, centers: np.ndarray) -> np.ndarray:
    """Cheaply label points by nearest mode centre (centres in normalised space).

    Used to extend a population's niche structure to the offspring pool without
    re-clustering every generation.
    """
    if centers is None or len(centers) == 0:
        return np.zeros(len(X), dtype=int)
    Xn = _normalize(np.asarray(X, dtype=float), xl, xu)
    D = np.linalg.norm(Xn[:, None, :] - centers[None, :, :], axis=2)
    return np.argmin(D, axis=1)


def _avg_nn_distance(Xn: np.ndarray) -> float:
    n = len(Xn)
    if n < 2:
        return 0.1
    # subsample for speed on large pops
    idx = np.arange(n)
    D = np.linalg.norm(Xn[idx][:, None, :] - Xn[None, idx, :], axis=2)
    np.fill_diagonal(D, np.inf)
    return float(np.median(D.min(axis=1)))
