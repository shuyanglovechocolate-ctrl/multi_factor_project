"""Market effect and beta-risk analysis for Week 4 v4.1."""

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def calculate_alpha_beta(portfolio_returns: pd.Series, benchmark_returns: pd.Series, trading_days: int) -> dict:
    df = pd.DataFrame({"p": portfolio_returns, "b": benchmark_returns}).dropna()
    if len(df) < 3 or df["b"].var() == 0:
        return {"alpha_daily": np.nan, "alpha_annual": np.nan, "beta": np.nan, "r_squared": np.nan}
    beta, alpha = np.polyfit(df["b"], df["p"], 1)
    pred = alpha + beta * df["b"]
    ss_res = float(((df["p"] - pred) ** 2).sum())
    ss_tot = float(((df["p"] - df["p"].mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot else np.nan
    return {
        "alpha_daily": float(alpha),
        "alpha_annual": float((1.0 + alpha) ** trading_days - 1.0),
        "beta": float(beta),
        "r_squared": float(r2),
    }


def calculate_rolling_beta(return_frame: pd.DataFrame, window: int) -> pd.DataFrame:
    if return_frame.empty or not {"strategy_ret", "hs300_ret"}.issubset(return_frame.columns):
        return pd.DataFrame()
    rows = []
    df = return_frame[["trade_date", "strategy_ret", "hs300_ret"]].dropna().reset_index(drop=True)
    for i in range(window, len(df) + 1):
        sub = df.iloc[i - window : i]
        beta = calculate_alpha_beta(sub["strategy_ret"], sub["hs300_ret"], 252)["beta"]
        rows.append({"trade_date": sub["trade_date"].iloc[-1], "rolling_beta": beta, "window": window})
    return pd.DataFrame(rows)


def calculate_up_down_capture(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame({"p": portfolio_returns, "b": benchmark_returns}).dropna()
    if df.empty:
        return pd.DataFrame()
    up = df[df["b"] > 0]
    down = df[df["b"] < 0]
    rows = []
    for name, sub in [("up_market", up), ("down_market", down)]:
        if sub.empty or sub["b"].mean() == 0:
            capture = np.nan
        else:
            capture = sub["p"].mean() / sub["b"].mean()
        rows.append(
            {
                "market_state": name,
                "strategy_avg_return": sub["p"].mean() if not sub.empty else np.nan,
                "benchmark_avg_return": sub["b"].mean() if not sub.empty else np.nan,
                "capture_ratio": capture,
                "sample_days": len(sub),
            }
        )
    return pd.DataFrame(rows)


def build_total_return_decomposition(return_frame: pd.DataFrame, brinson_outputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if return_frame.empty or "strategy_ret" not in return_frame.columns:
        return pd.DataFrame()
    strategy_total = float((1.0 + return_frame["strategy_ret"].fillna(0.0)).prod() - 1.0)
    market_effect = (
        float((1.0 + return_frame["hs300_ret"].fillna(0.0)).prod() - 1.0)
        if "hs300_ret" in return_frame.columns
        else np.nan
    )
    brinson_total = brinson_outputs.get("brinson_total", pd.DataFrame())
    effects = {"allocation_effect": 0.0, "selection_effect": 0.0, "interaction_effect": 0.0}
    if not brinson_total.empty and {"effect", "value"}.issubset(brinson_total.columns):
        effects.update(dict(zip(brinson_total["effect"], brinson_total["value"])))
    explained = market_effect + sum(effects.values()) if np.isfinite(market_effect) else np.nan
    residual = strategy_total - explained if np.isfinite(explained) else np.nan
    return pd.DataFrame(
        [
            {"component": "market_effect", "value": market_effect},
            {"component": "allocation_effect", "value": effects["allocation_effect"]},
            {"component": "selection_effect", "value": effects["selection_effect"]},
            {"component": "interaction_effect", "value": effects["interaction_effect"]},
            {"component": "residual", "value": residual},
            {"component": "strategy_total_return", "value": strategy_total},
        ]
    )


def _plot_decomposition(decomp: pd.DataFrame, chart_dir: Path) -> Path | None:
    if decomp.empty:
        return None
    plot_df = decomp[~decomp["component"].eq("strategy_total_return")]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(plot_df["component"], plot_df["value"])
    ax.set_title("Total Return Decomposition")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out = chart_dir / "market_effect_decomposition.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def _plot_rolling_beta(rolling_beta: pd.DataFrame, chart_dir: Path) -> Path | None:
    if rolling_beta.empty:
        return None
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(rolling_beta["trade_date"], rolling_beta["rolling_beta"])
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    ax.axhline(0.0, color="gray", linestyle=":", linewidth=1)
    ax.set_title("Rolling Beta vs HS300")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out = chart_dir / "rolling_beta.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def _plot_capture(capture: pd.DataFrame, chart_dir: Path) -> Path | None:
    if capture.empty:
        return None
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(capture["market_state"], capture["capture_ratio"])
    ax.set_title("Up / Down Capture Ratio")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out = chart_dir / "up_down_capture.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def run_market_effect_analysis(return_frame: pd.DataFrame, brinson_outputs: dict[str, pd.DataFrame], config) -> tuple[dict[str, pd.DataFrame], list[Path]]:
    if return_frame.empty:
        return {}, []

    strategy_ret = return_frame.get("strategy_ret", pd.Series(dtype=float))
    hs300_ret = return_frame.get("hs300_ret", pd.Series(dtype=float))
    market_effect_summary = pd.DataFrame(
        [
            {
                "market_effect_total_return": float((1.0 + hs300_ret.fillna(0.0)).prod() - 1.0) if len(hs300_ret) else np.nan,
                "strategy_total_return": float((1.0 + strategy_ret.fillna(0.0)).prod() - 1.0) if len(strategy_ret) else np.nan,
                "excess_return": float((1.0 + strategy_ret.fillna(0.0)).prod() - (1.0 + hs300_ret.fillna(0.0)).prod())
                if len(strategy_ret) and len(hs300_ret)
                else np.nan,
            }
        ]
    )
    alpha_beta = pd.DataFrame([calculate_alpha_beta(strategy_ret, hs300_ret, config.TRADING_DAYS)])
    rolling_beta = calculate_rolling_beta(return_frame, config.ROLLING_BETA_WINDOW)
    capture = calculate_up_down_capture(strategy_ret, hs300_ret)
    decomp = build_total_return_decomposition(return_frame, brinson_outputs)

    charts = [
        _plot_decomposition(decomp, config.CHART_DIR),
        _plot_rolling_beta(rolling_beta, config.CHART_DIR),
        _plot_capture(capture, config.CHART_DIR),
    ]
    charts = [p for p in charts if p is not None]
    return (
        {
            "market_effect_summary": market_effect_summary,
            "alpha_beta_summary": alpha_beta,
            "rolling_beta": rolling_beta,
            "up_down_capture": capture,
            "total_return_decomposition": decomp,
        },
        charts,
    )
