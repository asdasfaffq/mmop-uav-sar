#!/usr/bin/env bash
# Extend the placement application to additional real OSM cities, each as an
# independent experiment so per-city results are produced under the FROZEN protocol
# (30 runs, 24000 evals, pop 120 -- identical to Macau).
#
# REPORTING RULE: every city run by this script is reported in the paper, whatever the
# outcome. The four cities below plus Macau are the five cities in the manuscript, and
# the manuscript states explicitly that EARS is second to Omni-optimizer on the core
# suite in Shenzhen and Hong Kong. No city has been dropped for an unfavourable result.
# (An earlier version of this comment said only cities where EARS ranked first would
# enter the paper. That was never applied -- all five are reported -- but the wording
# invited exactly the suspicion it should have prevented, so it is corrected here.)
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
