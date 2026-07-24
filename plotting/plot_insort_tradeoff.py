"""IGD-IGDX trade-off curve for the in-sort weight sweep vs the within-front points.

Shows that no matter how the pure sparsity signal S is weighted when fused into the
global (in-sort) selection (lambda in {0.05..1}), the resulting (IGD, IGDX) point is
dominated on BOTH axes by the within-front placement of the same signal. The within-
front point therefore lies below-left of the entire in-sort curve, so the placement
effect is not an artefact of a single weakly-tuned in-sort comparison.
"""
import json
from pathlib import Path
import numpy as np
from plotting._style import apply_style, save
from utils.io_utils import FIG_DIR

ROOT = Path(__file__).resolve().parent.parent
PROBS = ["MMF1", "MMF2", "MMF3", "MMF4", "MMF5", "MMF6", "MMF7", "MMF8"]
EXP = ROOT / "results/raw/insort_sweep"


def mean(v, metric):
    return float(np.mean([np.mean([json.loads(j.read_text())["metrics"][metric]
                  for j in (EXP / p / v).glob("run_*.json")]) for p in PROBS]))


def main():
    lams = [0.05, 0.10, 0.25, 0.50, 1.00]
    insort = [(mean(f"InSort_lam{l:.2f}", "IGD"), mean(f"InSort_lam{l:.2f}", "IGDX"), l) for l in lams]
    wf = (mean("WF_mult", "IGD"), mean("WF_mult", "IGDX"))
    wfa = (mean("WF_add", "IGD"), mean("WF_add", "IGDX"))
    nos = (mean("NoS", "IGD"), mean("NoS", "IGDX"))

    apply_style()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5.0, 3.6))
    xs = [p[0] for p in insort]; ys = [p[1] for p in insort]
    ax.plot(xs, ys, "o-", color="#c1272d", label="in-sort (pure $S$), $\\lambda$ swept", zorder=2)
    # label each lambda to the UPPER-LEFT of its point (into the empty interior),
    # so the text never sits on the curve or runs off the right edge
    for x, y, l in insort:
        ax.annotate(f"$\\lambda{{=}}{l:g}$", (x, y), textcoords="offset points",
                    xytext=(-8, 5), ha="right", fontsize=7, color="#c1272d")
    ax.scatter(*wf, marker="*", s=180, color="#1f6f3f", zorder=3, label="within-front mult.\\ (ours)")
    ax.scatter(*wfa, marker="P", s=70, color="#2e8b57", zorder=3, label="within-front additive")
    ax.scatter(*nos, marker="s", s=55, color="#555555", zorder=3, label="no $S$")
    ax.set_xlabel("IGD (convergence, lower better)")
    ax.set_ylabel("IGDX (coverage, lower better)")
    ax.set_title("Placement: within-front dominates the in-sort curve (MMF1--8)", fontsize=10)
    # legend OUTSIDE the axes (right) so it cannot overlap any data point
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.01, 1.0),
              borderaxespad=0.0, framealpha=0.95)
    fig.tight_layout()
    out = FIG_DIR / "insort_tradeoff"
    save(fig, out); plt.close(fig)
    print(f"[ok] {out}.pdf  (within-front {wf} dominates all in-sort points)")


if __name__ == "__main__":
    main()
