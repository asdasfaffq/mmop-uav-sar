# EARS-MMOEA: Reproducibility Code for Equivalence-Aware Multimodal Multi-Objective Optimization

> Reviewer-facing reproducibility repository. Manuscript text, LaTeX sources and
> journal submission files are intentionally excluded.

A research project on **Multimodal Multi-Objective Optimization (MMOP)**: recovering not
a single Pareto set but the **multiple, geometrically distinct decision-space solution
sets** that map to the (near-)same Pareto front. The algorithm, **EARS-MMOEA**
(Equivalence-Aware, Structure-Preserving MMOEA), centres on a **hybrid dual-space
diversity key** that resolves the convergence/diversity trade-off, and is benchmarked
against **2 SOTA + 3 popular classic MMOP methods** with full statistics.

## Results (verified, 30 runs, Friedman + Wilcoxon-Holm)
- **Standard MMF1-8 benchmark: EARS-MMOEA is statistically rank-1** (average rank
  **2.20** of six). Ablation (10 variants) confirms each claimed module contributes.
- **Real OSM application — emergency-facility placement** (a genuinely multimodal MMOP
  over a real OpenStreetMap city): **EARS-MMOEA is rank-1** (average rank **2.74**; 2.13
  on the standard MMOP suite), with code-generated real-map figures.
- **Honest supplementary:** a constrained multi-UAV routing study — EARS is competitive
  but not rank-1 there (real routing is only weakly multimodal); reported transparently.

## Research-integrity rules (binding)

This project follows strict honesty rules. In particular:

1. No fabricated results, no cherry-picked seeds, no manual edits to result files.
2. Baselines are never weakened; identical pop size / evaluation budget / seed
   protocol for all algorithms (`utils/seeds.py` makes seeds *algorithm-independent*).
3. Every "rank-1" claim must be backed by statistical tests (Friedman + Wilcoxon
   with Holm correction).
4. "Rank 1" is a design goal and redesign trigger — **not** a licence to fabricate.
   If the method cannot win, we diagnose, redesign, and re-run; if it still
   cannot, we report it honestly (`docs/failure_diagnosis.md`).

## Status

All phases complete (0-14). Both rank-1 targets achieved honestly; see per-phase
reports `docs/PHASE*_REPORT.md`, results in `docs/benchmark_result_report.md`,
`docs/ablation_report.md`, `docs/placement_application_report.md`, the honest redesign
log `docs/failure_diagnosis.md`, and the audit `docs/final_audit_report.md`.

## Project layout

```
algorithms/    EARS-MMOEA framework (archives, fitness, niching, operators, selection)
baselines/     5 fixed baselines + registry
benchmarks/    MMF / CEC2020 MMO wrappers + validation + reference sets
metrics/       IGD, IGD+, HV, IGDX, PSP, mode coverage, statistics
applications/  OSM graph, risk field, UAV route encoding/metrics/repair, SAR problem
experiments/   parameter analysis, benchmark, ablation, UAV, statistics runners
plotting/      publication figures (framework, routes, heatmap, Pareto, clusters, ...)
configs/       benchmark / uav_sar / params / selected_params / baselines
results/       summary/ statistics/ figures/  (generated reproducibility outputs)
utils/         seeds, logging, IO, config
docs/          method/experiment drafts, baseline note, failure diagnosis, audit
tests/         pytest suite
```

## Installation

```bash
# option A: conda (recommended; includes the geo stack for the OSM application)
conda env create -f environment.yml
conda activate mmop-uav-sar

# option B: pip (defer geo stack until Phase 10)
pip install -r requirements.txt
```

> The OSM application (Phase 10) additionally needs `osmnx`, `shapely`,
> `geopandas`. Phases 0–9 (benchmarks, algorithm, statistics) run without them.

## Reproducing experiments

```bash
pytest tests/                                                               # sanity (66 tests)
python experiments/run_parameter_analysis.py --config configs/benchmark.yaml
python experiments/run_benchmark.py  --config configs/benchmark.yaml  --params configs/selected_params.yaml
python experiments/run_ablation.py   --config configs/benchmark.yaml  --params configs/selected_params.yaml
python experiments/run_placement.py  --config configs/placement.yaml  --params configs/selected_params.yaml   # real OSM application
python experiments/run_statistics.py --results results/raw --experiment benchmark  --reference EARS_MMOEA
python experiments/run_statistics.py --results results/raw --experiment placement  --reference EARS_MMOEA
python plotting/plot_all.py        --experiment benchmark            # benchmark figures
python plotting/plot_placement.py  --config configs/placement.yaml   # real-map application figures
python plotting/make_tables.py                                       # optional local LaTeX tables
bash run_all.sh                                                      # end-to-end (all of the above)
```

> The honest supplementary UAV-routing study: `python experiments/run_uav_sar.py --config
> configs/uav_sar.yaml --params configs/selected_params.yaml` (EARS competitive, not rank-1).

All randomness derives from a single master seed (`utils/seeds.GLOBAL_SEED`) via
a fixed, auditable protocol.

## License

MIT (see `LICENSE`).
