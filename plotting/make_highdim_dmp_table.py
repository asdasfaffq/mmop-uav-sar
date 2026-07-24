"""Compact high-dimensional table for the SECOND scalable family, ScalableDMP
(distance-minimization, two equivalent segments, linear front): mean IGDX and IGD
per algorithm vs decision dimension. Confirms the ScalableMMF2 pattern on a
structurally different problem (piecewise distance landscape, linear PF)."""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DIMS = [5, 10, 30, 50, 100]
DISP = {"EARS_MMOEA": "EARS-MMOEA", "CPDEA": "CPDEA", "DN_NSGAII": "DN-NSGA-II",
        "MMEA_WI": "MMEA-WI", "MO_Ring_PSO_SCD": "MO\\_Ring\\_PSO\\_SCD",
        "OmniOptimizer": "Omni-opt", "HREA": "HREA"}


def mean_metric(algo, d, metric):
    pth = ROOT / f"results/raw/highdim/ScalDMP_d{d}/{algo}"
    vals = [json.loads(jf.read_text())["metrics"][metric] for jf in pth.glob("run_*.json")]
    return float(np.mean(vals)) if vals else float("nan")


def block(metric, label):
    algos = list(DISP)
    M = {a: {d: mean_metric(a, d, metric) for d in DIMS} for a in algos}
    order = sorted(algos, key=lambda a: np.nanmean([M[a][d] for d in DIMS]))
    best = {d: min(algos, key=lambda a: M[a][d]) for d in DIMS}
    out = [r"\multicolumn{" + str(len(DIMS) + 1) + r"}{l}{\emph{" + label + r"}}\\"]
    for a in order:
        cells = [(r"\textbf{" + f"{M[a][d]:.4f}" + "}") if best[d] == a else f"{M[a][d]:.4f}"
                 for d in DIMS]
        out.append(DISP[a] + " & " + " & ".join(cells) + r" \\")
    return out


def main():
    L = [r"\begin{table}[t]", r"\centering\small",
         (r"\caption{High-dimensional study on the second scalable family ScalableDMP "
          r"(distance minimization, two equivalent segment Pareto sets, linear front; analytic "
          r"reference verified): mean IGDX and IGD over $30$ runs vs decision dimension $d$, "
          r"frozen protocol, best per column in bold. The pattern of Table~\ref{tab:highdim} "
          r"recurs on this structurally different landscape: EARS degrades the most gracefully "
          r"and leads at high $d$, confirming the high-dimensional finding is not specific to one "
          r"constructed problem.}"),
         r"\label{tab:highdim_dmp}",
         r"\begin{tabular}{l" + "r" * len(DIMS) + "}", r"\toprule",
         "algorithm & " + " & ".join(f"$d{{=}}{d}$" for d in DIMS) + r" \\", r"\midrule"]
    L += block("IGDX", "IGDX (decision-space, lower better)")
    L.append(r"\midrule")
    L += block("IGD", "IGD (convergence, lower better)")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    out = ROOT / "results/tables/highdim_dmp.tex"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
