"""Basic risk metrics used in Week 4."""

import math

import numpy as np
import pandas as pd


def max_drawdown(nav: pd.Series) -> float:
    nav = pd.to_numeric(nav, errors="coerce").dropna()
    if nav.empty:
        return np.nan
    running_max = nav.cummax()
    drawdown = nav / running_max - 1.0
    return float(drawdown.min())


def annual_return(ret: pd.Series, trading_days: int = 252) -> float:
    ret = pd.to_numeric(ret, errors="coerce").dropna()
    if ret.empty:
        return np.nan
    total = (1.0 + ret).prod()
    years = len(ret) / trading_days
    if years <= 0:
        return np.nan
    return float(total ** (1.0 / years) - 1.0)


def annual_volatility(ret: pd.Series, trading_days: int = 252) -> float:
    ret = pd.to_numeric(ret, errors="coerce").dropna()
    if len(ret) < 2:
        return np.nan
    return float(ret.std(ddof=1) * math.sqrt(trading_days))


def sharpe_ratio(ret: pd.Series, risk_free_rate: float = 0.02, trading_days: int = 252) -> float:
    ann_ret = annual_return(ret, trading_days)
    ann_vol = annual_volatility(ret, trading_days)
    if not np.isfinite(ann_vol) or ann_vol == 0:
        return np.nan
    return float((ann_ret - risk_free_rate) / ann_vol)


def calmar_ratio(ret: pd.Series, nav: pd.Series, trading_days: int = 252) -> float:
    ann_ret = annual_return(ret, trading_days)
    mdd = max_drawdown(nav)
    if not np.isfinite(mdd) or mdd == 0:
        return np.nan
    return float(ann_ret / abs(mdd))


def summarize_series(name: str, ret: pd.Series, nav: pd.Series, config) -> dict:
    ret = pd.to_numeric(ret, errors="coerce").fillna(0.0)
    nav = pd.to_numeric(nav, errors="coerce").ffill()
    return {
        "series": name,
        "annual_return": annual_return(ret, config.TRADING_DAYS),
        "annual_volatility": annual_volatility(ret, config.TRADING_DAYS),
        "sharpe": sharpe_ratio(ret, config.RISK_FREE_RATE, config.TRADING_DAYS),
        "max_drawdown": max_drawdown(nav),
        "calmar": calmar_ratio(ret, nav, config.TRADING_DAYS),
        "win_rate": float((ret > 0).mean()) if len(ret) else np.nan,
        "sample_days": int(len(ret)),
    }


def run_risk_metrics(return_frame: pd.DataFrame, config) -> pd.DataFrame:
    if return_frame.empty:
        return pd.DataFrame()

    rows = []
    if {"strategy_ret", "strategy_nav"}.issubset(return_frame.columns):
        rows.append(summarize_series("strategy", return_frame["strategy_ret"], return_frame["strategy_nav"], config))
    if {"benchmark_ret", "benchmark_nav"}.issubset(return_frame.columns):
        rows.append(summarize_series("sample_equal_benchmark", return_frame["benchmark_ret"], return_frame["benchmark_nav"], config))
    if {"hs300_ret", "hs300_nav"}.issubset(return_frame.columns):
        rows.append(summarize_series("hs300", return_frame["hs300_ret"], return_frame["hs300_nav"], config))

    if {"strategy_ret", "hs300_ret"}.issubset(return_frame.columns):
        excess = return_frame["strategy_ret"].fillna(0.0) - return_frame["hs300_ret"].fillna(0.0)
        rows.append(
            {
                "series": "excess_vs_hs300",
                "annual_return": annual_return(excess, config.TRADING_DAYS),
                "annual_volatility": annual_volatility(excess, config.TRADING_DAYS),
                "sharpe": sharpe_ratio(excess, 0.0, config.TRADING_DAYS),
                "max_drawdown": np.nan,
                "calmar": np.nan,
                "win_rate": float((excess > 0).mean()),
                "sample_days": int(len(excess)),
            }
        )
    return pd.DataFrame(rows)
