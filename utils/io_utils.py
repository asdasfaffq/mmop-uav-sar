"""Result persistence helpers.

All experiment outputs flow through here so that directory layout, file naming,
and metadata stamping are consistent and auditable. We deliberately keep raw
per-run artefacts (so results can never be silently "edited") separate from
aggregated summaries.

Layout
------
results/raw/<experiment>/<problem>/<algorithm>/run_<idx>.npz   # objectives, decisions
results/raw/<experiment>/<problem>/<algorithm>/run_<idx>.json  # metrics + provenance
results/summary/<experiment>_summary.csv
"""
from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
RAW_DIR = RESULTS_DIR / "raw"
SUMMARY_DIR = RESULTS_DIR / "summary"
STATS_DIR = RESULTS_DIR / "statistics"
FIG_DIR = RESULTS_DIR / "figures"
TABLE_DIR = RESULTS_DIR / "tables"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def provenance(seed: int, **extra: Any) -> dict[str, Any]:
    """Standard provenance block stamped into every result file."""
    prov = {
        "timestamp_utc": _utc_now(),
        "seed": int(seed),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
    }
    prov.update(extra)
    return prov


#: EARS-MMOEA hyperparameters stamped into each run's provenance so that the
#: exact frozen configuration is recoverable from any single result file,
#: rather than inferred from external config-file mtimes. Missing keys are
#: recorded as None so an omission is itself auditable.
EARS_AUDIT_KEYS = (
    "niche_boost", "max_modes", "min_modes", "hybrid_beta", "selection_mode",
    "cross_mode_mating_prob", "clustering_update_freq",
    "decision_mode_archive_size", "operator_lr", "operator_min_prob",
)


def hyperparam_stamp(params: dict[str, Any] | None,
                     keys: tuple[str, ...] = EARS_AUDIT_KEYS) -> dict[str, Any]:
    """Pull audit-relevant hyperparameters from a resolved config block.

    Returns ``{"hyperparams": {...}}`` ready to splat into a ``save_run`` meta,
    so callers write ``meta={..., **hyperparam_stamp(params)}``.
    """
    p = params or {}
    return {"hyperparams": {k: p.get(k) for k in keys}}


def run_dir(experiment: str, problem: str, algorithm: str) -> Path:
    d = RAW_DIR / experiment / problem / algorithm
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_run(experiment: str, problem: str, algorithm: str, run_index: int,
             *, objectives: np.ndarray, decisions: np.ndarray,
             metrics: dict[str, float], seed: int,
             extra_arrays: dict[str, np.ndarray] | None = None,
             meta: dict[str, Any] | None = None) -> Path:
    """Persist one run: arrays to .npz, metrics+provenance to .json.

    Returns the json path. Raw files are never overwritten silently -- a
    pre-existing file for the same run raises unless explicitly removed.
    """
    d = run_dir(experiment, problem, algorithm)
    npz_path = d / f"run_{run_index:03d}.npz"
    json_path = d / f"run_{run_index:03d}.json"

    arrays = {"objectives": np.asarray(objectives), "decisions": np.asarray(decisions)}
    if extra_arrays:
        arrays.update({k: np.asarray(v) for k, v in extra_arrays.items()})
    np.savez_compressed(npz_path, **arrays)

    record = {
        "experiment": experiment,
        "problem": problem,
        "algorithm": algorithm,
        "run_index": int(run_index),
        "metrics": {k: float(v) for k, v in metrics.items()},
        "provenance": provenance(seed, **(meta or {})),
        "arrays_file": npz_path.name,
    }
    json_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return json_path


def load_run(json_path: str | Path) -> dict[str, Any]:
    json_path = Path(json_path)
    record = json.loads(json_path.read_text(encoding="utf-8"))
    npz_path = json_path.parent / record["arrays_file"]
    if npz_path.exists():
        with np.load(npz_path) as data:
            record["arrays"] = {k: data[k] for k in data.files}
    return record


def save_json(path: str | Path, obj: Any) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=float), encoding="utf-8")
    return path
