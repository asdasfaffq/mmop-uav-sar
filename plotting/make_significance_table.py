"""Explicit Friedman post-hoc significance table (Demsar): EARS as the control method,
Holm-adjusted p-values for EARS vs each baseline. Complements the per-problem
Wilcoxon-signed-rank + Holm win/tie/loss already reported, by giving the omnibus
post-hoc p-values SWEVO reviewers expect. Computed for the benchmark primary metric
(IGDX) and for the application (per-city core-suite ranks)."""
import csv, glob, json
from pathlib import Path
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DISP = {"EARS_MMOEA": "EARS", "CPDEA": "CPDEA", "DN_NSGAII": "DN-NSGA-II", "MMEA_WI": "MMEA-WI",
        "MO_Ring_PSO_SCD": r"MO\_Ring", "OmniOptimizer": "Omni", "HREA": "HREA"}
CORE = ["HV", "IGD_ref", "IGDX_ref"]   # n_modes excluded (metric-search geometry alignment)
CITIES = ["placement", "placement_guangzhou", "placement_shenzhen",
          "placement_sanfrancisco", "placement_hongkong"]


def holm_posthoc(rank_per_block, algos, ctrl="EARS_MMOEA"):
    """rank_per_block: (N_blocks, k) average-rank matrix. Returns control mean rank +
    list of (algo, mean_rank, z, p_holm)."""
    R = rank_per_block.mean(0)
    k = len(algos); N = rank_per_block.shape[0]
    SE = np.sqrt(k * (k + 1) / (6.0 * N))
    ci = algos.index(ctrl)
    rows = []
    for j, a in enumerate(algos):
        if a == ctrl:
            continue
        z = (R[j] - R[ci]) / SE
        p = 2 * (1 - stats.norm.cdf(abs(z)))
        rows.append([a, R[j], z, p])
    rows.sort(key=lambda r: r[3]); m = len(rows)
    prev = 0.0
    for i, r in enumerate(rows):              # proper Holm step-down (cumulative max)
        prev = max(prev, min(1.0, (m - i) * r[3]))
        r.append(prev)
    return R[ci], rows


def bench_igdx_blocks():
    # per-problem IGDX ranks (N=8 problems, k=7)
    d = {}
    algos = None
    for jp in glob.glob(f"{ROOT}/results/raw/benchmark/*/*/run_*.json"):
        r = json.load(open(jp)); d.setdefault(r["problem"], {}).setdefault(r["algorithm"], []).append(r["metrics"]["IGDX"])
    probs = sorted(d); algos = sorted(next(iter(d.values())))
    M = np.array([[np.mean(d[p][a]) for a in algos] for p in probs])
    R = np.array([stats.rankdata(row) for row in M])   # lower IGDX = rank 1
    return R, algos


def place_core_blocks():
    # per-city core-suite mean rank (N=5 cities, k=7)
    def city_corerank(exp):
        rows = list(csv.reader(open(f"{ROOT}/results/statistics/{exp}_ranks.csv")))
        hdr = rows[0][1:]; data = {x[0]: dict(zip(hdr, map(float, x[1:]))) for x in rows[1:]}
        return hdr, {a: np.mean([data[m][a] for m in CORE]) for a in hdr}
    hdr, _ = city_corerank("placement")
    M = np.array([[city_corerank(c)[1][a] for a in hdr] for c in CITIES])
    R = np.array([stats.rankdata(row) for row in M])   # lower core-rank = better
    return R, hdr


def emit():
    L = [r"\begin{table}[t]", r"\centering\small",
         (r"\caption{Friedman post-hoc significance (Dem\v{s}ar), \textbf{EARS-MMOEA as control}: "
          r"Holm-adjusted $p$-values of EARS vs each baseline, on the benchmark primary metric "
          r"IGDX ($N{=}8$ problems) and the application core suite ($N{=}5$ cities). "
          r"$z>0$ favours EARS; $^{*}$ marks Holm $p<0.05$. This complements the per-problem "
          r"Wilcoxon-signed-rank + Holm win/tie/loss reported elsewhere.}"),
         r"\label{tab:significance}",
         r"\begin{tabular}{lcc@{\quad}cc}", r"\toprule",
         r"& \multicolumn{2}{c}{Benchmark IGDX ($N{=}8$)} & \multicolumn{2}{c}{Application core ($N{=}5$)}\\",
         r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
         r"EARS vs & $z$ & Holm $p$ & $z$ & Holm $p$ \\", r"\midrule"]
    Rb, ab = bench_igdx_blocks(); cb, rowsb = holm_posthoc(Rb, ab)
    Rp, ap = place_core_blocks(); cp, rowsp = holm_posthoc(Rp, ap)
    db = {r[0]: r for r in rowsb}; dp = {r[0]: r for r in rowsp}
    order = ["CPDEA", "MMEA_WI", "HREA", "MO_Ring_PSO_SCD", "DN_NSGAII", "OmniOptimizer"]
    for a in order:
        b = db.get(a); p = dp.get(a)
        bz = f"{b[2]:.2f}" if b else "--"; bp = (f"{b[4]:.3f}" + ("$^{*}$" if b[4] < 0.05 else "")) if b else "--"
        pz = f"{p[2]:.2f}" if p else "--"; pp = (f"{p[4]:.3f}" + ("$^{*}$" if p[4] < 0.05 else "")) if p else "--"
        L.append(f"{DISP[a]} & {bz} & {bp} & {pz} & {pp} " + r"\\")
    L += [r"\bottomrule", r"\end{tabular}",
          r"\par\smallskip\footnotesize EARS control mean rank: IGDX "
          f"{cb:.2f}; application core {cp:.2f}.",
          r"\end{table}"]
    out = ROOT / "results/tables/significance.tex"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print(f"\n[ok] {out}")


if __name__ == "__main__":
    emit()
