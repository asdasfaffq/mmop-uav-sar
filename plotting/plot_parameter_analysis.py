"""Re-render the parameter sensitivity figure from results/summary/parameter_analysis.csv.

The analysis driver (experiments/run_parameter_analysis.py) also writes the figure
directly; this module lets the figure be regenerated from the CSV alone (e.g. for
Phase 12 figure assembly) without re-running experiments.

Usage:
  python plotting/plot_parameter_analysis.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from plotting._style import apply_style, save
from utils.io_utils import FIG_DIR, SUMMARY_DIR


def plot(csv_path=None, out_stem=None):
    apply_style()
    import matplotlib.pyplot as plt
    csv_path = Path(csv_path or SUMMARY_DIR / "parameter_analysis.csv")
    df = pd.read_csv(csv_path)
    params = list(dict.fromkeys(df["param"]))
    problems = list(dict.fromkeys(df["problem"]))

    n = len(params)
    cols = 4; rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(4.5 * cols, 3.6 * rows))
    axes = np.atleast_1d(axes).ravel()

    for k, param in enumerate(params):
        ax = axes[k]
        sub = df[df["param"] == param]
        values = list(dict.fromkeys(sub["value"]))
        igdx_avg, igd_avg = [], []
        for v in values:
            s = sub[sub["value"] == v]
            igdx_avg.append(s["mean_IGDX"].mean())
            igd_avg.append(s["mean_IGD"].mean())
        x = range(len(values))
        ax.plot(x, igdx_avg, "o-", color="#D55E00", label="mean IGDX")
        ax2 = ax.twinx()
        ax2.plot(x, igd_avg, "s--", color="#0072B2", label="mean IGD")
        ax.set_xticks(list(x)); ax.set_xticklabels([str(v) for v in values])
        ax.set_title(param); ax.set_xlabel("value")
        ax.set_ylabel("IGDX", color="#D55E00")
        ax2.set_ylabel("IGD", color="#0072B2")
    for k in range(n, len(axes)):
        axes[k].axis("off")
    fig.suptitle("EARS-MMOEA parameter sensitivity (validation subset)", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out_stem = out_stem or (FIG_DIR / "parameter_sensitivity")
    save(fig, out_stem)
    print(f"[ok] wrote {out_stem}.png/.pdf")


if __name__ == "__main__":
    plot()
