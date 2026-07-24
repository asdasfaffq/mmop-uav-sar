"""Ablation bar charts: mean metric per variant (A0_Full vs ablated), showing the
contribution of each EARS-MMOEA module. Reads raw ablation results directly.

Usage:
  python plotting/plot_ablation.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from plotting._style import apply_style, save
from utils.io_utils import FIG_DIR, RAW_DIR

VARIANT_ORDER = ["A0_Full", "A1_noDMArchive", "A2_noRouteFamily", "A3_noEquivFitness",
                 "A4_noNiching", "A5_noCrossMode", "A6_noConstraintAware",
                 "A7_noPortfolio", "A8_BackboneOnly", "A9_noSparsityBonus"]
METRICS = ["IGDX", "IGD", "PSP", "HV"]
LOWER_BETTER = {"IGDX": True, "IGD": True, "PSP": False, "HV": False}


def _load():
    data = defaultdict(lambda: defaultdict(list))  # variant -> metric -> [vals]
    for jf in (RAW_DIR / "ablation").glob("*/*/run_*.json"):
        r = json.loads(jf.read_text())
        for m in METRICS:
            if m in r["metrics"]:
                data[r["algorithm"]][m].append(r["metrics"][m])
    return data


def plot(out_stem=None):
    apply_style()
    import matplotlib.pyplot as plt
    data = _load()
    variants = [v for v in VARIANT_ORDER if v in data]
    if not variants:
        print("[skip] no ablation results yet"); return

    fig, axes = plt.subplots(2, 2, figsize=(13, 9)); axes = axes.ravel()
    for ax, m in zip(axes, METRICS):
        means = [np.mean(data[v][m]) for v in variants]
        stds = [np.std(data[v][m]) for v in variants]
        colors = ["#D55E00" if v == "A0_Full" else "#0072B2" for v in variants]
        ax.bar(range(len(variants)), means, yerr=stds, capsize=3,
               color=colors, edgecolor="white")
        ax.set_xticks(range(len(variants)))
        ax.set_xticklabels([v.replace("_", "\n", 1) for v in variants],
                           rotation=45, ha="right", fontsize=8)
        ax.set_title(f"{m} ({'lower better' if LOWER_BETTER[m] else 'higher better'})")
        ax.set_ylabel(m)
    fig.suptitle("Ablation: full EARS-MMOEA (orange) vs module removed (blue), mean over MMF1-8",
                 fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out_stem = out_stem or (FIG_DIR / "ablation_study")
    save(fig, out_stem); plt.close(fig)
    print(f"[ok] wrote {out_stem}.png/.pdf")


if __name__ == "__main__":
    plot()
