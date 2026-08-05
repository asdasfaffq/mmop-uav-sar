"""INDEPENDENT integrity re-computation: read raw run_*.json metrics directly
(NOT the pipeline CSVs) and recompute every headline number the paper cites.
If these match the paper text, the paper is faithful to the real runs.
"""
import json, glob, os
from collections import defaultdict
import numpy as np
from scipy import stats

ROOT = "/home/lyx/桌面/mmop-uav-sar"
LOWER = {"IGD": 1, "IGDplus": 1, "HV": 0, "IGDX": 1, "PSP": 0, "mode_coverage": 0,
         "n_modes": 0, "spacing": 1, "IGD_ref": 1, "IGDX_ref": 1, "placement_diversity": 0,
         "mean_access": 1, "max_access": 1}


def load(exp):
    """per_run[metric][problem][algo] = [vals]; also problems, algos."""
    d = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    probs, algos = set(), set()
    for jp in glob.glob(f"{ROOT}/results/raw/{exp}/*/*/run_*.json"):
        rec = json.load(open(jp))
        p, a = rec["problem"], rec["algorithm"]
        probs.add(p); algos.add(a)
        for m, v in rec["metrics"].items():
            d[m][p][a].append(float(v))
    return d, sorted(probs), sorted(algos)


def avg_rank(d, metric, probs, algos):
    M = np.full((len(probs), len(algos)), np.nan)
    for i, p in enumerate(probs):
        for j, a in enumerate(algos):
            if d[metric][p][a]:
                M[i, j] = np.mean(d[metric][p][a])
    R = np.full_like(M, np.nan)
    for i in range(M.shape[0]):
        row = M[i]; ok = ~np.isnan(row)
        vals = row[ok] if LOWER[metric] else -row[ok]
        R[i, ok] = stats.rankdata(vals, method="average")
    return dict(zip(algos, np.nanmean(R, axis=0)))


def holm(pvals):
    m = len(pvals); order = np.argsort(pvals); adj = [0.0]*m; run = 0.0
    for k, idx in enumerate(order):
        run = max(run, (m-k)*pvals[idx]); adj[idx] = min(run, 1.0)
    return adj


def wtl(d, metric, probs, ref, others, alpha=0.05):
    raw, pvals = [], []
    for p in probs:
        rv = np.asarray(d[metric][p][ref], float)
        for a in others:
            ov = np.asarray(d[metric][p][a], float)
            if len(rv)==0 or len(rv)!=len(ov): pv,mr,mo = np.nan,np.nan,np.nan
            elif np.allclose(rv-ov,0): pv,mr,mo = 1.0,np.median(rv),np.median(ov)
            else:
                try: pv = stats.wilcoxon(rv,ov,zero_method="wilcox").pvalue
                except ValueError: pv = 1.0
                mr,mo = np.median(rv),np.median(ov)
            raw.append((a,pv,mr,mo)); pvals.append(1.0 if np.isnan(pv) else pv)
    adj = holm(pvals); res = {a:[0,0,0] for a in others}
    for (a,pv,mr,mo),pa in zip(raw,adj):
        if np.isnan(pv) or pa>alpha: res[a][1]+=1
        else:
            better = (mr<mo) if LOWER[metric] else (mr>mo)
            res[a][0 if better else 2]+=1
    return {a:tuple(v) for a,v in res.items()}


def mean_metric(d, metric, probs, algo):
    vals = [v for p in probs for v in d[metric][p][algo]]
    return float(np.mean(vals)) if vals else float("nan")


print("="*70); print("BENCHMARK (MMF1-8)"); print("="*70)
d,probs,algos = load("benchmark")
print("problems:", probs); print("algos:", algos)
CORE = ["HV","IGD","IGDX","n_modes"]; STD4 = ["IGDX","PSP","mode_coverage","n_modes"]
ALL8 = ["IGD","IGDplus","HV","IGDX","PSP","mode_coverage","n_modes","spacing"]
for name,ms in [("std-4 (IGDX,PSP,mode_cov,n_modes)",STD4),("all-8",ALL8)]:
    per = {a: np.mean([avg_rank(d,m,probs,algos)[a] for m in ms]) for a in algos}
    best = min(per,key=per.get)
    print(f"  EARS avg rank [{name}] = {per['EARS_MMOEA']:.3f}  (best={best} {per[best]:.3f})")
