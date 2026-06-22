"""Extreme market period tests for Week 4."""

import numpy as np
import pandas as pd


def _period_metrics(df: pd.DataFrame, start: str, end: str) -> dict:
    period = df[(df["trade_date"] >= pd.Timestamp(start)) & (df["trade_date"] <= pd.Timestamp(end))].copy()
    if period.empty:
        return {
            "data_available": False,
            "strategy_return": np.nan,
            "hs300_return": np.nan,
            "excess_return": np.nan,
            "strategy_max_drawdown": np.nan,
            "hs300_max_drawdown": np.nan,
        }

    def total_ret(col: str) -> float:
        if col not in period.columns:
            return np.nan
        return float((1.0 + period[col].fillna(0.0)).prod() - 1.0)

    def mdd_from_ret(col: str) -> float:
        if col not in period.columns:
            return np.nan
        nav = (1.0 + period[col].fillna(0.0)).cumprod()
        dd = nav / nav.cummax() - 1.0
        return float(dd.min())

    strategy_return = total_ret("strategy_ret")
    hs300_return = total_ret("hs300_ret")
    return {
        "data_available": True,
        "strategy_return": strategy_return,
        "hs300_return": hs300_return,
        "excess_return": strategy_return - hs300_return if np.isfinite(hs300_return) else np.nan,
        "strategy_max_drawdown": mdd_from_ret("strategy_ret"),
        "hs300_max_drawdown": mdd_from_ret("hs300_ret"),
    }


def run_extreme_market_test(return_frame: pd.DataFrame, config) -> pd.DataFrame:
    if return_frame.empty:
        return pd.DataFrame()
    rows = []
    for name, (start, end) in config.EXTREME_PERIODS.items():
        metrics = _period_metrics(return_frame, start, end)
        rows.append({"stress_period": name, "start_date": start, "end_date": end, **metrics})
    return pd.DataFrame(rows)
