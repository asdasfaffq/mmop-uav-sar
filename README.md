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

Headline claims, each reproducible from the scripts below.

- **Five real OSM cities, emergency-facility placement: EARS-MMOEA is rank-1 on the
  five-city average** on both the full suite (3.13) and the core reference-based suite
  (2.33), over **eight** methods including a non-multimodal NSGA-II control.
  Per city it is rank-1 on the full suite in 4 of 5 and on the core suite in 3 of 5;
  **Hong Kong and the Shenzhen core suite go to Omni-optimizer, and we report that.**
- **Reference sets are independent.** Case-study metrics are scored against a separate
  high-budget panel (5x budget, four methods, disjoint seed stream) that no compared
  method contributed to. The conventional self-inclusive reference yields the *same*
  rankings; average ranks move by at most 0.06.
- **The placement rule transfers.** Attached at its frozen default weight, with no
  per-backbone tuning, the within-front sparsity term improves decision-space quality on
  DN-NSGA-II, Omni-optimizer and MO_Ring_PSO_SCD with **zero losses**; the untouched
  control arms reproduce the benchmark runs bit-for-bit (720 runs, 0 mismatches).
- **A refutation of our own earlier claim, kept in the record.** Sweeping the in-sort
  fusion weight to 32 (an earlier version stopped at 1, where both axes were still
  improving) shows in-sort fusion *matches* the within-front key on coverage and *beats*
  it on convergence inside our framework. What survives is a robustness claim, not a
  superiority claim: 1.03x vs 3.29x weight sensitivity, and no dependence on an archive
  to repair convergence (established causally in `run_archive_masking.py`).
- **Post-planning resilience, including a metric trap.** Over 72,000 constraint scenarios
  with no re-optimization allowed, portfolios absorb 92-100% of constraints — but the
  *highest* recovery rate belongs to the baseline that collapses to ~2 modes, because an
  unconverged scattered set almost always dodges an unforeseen constraint. Recovery rate
  rewards non-convergence; post-switch service level is the defensible criterion, and by
  that measure EARS is best of eight.
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

Controlled studies and the case-study evaluation reported in the paper:

```bash
# Where the diversity term is applied: sweep the in-sort weight far enough for the curve to turn
python experiments/run_insort_sweep.py       --params configs/selected_params.yaml

# Causal test of archive masking: toggles ONLY the reporting rule inside one algorithm
python experiments/run_archive_masking.py
python experiments/analyze_archive_masking.py

# Does the rule transfer to other published algorithms? (untuned, frozen beta)
python experiments/run_transfer.py
python experiments/analyze_transfer.py

# Independent high-budget reference sets, then re-score the case study against them
python experiments/run_independent_reference.py     # ~180 runs at 5x budget
python experiments/rescore_independent.py
for e in placement placement_guangzhou placement_shenzhen placement_sanfrancisco placement_hongkong; do
  python experiments/run_statistics.py --results results/raw --experiment ${e}_indref --reference EARS_MMOEA
done

# Post-planning constraint resilience (post-processes saved layouts; no re-optimization)
python experiments/run_posthoc_resilience.py
```

> The honest supplementary UAV-routing study: `python experiments/run_uav_sar.py --config
> configs/uav_sar.yaml --params configs/selected_params.yaml` (EARS competitive, not rank-1).

### What is and is not in this repository

Per-run raw outputs (`results/raw/`, ~430 MB) are **not** mirrored here. Every run derives from
a fixed, algorithm-independent seed protocol (`utils/seeds.py`), so the scripts above regenerate
them bit-for-bit; `verify_paper_numbers.py` re-derives every number quoted in the paper from
those outputs. The independent high-budget reference sets (`results/reference/`, 108 KB) **are**
included, because they are the one input that cannot be re-derived from a seed alone.

All randomness derives from a single master seed (`utils/seeds.GLOBAL_SEED`) via
a fixed, auditable protocol.

## License

MIT (see `LICENSE`).
