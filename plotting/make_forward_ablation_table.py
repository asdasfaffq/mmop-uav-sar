"""Forward (constructive) ablation table: mean metric VALUES across the six-rung
ladder F0..F5, each rung adding one capability onto the previous.

We report absolute means (not ranks-among-6) on purpose: the convergence
indicators (IGD/HV) barely move across the whole ladder, so a rank-among-six
would amplify a ~0.0002 IGD difference into a large rank swing and misrepresent
the magnitude. The absolute values show the real shape: decision-space quality
(IGDX/PSP/mode-cov) is built by +E, +S and +portfolio, while +cross-mode and
+archive are inert on the unconstrained benchmark (they act on the constrained
application), and the entire diversity stack costs only a few percent of IGD.

Endpoints F0/F5 reproduce the subtractive A8/A0 numerically (same configuration).
"""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ORDER = ["F0_NSGAII", "F1_plusE", "F2_plusS_core", "F3_plusPortfolio",
         "F4_plusCrossMode", "F5_Full"]
LAB = {"F0_NSGAII": "F0 base (NSGA-II-like)", "F1_plusE": r"\;\;$+E$ (equivalence key)",
       "F2_plusS_core": r"\;\;$+S$ (within-front, core)", "F3_plusPortfolio": r"\;\;$+$ portfolio",
       "F4_plusCrossMode": r"\;\;$+$ cross-mode", "F5_Full": r"\;\;$+$ archive $=$ \textbf{full}"}
# (metric, header, fmt, lower_is_better)
COLS = [("IGDX", r"IGDX\,$\downarrow$", "{:.4f}", True),
        ("PSP", r"PSP\,$\uparrow$", "{:.1f}", False),
        ("mode_coverage", r"mode-cov\,$\uparrow$", "{:.3f}", False),
        ("IGD", r"IGD\,$\downarrow$", "{:.4f}", True),
        ("HV", r"HV\,$\uparrow$", "{:.4f}", False)]


def mean_metric(variant, metric):
    vals = [json.loads(jf.read_text())["metrics"][metric]
            for jf in (ROOT / "results/raw/forward_ablation").glob(f"*/{variant}/run_*.json")]
    return float(np.mean(vals))


def main():
    M = {v: {c[0]: mean_metric(v, c[0]) for c in COLS} for v in ORDER}
    L = [r"\begin{table}[t]", r"\centering\small",
         (r"\caption{Forward (constructive) ablation on MMF1--8: mean metric values "
          r"($30$ runs) across a six-rung ladder, each rung adding one capability onto the "
          r"previous, starting from an NSGA-II-like base. Decision-space quality "
          r"(IGDX/PSP/mode-cov) is built by the equivalence key $+E$, the within-front "
          r"sparsity $+S$ (the core selection mechanism), and the operator portfolio, while "
          r"cross-mode mating and the decision-mode archive are inert on the unconstrained "
          r"benchmark (they act on the constrained application). Convergence (IGD/HV) is "
          r"essentially flat across the whole ladder: the entire diversity stack costs "
          r"$\approx 7\%$ of IGD ($0.0027\!\to\!0.0029$). This locates the benchmark gain in "
          r"the core selection idea rather than in module count. Endpoints F0/F5 reproduce "
          r"the subtractive A8/A0 (Table~\ref{tab:ablation_rank}) numerically.}"),
         r"\label{tab:forward_ablation}",
         r"\begin{tabular}{l" + "r" * len(COLS) + "}", r"\toprule",
         "rung (cumulative) & " + " & ".join(c[1] for c in COLS) + r" \\", r"\midrule"]
    for v in ORDER:
        cells = []
        for metric, _, fmt, _ in COLS:
            s = fmt.format(M[v][metric])
            cells.append((r"\textbf{" + s + "}") if v == "F5_Full" else s)
        L.append(LAB[v] + " & " + " & ".join(cells) + r" \\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    out = ROOT / "results/tables/forward_ablation.tex"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
