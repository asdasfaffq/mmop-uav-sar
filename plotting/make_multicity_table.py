"""Emit the multi-city placement generalization table (full-suite avg rank per
algorithm per real OSM city), reading the per-city *_ranks.csv. EARS-MMOEA is
bolded where it is rank-1; Hong Kong (not rank-1 on the core suite) is flagged.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ["HV", "IGD_ref", "IGDX_ref"]   # n_modes excluded: search and metric share a
                                        # silhouette-k-means geometry (alignment risk), so the
                                        # core suite uses only reference-based indicators
CITIES = [("Macau", "placement"), ("Guangzhou", "placement_guangzhou"),
          ("Shenzhen", "placement_shenzhen"),
          ("San Francisco", "placement_sanfrancisco"),
          ("Hong Kong", "placement_hongkong")]
ALGOS = ["EARS_MMOEA", "CPDEA", "DN_NSGAII", "MMEA_WI", "MO_Ring_PSO_SCD", "OmniOptimizer", "HREA"]
DISP = {"EARS_MMOEA": "EARS", "CPDEA": "CPDEA", "DN_NSGAII": "DN-NSGA-II",
        "MMEA_WI": "MMEA-WI", "MO_Ring_PSO_SCD": r"MO\_Ring", "OmniOptimizer": "Omni", "HREA": "HREA"}


def ranks(exp):
    rows = list(csv.reader(open(ROOT / f"results/statistics/{exp}_ranks.csv")))
    hdr = rows[0][1:]
    data = {r[0]: dict(zip(hdr, map(float, r[1:]))) for r in rows[1:]}
    full = {a: sum(d[a] for d in data.values()) / len(data) for a in hdr}
    core = {a: sum(data[m][a] for m in CORE) / len(CORE) for a in hdr}
    return full, core


L = [r"\begin{table}[t]", r"\centering\small",
     (r"\caption{Generalization across five real OSM cities (7 algorithms incl.\ HREA): "
      r"full-suite average rank (7 metrics) per algorithm under the identical frozen protocol "
      r"(30 runs). The bottom \textbf{Average} row is the mean rank over all five cities. "
      r"EARS-MMOEA is rank-1 on the five-city average on both suites (full $2.71$, core "
      r"$1.94$; next HREA $3.37$/$3.21$) and rank-1 \emph{individually} on the full suite of "
      r"all five cities; on the core suite it is rank-1 on three (Macau, Guangzhou, "
      r"San~Francisco) and second to Omni-optimizer on two (Shenzhen, Hong~Kong), which we "
      r"report. The \emph{core suite is the three reference-based indicators} (HV, IGD, IGDX); "
      r"$\#$modes is excluded because the search and that metric share a silhouette-$k$-means "
      r"geometry. The last column is EARS's per-city core-suite average rank.}"),
     r"\label{tab:placement_multicity}",
     r"\resizebox{\linewidth}{!}{%",
     r"\begin{tabular}{l" + "c" * len(ALGOS) + "c}", r"\toprule",
     "City & " + " & ".join(DISP[a] for a in ALGOS) + r" & EARS core \\", r"\midrule"]

full_acc = {a: [] for a in ALGOS}
core_acc = {a: [] for a in ALGOS}
for name, exp in CITIES:
    full, core = ranks(exp)
    for a in ALGOS:
        full_acc[a].append(full[a]); core_acc[a].append(core[a])
    win = min(full, key=full.get)
    cells = []
    for a in ALGOS:
        v = f"{full[a]:.2f}"
        if a == "EARS_MMOEA" and win == "EARS_MMOEA":
            v = r"\textbf{" + v + "}"
        cells.append(v)
    cwin = min(core, key=core.get)
    ctag = f"{core['EARS_MMOEA']:.2f}" + ("" if cwin == "EARS_MMOEA" else r"$^\dagger$")
    L.append(name + " & " + " & ".join(cells) + " & " + ctag + r" \\")

# summary row: mean rank across the five cities
favg = {a: sum(full_acc[a]) / len(CITIES) for a in ALGOS}
cavg_ears = sum(core_acc["EARS_MMOEA"]) / len(CITIES)
fwin = min(favg, key=favg.get)
scells = []
for a in ALGOS:
    v = f"{favg[a]:.2f}"
    if a == "EARS_MMOEA" and fwin == "EARS_MMOEA":
        v = r"\textbf{" + v + "}"
    scells.append(v)
L.append(r"\midrule")
L.append(r"\textbf{Average (5 cities)} & " + " & ".join(scells)
         + r" & \textbf{" + f"{cavg_ears:.2f}" + r"} \\")

L += [r"\bottomrule", r"\end{tabular}}",
      (r"\par\smallskip\footnotesize $^\dagger$Core-suite second to Omni-optimizer "
       r"(Shenzhen $2.06$ vs $2.17$; Hong~Kong $2.22$ vs $2.56$), but rank-1 on the full suite. "
       r"On the five-city average EARS is rank-1 on both the core and the full suites."),
      r"\end{table}"]

out = ROOT / "results/tables/placement_multicity.tex"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
print(f"\n[ok] wrote {out}")
