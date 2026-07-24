"""Lightweight, consistent logging for experiments.

A single ``get_logger`` entry point returns a configured logger that writes to
both stderr and (optionally) a per-experiment log file. Format is fixed so logs
are grep-able and comparable across runs.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

_FMT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"
_configured: set[str] = set()


def get_logger(name: str = "mmop", logfile: str | Path | None = None,
               level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger. Idempotent per (name, logfile)."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    tag = f"{name}|{logfile}"
    if tag in _configured:
        return logger
    logger.handlers.clear()
    formatter = logging.Formatter(_FMT, datefmt=_DATEFMT)

    sh = logging.StreamHandler(stream=sys.stderr)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    if logfile is not None:
        logfile = Path(logfile)
        logfile.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(logfile, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    logger.propagate = False
    _configured.add(tag)
    return logger
