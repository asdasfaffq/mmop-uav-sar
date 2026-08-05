"""IGD-IGDX trade-off: in-sort weight sweep vs the within-front points.

The sweep is deliberately carried far enough for the in-sort curve to TURN (lambda up
to 32). Truncating it at lambda=1, where both axes are still improving monotonically,
would make the within-front point look unconditionally dominant; it is not. Beyond
lambda~4 the in-sort curve saturates at a point competitive with the within-front key.
What separates the placements is weight sensitivity -- the within-front key barely moves
across an eightfold change in beta -- and, on backbones without an archive to restore
converged solutions, the in-sort curve never approaches it at any weight (see the
transfer study).
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
    lams = [0.05, 0.10, 0.25, 0.50, 1.00, 2.00, 4.00, 8.00, 16.00, 32.00]
    insort = [(mean(f"InSort_lam{l:.2f}", "IGD"), mean(f"InSort_lam{l:.2f}", "IGDX"), l)
              for l in lams]
    wf = (mean("WF_mult", "IGD"), mean("WF_mult", "IGDX"))
    wfa = (mean("WF_add", "IGD"), mean("WF_add", "IGDX"))
    nos = (mean("NoS", "IGD"), mean("NoS", "IGDX"))

    apply_style()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5.4, 3.8))
    xs = [p[0] for p in insort]; ys = [p[1] for p in insort]
    ax.plot(xs, ys, "o-", color="#c1272d", ms=4,
            label="in-sort (pure $S$), $\\lambda$ swept", zorder=2)
    # Label only the endpoints and the knee: labelling all ten crowds the saturated tail.
    for x, y, l in insort:
        if l in (0.05, 0.5, 2.0, 32.0):
            ax.annotate(f"$\\lambda{{=}}{l:g}$", (x, y), textcoords="offset points",
                        xytext=(-8, 5), ha="right", fontsize=7, color="#c1272d")
    ax.scatter(*wf, marker="*", s=180, color="#1f6f3f", zorder=3,
               label="within-front mult.\\ (ours)")
    ax.scatter(*wfa, marker="P", s=70, color="#2e8b57", zorder=3,
               label="within-front additive")
    ax.scatter(*nos, marker="s", s=55, color="#555555", zorder=3, label="no $S$")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("IGD (convergence, lower better)")
    ax.set_ylabel("IGDX (coverage, lower better)")
    ax.set_title("The in-sort curve saturates near the within-front key (MMF1--8)",
                 fontsize=9.5)
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.01, 1.0),
              borderaxespad=0.0, framealpha=0.95)
    fig.tight_layout()
    out = FIG_DIR / "insort_tradeoff"
    save(fig, out); plt.close(fig)
    print(f"[ok] {out}.pdf")
    print(f"     within-front {wf}")
    print(f"     in-sort saturates at {insort[-1][:2]} (lambda=32)")


if __name__ == "__main__":
    main()
