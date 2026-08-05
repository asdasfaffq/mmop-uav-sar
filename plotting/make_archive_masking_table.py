"""Generate the archive-masking table (paper/tables/archive_masking.tex).

The 2x2 causal test: {within-front, in-sort at its best weight} x {report population
+ archives, report population only}, inside EARS with everything but the reporting rule
held fixed. Numbers come straight from results/raw/archive_masking/**.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from metrics.statistics import wilcoxon_holm  # noqa: E402

RAW = ROOT / "results/raw/archive_masking"
PROBS = [f"MMF{i}" for i in range(1, 9)]
BLOCKS = [
    (r"population $\cup$ archives", ["WF_arch", "InSort8_arch", "NoS_arch"]),
    (r"population only", ["WF_pop", "InSort8_pop", "NoS_pop"]),
]
LABEL = {
    "WF_arch": r"\textbf{within-front (ours)}",
    "InSort8_arch": r"in the dominance sort ($\lambda{=}8$)",
    "NoS_arch": r"no $S$ (reference)",
    "WF_pop": r"\textbf{within-front (ours)}",
    "InSort8_pop": r"in the dominance sort ($\lambda{=}8$)",
    "NoS_pop": r"no $S$ (reference)",
}

CAPTION = r"""Does the gap between selection designs survive without the archives?
The \emph{same} sparsity signal $S$ is placed within the splitting front (ours) or fused into the
dominance sort at $\lambda{=}8$, the weight at which in-sort fusion is strongest
(Figure~\ref{fig:insort}); everything else --- algorithm, operators, niching, budget and the
algorithm-independent seeds --- is held fixed, and only the \emph{reporting rule} differs between
the two blocks. With the archives included (top) the two placements are close, because the Pareto
archive retains converged solutions and repairs the damage the in-sort key inflicts on the
population. Reporting the population alone (bottom) removes that repair: the within-front key is
unaffected, while in-sort fusion collapses. The advantage of within-front placement is therefore
independence from external convergence repair, not a higher attainable quality. W/T/L is the
within-front variant against the in-sort variant (paired Wilcoxon, Holm-corrected over MMF1--8,
$30$ runs, $\alpha{=}0.05$)."""


def load():
    per = defaultdict(lambda: defaultdict(dict))
    for jf in RAW.glob("*/*/run_*.json"):
        r = json.loads(jf.read_text())
        for m in ("IGD", "IGDX"):
            per[m].setdefault(r["problem"], {}).setdefault(r["algorithm"], {})[r["run_index"]] = \
                r["metrics"][m]
    return {m: {p: {a: np.array([v[k] for k in sorted(v)]) for a, v in am.items()}
                for p, am in pm.items()} for m, pm in per.items()}


def main():
    per = load()
    mean = {a: {m: float(np.mean([per[m][p][a].mean() for p in PROBS]))
                for m in ("IGD", "IGDX")}
            for _, arms in BLOCKS for a in arms}

    wtl = {}
    for ref, other in [("WF_arch", "InSort8_arch"), ("WF_pop", "InSort8_pop")]:
        cells = []
        for m in ("IGD", "IGDX"):
            res = wilcoxon_holm(per[m], PROBS, [ref, other], reference=ref,
                                lower_better=True, alpha=0.05)
            w, t, l = res.wtl[other]
            cells.append(f"{m} {w}/{t}/{l}")
        wtl[ref] = ", ".join(cells)

    lines = []
    for bi, (block, arms) in enumerate(BLOCKS):
        if bi:
            lines.append(r"\midrule")
        for ai, a in enumerate(arms):
            first = block if ai == 0 else ""
            note = wtl.get(a, "")
            lines.append(f"{first} & {LABEL[a]} & {mean[a]['IGD']:.4f} & "
                         f"{mean[a]['IGDX']:.4f} & {note} \\\\")

    tex = (
        "\\begin{table}[t]\n\\centering\\small\n"
        f"\\caption{{{CAPTION}}}\n"
        "\\label{tab:archive_masking}\n"
        "\\resizebox{\\linewidth}{!}{%\n"
        "\\begin{tabular}{llrrl}\n\\toprule\n"
        "reported set & placement of $S$ & IGD & IGDX & W/T/L (within-front vs in-sort) \\\\\n"
        "\\midrule\n" + "\n".join(lines) + "\n"
        "\\bottomrule\n\\end{tabular}}\n\\end{table}\n"
    )
    out = ROOT / "paper/tables/archive_masking.tex"
    out.write_text(tex)
    print(tex)
    for _, arms in BLOCKS:
        for a in arms:
            n = len(list((RAW / PROBS[0] / a).glob("run_*.json")))
            print(f"   {a:14s} IGD={mean[a]['IGD']:.5f} IGDX={mean[a]['IGDX']:.5f} "
                  f"(runs on {PROBS[0]}={n})")


if __name__ == "__main__":
    main()
