"""Export the paper's LaTeX tables (rank, win/tie/loss, parameters, baselines).

Per-problem mean(std) summary tables and per-metric W/T/L CSVs are produced by
run_statistics.py; this consolidates the remaining required tables to .tex.

Usage:
  python plotting/make_tables.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import yaml

from utils.io_utils import STATS_DIR, TABLE_DIR

ROOT = Path(__file__).resolve().parent.parent


def _save(df, name, caption, label, index=True):
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    body = df.to_latex(index=index, escape=True, na_rep="--")
    # wrap the tabular in \resizebox so wide tables fit the text width
    tex = (f"\\begin{{table}}[t]\n\\centering\n\\caption{{{caption}}}\n"
           f"\\label{{{label}}}\n\\resizebox{{\\linewidth}}{{!}}{{%\n{body}}}\n"
           f"\\end{{table}}\n")
    (TABLE_DIR / name).write_text(tex, encoding="utf-8")
    print(f"[ok] {TABLE_DIR / name}")


def rank_table(experiment):
    f = STATS_DIR / f"{experiment}_ranks.csv"
    if not f.exists():
        return
    df = pd.read_csv(f, index_col=0)
    df.loc["MEAN"] = df.mean(0)
    safe = experiment.replace("_", r"\_")
    _save(df.round(2), f"{experiment}_avg_rank.tex",
          f"Average rank per metric on the {safe} study (lower is better).",
          f"tab:{experiment}_rank")


def wtl_table(experiment, metrics):
    rows = {}
    for m in metrics:
        f = STATS_DIR / f"{experiment}_{m}_wtl.csv"
        if not f.exists():
            continue
        d = pd.read_csv(f)
        rows[m] = {r["vs"]: f"{r['win']}/{r['tie']}/{r['loss']}" for _, r in d.iterrows()}
    if rows:
        _save(pd.DataFrame(rows), f"{experiment}_wtl.tex",
              f"EARS-MMOEA win/tie/loss vs each baseline (Wilcoxon+Holm) on {experiment}.",
              f"tab:{experiment}_wtl")


def param_table():
    sp = yaml.safe_load((ROOT / "configs/selected_params.yaml").read_text())["ears_mmoea"]
    rows = [{"parameter": k, "value": v} for k, v in sp.items()]
    _save(pd.DataFrame(rows), "parameters.tex",
          "Frozen EARS-MMOEA parameters (selected on the validation subset, Phase 6).",
          "tab:params", index=False)


def baseline_table():
    cfg = yaml.safe_load((ROOT / "configs/baselines.yaml").read_text())["baselines"]
    rows = [{"method": k, "type": v["type"], "mechanism": v["mechanism"],
             "venue": v["venue"]} for k, v in cfg.items()]
    _save(pd.DataFrame(rows), "baselines.tex",
          "Selected baselines: 3 SOTA + 3 popular classic MMOP methods.",
          "tab:baselines", index=False)


def main():
    for exp in ["benchmark", "ablation", "placement"]:
        rank_table(exp)
    wtl_table("benchmark", ["IGD", "IGDX", "PSP", "HV"])
    wtl_table("placement", ["HV", "IGD_ref", "IGDX_ref", "n_modes"])
    wtl_table("ablation", ["IGDX"])
    param_table()
    baseline_table()
    print("[ok] LaTeX tables exported to", TABLE_DIR)


if __name__ == "__main__":
    main()
