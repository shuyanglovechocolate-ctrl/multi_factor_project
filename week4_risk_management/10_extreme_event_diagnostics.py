"""Extreme event diagnostic cards for Week 4 v4.1."""

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def build_extreme_event_calendar(config) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"event_name": name, "start_date": start, "end_date": end}
            for name, (start, end) in config.EXTREME_PERIODS.items()
        ]
    )


def _max_drawdown_from_returns(ret: pd.Series) -> float:
    if ret.empty:
        return np.nan
    nav = (1.0 + ret.fillna(0.0)).cumprod()
    return float((nav / nav.cummax() - 1.0).min())


def _recovery_days(ret: pd.Series) -> float:
    if ret.empty:
        return np.nan
    nav = (1.0 + ret.fillna(0.0)).cumprod()
    peak = nav.cummax()
    dd = nav / peak - 1.0
    trough_idx = dd.idxmin()
    previous_peak = peak.loc[:trough_idx].iloc[-1]
    after = nav.loc[trough_idx:]
    recovered = after[after >= previous_peak]
    if recovered.empty:
        return np.nan
    return int(recovered.index[0] - trough_idx)


def calculate_stress_score(row: dict, config) -> float:
    if not row.get("data_available", False):
        return np.nan
    drawdown_score = min(abs(row.get("max_drawdown", 0.0)) / 0.4, 1.0) * 100
    vol_score = min(row.get("volatility", 0.0) / 0.5, 1.0) * 100
    loss_score = min(abs(min(row.get("portfolio_return", 0.0), 0.0)) / 0.3, 1.0) * 100
    recovery_days = row.get("recovery_days", np.nan)
    recovery_score = min(recovery_days / 120, 1.0) * 100 if np.isfinite(recovery_days) else 70
    w = config.STRESS_SCORE_WEIGHTS
    return float(
        drawdown_score * w["drawdown"]
        + vol_score * w["volatility"]
        + loss_score * w["loss"]
        + recovery_score * w["recovery_days"]
    )


def generate_event_interpretation(row: dict) -> str:
    if not row.get("data_available", False):
        return "当前静态样本未覆盖该事件区间，保留事件框架，待动态股票池数据补齐后自动重跑。"
    excess = row.get("excess_return", np.nan)
    mdd = row.get("max_drawdown", np.nan)
    if np.isfinite(excess) and excess > 0 and np.isfinite(mdd):
        return "策略在该压力阶段相对基准取得正超额收益，但仍需关注阶段内回撤。"
    if np.isfinite(excess) and excess <= 0:
        return "策略在该压力阶段未能跑赢基准，说明风险控制和风格适应性仍需加强。"
    return "该阶段数据可用但指标不完整，需要结合净值曲线进一步判断。"


def run_extreme_event_diagnostics(return_frame: pd.DataFrame, config) -> tuple[dict[str, pd.DataFrame], list[Path]]:
    calendar = build_extreme_event_calendar(config)
    rows = []
    for _, event in calendar.iterrows():
        start = pd.Timestamp(event["start_date"])
        end = pd.Timestamp(event["end_date"])
        sub = return_frame[(return_frame["trade_date"] >= start) & (return_frame["trade_date"] <= end)].copy()
        data_available = not sub.empty and "strategy_ret" in sub.columns
        benchmark_available = not sub.empty and "hs300_ret" in sub.columns
        row = {
            "event_name": event["event_name"],
            "start_date": event["start_date"],
            "end_date": event["end_date"],
            "data_available": data_available,
            "benchmark_available": benchmark_available,
            "portfolio_return": np.nan,
            "benchmark_return": np.nan,
            "excess_return": np.nan,
            "max_drawdown": np.nan,
            "volatility": np.nan,
            "recovery_days": np.nan,
            "limitation_note": "",
        }
        if data_available:
            p = sub["strategy_ret"].fillna(0.0)
            b = sub["hs300_ret"].fillna(0.0) if "hs300_ret" in sub.columns else pd.Series(dtype=float)
            row.update(
                {
                    "portfolio_return": float((1.0 + p).prod() - 1.0),
                    "benchmark_return": float((1.0 + b).prod() - 1.0) if len(b) else np.nan,
                    "max_drawdown": _max_drawdown_from_returns(p),
                    "volatility": float(p.std(ddof=1) * np.sqrt(252)) if len(p) > 1 else np.nan,
                    "recovery_days": _recovery_days(p),
                }
            )
            row["excess_return"] = row["portfolio_return"] - row["benchmark_return"] if np.isfinite(row["benchmark_return"]) else np.nan
        else:
            row["limitation_note"] = "当前静态样本不覆盖该区间。"
        row["stress_score"] = calculate_stress_score(row, config)
        row["interpretation"] = generate_event_interpretation(row)
        rows.append(row)

    diagnostics = pd.DataFrame(rows)
    availability = diagnostics[["event_name", "start_date", "end_date", "data_available", "benchmark_available", "limitation_note"]]
    stress_score = diagnostics[["event_name", "stress_score", "interpretation"]]
    charts = _plot_extreme_diagnostics(diagnostics, config.CHART_DIR)
    return (
        {
            "extreme_event_calendar": calendar,
            "extreme_event_availability": availability,
            "extreme_event_diagnostics": diagnostics,
            "extreme_event_stress_score": stress_score,
        },
        charts,
    )


def _plot_extreme_diagnostics(diagnostics: pd.DataFrame, chart_dir: Path) -> list[Path]:
    paths = []
    available = diagnostics[diagnostics["data_available"] == True].copy()
    if available.empty:
        return paths
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(available["event_name"], available["stress_score"])
    ax.set_title("Extreme Event Stress Score")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out = chart_dir / "extreme_event_score_bar.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    paths.append(out)

    fig, ax = plt.subplots(figsize=(9, 4))
    x = np.arange(len(available))
    ax.bar(x - 0.2, available["portfolio_return"], width=0.4, label="Portfolio Return")
    ax.bar(x + 0.2, available["max_drawdown"], width=0.4, label="Max Drawdown")
    ax.set_xticks(x)
    ax.set_xticklabels(available["event_name"], rotation=25, ha="right")
    ax.set_title("Extreme Event Return and Drawdown")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out = chart_dir / "extreme_event_return_drawdown.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    paths.append(out)
    return paths
