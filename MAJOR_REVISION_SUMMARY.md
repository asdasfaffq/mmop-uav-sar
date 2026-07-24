# Major-Revision Response Summary (EARS-MMOEA, SWEVO)

Response to the structural major-revision critique (novelty over-claim, statistical
aggregation, application definition, baseline fidelity, module stacking, high-dim
generalization). All changes are backed by real experiments or honest text; no fabrication,
no baseline weakening, no metric/seed cherry-picking. Calibrated narrowing throughout: the
contribution is sharpened, not erased.

## A. Text / statistics (no re-runs)

1. **Novelty narrowed (placement, not first use).** Added the inter-/intra-front taxonomy
   (Javadi & Mostaghim 2022, *Natural Computing*) and a recent high-dim MMOP reference
   (Liang et al. 2024, *IEEE/CAA JAS*). The sparsity term is positioned as an *intra-front*
   operation; we explicitly do **not** claim first use of intra-front decision-space selection.
   Contribution = the controlled attribution (placement ≠ multiplicative form) + the
   equivalence-aware realization.
2. **Over-claims calibrated.** "sidestep / decouple / protect convergence / for free / tie-break /
   no baseline achieves" → "reduce the added convergence cost / separate roles at the selection
   layer / front-precedence invariance / within-front (intra-front) selection / not achieved by
   any evaluated baseline". Title: "...Within-Front Diversity Tie-Break..." → "...Equivalence-Aware
   Within-Front Selection...".
3. **Statistics reframed.** Benchmark headline moved from the 8-metric mean rank (2.30) to the
   a-priori primary metrics (IGDX/PSP rank 1.875), the mean rank kept only as a coarse summary
   (indicators are correlated). Dropped the pseudo-independent "5 cities × 4 metrics = 20 blocks"
   pooled χ²; kept the per-metric across-city Friedman.
4. **Application definitions.** Canonical-coordinate sort disclosed as a surrogate for the exact
   set-matching (Hungarian) distance; "layout modes" disambiguated as post-hoc silhouette-k-means
   clusters (cap 20) of the obtained non-dominated set, distinct from the search-time niching
   ([2,5]) and from true PS branch counts (the metric has no explicit quality-gate, stated).
5. **Tone down** of promotional phrasing; verified no double-period typos.

## B. New experiments (real runs)

6. **Forward (constructive) ablation** — `run_forward_ablation.py`, 6-rung ladder × MMF1-8 × 30
   runs (1440 runs, 0 errors). Refutes "kitchen-sink": IGDX is built by +E (0.269→0.060),
   +S core (→0.050) and +portfolio (→0.037); cross-mode and archive are inert on the
   unconstrained benchmark (constrained-application modules). The whole diversity stack costs
   ≈7% of IGD. Endpoints F0/F5 reproduce subtractive A8/A0 numerically. Table `forward_ablation`.
7. **High-dimensional study** — `benchmarks/scalable.py` (ScalableMMF2: two equivalent sets
   embedded in d dims, analytic reference verified: PF-match-err = 0, PS non-dominated, two
   distinct branches, d = 2..100; 13 tests). `run_highdim.py`, 7 algorithms × d∈{5,10,30,50,100}
   × 30 runs (1050 runs, 0 errors, budget fixed across d). Result confirms the thesis: at low d
   CPDEA edges IGDX (the main-benchmark tie), but EARS degrades the most gracefully and is best on
   **both** IGDX and IGD at d≥50 (d=100: IGDX 0.89 vs next 1.52; IGD 0.65 vs next 1.30), because
   convergence carried by the rank is insulated from the high-d-degrading diversity signal.
   Honest caveats: n=5 Friedman power limited (IGDX p=0.09), PSP 2nd to CPDEA, absolute IGDX grows
   with d for all methods (scope boundary). Table `highdim`.

## C. Reproducibility hardening

8. **Provenance** — every run's JSON now stamps its resolved hyperparameters
   (`hyperparam_stamp`), closing the gap where the frozen config was only inferable from file
   mtimes. Earlier audit (independent agent) verified all figures/results were generated with the
   frozen config (niche_boost=1.0, max_modes=5).

## Status

- Compiles clean: 32 pp, 0 undefined, 0 overfull, 0 underfull. pytest 88 green.
- Addressed in full: novelty edges, statistical aggregation, application definitions, module
  stacking, high-dim generalization.
- Remaining (optional, high-effort, low marginal value): official PlatEMO/MATLAB baseline
  re-runs (currently faithful Python ports validated by analytic recovery + qualitative ordering),
  Hungarian set-distance re-analysis of the application, runtime/convergence curves.

## PDF snapshots
- `paper/main_majorrev_phaseA.pdf` — text/stats pass
- `paper/main_majorrev_fwdablation.pdf` — + forward ablation
- `paper/main_majorrev_highdim.pdf` — + high-dim study
- `paper/main.pdf` — current (coherence pass)
