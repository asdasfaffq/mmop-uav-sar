# Experiment Protocol (binding across all phases)

This protocol is fixed in Phase 0 and applies to every formal experiment.
Deviations must be recorded here with justification.

## Fairness invariants

| Invariant | Rule | Enforced by |
|---|---|---|
| Population size | Identical for all algorithms in a comparison | `configs/*.yaml: protocol.pop_size` |
| Evaluation budget | Identical `max_evaluations` for all algorithms | `configs/*.yaml: protocol.max_evaluations` |
| Termination | Solely by `max_evaluations` (no early stop tuned per method) | runners |
| Seeds | `seed = f(global_seed, problem, run_index)` — **independent of algorithm** | `utils/seeds.derive_seed` |
| Runs | 30 independent runs per (algorithm, problem) | `configs/*.yaml: protocol.n_runs` |
| Baseline strength | No weakening; use authors' recommended params or faithful reimplementation | `docs/baseline_selection_note.md` |

Because seeds depend only on `(problem, run_index)`, every algorithm sees the
**same** initial population and problem instance for run `r`. This blocks both
seed cherry-picking and accidental unfairness.

## Result handling

* Raw per-run artefacts: `results/raw/<exp>/<problem>/<algo>/run_XXX.{npz,json}`.
* Raw files carry a provenance block (seed, timestamp, platform, numpy version).
* Summaries (`results/summary/*.csv`) are **derived** from raw files by code only;
  raw files are never hand-edited.
* Statistics (`results/statistics/*.csv`): Friedman omnibus, then Wilcoxon
  signed-rank pairwise with Holm correction; plus average-rank and win/tie/loss.

## Metric protocol (MMOP — both spaces)

Objective space: IGD, IGD+, HV (normalized), spacing.
Decision space: IGDX, PSP, decision-space mode coverage, number of detected modes.
Application adds: feasible ratio, constraint violation, route-family diversity,
number of route families.

## Validation vs test separation

Parameter analysis (Phase 6) uses only the `validation_subset` declared in
`configs/benchmark.yaml`. The frozen `configs/selected_params.yaml` is then used
unchanged for benchmark comparison, ablation, and applications. No tuning on the
final test set.
