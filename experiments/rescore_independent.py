"""Re-score the placement case study against the INDEPENDENT high-budget reference.

Writes metrics into a parallel experiment name (`<exp>_indref`) rather than overwriting the
self-inclusive-reference results, so both can be compared and neither is silently replaced.

Usage: python experiments/rescore_independent.py
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from applications.app_metrics import compute_placement_metrics  # noqa: E402
from experiments.run_placement import _build_problems  # noqa: E402
from utils.config import load_config  # noqa: E402
from utils.io_utils import RAW_DIR, load_run  # noqa: E402

CITIES = [("Macau", "placement"), ("Guangzhou", "placement_guangzhou"),
          ("Shenzhen", "placement_shenzhen"),
          ("SanFrancisco", "placement_sanfrancisco"),
          ("HongKong", "placement_hongkong")]
REFDIR = ROOT / "results/reference"


def main():
    cfg = load_config(ROOT / "configs/placement.yaml")
    seeds = cfg.get("instance_seeds", [11, 22, 33])
    t0 = time.time()
    n = 0
    for city, exp in CITIES:
        probs = _build_problems(city, seeds, cfg["n_stations"], cfg["n_demand"])
        for inst, prob in probs.items():
            rf = REFDIR / exp / f"{inst}.npz"
            if not rf.exists():
                print(f"  MISSING reference: {exp}/{inst}"); continue
            z = np.load(rf); ref, refPS = z["F"], z["PS"]
            for algo_dir in sorted((RAW_DIR / exp / inst).iterdir()):
                if not algo_dir.is_dir():
                    continue
                out = RAW_DIR / f"{exp}_indref" / inst / algo_dir.name
                out.mkdir(parents=True, exist_ok=True)
                for jp in sorted(algo_dir.glob("run_*.json")):
                    rec = load_run(jp)
                    X = rec["arrays"]["decisions"]; F = rec["arrays"]["objectives"]
                    m = compute_placement_metrics(prob, X, F, ref, refPS)
                    doc = json.loads(jp.read_text())
                    doc["metrics"] = {k: float(v) for k, v in m.items()}
                    doc["experiment"] = f"{exp}_indref"
                    doc.setdefault("provenance", {})["reference"] = \
                        "independent high-budget panel (5x budget, disjoint seed stream)"
                    (out / jp.name).write_text(json.dumps(doc, indent=2), encoding="utf-8")
                    n += 1
            print(f"  [ok] {exp}/{inst}", flush=True)
    print(f"re-scored {n} runs against independent references in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
