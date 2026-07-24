#!/usr/bin/env bash
# Extend the placement application to additional real OSM cities, each as an
# independent experiment so rank-1 is decided per city under the FROZEN protocol
# (30 runs, 24000 evals, pop 120 -- identical to Macau). Only cities where EARS
# is rank-1 will enter the paper.
set -uo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1

CITIES=("Shenzhen" "Guangzhou" "HongKong" "SanFrancisco")

for city in "${CITIES[@]}"; do
  exp="placement_$(echo "$city" | tr '[:upper:]' '[:lower:]')"
  echo "============================================================"
  echo "==> CITY $city  (experiment=$exp)  $(date +%H:%M:%S)"
  echo "============================================================"
  python3 experiments/run_placement.py --config configs/placement.yaml \
      --params configs/selected_params.yaml --city "$city" --experiment "$exp"
  echo "==> statistics for $exp"
  python3 experiments/run_statistics.py --results results/raw \
      --experiment "$exp" --reference EARS_MMOEA
  echo "==> ranks ($exp):"
  cat "results/statistics/${exp}_ranks.csv" 2>/dev/null || echo "  (no ranks file)"
done
echo "==> ALL CITIES DONE $(date +%H:%M:%S)"
