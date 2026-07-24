"""Re-evaluate the five-city placement decision-space metric (IGDX) with the EXACT
Hungarian set-matching distance instead of the sorted-coordinate Euclidean surrogate,
from the already-saved layouts (no re-search). Verifies the core-suite ranking is not
an artefact of the canonical-sort approximation (reviewer point 6).

For each city we rebuild the combined reference Pareto set exactly as the experiment
does (union of all algorithms' canonicalised non-dominated layouts, capped), then
recompute, per algorithm, IGDX under both distances and the resulting average rank.
For tractability the reference set and obtained sets are subsampled identically for
every algorithm (so the comparison stays fair).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.io_utils import RAW_DIR, load_run
from applications.app_metrics import igdx_hungarian
from applications.placement_problem import FacilityPlacementProblem
from applications.osm_graph_builder import build_flight_graph
from algorithms.equivalence_fitness import fast_nondominated_sort
from scipy.stats import rankdata

CITIES = [("Macau", "placement"), ("Guangzhou", "placement_guangzhou"),
          ("Shenzhen", "placement_shenzhen"), ("San Francisco", "placement_sanfrancisco"),
          ("Hong Kong", "placement_hongkong")]
ALGOS = ["EARS_MMOEA", "CPDEA", "DN_NSGAII", "MMEA_WI", "MO_Ring_PSO_SCD", "OmniOptimizer", "HREA"]
N_REF, N_OBT = 40, 20           # identical subsampling for every algorithm (fair);
                                # the rank among 7 algorithms is robust to it


def _instances(exp):
    return sorted({p.name for p in (RAW_DIR / exp).glob("*") if p.is_dir()})


def main():
    rng = np.random.default_rng(0)
    core_euc = {a: [] for a in ALGOS}
    core_hun = {a: [] for a in ALGOS}
    for name, exp in CITIES:
        igdx_e = {a: [] for a in ALGOS}
        igdx_h = {a: [] for a in ALGOS}
        insts = _instances(exp)
        # feature_map geometry depends only on the city graph (not the demand seed),
        # so build one problem per city and reuse it for all instances.
        city = insts[0].split("_p")[0]
        sample = next((RAW_DIR / exp / insts[0] / ALGOS[0]).glob("run_*.json"))
        K = load_run(sample)["arrays"]["decisions"].shape[1] // 2
        prob = FacilityPlacementProblem(build_flight_graph(city), n_stations=K, seed=0)
        for inst in insts:
            allF, allPS = [], []
            runs = {a: [] for a in ALGOS}
            for a in ALGOS:
                for jp in sorted((RAW_DIR / exp / inst / a).glob("run_*.json")):
                    rec = load_run(jp); F = rec["arrays"]["objectives"]; X = rec["arrays"]["decisions"]
                    nd = fast_nondominated_sort(F)[0]
                    Xc = prob.feature_map(X[nd])
                    runs[a].append(Xc)
                    allF.append(F); allPS.append(prob.feature_map(X[nd]))
            if not allPS:
                continue
            refPS = np.vstack(allPS)
            if len(refPS) > N_REF:
                refPS = refPS[rng.choice(len(refPS), N_REF, replace=False)]
            for a in ALGOS:
                for Xc in runs[a]:
                    Xo = Xc if len(Xc) <= N_OBT else Xc[rng.choice(len(Xc), N_OBT, replace=False)]
                    euc = float(np.linalg.norm(refPS[:, None, :] - Xo[None, :, :], axis=2).min(1).mean())
                    hun = igdx_hungarian(refPS, Xo, K)
                    igdx_e[a].append(euc); igdx_h[a].append(hun)
        me = {a: np.mean(igdx_e[a]) for a in ALGOS}
        mh = {a: np.mean(igdx_h[a]) for a in ALGOS}
        re_ = dict(zip(ALGOS, rankdata([me[a] for a in ALGOS])))
        rh = dict(zip(ALGOS, rankdata([mh[a] for a in ALGOS])))
        for a in ALGOS:
            core_euc[a].append(re_[a]); core_hun[a].append(rh[a])
        ew = min(me, key=me.get); hw = min(mh, key=mh.get)
        print(f"{name:14s} IGDX Euclid: EARS {me['EARS_MMOEA']:.4f} (rank {re_['EARS_MMOEA']:.0f}, best {ew.split('_')[0]}) | "
              f"Hungarian: EARS {mh['EARS_MMOEA']:.4f} (rank {rh['EARS_MMOEA']:.0f}, best {hw.split('_')[0]})", flush=True)
    print("\n=== mean IGDX rank across 5 cities ===")
    for a in sorted(ALGOS, key=lambda a: np.mean(core_hun[a])):
        print(f"  {a:18s} Euclid {np.mean(core_euc[a]):.2f}  Hungarian {np.mean(core_hun[a]):.2f}")


if __name__ == "__main__":
    main()
