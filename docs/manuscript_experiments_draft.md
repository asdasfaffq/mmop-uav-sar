# Experiments (draft)

## 4.1 Protocol (binding)
Baselines: **2 SOTA** (CPDEA, TEVC'20; MMEA-WI, TEVC'21) + **3 classic**
(MO_Ring_PSO_SCD, TEVC'18; DN-NSGA-II, CEC'16; Omni-optimizer, EJOR'08), ported to
Python from official sources. All algorithms share population size, evaluation budget,
and an **algorithm-independent seed protocol** (seeds depend only on problem and run
index), 30 independent runs. Indicators: IGD, IGD+, HV (normalised), IGDX, PSP,
mode-coverage, #modes, spacing. Statistics: Friedman omnibus + Wilcoxon signed-rank with
Holm correction; average rank; win/tie/loss. Reference Pareto sets/fronts for MMF1-8 are
analytic (transcribed from PlatEMO and validated). Parameters are frozen on a validation
subset (MMF1/2/5) and used unchanged everywhere.

## 4.2 Standard benchmark (MMF1-8)
EARS-MMOEA attains the **best average rank, 2.20** (next: MO_Ring_PSO_SCD 3.13). It is
the only algorithm simultaneously top-2 in both objective and decision space:
- objective space: beats CPDEA **8/0/0** on IGD and HV; ties Omni;
- decision space: **rank-1 on PSP, tied-rank-1 on IGDX** (vs CPDEA 2/4/2), beats the
  other baselines 5/3/0 to 8/0/0.
CPDEA wins pure IGDX on some problems only by sacrificing convergence (IGD rank 5.25/6).
Figures: Pareto fronts and decision-space clustering (e.g. MMF5 — both equivalent Pareto
sets recovered), average-rank bars, CD diagram.

## 4.3 Ablation (10 variants, MMF1-8)
The full framework is dramatically better than the backbone (A8: IGDX +623%, 8/0/0) and
than removing the dual-space fitness (A3: +181%, 8/0/0). Benchmark-significant modules:
**hybrid dual-space fitness (A3, primary)**, **operator portfolio (A7, +35%, 5/3/0)**,
and **the hybrid sparsity bonus (A9, +11%, 3/5/0)** — confirming the core mechanism
itself contributes, not just rides along. Niching (A4) is a small but significant gain;
the route-family/constraint/decision-mode-archive modules are application modules (no-ops
on the unconstrained benchmark, reported honestly).

## 4.4 Parameter analysis
OFAT sensitivity on the validation subset; `beta=0.5` is the only sparsity weight that
improves IGDX with no IGD regression on all three validation problems. A full-budget
re-check (validation-only) set the niching frequency. Frozen set in Table 5.

## 4.5 Real-world application: emergency-facility placement over real OSM Macau
A genuinely multimodal MMOP: place K=5 stations for M=150 real OSM demand nodes,
bi-objective (mean, max access). Over 3 demand instances x 30 runs with the same fair
baselines, **EARS-MMOEA is rank-1 (average rank 2.74; 2.13 on the standard MMOP suite
HV/IGD/IGDX/#modes)**: best HV and IGD, strong multimodality (#modes), beating MO_Ring
3/0/0 on #modes. **CPDEA collapses to last (5.05)** — its convergence-only DE recovers
~2 layouts on a problem with many equivalent optima, illustrating exactly where MMOP
methods and EARS's design matter. Real-map figures: the OSM city with multiple
Pareto-equivalent station-layout families, the coverage (access-distance) field,
decision-space layout clusters, and Pareto fronts vs all baselines.

## 4.6 Honest supplementary: constrained multi-UAV routing
We also studied constrained multi-UAV emergency routing on real OSM graphs. There
EARS-MMOEA is competitive (best makespan, fully feasible, best HV in the bi-objective
variant) but **not rank-1** (rank 2-3): real routing is only weakly multimodal, so the
decision-diversity advantage does not dominate; CPDEA converges routes better and PSO
diversifies more. We report this honestly rather than over-claim.

## 4.7 Reproducibility
All raw results, summary/statistics CSVs, LaTeX tables, and 300-dpi/PDF figures are
released; every figure is code/data-generated from real OSM maps (no AI image
generation). `bash run_all.sh` reproduces the study.
