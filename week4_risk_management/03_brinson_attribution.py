"""Simplified Brinson attribution module.

The current project has a learning-version industry mapping and daily stock
panel. This module implements a practical Brinson-style approximation that can
be replaced by formal index constituent weights once full data is available.
"""

import numpy as np
import pandas as pd


def _prepare_inputs(holdings: pd.DataFrame, factor_panel: pd.DataFrame) -> pd.DataFrame:
    if holdings.empty or factor_panel.empty:
        return pd.DataFrame()
    needed = ["trade_date", "ts_code", "industry", "ret_20d_fwd"]
    if not set(needed).issubset(factor_panel.columns):
        return pd.DataFrame()
    panel = factor_panel[needed].copy()
    merged = holdings.merge(panel, on=["trade_date", "ts_code"], how="left")
    merged["industry"] = merged["industry"].fillna("Unknown")
    merged["ret_20d_fwd"] = pd.to_numeric(merged["ret_20d_fwd"], errors="coerce")
    return merged.dropna(subset=["ret_20d_fwd"])


def calculate_brinson_by_period(holdings: pd.DataFrame, factor_panel: pd.DataFrame) -> pd.DataFrame:
    merged = _prepare_inputs(holdings, factor_panel)
    if merged.empty:
        return pd.DataFrame()

    panel = factor_panel[["trade_date", "ts_code", "industry", "ret_20d_fwd"]].copy()
    panel["industry"] = panel["industry"].fillna("Unknown")
    panel["ret_20d_fwd"] = pd.to_numeric(panel["ret_20d_fwd"], errors="coerce")
    panel = panel.dropna(subset=["ret_20d_fwd"])

    rows = []
    for date, hld in merged.groupby("trade_date"):
        universe = panel[panel["trade_date"] == date]
        if universe.empty:
            continue

        benchmark_by_industry = (
            universe.groupby("industry")["ret_20d_fwd"]
            .agg(benchmark_return="mean", count="count")
            .reset_index()
        )
        benchmark_by_industry["benchmark_weight"] = (
            benchmark_by_industry["count"] / benchmark_by_industry["count"].sum()
        )
        benchmark_total = float(
            (benchmark_by_industry["benchmark_weight"] * benchmark_by_industry["benchmark_return"]).sum()
        )

        portfolio_by_industry = (
            hld.groupby("industry")
            .apply(lambda x: pd.Series({
                "portfolio_weight": x["weight"].sum(),
                "portfolio_return": np.average(x["ret_20d_fwd"], weights=x["weight"]),
            }), include_groups=False)
            .reset_index()
        )

        attrib = benchmark_by_industry.merge(portfolio_by_industry, on="industry", how="outer")
        attrib[["benchmark_weight", "portfolio_weight"]] = attrib[["benchmark_weight", "portfolio_weight"]].fillna(0.0)
        attrib[["benchmark_return", "portfolio_return"]] = attrib[["benchmark_return", "portfolio_return"]].fillna(0.0)
        attrib["trade_date"] = date
        attrib["benchmark_total_return"] = benchmark_total
        attrib["allocation_effect"] = (
            (attrib["portfolio_weight"] - attrib["benchmark_weight"])
            * (attrib["benchmark_return"] - benchmark_total)
        )
        attrib["selection_effect"] = attrib["benchmark_weight"] * (
            attrib["portfolio_return"] - attrib["benchmark_return"]
        )
        attrib["interaction_effect"] = (
            (attrib["portfolio_weight"] - attrib["benchmark_weight"])
            * (attrib["portfolio_return"] - attrib["benchmark_return"])
        )
        rows.append(attrib)

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def aggregate_brinson(attribution: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if attribution.empty:
        empty = pd.DataFrame()
        return {"brinson_total": empty, "brinson_by_year": empty, "brinson_by_industry": empty}

    effect_cols = ["allocation_effect", "selection_effect", "interaction_effect"]
    total = attribution[effect_cols].sum().to_frame("value").reset_index().rename(columns={"index": "effect"})
    total["total_effect"] = total["value"]

    df = attribution.copy()
    df["year"] = pd.to_datetime(df["trade_date"]).dt.year
    by_year = df.groupby("year", as_index=False)[effect_cols].sum()
    by_industry = df.groupby("industry", as_index=False)[effect_cols].sum()
    return {
        "brinson_total": total,
        "brinson_by_year": by_year,
        "brinson_by_industry": by_industry,
    }


def run_brinson_attribution(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    attribution = calculate_brinson_by_period(data.get("holdings", pd.DataFrame()), data.get("factor_panel", pd.DataFrame()))
    outputs = aggregate_brinson(attribution)
    outputs["brinson_by_period"] = attribution
    return outputs
