"""Dynamic factor-weight analysis for Week 4 v4.1."""

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _daily_ic(panel: pd.DataFrame, factor_cols: list[str], ret_col: str, method: str) -> pd.DataFrame:
    rows = []
    cols = [c for c in factor_cols if c in panel.columns]
    if ret_col not in panel.columns or not cols:
        return pd.DataFrame()
    for date, group in panel.groupby("trade_date"):
        for factor in cols:
            sub = group[[factor, ret_col]].dropna()
            if len(sub) < 5:
                continue
            corr = sub[factor].corr(sub[ret_col], method=method)
            rows.append({"trade_date": date, "factor": factor, f"{method}_ic": corr})
    return pd.DataFrame(rows)


def _summary(ic_df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    if ic_df.empty:
        return pd.DataFrame()
    rows = []
    for factor, group in ic_df.groupby("factor"):
        values = group[value_col].dropna()
        std = values.std(ddof=1)
        rows.append(
            {
                "factor": factor,
                f"{value_col}_mean": values.mean(),
                f"{value_col}_std": std,
                f"{value_col}_icir": values.mean() / std if std and np.isfinite(std) else np.nan,
                f"{value_col}_win_rate": (values > 0).mean() if len(values) else np.nan,
                "sample_periods": len(values),
            }
        )
    return pd.DataFrame(rows)


def generate_dynamic_factor_weights(rank_summary: pd.DataFrame) -> pd.DataFrame:
    if rank_summary.empty:
        return pd.DataFrame()
    icir_col = "spearman_ic_icir"
    df = rank_summary[["factor", icir_col]].copy()
    df["positive_icir"] = df[icir_col].clip(lower=0)
    denom = df["positive_icir"].sum()
    if denom <= 0 or not np.isfinite(denom):
        df["proposed_weight"] = 1.0 / len(df)
        df["weight_method"] = "equal_weight_fallback"
    else:
        df["proposed_weight"] = df["positive_icir"] / denom
        df["weight_method"] = "positive_icir_weight"
    return df.sort_values("proposed_weight", ascending=False)


def _rolling_rank_ic(rank_ic: pd.DataFrame, window: int) -> pd.DataFrame:
    if rank_ic.empty:
        return pd.DataFrame()
    df = rank_ic.sort_values(["factor", "trade_date"]).copy()
    df["rolling_rank_ic"] = df.groupby("factor")["spearman_ic"].transform(lambda x: x.rolling(window, min_periods=10).mean())
    df["window"] = window
    return df


def _plot_factor_ic(summary: pd.DataFrame, chart_dir: Path) -> Path | None:
    if summary.empty:
        return None
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(summary["factor"], summary["spearman_ic_mean"])
    ax.set_title("Factor Rank IC Mean")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out = chart_dir / "factor_ic_bar.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def _plot_rolling_ic(rolling_ic: pd.DataFrame, chart_dir: Path) -> Path | None:
    if rolling_ic.empty:
        return None
    fig, ax = plt.subplots(figsize=(10, 5))
    for factor, group in rolling_ic.groupby("factor"):
        ax.plot(group["trade_date"], group["rolling_rank_ic"], label=factor)
    ax.set_title("Rolling Factor Rank IC")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out = chart_dir / "factor_rolling_ic.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def _plot_weights(weights: pd.DataFrame, chart_dir: Path) -> Path | None:
    if weights.empty:
        return None
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(weights["factor"], weights["proposed_weight"])
    ax.set_title("Dynamic Factor Weight Proposal")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out = chart_dir / "dynamic_factor_weight.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def run_factor_dynamic_weight_analysis(factor_panel: pd.DataFrame, config) -> tuple[dict[str, pd.DataFrame], list[Path]]:
    if factor_panel.empty:
        return {}, []
    pearson_ic = _daily_ic(factor_panel, config.FACTOR_COLS, config.FUTURE_RETURN_COL, "pearson")
    spearman_ic = _daily_ic(factor_panel, config.FACTOR_COLS, config.FUTURE_RETURN_COL, "spearman")
    factor_ic_summary = _summary(pearson_ic, "pearson_ic")
    factor_rank_ic_summary = _summary(spearman_ic, "spearman_ic")
    rolling = _rolling_rank_ic(spearman_ic, config.ROLLING_IC_WINDOW)
    weights = generate_dynamic_factor_weights(factor_rank_ic_summary)
    charts = [
        _plot_factor_ic(factor_rank_ic_summary, config.CHART_DIR),
        _plot_rolling_ic(rolling, config.CHART_DIR),
        _plot_weights(weights, config.CHART_DIR),
    ]
    return (
        {
            "factor_ic_summary": factor_ic_summary,
            "factor_rank_ic_summary": factor_rank_ic_summary,
            "factor_rolling_ic": rolling,
            "dynamic_factor_weight_proposal": weights,
        },
        [p for p in charts if p is not None],
    )
