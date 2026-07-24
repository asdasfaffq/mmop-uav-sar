"""Fig. 1 -- EARS-MMOEA method framework diagram (code-generated, matplotlib).

Real OSM city  ->  MMOP formulation  ->  EARS-MMOEA (7 modules)  ->  multiple
Pareto-equivalent solution families. Publication-style schematic; no AI image gen.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plotting._style import apply_style, save
from utils.io_utils import FIG_DIR


def _box(ax, x, y, w, h, text, fc, fs=9, ec="black"):
    import matplotlib.patches as mp
    ax.add_patch(mp.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012",
                                   linewidth=1.0, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, zorder=3)


def _arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="0.3"), zorder=1)


def plot(out_stem=None):
    apply_style()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off")

    # pipeline (top)
    _box(ax, 2, 50, 18, 9, "Real OSM city\n(graph, demand,\nrisk field)", "#D6EAF8", 9)
    _box(ax, 24, 50, 18, 9, "MMOP\nformulation\n(objectives + decision\nspace)", "#D6EAF8", 9)
    _box(ax, 80, 50, 18, 9, "Multiple\nPareto-equivalent\nsolution families", "#FCF3CF", 9)
    _arrow(ax, 20, 54.5, 24, 54.5)
    _arrow(ax, 42, 54.5, 50, 54.5)          # into core
    _arrow(ax, 78, 54.5, 80, 54.5)          # core -> output

    # EARS-MMOEA core (center big box)
    import matplotlib.patches as mp
    ax.add_patch(mp.FancyBboxPatch((46, 6), 36, 50, boxstyle="round,pad=0.02",
                                   linewidth=1.6, edgecolor="#1F618D",
                                   facecolor="#EBF5FB", zorder=1))
    ax.text(64, 52.5, "EARS-MMOEA", ha="center", fontsize=13, fontweight="bold",
            color="#1F618D")

    mods = [
        ("M1  Hybrid dual-space fitness\n(SCD x decision-sparsity bonus)", "#FADBD8"),
        ("M2  Three-archive system\n(Pareto / decision-mode / family)", "#D5F5E3"),
        ("M3  Adaptive multimodal niching", "#D6EAF8"),
        ("M4  Within-/cross-mode mating", "#FCF3CF"),
        ("M5  Constraint-aware selection", "#E8DAEF"),
        ("M6  Adaptive operator portfolio (bandit)", "#FDEBD0"),
        ("M7  Environmental selection", "#D1F2EB"),
    ]
    y = 46
    for txt, fc in mods:
        _box(ax, 48, y, 32, 4.6, txt, fc, 8.2)
        y -= 5.7

    # evaluation arms (bottom)
    _box(ax, 6, 30, 30, 9,
         "Standard MMOP benchmark\nMMF1-8 (30 runs)\n-> rank-1 (avg rank 2.20)", "#E8F8F5", 9)
    _box(ax, 6, 14, 30, 11,
         "Real OSM application\nemergency-station placement\n(3 instances x 30 runs)\n-> rank-1 (avg rank 2.74)",
         "#FEF9E7", 9)
    _arrow(ax, 46, 31, 36, 34.5)
    _arrow(ax, 46, 20, 36, 19.5)

    fig.suptitle("EARS-MMOEA framework: equivalence-aware multimodal "
                 "multi-objective optimization", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out_stem = out_stem or (FIG_DIR / "framework")
    save(fig, out_stem); plt.close(fig)
    print(f"[ok] wrote {out_stem}.png/.pdf")


if __name__ == "__main__":
    plot()
