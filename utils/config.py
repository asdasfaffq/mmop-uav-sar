"""YAML config loading with light validation and dotted access."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    if not isinstance(cfg, dict):
        raise ValueError(f"config root must be a mapping: {path}")
    return cfg


def merge_params(base: dict[str, Any], override: dict[str, Any] | None) -> dict[str, Any]:
    """Shallow-merge an override dict onto base (override wins). Non-mutating."""
    out = dict(base)
    if override:
        out.update(override)
    return out
