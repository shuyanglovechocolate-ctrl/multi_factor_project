"""Risk exposure summaries for Week 4."""

import numpy as np
import pandas as pd


def summarize_industry_exposure(industry_exposure: pd.DataFrame) -> pd.DataFrame:
    if industry_exposure.empty or not {"industry", "industry_weight"}.issubset(industry_exposure.columns):
        return pd.DataFrame()
    return (
        industry_exposure.groupby("industry")["industry_weight"]
        .agg(avg_weight="mean", max_weight="max", min_weight="min", observations="count")
        .reset_index()
        .sort_values("avg_weight", ascending=False)
    )


def summarize_holding_concentration(holdings: pd.DataFrame) -> pd.DataFrame:
    if holdings.empty or not {"trade_date", "weight"}.issubset(holdings.columns):
        return pd.DataFrame()

    def calc(group: pd.DataFrame) -> pd.Series:
        weights = group["weight"].astype(float)
        hhi = float((weights ** 2).sum())
        return pd.Series(
            {
                "stock_count": group["ts_code"].nunique() if "ts_code" in group.columns else len(group),
                "top1_weight": float(weights.max()),
                "top5_weight": float(weights.sort_values(ascending=False).head(5).sum()),
                "herfindahl_index": hhi,
                "effective_num_stocks": 1.0 / hhi if hhi > 0 else np.nan,
            }
        )

    return holdings.groupby("trade_date").apply(calc, include_groups=False).reset_index()


def summarize_turnover(turnover: pd.DataFrame) -> pd.DataFrame:
    if turnover.empty or "turnover" not in turnover.columns:
        return pd.DataFrame()
    df = turnover.copy()
    if "is_rebalance" in df.columns:
        df = df[df["is_rebalance"].astype(bool)]
    return pd.DataFrame(
        [
            {
                "avg_turnover": df["turnover"].mean(),
                "median_turnover": df["turnover"].median(),
                "max_turnover": df["turnover"].max(),
                "rebalance_count": len(df),
            }
        ]
    )


def run_risk_exposure(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {
        "industry_exposure_summary": summarize_industry_exposure(data.get("industry_exposure", pd.DataFrame())),
        "holding_concentration_summary": summarize_holding_concentration(data.get("holdings", pd.DataFrame())),
        "turnover_summary": summarize_turnover(data.get("turnover", pd.DataFrame())),
    }