oth = [a for a in algos if a!="EARS_MMOEA"]
for m in ["IGDX","PSP"]:
    w = wtl(d,m,probs,"EARS_MMOEA",oth); print(f"  EARS vs MMEA_WI on {m}: {w['MMEA_WI']}")
for m in ["IGD","HV","IGDX"]:
    w = wtl(d,m,probs,"EARS_MMOEA",oth); print(f"  EARS vs CPDEA on {m}: {w['CPDEA']}")

print(); print("="*70); print("ABLATION (MMF1-8)"); print("="*70)
d,probs,algos = load("ablation")
oth = [a for a in algos if a!="A0_Full"]
for m in ["IGDX","mode_coverage"]:
    w = wtl(d,m,probs,"A0_Full",oth)
    losses = {a:v for a,v in w.items() if v[2]>0}
    print(f"  A0_Full WTL on {m}: A8={w['A8_BackboneOnly']} A3={w['A3_noEquivFitness']} "
          f"A7={w['A7_noPortfolio']} A9={w['A9_noSparsityBonus']}  | any losses: {losses or 'NONE'}")
# % IGDX deltas (mean IGDX of variant vs A0)
igdx0 = mean_metric(d,"IGDX",probs,"A0_Full")
for a in ["A8_BackboneOnly","A3_noEquivFitness","A7_noPortfolio","A9_noSparsityBonus"]:
    iv = mean_metric(d,"IGDX",probs,a)
    print(f"  IGDX: A0={igdx0:.4f}  {a}={iv:.4f}  -> variant worse by {100*(iv-igdx0)/igdx0:.0f}%")

print(); print("="*70); print("PLACEMENT (5 cities)"); print("="*70)
CITIES = [("Macau","placement"),("Guangzhou","placement_guangzhou"),
          ("Shenzhen","placement_shenzhen"),("SanFrancisco","placement_sanfrancisco"),
          ("HongKong","placement_hongkong")]
# Core suite MUST match plotting/make_multicity_table.py: n_modes is excluded because
# the search and that metric share a silhouette-k-means geometry. Keeping n_modes here
# silently disagreed with the paper table (audit said core 2.06/2.93, table 1.94/3.21).
CORE4 = ["HV","IGD_ref","IGDX_ref"]
FULL7 = ["HV","IGD_ref","IGDX_ref","n_modes","placement_diversity","mean_access","max_access"]
fullacc, coreacc = defaultdict(list), defaultdict(list)
for disp,exp in CITIES:
    d,probs,algos = load(exp)
    full = {a: np.mean([avg_rank(d,m,probs,algos)[a] for m in FULL7]) for a in algos}
    core = {a: np.mean([avg_rank(d,m,probs,algos)[a] for m in CORE4]) for a in algos}
    for a in algos: fullacc[a].append(full[a]); coreacc[a].append(core[a])
    fb=min(full,key=full.get); cb=min(core,key=core.get)
    print(f"  {disp:13} full EARS={full['EARS_MMOEA']:.2f}(best {fb} {full[fb]:.2f}) "
          f"core EARS={core['EARS_MMOEA']:.2f}(best {cb} {core[cb]:.2f})")
print("  --- 5-city AVERAGE ---")
fa={a:np.mean(fullacc[a]) for a in fullacc}; ca={a:np.mean(coreacc[a]) for a in coreacc}
for lab,agg in [("full",fa),("core",ca)]:
    order=sorted(agg,key=agg.get)
    top3=", ".join("%s %.2f"%(a.split("_")[0],agg[a]) for a in order[:3])
    print("  %s: EARS=%.2f  ranking: %s"%(lab,agg['EARS_MMOEA'],top3))
# placement mean HV / modes (Macau)
d,probs,algos = load("placement")
print(f"  Macau mean HV: EARS={mean_metric(d,'HV',probs,'EARS_MMOEA'):.3f} "
      f"CPDEA={mean_metric(d,'HV',probs,'CPDEA'):.3f}")
print(f"  Macau mean n_modes: EARS={mean_metric(d,'n_modes',probs,'EARS_MMOEA'):.2f} "
      f"CPDEA={mean_metric(d,'n_modes',probs,'CPDEA'):.2f}")
