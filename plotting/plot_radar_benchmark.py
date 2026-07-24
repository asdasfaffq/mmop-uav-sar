"""Radar (spider) chart of benchmark average ranks across the eight metrics, seven
algorithms. Plotted as (n_algos + 1 - rank) so the OUTER edge is best (rank 1) and the
inner is worst; EARS-MMOEA is drawn filled and bold. Replaces the IGDX critical-
difference diagram with a multi-metric view."""
import csv
from pathlib import Path
import numpy as np
from plotting._style import apply_style, save, algo_style
from utils.io_utils import FIG_DIR

ROOT = Path(__file__).resolve().parent.parent
METRICS = ["IGD", "IGDplus", "HV", "IGDX", "PSP", "mode_coverage", "n_modes", "spacing"]
MLABEL = {"IGD": "IGD", "IGDplus": "IGD+", "HV": "HV", "IGDX": "IGDX", "PSP": "PSP",
          "mode_coverage": "mode-cov", "n_modes": "#modes", "spacing": "spacing"}
DISP = {"EARS_MMOEA": "EARS", "CPDEA": "CPDEA", "DN_NSGAII": "DN-NSGA-II", "MMEA_WI": "MMEA-WI",
        "MO_Ring_PSO_SCD": "MO_Ring", "OmniOptimizer": "Omni", "HREA": "HREA"}
ORDER = ["EARS_MMOEA", "CPDEA", "MMEA_WI", "HREA", "MO_Ring_PSO_SCD", "OmniOptimizer", "DN_NSGAII"]


def main():
    rows = list(csv.reader(open(ROOT / "results/statistics/benchmark_ranks.csv")))
    hdr = rows[0][1:]
    data = {r[0]: dict(zip(hdr, map(float, r[1:]))) for r in rows[1:]}
    n = len(hdr)                                   # 7 algorithms
    apply_style()
    import matplotlib.pyplot as plt
    ang = np.linspace(0, 2 * np.pi, len(METRICS), endpoint=False).tolist()
    ang += ang[:1]
    fig, ax = plt.subplots(figsize=(6.4, 6.0), subplot_kw=dict(polar=True))
    for a in ORDER:
        vals = [(n + 1) - data[m][a] for m in METRICS]   # outer = best (rank 1 -> n)
        vals += vals[:1]
        st = algo_style(a)
        if a == "EARS_MMOEA":
            ax.plot(ang, vals, color=st["color"], lw=2.8, marker="o", ms=5,
                    label=DISP[a], zorder=5)
            ax.fill(ang, vals, color=st["color"], alpha=0.18, zorder=4)
        else:
            ax.plot(ang, vals, color=st["color"], lw=1.3, ls="--", alpha=0.85,
                    marker=st["marker"], ms=3, label=DISP[a])
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels([MLABEL[m] for m in METRICS], fontsize=10)
    ax.set_yticks(range(1, n + 1))
    ax.set_yticklabels([str(n + 1 - r) for r in range(1, n + 1)], fontsize=7, color="0.5")
    ax.set_ylim(0, n)
    ax.set_title("Benchmark average rank per metric (outer = best)", fontsize=11, pad=18)
    ax.legend(loc="upper right", bbox_to_anchor=(1.32, 1.10), fontsize=8, framealpha=0.9)
    out = FIG_DIR / "radar_benchmark"
    save(fig, out); plt.close(fig)
    print(f"[ok] {out}.png/.pdf")


if __name__ == "__main__":
    main()
