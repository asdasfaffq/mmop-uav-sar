#!/usr/bin/env bash
# End-to-end reproduction driver. Stages are gated by phase completion; stages
# whose code is not yet implemented are skipped with a notice (Phase 0 state).
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="$PWD:${PYTHONPATH:-}"

echo "==> [sanity] pytest"
python3 -m pytest tests/ -q

run_if_exists() {  # run_if_exists <script> <args...>
  local script="$1"; shift
  if [[ -f "$script" ]] && ! grep -q "NotImplemented_PHASE_STUB" "$script" 2>/dev/null; then
    echo "==> $script $*"
    python3 "$script" "$@"
  else
    echo "==> [skip] $script (not yet implemented in this phase)"
  fi
}

run_if_exists experiments/run_parameter_analysis.py --config configs/benchmark.yaml
run_if_exists experiments/run_beta_sweep.py  # validation-only beta robustness sweep
run_if_exists experiments/run_benchmark.py  --config configs/benchmark.yaml --params configs/selected_params.yaml
run_if_exists experiments/run_benchmark_ext.py --config configs/benchmark.yaml --params configs/selected_params.yaml  # CEC MMO competition extension
run_if_exists experiments/run_deceptive.py --config configs/benchmark.yaml --params configs/selected_params.yaml  # deceptive scalable MMF10-12 (EARS not rank-1, reported)
run_if_exists experiments/run_ablation.py   --config configs/benchmark.yaml --params configs/selected_params.yaml
# Real-world application: multi-facility emergency-station placement MMOP (EARS rank-1).
run_if_exists experiments/run_placement.py  --config configs/placement.yaml --params configs/selected_params.yaml

echo "==> statistics"
python3 experiments/run_statistics.py --results results/raw --experiment benchmark  --reference EARS_MMOEA
python3 experiments/run_statistics.py --results results/raw --experiment benchmark_ext --reference EARS_MMOEA
python3 experiments/run_statistics.py --results results/raw --experiment deceptive --reference EARS_MMOEA
python3 experiments/run_statistics.py --results results/raw --experiment ablation   --reference A0_Full
python3 experiments/run_statistics.py --results results/raw --experiment placement  --reference EARS_MMOEA

echo "==> figures"
run_if_exists plotting/plot_all.py        --experiment benchmark
run_if_exists plotting/plot_placement.py      --config configs/placement.yaml --instance-seed 11
run_if_exists plotting/plot_placement_real.py --config configs/placement.yaml --instance-seed 11  # real OSM map tiles
run_if_exists plotting/plot_framework.py
run_if_exists plotting/plot_cd_diagram.py  --experiment benchmark --metric IGDX
run_if_exists plotting/make_tables.py
run_if_exists plotting/make_significance_table.py
run_if_exists plotting/plot_beta_robustness.py
run_if_exists plotting/plot_rank_tables.py --experiment placement

echo "==> done"
