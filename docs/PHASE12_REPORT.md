# Phase 12 Report — Figures & Tables

## 1. Completed
- **Fig. 1 framework** (`plot_framework.py`): code-generated EARS-MMOEA schematic.
- **Critical-difference diagrams** (`plot_cd_diagram.py`): Nemenyi CD for benchmark/IGDX
  and placement/HV (Fig. 9).
- **Full application figure set** (`plot_placement.py`): real OSM map + station-layout
  families, access heatmap, decision clusters, Pareto front, average-rank bars.
- **LaTeX table export** (`make_tables.py`): average-rank, win/tie/loss, parameters,
  baselines tables for benchmark / ablation / placement (+ per-metric mean(std)
  summaries from run_statistics).
- **Caption draft** (`figure_table_caption_draft.md`): paper Fig 1-9 / Table 1-7 mapping.

## 2. Inventory
- `results/figures/`: 32 figures (PNG 300dpi + PDF) — framework, benchmark Pareto/clusters
  (MMF1-8), parameter sensitivity, ablation, average rank, CD diagrams, and the real-OSM
  placement application (map/heatmap/clusters/pareto/rank).
- `results/tables/`: 39 LaTeX tables.

## 3. Sanity check
- `pytest tests/` -> 66 passed; all Phase-12 plotting modules import; every figure
  regenerated from real results, every table from the statistics CSVs.
- All figures are code/data-generated from real OSM maps and experiment outputs — no AI
  image generation.

## 4. Next phase
**Phase 13 — manuscript drafts**: title candidates, abstract, contributions, related
work, problem formulation, method, experiment protocol, benchmark + application analysis,
ablation, parameter analysis, limitations, conclusion — grounded in the real numbers.

## 5. Risks / honesty
- The application figures/tables feature the placement MMOP (EARS rank-1); the UAV-routing
  study remains as honest supplementary (`uav_sar_*` tables present but not headline).
- No fabricated or AI-drawn figures; captions report exact numbers including the honest
  caveats (narrow margin over MO_Ring on the full placement suite).
