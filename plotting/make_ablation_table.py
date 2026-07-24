"""Regenerate the ablation average-rank table with metrics GROUPED into a
convergence block and a decision-space (MMOP) block, plus per-block mean ranks.

Why grouped: averaging convergence and decision-space ranks into one number is
misleading for MMOP, because a variant that COLLAPSES to a single mode scores
best on pure-convergence indicators (IGD/HV) while being useless for MMOP. The
two block means expose the convergence/diversity trade-off honestly; the
decision-space block is the MMOP-relevant aggregate. All per-metric rows are kept.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONV = ["IGD", "IGDplus", "HV", "spacing"]          # pure convergence / spread
DEC = ["IGDX", "PSP", "mode_coverage"]              # decision-space (MMOP) quality
OTHER = ["n_modes"]                                  # count, shown but not aggregated

DISP = {"A0_Full": r"\textbf{A0 Full}", "A1_noDMArchive": "A1", "A2_noRouteFamily": "A2",
        "A3_noEquivFitness": "A3", "A4_noNiching": "A4", "A5_noCrossMode": "A5",
        "A6_noConstraintAware": "A6", "A7_noPortfolio": "A7", "A8_BackboneOnly": "A8",
        "A9_noSparsityBonus": "A9"}
ROWLAB = {"IGD": "IGD", "IGDplus": "IGD$^+$", "HV": "HV", "spacing": "spacing",
          "IGDX": "IGDX", "PSP": "PSP", "mode_coverage": "mode\\_cov.", "n_modes": "\\#modes"}


def load():
    rows = list(csv.reader(open(ROOT / "results/statistics/ablation_ranks.csv")))
    hdr = rows[0][1:]
    data = {r[0]: dict(zip(hdr, map(float, r[1:]))) for r in rows[1:]}  # metric -> algo -> rank
    return hdr, data


def main():
    algos, data = load()
    L = [r"\begin{table}[t]", r"\centering",
         (r"\caption{Ablation on MMF1--8: average rank per metric (lower is better), "
          r"metrics grouped into a \emph{convergence} block and a \emph{decision-space} "
          r"(MMOP) block. An all-metric average is omitted because it conflates the "
          r"convergence/diversity trade-off---variants that collapse to one mode (e.g.\ A8) "
          r"win pure-convergence indicators yet are useless for MMOP; the decision-space "
          r"block is the MMOP-relevant aggregate. A0 (full) legend: A1 no decision-mode "
          r"archive, A2 no structure-family archive, A3 no equivalence fitness, A4 no niching, A5 no "
          r"cross-mode mating, A6 no constraint-aware selection, A7 no operator portfolio, "
          r"A8 backbone only, A9 no sparsity bonus.}"),
         r"\label{tab:ablation_rank}",
         r"\resizebox{\linewidth}{!}{%",
         r"\begin{tabular}{l" + "r" * len(algos) + "}", r"\toprule",
         " & " + " & ".join(DISP[a] for a in algos) + r" \\", r"\midrule",
         r"\multicolumn{" + str(len(algos) + 1) + r"}{l}{\emph{Convergence block}}\\"]

    def row(metric, lab=None):
        return (ROWLAB.get(metric, metric) if lab is None else lab) + " & " + \
            " & ".join(f"{data[metric][a]:.2f}" for a in algos) + r" \\"

    def mean_row(metrics, lab):
        vals = {a: sum(data[m][a] for m in metrics) / len(metrics) for a in algos}
        cells = " & ".join((r"\textbf{" + f"{vals[a]:.2f}" + "}") if a == "A0_Full"
                           else f"{vals[a]:.2f}" for a in algos)
        return lab + " & " + cells + r" \\"

    for m in CONV:
        L.append(row(m))
    L.append(r"\rowcolor{black!4}" if False else "")  # (no colour dep)
    L = [x for x in L if x != ""]
    L.append(r"\;\;\emph{convergence mean} & " +
             " & ".join(f"{sum(data[m][a] for m in CONV)/len(CONV):.2f}" for a in algos) + r" \\")
    L.append(r"\midrule")
    L.append(r"\multicolumn{" + str(len(algos) + 1) + r"}{l}{\emph{Decision-space (MMOP) block}}\\")
    for m in DEC:
        L.append(row(m))
    L.append(r"\;\;\textbf{decision-space mean} & " +
             " & ".join(f"{sum(data[m][a] for m in DEC)/len(DEC):.2f}" for a in algos) + r" \\")
    L.append(r"\midrule")
    for m in OTHER:
        L.append(row(m))
    L += [r"\bottomrule", r"\end{tabular}}", r"\end{table}"]

    out = ROOT / "results/tables/ablation_avg_rank.tex"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\n[ok] wrote {out}")


if __name__ == "__main__":
    main()
