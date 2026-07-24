"""Controlled novelty experiment table: isolate placement vs form of the sparsity term.
Reads results/raw/novelty and emits a LaTeX table with per-variant means + the paired
Wilcoxon verdicts of the proposed within-front key against the counterfactuals.
"""
import json, glob
from pathlib import Path
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
V = [("Mult_within", r"Multiplicative equivalence key $E(1{+}\beta S)$ (\textbf{ours})"),
     ("Add_within",  r"Additive equivalence key $E{+}\beta\,\mathrm{med}(E)\,S$"),
     ("Penalized",   r"Penalised-density key (CPDEA-style)"),
     ("NoS_equiv",   r"No sparsity ($D{=}E$)")]
METRICS = ["IGD", "IGDX", "HV", "mode_coverage"]
probs = sorted({f.split("/")[-3] for f in glob.glob(f"{ROOT}/results/raw/novelty/*/*/run_*.json")})


def per_run(v, m):
    return [json.load(open(f))["metrics"][m]
            for f in glob.glob(f"{ROOT}/results/raw/novelty/*/{v}/run_*.json")]


def per_prob(v, m):
    return np.array([np.mean([json.load(open(f))["metrics"][m]
                              for f in glob.glob(f"{ROOT}/results/raw/novelty/{p}/{v}/run_*.json")])
                     for p in probs])


def wtl(ref, other, m, lower):
    a, b = per_prob(ref, m), per_prob(other, m)
    p = 1.0 if np.allclose(a, b) else stats.wilcoxon(a, b).pvalue
    better = int((a < b).sum() if lower else (a > b).sum())
    return better, len(probs) - better, p


L = [r"\begin{table}[t]", r"\centering\small",
     (r"\caption{Within-front \emph{key form}: comparison of within-front selection keys on "
      r"MMF1--8 (EARS, 30 runs, identical protocol; only the within-front key changes). Mean "
      r"indicator values and, in the last rows, the paired Wilcoxon verdict (win/tie/loss over "
      r"8 problems, $p$) of the proposed key vs each alternative. \emph{The multiplicative and "
      r"additive equivalence keys are statistically indistinguishable}, so the multiplicative "
      r"form is not the source of the gain; the equivalence key also beats a CPDEA-style "
      r"penalised-density key within the front (IGD $8/0/0$). This table varies the key; the "
      r"orthogonal question of where $S$ is \emph{placed} (within-front vs in the dominance "
      r"sort) is isolated in Table~\ref{tab:isolation}.}"),
     r"\label{tab:novelty}",
     r"\resizebox{\linewidth}{!}{%",
     r"\begin{tabular}{lcccc}", r"\toprule",
     r"Selection key & IGD & IGDX & HV & mode\_cov \\", r"\midrule"]
for v, lab in V:
    L.append(f"{lab} & " + " & ".join(f"{np.mean(per_run(v, m)):.4f}" if m != "HV"
                                      else f"{np.mean(per_run(v, m)):.3f}" for m in METRICS) + r" \\")
L += [r"\midrule",
      r"\multicolumn{5}{l}{\emph{Proposed (within-front mult.) vs counterfactual --- Wilcoxon W/T/L ($p$):}}\\"]
for v, lab in V[1:]:
    igd = wtl("Mult_within", v, "IGD", True)
    igx = wtl("Mult_within", v, "IGDX", True)
    short = {"Add_within": "vs additive key", "Penalized": "vs penalised-density key",
             "NoS_equiv": "vs no sparsity"}[v]
    L.append(f"\\quad {short} & \\multicolumn{{2}}{{l}}{{IGD {igd[0]}/{igd[1]}/{8-igd[0]-igd[1]} "
             f"($p{{=}}{igd[2]:.3f}$)}} & \\multicolumn{{2}}{{l}}{{IGDX {igx[0]}/{igx[1]}/{8-igx[0]-igx[1]} "
             f"($p{{=}}{igx[2]:.3f}$)}} \\\\")
L += [r"\bottomrule", r"\end{tabular}}", r"\end{table}"]
out = ROOT / "results/tables/novelty.tex"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L)); print(f"\n[ok] {out}")
