"""Benchmark average-rank table with metrics GROUPED, not pooled.

The protocol does not average correlated indicators into a single overall rank.
This table therefore reports two metric groups separately -- objective-space
(IGD, IGD+, HV, spacing) and decision-space (IGDX, PSP, mode coverage) -- each with
its own group-mean rank, and the indicative #modes on its own. The a-priori primary
metrics are the decision-space indicators IGDX and PSP. There is no single all-metric
mean: EARS is read as the only algorithm top-2 in BOTH group means.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OBJ = ["IGD", "IGDplus", "HV", "spacing"]
DEC = ["IGDX", "PSP", "mode_coverage"]
OTHER = ["n_modes"]
ROWLAB = {"IGD": "IGD", "IGDplus": "IGD$^+$", "HV": "HV", "spacing": "spacing",
          "IGDX": r"IGDX$^\ast$", "PSP": r"PSP$^\ast$", "mode_coverage": "mode-cov",
          "n_modes": "\\#modes"}
DISP = {"EARS_MMOEA": r"\textbf{EARS}", "CPDEA": "CPDEA", "DN_NSGAII": "DN-NSGA-II",
        "MMEA_WI": "MMEA-WI", "MO_Ring_PSO_SCD": r"MO\_Ring", "OmniOptimizer": "Omni",
        "HREA": "HREA"}


def main():
    rows = list(csv.reader(open(ROOT / "results/statistics/benchmark_ranks.csv")))
    hdr = rows[0][1:]
    data = {r[0]: dict(zip(hdr, map(float, r[1:]))) for r in rows[1:]}   # metric->algo->rank
    gmean = lambda grp, a: sum(data[m][a] for m in grp) / len(grp)
    algos = sorted(hdr, key=lambda a: gmean(DEC, a))                     # by decision-space (primary)

    def row(metric):
        best = min(algos, key=lambda a: data[metric][a])
        cells = [(r"\textbf{" + f"{data[metric][a]:.2f}" + "}") if a == best else f"{data[metric][a]:.2f}"
                 for a in algos]
        return ROWLAB.get(metric, metric) + " & " + " & ".join(cells) + r" \\"

    def mean_row(grp, lab):
        best = min(algos, key=lambda a: gmean(grp, a))
        cells = [(r"\textbf{" + f"{gmean(grp, a):.2f}" + "}") if a == best else f"{gmean(grp, a):.2f}"
                 for a in algos]
        return r"\;\;\emph{" + lab + "} & " + " & ".join(cells) + r" \\"

    L = [r"\begin{table}[t]", r"\centering\small",
         (r"\caption{Average rank per metric on MMF1--8 (lower is better), metrics \emph{grouped} "
          r"rather than pooled. The a-priori primary metrics are the decision-space indicators "
          r"IGDX and PSP ($^\ast$). We do not report a single all-metric mean (the indicators are "
          r"correlated); instead each group has its own mean rank. EARS is the only algorithm "
          r"top-2 in \emph{both} group means: best in objective space and second (a statistical "
          r"tie with CPDEA) in decision space, whereas CPDEA leads decision space but is near-last "
          r"in objective space and Omni-optimizer is the reverse. $\#$modes is indicative.}"),
         r"\label{tab:benchmark_rank}",
         r"\resizebox{\linewidth}{!}{%",
         r"\begin{tabular}{l" + "r" * len(algos) + "}", r"\toprule",
         " & " + " & ".join(DISP[a] for a in algos) + r" \\", r"\midrule",
         r"\multicolumn{" + str(len(algos) + 1) + r"}{l}{\emph{Objective-space group}}\\"]
    for m in OBJ:
        L.append(row(m))
    L.append(mean_row(OBJ, "objective-space mean"))
    L.append(r"\midrule")
    L.append(r"\multicolumn{" + str(len(algos) + 1) + r"}{l}{\emph{Decision-space group (primary)}}\\")
    for m in DEC:
        L.append(row(m))
    L.append(mean_row(DEC, "decision-space mean"))
    L.append(r"\midrule")
    for m in OTHER:
        L.append(row(m))
    L += [r"\bottomrule", r"\end{tabular}}", r"\end{table}"]
    out = ROOT / "results/tables/benchmark_avg_rank.tex"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
