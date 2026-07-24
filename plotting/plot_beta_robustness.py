"""Parameter-robustness figure for the sparsity weight beta on the validation subset:
IGD (convergence) and IGDX (decision-space) vs beta, per problem + mean, with the frozen
choice beta=0.5 marked. Shows that beta=0.5 improves IGDX with no IGD regression, while
larger beta regresses convergence on some problems (the disclosed sensitivity)."""
import csv
from collections import defaultdict
from pathlib import Path
import numpy as np
from plotting._style import apply_style, save
from utils.io_utils import FIG_DIR

ROOT = Path(__file__).resolve().parent.parent
PROBS = ["MMF1", "MMF2", "MMF5"]
COL = {"MMF1": "#0072B2", "MMF2": "#D55E00", "MMF5": "#009E73"}


def main():
    rows = list(csv.DictReader(open(ROOT / "results/summary/beta_sweep.csv")))
    betas = sorted({float(r["beta"]) for r in rows})
    agg = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))  # metric->prob->beta->[vals]
    for r in rows:
        for m in ("IGD", "IGDX"):
            agg[m][r["problem"]][float(r["beta"])].append(float(r[m]))
    apply_style()
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    titles = {"IGD": "IGD  (convergence, lower better)",
              "IGDX": "IGDX  (decision-space, lower better)"}
    for ax, m in zip(axes, ("IGD", "IGDX")):
        for prob in PROBS:
            mean = [np.mean(agg[m][prob][b]) for b in betas]
            se = [np.std(agg[m][prob][b]) / np.sqrt(len(agg[m][prob][b])) for b in betas]
            # normalise each problem to its beta=0 value for comparability
            base = mean[0] if mean[0] > 0 else 1.0
            rel = np.array(mean) / base
            ax.plot(betas, rel, "-o", color=COL[prob], label=prob, lw=1.8, ms=5)
        ax.axvline(0.5, color="0.4", ls="--", lw=1.2)
        ax.text(0.5, ax.get_ylim()[1], " chosen $\\beta{=}0.5$", color="0.3",
                fontsize=9, va="top", ha="left")
        ax.axhline(1.0, color="0.7", ls=":", lw=0.9)
        ax.set_xlabel(r"sparsity weight $\beta$"); ax.set_title(titles[m])
        ax.set_ylabel(f"{m} relative to $\\beta{{=}}0$")
        # place the legend in the empty corner of each panel (IGD rises -> upper-left
        # is clear; IGDX fans downward -> lower-left is clear) so it never sits on a line
        ax.legend(fontsize=9, framealpha=0.95,
                  loc=("upper left" if m == "IGD" else "lower left"))
    fig.suptitle(r"Robustness to the sparsity weight $\beta$ on the validation subset "
                 r"(MMF1/MMF2/MMF5): IGDX improves with $\beta$ (most gain by $\beta{=}0.5$), "
                 r"while $\beta\geq 1$ significantly regresses IGD on MMF1/MMF5", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = FIG_DIR / "beta_robustness"
    save(fig, out); plt.close(fig)
    print(f"[ok] {out}.png/.pdf")
    # quick numeric summary
    for m in ("IGD", "IGDX"):
        print(m, "mean over validation subset by beta:",
              {b: round(np.mean([np.mean(agg[m][p][b]) for p in PROBS]), 4) for b in betas})


if __name__ == "__main__":
    main()
