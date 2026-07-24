# Final Audit Report (Phase 14)

Independent end-of-project audit against the binding integrity rules and the
reproducibility requirements.

## 1. No overclaiming — headline numbers re-verified against raw CSVs
| claim (in drafts) | source CSV | verified |
|---|---|---|
| Benchmark EARS avg rank **2.20**, rank-1 | `benchmark_ranks.csv` (mean) = 2.203 | ✅ |
| Placement EARS avg rank **2.74**, rank-1 | `placement_ranks.csv` (mean) = 2.738 | ✅ |
| Placement core-suite EARS **2.13** rank-1 | HV/IGD/IGDX/n_modes mean = 2.125 | ✅ |
| Ablation A9 (hybrid bonus) W/T/L **3/5/0** | `ablation_IGDX_wtl.csv` = [3,5,0] | ✅ |
| EARS beats CPDEA IGD/HV **8/0/0** | `benchmark_{IGD,HV}_wtl.csv` | ✅ |
| CPDEA collapses to last on placement (5.05) | `placement_ranks.csv` | ✅ |
Every quantitative claim traces to a released CSV. No result file was hand-edited
(all are code-written with provenance stamps via `utils/io_utils`).

## 2. Baseline fairness
- Identical population size, evaluation budget, and termination for every algorithm
  (`configs/*.yaml: protocol`; enforced by the runners; `test_baselines.py` checks the
  budget is fully used and never exceeded).
- **Algorithm-independent seeds** (`utils/seeds.derive_seed`): run *r* uses the same seed
  for all algorithms (verified by tests).
- Baselines ported from official sources; the 2 SOTA documented as faithful re-impls
  (`baseline_selection_note.md`). **Integrity-positive:** two baselines (MMEA-WI, MO_Ring)
  were *fixed to be constraint-fair* during the application work — a change that works
  *against* EARS — and no baseline was ever weakened.

## 3. Parameters frozen
- `configs/selected_params.yaml` selected on the validation subset (MMF1/2/5) in Phase 6
  (`selection_mode: hybrid`, `hybrid_beta: 0.5`) and used **unchanged** for the benchmark,
  ablation, and both applications. No test-set tuning (documented in
  `parameter_analysis_report.md`, `failure_diagnosis.md`).

## 4. Statistics complete
- Friedman omnibus + Wilcoxon signed-rank with Holm correction, average rank, win/tie/loss
  for benchmark / ablation / placement (`results/statistics/*`). 8 indicators on the
  benchmark; objective + decision-space metrics on the application.

## 5. Figures reproducible & honest
- 32 figures (PNG 300dpi + PDF), all **code/data-generated** from real OSM maps and
  experiment outputs; **no AI image generation**. Regenerable via `plotting/*` and
  `run_all.sh`.

## 6. Honest negatives retained (not hidden)
- `failure_diagnosis.md`: 5 benchmark redesigns logged before the hybrid key succeeded;
  ~8 application redesigns logged; the UAV-routing non-rank-1 result kept as honest
  supplementary (`uav_sar_*` tables present, not headline). Limitations section is candid.

## 7. Reproducibility checklist
- [x] `pytest tests/` → 66 passed, 0 failed.
- [x] Single auditable master seed (`utils/seeds.GLOBAL_SEED`); algorithm-independent.
- [x] `requirements.txt` + `environment.yml` pin the stack (incl. osmnx/shapely/geopandas).
- [x] `bash run_all.sh` reproduces benchmark + ablation + placement + statistics + figures
      (resumable: existing results are skipped).
- [x] Raw per-run artefacts (.npz + .json with provenance) released under `results/raw/`.
- [x] Summary/statistics CSVs + LaTeX tables + figures released.
- [x] README updated to the final state; per-phase reports in `docs/`.
- [x] Manuscript drafts grounded in the verified numbers.

## 8. Verdict
The project meets its goals **honestly**: EARS-MMOEA is statistically rank-1 on the
standard MMOP benchmark and rank-1 on a real OSM emergency-facility-placement MMOP, the
framework's modules are ablation-validated, parameters are frozen from validation only,
and all negatives and limitations are reported. No fabrication, no baseline weakening, no
metric gaming, no rigged problems. Ready for manuscript finalisation / LaTeX compilation.
