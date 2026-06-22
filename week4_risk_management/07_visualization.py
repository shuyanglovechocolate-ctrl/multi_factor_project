"""Visualization helpers for Week 4."""

import os
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(__file__).resolve().parents[1] / ".matplotlib-cache"),
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_nav_comparison(return_frame: pd.DataFrame, chart_dir: Path) -> Path | None:
    if return_frame.empty or "strategy_nav" not in return_frame.columns:
        return None
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(return_frame["trade_date"], return_frame["strategy_nav"], label="Strategy")
    if "benchmark_nav" in return_frame.columns:
        ax.plot(return_frame["trade_date"], return_frame["benchmark_nav"], label="Sample Equal Benchmark")
    if "hs300_nav" in return_frame.columns:
        ax.plot(return_frame["trade_date"], return_frame["hs300_nav"], label="HS300")
    ax.set_title("Week 4 NAV Comparison")
    ax.set_ylabel("NAV")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out = chart_dir / "nav_comparison.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_drawdown(return_frame: pd.DataFrame, chart_dir: Path) -> Path | None:
    if return_frame.empty:
        return None
    if "drawdown" in return_frame.columns:
        drawdown = return_frame["drawdown"]
    elif "strategy_nav" in return_frame.columns:
        drawdown = return_frame["strategy_nav"] / return_frame["strategy_nav"].cummax() - 1.0
    else:
        return None
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(return_frame["trade_date"], drawdown, 0, alpha=0.35)
    ax.set_title("Strategy Drawdown Curve")
    ax.set_ylabel("Drawdown")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out = chart_dir / "drawdown_curve.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_brinson_stack(brinson_by_year: pd.DataFrame, chart_dir: Path) -> Path | None:
    if brinson_by_year.empty or "year" not in brinson_by_year.columns:
        return None
    effect_cols = [c for c in ["allocation_effect", "selection_effect", "interaction_effect"] if c in brinson_by_year.columns]
    if not effect_cols:
        return None
    fig, ax = plt.subplots(figsize=(10, 5))
    brinson_by_year.set_index("year")[effect_cols].plot(kind="bar", stacked=True, ax=ax)
    ax.set_title("Brinson Attribution by Year")
    ax.set_ylabel("Effect")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out = chart_dir / "brinson_stack_chart.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_extreme_market(extreme_df: pd.DataFrame, chart_dir: Path) -> list[Path]:
    paths = []
    if extreme_df.empty:
        return paths
    available = extreme_df[extreme_df.get("data_available", False) == True].copy()
    if available.empty:
        return paths
    for _, row in available.iterrows():
        period = row["stress_period"]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(["Strategy", "HS300", "Excess"], [row["strategy_return"], row["hs300_return"], row["excess_return"]])
        ax.set_title(f"Extreme Market Test: {period}")
        ax.set_ylabel("Return")
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        out = chart_dir / f"extreme_market_{period}.png"
        fig.savefig(out, dpi=160)
        plt.close(fig)
        paths.append(out)
    return paths


def run_visualizations(return_frame: pd.DataFrame, brinson_outputs: dict[str, pd.DataFrame], extreme_df: pd.DataFrame, config) -> list[Path]:
    paths = []
    for path in [
        plot_nav_comparison(return_frame, config.CHART_DIR),
        plot_drawdown(return_frame, config.CHART_DIR),
        plot_brinson_stack(brinson_outputs.get("brinson_by_year", pd.DataFrame()), config.CHART_DIR),
    ]:
        if path is not None:
            paths.append(path)
    paths.extend(plot_extreme_market(extreme_df, config.CHART_DIR))
    return paths
