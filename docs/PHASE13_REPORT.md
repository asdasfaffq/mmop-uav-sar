# Phase 13 Report — Manuscript Drafts

## 1. Completed (markdown drafts, grounded in real numbers)
- `title_candidates.md` — chosen working title #1 (EARS-MMOEA, hybrid-diversity, with
  real-city facility application); naming note (drop "Route", keep EARS).
- `abstract_draft.md` — full abstract with both rank-1 results and the mechanism.
- `contribution_draft.md` — C1 problem (placement MMOP), C2 algorithm (hybrid key),
  C3 validation (two rank-1 results, fair protocol).
- `manuscript_method_draft.md` — Sec 3: hybrid dual-space key (with the why), 7 modules,
  structure-preserving diversity, complexity.
- `manuscript_experiments_draft.md` — Sec 4: protocol, benchmark, ablation, parameter
  analysis, placement application, honest UAV-routing supplementary, reproducibility.
- `manuscript_sections_draft.md` — intro/related-work outline, problem formulation,
  limitations, conclusion.

## 2. Sanity / honesty
- Every claim traces to the actual results (benchmark avg rank 2.20; ablation A3 +181%,
  A9 +11%; placement avg rank 2.74 / 2.13 core suite; CPDEA collapse).
- Limitations section states the UAV-routing non-rank-1 result, baseline-fidelity caveat,
  and the narrow placement margin vs MO_Ring honestly.

## 3. Next phase
**Phase 14 — final audit + reproducibility checklist**: verify no overclaiming, baseline
fairness, all figures reproducible, params frozen, statistics complete, README updated,
`run_all.sh` reproduces. Optionally compile to LaTeX/PDF via the paper-write/compile
tooling.
