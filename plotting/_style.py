"""Shared publication figure style (white background, clear fonts, 300+ dpi).

Import `apply_style()` at the top of every plotting module so all paper figures
are visually consistent and submission-ready.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# A colour-blind-friendly qualitative palette (Okabe-Ito), reused everywhere.
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7",
           "#E69F00", "#56B4E9", "#F0E442", "#000000"]

# Stable per-algorithm colours/markers for cross-figure consistency.
ALGO_STYLE = {
    "EARS_MMOEA":      dict(color="#D55E00", marker="o"),
    "MO_Ring_PSO_SCD": dict(color="#0072B2", marker="s"),
    "DN_NSGAII":       dict(color="#009E73", marker="^"),
    "OmniOptimizer":   dict(color="#CC79A7", marker="D"),
    "CPDEA":           dict(color="#E69F00", marker="v"),
    "MMEA_WI":         dict(color="#56B4E9", marker="P"),
}


def apply_style():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 300,
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "legend.fontsize": 9,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.autolayout": False,
    })


def algo_style(name: str) -> dict:
    return ALGO_STYLE.get(name, dict(color="#000000", marker="o"))


def save(fig, path_stem, also_pdf: bool = True):
    """Save a figure as PNG (300dpi) and PDF (vector) given a path without suffix."""
    from pathlib import Path
    p = Path(path_stem)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p.with_suffix(".png"), dpi=300, bbox_inches="tight")
    if also_pdf:
        fig.savefig(p.with_suffix(".pdf"), bbox_inches="tight")
