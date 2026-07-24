# Remaining Manuscript Sections (draft)

## 1. Introduction — contribution paragraph
(see `contribution_draft.md` for C1-C3; lead with the convergence/diversity trade-off,
the hybrid dual-space key as the resolution, and the two rank-1 results.)

## 2. Related work (outline)
- **MMOP test suites & metrics**: MMF (Yue et al. TEVC'18, SWEVO'19), CEC2019/2020 MMO;
  decision-space metrics IGDX, PSP, cover-rate.
- **Decision-space niching MOEAs**: DN-NSGA-II, Omni-optimizer, MO_Ring_PSO_SCD (ring
  topology + SCD).
- **Convergence/diversity in decision space**: CPDEA (convergence-penalised density,
  TEVC'20), MMEA-WI (weighted indicator, TEVC'21), TriMOEA-TA&R, MMOEA/DC; local-PF
  methods (HREA).
- **Gap**: prior methods trade objective convergence against decision-space coverage;
  none couple them multiplicatively to preserve both. **Position EARS's hybrid key here.**
- **MMOP applications**: limited real-world; facility location as MMOP is under-explored.

## 3. Problem formulation
- **General MMOP** (Sec 3.1 of method): min `F(x)` over `Omega`; recover Pareto front +
  all decision-space pre-images.
- **Facility-placement MMOP**: decision = K station positions in the city bbox (snapped
  to OSM nodes); objectives `f1 = mean_d access(d)`, `f2 = max_d access(d)` over M demand
  nodes (p-median vs p-center). Multiple geographically distinct layouts achieve
  near-identical `(f1,f2)` -> Pareto-equivalent placement families.
- **(Supplementary) constrained multi-UAV routing**: random-key assignment+order+style
  encoding; objectives (distance, risk[, makespan]); battery/no-fly constraints.

## 4. Limitations (honest)
- The hybrid sparsity bonus helps decision-space coverage but does not, by itself,
  manufacture multimodality where a problem has few equivalent optima — hence EARS is
  competitive but not rank-1 on the weakly-multimodal constrained-routing application.
- Baselines are faithful Python re-implementations (validated on MMF), not the original
  MATLAB; small fidelity gaps are possible and are disclosed.
- The placement win over the strongest classic baseline (MO_Ring) is clear on the
  standard MMOP suite but narrow on the full 7-metric suite; we report both.
- MMF9-14 / IDMP and additional real cities are left to future work (the analytic-
  reference core is MMF1-8).

## 5. Conclusion
EARS-MMOEA introduces a hybrid dual-space diversity key that resolves the
convergence/diversity trade-off in MMOP: it is statistically rank-1 on the standard MMF
benchmark and rank-1 on a real OSM emergency-facility-placement MMOP, while remaining
competitive on a constrained UAV-routing study. Ablations confirm the mechanism is the
driver. Future work: stronger search-side multimodality for weakly-multimodal
applications, larger suites, and additional real cities. All code, data, and statistics
are released.
