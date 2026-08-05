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
# Primary evaluation uses the INDEPENDENT high-budget reference (Appendix): the scored
# algorithms did not contribute to the yardstick. Set REF_SUFFIX="" to reproduce the
# self-inclusive-reference numbers, which give the same rankings.
REF_SUFFIX = "_indref"
CITIES = [("Macau", "placement" + REF_SUFFIX),
          ("Guangzhou", "placement_guangzhou" + REF_SUFFIX),
          ("Shenzhen", "placement_shenzhen" + REF_SUFFIX),
          ("San Francisco", "placement_sanfrancisco" + REF_SUFFIX),
          ("Hong Kong", "placement_hongkong" + REF_SUFFIX)]
ALGOS = ["EARS_MMOEA", "CPDEA", "DN_NSGAII", "MMEA_WI", "MO_Ring_PSO_SCD", "OmniOptimizer",
         "HREA", "NSGAII"]
DISP = {"EARS_MMOEA": "EARS", "CPDEA": "CPDEA", "DN_NSGAII": "DN-NSGA-II",
        "MMEA_WI": "MMEA-WI", "MO_Ring_PSO_SCD": r"MO\_Ring", "OmniOptimizer": "Omni", "HREA": "HREA",
        "NSGAII": "NSGA-II$^{c}$"}


def ranks(exp):
    rows = list(csv.reader(open(ROOT / f"results/statistics/{exp}_ranks.csv")))
    hdr = rows[0][1:]
    data = {r[0]: dict(zip(hdr, map(float, r[1:]))) for r in rows[1:]}
    full = {a: sum(d[a] for d in data.values()) / len(data) for a in hdr}
    core = {a: sum(data[m][a] for m in CORE) / len(CORE) for a in hdr}
    return full, core


# --- derive the caption's factual claims from the data, never hardcode them -----
_per_city = {}
for _name, _exp in CITIES:
    _f, _c = ranks(_exp)
    _per_city[_name] = (_f, _c)
_avg_full = {a: sum(_per_city[n][0][a] for n, _ in CITIES) / len(CITIES) for a in ALGOS}
_avg_core = {a: sum(_per_city[n][1][a] for n, _ in CITIES) / len(CITIES) for a in ALGOS}
_ord_f = sorted(_avg_full, key=_avg_full.get); _ord_c = sorted(_avg_core, key=_avg_core.get)
_full_wins = [n for n, _ in CITIES if min(_per_city[n][0], key=_per_city[n][0].get) == "EARS_MMOEA"]
_core_wins = [n for n, _ in CITIES if min(_per_city[n][1], key=_per_city[n][1].get) == "EARS_MMOEA"]
_full_lost = [(n, min(_per_city[n][0], key=_per_city[n][0].get)) for n, _ in CITIES
              if n not in _full_wins]
_core_lost = [(n, min(_per_city[n][1], key=_per_city[n][1].get)) for n, _ in CITIES
              if n not in _core_wins]
def _lst(items):
    d = {"San Francisco": "San~Francisco", "Hong Kong": "Hong~Kong"}
    return ", ".join(d.get(x, x) for x in items)
def _lost(items):
    d = {"San Francisco": "San~Francisco", "Hong Kong": "Hong~Kong"}
    return ", ".join(f"{d.get(n, n)} to {DISP[a].replace('$^{c}$','')}" for n, a in items)

_cap = (
    r"\caption{Generalization across five real OSM cities under the identical frozen protocol "
    r"(30 runs): average rank per algorithm, full suite (7 metrics) and core suite. "
    r"$^{c}$NSGA-II is a \emph{control} carrying no decision-space machinery, included so the "
    r"ranking is not restricted to methods designed for this task. "
    r"The bottom \textbf{Average} row is the mean over the five cities. "
    f"EARS-MMOEA is rank-1 on the five-city average on both suites (full ${_avg_full['EARS_MMOEA']:.2f}$, "
    f"core ${_avg_core['EARS_MMOEA']:.2f}$; next {DISP[_ord_f[1]].replace('$^{{c}}$','')} "
    f"${_avg_full[_ord_f[1]]:.2f}$ and {DISP[_ord_c[1]].replace('$^{{c}}$','')} ${_avg_core[_ord_c[1]]:.2f}$). "
    f"Per city it is rank-1 on the full suite in {len(_full_wins)} of five ({_lst(_full_wins)})"
    + (f", losing {_lost(_full_lost)}" if _full_lost else "")
    + f", and on the core suite in {len(_core_wins)} of five ({_lst(_core_wins)})"
    + (f", losing {_lost(_core_lost)}" if _core_lost else "")
    + r". These per-city losses are reported rather than aggregated away. "
    r"The \emph{core suite is the three reference-based indicators} (HV, IGD, IGDX); "
    r"$\#$modes is excluded because the search and that metric share a silhouette-$k$-means "
    r"geometry. The last column is EARS's per-city core-suite average rank.}")

L = [r"\begin{table}[t]", r"\centering\small", _cap,
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
      (r"\par\smallskip\footnotesize $^\dagger$Core-suite rank-1 goes to another method in "
       + f"{len(_core_lost)} " + ("city" if len(_core_lost) == 1 else "cities") + ": "
       + _lost(_core_lost)
       + r". On the five-city average EARS is rank-1 on both the core and the full suites."),
      r"\end{table}"]

out = ROOT / "results/tables/placement_multicity.tex"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
print(f"\n[ok] wrote {out}")
