"""Benchmark average-rank heatmap: rows = seven algorithms (sorted best-first by mean
rank), columns = the eight metrics plus a Mean column, each cell annotated with the
average rank and colour-coded (green = best rank 1, red = worst). Shows the complete
per-metric comparison in one compact, fully-readable figure."""
import csv
from pathlib import Path
import numpy as np
from plotting._style import apply_style, save
from utils.io_utils import FIG_DIR

ROOT = Path(__file__).resolve().parent.parent
OBJ = ["IGD", "IGDplus", "HV", "spacing"]            # objective-space group
DEC = ["IGDX", "PSP", "mode_coverage"]               # decision-space group (primary)
METRICS = OBJ + DEC + ["n_modes"]
MLABEL = {"IGD": "IGD", "IGDplus": "IGD+", "HV": "HV", "IGDX": "IGDX", "PSP": "PSP",
          "mode_coverage": "mode-cov", "n_modes": "#modes", "spacing": "spacing",
          "objbar": "obj mean", "decbar": "dec mean"}
DISP = {"EARS_MMOEA": "EARS-MMOEA", "CPDEA": "CPDEA", "DN_NSGAII": "DN-NSGA-II",
        "MMEA_WI": "MMEA-WI", "MO_Ring_PSO_SCD": "MO_Ring_PSO_SCD", "OmniOptimizer": "Omni-opt",
        "HREA": "HREA"}


def main():
    rows = list(csv.reader(open(ROOT / "results/statistics/benchmark_ranks.csv")))
    hdr = rows[0][1:]
    data = {r[0]: dict(zip(hdr, map(float, r[1:]))) for r in rows[1:]}
    algos = hdr
    objm = {a: np.mean([data[m][a] for m in OBJ]) for a in algos}
    decm = {a: np.mean([data[m][a] for m in DEC]) for a in algos}
    order = sorted(algos, key=lambda a: decm[a])           # by decision-space (primary)
    cols = METRICS + ["objbar", "decbar"]                  # two group means, no pooled MEAN
    M = np.array([[data[m][a] for m in METRICS] + [objm[a], decm[a]] for a in order])
    nmet = len(METRICS)

    apply_style()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8.8, 3.6))
    im = ax.imshow(M, cmap="RdYlGn_r", aspect="auto", vmin=1, vmax=len(algos))
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([MLABEL.get(c, c) for c in cols], fontsize=9, rotation=20, ha="right")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([DISP[a] for a in order], fontsize=9)
    # white separators between the two metric groups and before the group-mean columns
    for x in (len(OBJ) - 0.5, len(OBJ) + len(DEC) - 0.5, nmet - 0.5):
        ax.axvline(x, color="white", lw=2)
    for i in range(len(order)):
        for j in range(len(cols)):
            v = M[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                    color="black", fontweight="bold" if j >= nmet else "normal")
    ax.set_title("Benchmark average rank per metric, grouped (lower = better; MMF1--8, $N{=}8$)",
                 fontsize=11, pad=8)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cb.set_label("average rank", fontsize=8); cb.ax.tick_params(labelsize=7)
    fig.tight_layout()
    out = FIG_DIR / "heatmap_benchmark"
    save(fig, out); plt.close(fig)
    print(f"[ok] {out}.png/.pdf")


if __name__ == "__main__":
    main()
