"""Portfolio-level risk-control overlay simulation for Week 4 v4.1."""

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _metrics(name: str, ret: pd.Series, trading_days: int) -> dict:
    ret = ret.fillna(0.0)
    nav = (1.0 + ret).cumprod()
    ann_ret = float(nav.iloc[-1] ** (trading_days / len(ret)) - 1.0) if len(ret) else np.nan
    ann_vol = float(ret.std(ddof=1) * np.sqrt(trading_days)) if len(ret) > 1 else np.nan
    mdd = float((nav / nav.cummax() - 1.0).min()) if len(ret) else np.nan
    sharpe = ann_ret / ann_vol if ann_vol and np.isfinite(ann_vol) else np.nan
    calmar = ann_ret / abs(mdd) if mdd and np.isfinite(mdd) else np.nan
    return {
        "risk_control": name,
        "annual_return": ann_ret,
        "annual_volatility": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": mdd,
        "calmar": calmar,
        "win_rate": float((ret > 0).mean()) if len(ret) else np.nan,
        "final_nav": float(nav.iloc[-1]) if len(nav) else np.nan,
    }


def simulate_portfolio_stop_loss(returns: pd.Series, stop_loss: float = -0.10, reduce_position: float = 0.5) -> pd.Series:
    nav = 1.0
    peak = 1.0
    out = []
    for r in returns.fillna(0.0):
        dd = nav / peak - 1.0
        position = reduce_position if dd <= stop_loss else 1.0
        adjusted = r * position
        nav *= 1.0 + adjusted
        peak = max(peak, nav)
        out.append(adjusted)
    return pd.Series(out, index=returns.index)


def simulate_volatility_targeting(returns: pd.Series, target_vol: float = 0.15, window: int = 20) -> pd.Series:
    realized = returns.fillna(0.0).rolling(window, min_periods=5).std() * np.sqrt(252)
    position = (target_vol / realized).clip(lower=0.0, upper=1.0).fillna(1.0)
    return returns.fillna(0.0) * position


def simulate_ma_timing(returns: pd.Series, benchmark_nav: pd.Series, ma_window: int = 60, reduce_position: float = 0.5) -> pd.Series:
    ma = benchmark_nav.rolling(ma_window, min_periods=5).mean()
    position = np.where(benchmark_nav >= ma, 1.0, reduce_position)
    return returns.fillna(0.0) * pd.Series(position, index=returns.index)


def simulate_fixed_position(returns: pd.Series, position: float = 0.8) -> pd.Series:
    return returns.fillna(0.0) * position


def run_risk_control_simulation(return_frame: pd.DataFrame, config) -> tuple[dict[str, pd.DataFrame], list[Path]]:
    if return_frame.empty or "strategy_ret" not in return_frame.columns:
        return {}, []
    ret = return_frame["strategy_ret"].fillna(0.0).reset_index(drop=True)
    benchmark_nav = return_frame.get("hs300_nav", pd.Series(np.ones(len(ret)))).reset_index(drop=True)
    simulations = {
        "original": ret,
        "stop_loss_10pct_pos50": simulate_portfolio_stop_loss(ret, -0.10, 0.5),
        "vol_target_15pct": simulate_volatility_targeting(ret, 0.15),
        "ma60_timing_pos50": simulate_ma_timing(ret, benchmark_nav, 60, 0.5),
        "fixed_position_80pct": simulate_fixed_position(ret, 0.8),
    }
    summary = pd.DataFrame([_metrics(name, series, config.TRADING_DAYS) for name, series in simulations.items()])

    stop_rows = []
    for stop in config.STOP_LOSS_LEVELS:
        for pos in config.REDUCE_POSITION_LEVELS:
            sim = simulate_portfolio_stop_loss(ret, stop, pos)
            row = _metrics(f"stop_{stop}_pos_{pos}", sim, config.TRADING_DAYS)
            row.update({"stop_loss": stop, "reduce_position": pos})
            stop_rows.append(row)
    stop_sensitivity = pd.DataFrame(stop_rows)

    position_rows = []
    for pos in config.POSITION_LEVELS:
        sim = simulate_fixed_position(ret, pos)
        row = _metrics(f"fixed_position_{pos}", sim, config.TRADING_DAYS)
        row["position"] = pos
        position_rows.append(row)
    position_sensitivity = pd.DataFrame(position_rows)

    nav_panel = pd.DataFrame({"trade_date": return_frame["trade_date"].values})
    for name, series in simulations.items():
        nav_panel[name] = (1.0 + series.reset_index(drop=True)).cumprod()

    chart_paths = _plot_risk_control(nav_panel, summary, stop_sensitivity, config.CHART_DIR)
    return (
        {
            "risk_control_simulation_summary": summary,
            "risk_control_comparison": summary,
            "stop_loss_sensitivity": stop_sensitivity,
            "position_control_sensitivity": position_sensitivity,
        },
        chart_paths,
    )


def _plot_risk_control(nav_panel: pd.DataFrame, summary: pd.DataFrame, stop_sensitivity: pd.DataFrame, chart_dir: Path) -> list[Path]:
    paths = []
    if not nav_panel.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        for col in nav_panel.columns:
            if col != "trade_date":
                ax.plot(nav_panel["trade_date"], nav_panel[col], label=col)
        ax.set_title("Risk Control NAV Comparison")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        out = chart_dir / "risk_control_nav_comparison.png"
        fig.savefig(out, dpi=160)
        plt.close(fig)
        paths.append(out)

        dd = nav_panel.copy()
        for col in dd.columns:
            if col != "trade_date":
                dd[col] = dd[col] / dd[col].cummax() - 1.0
        fig, ax = plt.subplots(figsize=(10, 5))
        for col in dd.columns:
            if col != "trade_date":
                ax.plot(dd["trade_date"], dd[col], label=col)
        ax.set_title("Risk Control Drawdown Comparison")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        out = chart_dir / "risk_control_drawdown_comparison.png"
        fig.savefig(out, dpi=160)
        plt.close(fig)
        paths.append(out)

    if not stop_sensitivity.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        pivot = stop_sensitivity.pivot(index="stop_loss", columns="reduce_position", values="calmar")
        im = ax.imshow(pivot.values, aspect="auto")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        ax.set_title("Stop Loss Sensitivity: Calmar")
        fig.colorbar(im, ax=ax)
        fig.tight_layout()
        out = chart_dir / "stop_loss_sensitivity.png"
        fig.savefig(out, dpi=160)
        plt.close(fig)
        paths.append(out)
    return paths
