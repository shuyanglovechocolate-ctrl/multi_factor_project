"""Week 2 multi-factor model construction and layer backtest."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".matplotlib-cache"))
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


FACTOR_COLS = [
    "factor_momentum",
    "factor_volatility",
    "factor_turnover",
    "factor_size",
    "factor_reversal_5d",
]

COMPOSITE_COLS = [
    "composite_equal",
    "composite_equal_size_neutral",
    "composite_equal_industry_size_neutral",
    "composite_equal_neutral",
    "composite_ic_weight",
    "composite_ic_weight_size_neutral",
    "composite_ic_weight_industry_size_neutral",
    "composite_ic_weight_neutral",
    "composite_pca",
    "composite_pca_size_neutral",
    "composite_pca_industry_size_neutral",
    "composite_pca_neutral",
    "composite_rolling_ic_weight",
    "composite_rolling_ic_weight_size_neutral",
    "composite_rolling_ic_weight_industry_size_neutral",
]

BASE_COMPOSITE_COLS = [
    "composite_equal",
    "composite_ic_weight",
    "composite_pca",
    "composite_rolling_ic_weight",
]

ROLLING_IC_WINDOWS = [120, 252]

ECONOMIC_PRIORITY = {
    "factor_momentum": 5,
    "factor_volatility": 4,
    "factor_turnover": 4,
    "factor_reversal_5d": 3,
    "factor_size": 2,
}

INDUSTRY_BY_PREFIX = {
    "000": "Financials",
    "001": "Industrials",
    "002": "Real Estate",
    "300": "Technology",
    "600": "Financials",
    "601": "Financials",
    "603": "Consumer",
    "605": "Consumer",
    "688": "Technology",
}


def method_slug(factor_col: str) -> str:
    mapping = {
        "composite_equal": "equal_weight",
        "composite_equal_size_neutral": "equal_weight_size_neutral",
        "composite_equal_industry_size_neutral": "equal_weight_industry_size_neutral",
        "composite_equal_neutral": "equal_weight_neutral",
        "composite_ic_weight": "ic_weight",
        "composite_ic_weight_size_neutral": "ic_weight_size_neutral",
        "composite_ic_weight_industry_size_neutral": "ic_weight_industry_size_neutral",
        "composite_ic_weight_neutral": "ic_weight_neutral",
        "composite_pca": "pca",
        "composite_pca_size_neutral": "pca_size_neutral",
        "composite_pca_industry_size_neutral": "pca_industry_size_neutral",
        "composite_pca_neutral": "pca_neutral",
        "composite_rolling_ic_weight": "rolling_ic_weight",
        "composite_rolling_ic_weight_size_neutral": "rolling_ic_weight_size_neutral",
        "composite_rolling_ic_weight_industry_size_neutral": "rolling_ic_weight_industry_size_neutral",
    }
    return mapping.get(factor_col, factor_col.replace("composite_", ""))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Week 2 multi-factor model.")
    parser.add_argument("--panel-file", default=str(PROJECT_ROOT / "data" / "processed" / "factor_panel.csv"))
    parser.add_argument("--ic-file", default=str(PROJECT_ROOT / "outputs" / "week1" / "factor_ic_summary.csv"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "week2"))
    parser.add_argument("--return-col", default="ret_20d_fwd")
    parser.add_argument("--corr-threshold", type=float, default=0.7)
    parser.add_argument("--rolling-window", type=int, default=120)
    return parser.parse_args()


def read_inputs(panel_file: Path, ic_file: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = pd.read_csv(panel_file)
    ic = pd.read_csv(ic_file)
    panel["trade_date"] = pd.to_datetime(panel["trade_date"])
    return panel, ic


def infer_learning_industry(ts_code: str) -> str:
    prefix = str(ts_code).split(".")[0][:3]
    if prefix in INDUSTRY_BY_PREFIX:
        return INDUSTRY_BY_PREFIX[prefix]
    if prefix.startswith("00"):
        return "Consumer"
    if prefix.startswith("30"):
        return "Technology"
    if prefix.startswith("60"):
        return "Industrials"
    if prefix.startswith("68"):
        return "Technology"
    return "Diversified"


def add_learning_industry(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = panel.copy()
    if "industry" not in panel.columns:
        panel["industry"] = panel["ts_code"].map(infer_learning_industry)
    mapping = (
        panel[["ts_code", "industry"]]
        .drop_duplicates()
        .sort_values("ts_code")
        .assign(mapping_source="learning_code_prefix")
    )
    return panel, mapping


def build_redundancy_decision(
    corr: pd.DataFrame,
    ic_summary: pd.DataFrame,
    factor_cols: list[str],
    threshold: float,
) -> pd.DataFrame:
    score = (
        ic_summary.set_index("factor")
        .reindex(factor_cols)
        .assign(
            rank_ic_mean=lambda x: pd.to_numeric(x["rank_ic_mean"], errors="coerce").fillna(0),
            rank_icir=lambda x: pd.to_numeric(x["rank_icir"], errors="coerce").fillna(0),
        )
    )
    rows: list[dict[str, object]] = []
    for i, left in enumerate(factor_cols):
        for right in factor_cols[i + 1 :]:
            value = corr.loc[left, right]
            abs_corr = abs(value) if pd.notna(value) else np.nan
            keep = ""
            drop = ""
            if pd.isna(abs_corr) or abs_corr <= threshold:
                reason = "abs_corr_not_above_threshold_keep_both"
            else:
                left_rank = score.loc[left, "rank_ic_mean"]
                right_rank = score.loc[right, "rank_ic_mean"]
                left_ir = score.loc[left, "rank_icir"]
                right_ir = score.loc[right, "rank_icir"]
                if abs(left_rank - right_rank) > 0.005:
                    keep = left if left_rank >= right_rank else right
                    reason = "higher_rank_ic_mean"
                elif abs(left_ir - right_ir) > 0.05:
                    keep = left if left_ir >= right_ir else right
                    reason = "higher_rank_icir"
                else:
                    keep = left if ECONOMIC_PRIORITY.get(left, 0) >= ECONOMIC_PRIORITY.get(right, 0) else right
                    reason = "similar_ic_keep_clearer_economic_meaning"
                drop = right if keep == left else left
            rows.append(
                {
                    "factor_a": left,
                    "factor_b": right,
                    "spearman_corr": value,
                    "abs_corr": abs_corr,
                    "threshold": threshold,
                    "keep_factor": keep,
                    "drop_factor": drop,
                    "reason": reason,
                }
            )
    return pd.DataFrame(rows)


def average_cross_sectional_spearman(panel: pd.DataFrame, factor_cols: list[str]) -> pd.DataFrame:
    matrices: list[pd.DataFrame] = []
    for _, group in panel.groupby("trade_date"):
        usable = group[factor_cols].dropna(how="all")
        if len(usable) < 3:
            continue
        corr = usable.corr(method="spearman")
        matrices.append(corr)

    if not matrices:
        return pd.DataFrame(np.eye(len(factor_cols)), index=factor_cols, columns=factor_cols)

    stacked = np.stack([matrix.reindex(index=factor_cols, columns=factor_cols).to_numpy() for matrix in matrices])
    avg = np.nanmean(stacked, axis=0)
    return pd.DataFrame(avg, index=factor_cols, columns=factor_cols)


def select_factors(corr: pd.DataFrame, ic_summary: pd.DataFrame, factor_cols: list[str], threshold: float) -> pd.DataFrame:
    score = (
        ic_summary.set_index("factor")
        .reindex(factor_cols)
        .assign(
            rank_ic_mean=lambda x: pd.to_numeric(x["rank_ic_mean"], errors="coerce").fillna(0),
            rank_icir=lambda x: pd.to_numeric(x["rank_icir"], errors="coerce").fillna(0),
        )
    )
    score["selection_score"] = score["rank_ic_mean"].abs() + 0.25 * score["rank_icir"].abs()

    selected = set(factor_cols)
    pairs: list[dict[str, object]] = []
    for i, left in enumerate(factor_cols):
        for right in factor_cols[i + 1 :]:
            value = corr.loc[left, right]
            if pd.isna(value) or abs(value) <= threshold:
                continue
            left_score = score.loc[left, "selection_score"]
            right_score = score.loc[right, "selection_score"]
            drop = right if left_score >= right_score else left
            keep = left if drop == right else right
            selected.discard(drop)
            pairs.append({"factor_a": left, "factor_b": right, "corr": value, "keep": keep, "drop": drop})

    out = score.reset_index().rename(columns={"index": "factor"})
    out["selected"] = out["factor"].isin(selected)
    selected_count = int(out["selected"].sum())
    if selected_count == 0:
        out["selected"] = out["factor"].isin(factor_cols)

    selected_factors = out.loc[out["selected"], "factor"].tolist()
    out["weight_equal"] = out["selected"].astype(float) / max(len(selected_factors), 1)

    positive_rank_ic = out["rank_ic_mean"].where((out["selected"]) & (out["rank_ic_mean"] > 0), 0)
    if positive_rank_ic.sum() > 0:
        out["weight_ic"] = positive_rank_ic / positive_rank_ic.sum()
    else:
        out["weight_ic"] = out["weight_equal"]

    if pairs:
        pair_df = pd.DataFrame(pairs)
        out = out.merge(pair_df.groupby("drop")["corr"].max().rename("dropped_due_to_corr"), left_on="factor", right_index=True, how="left")
    else:
        out["dropped_due_to_corr"] = np.nan
    return out


def neutralize_cross_section(
    panel: pd.DataFrame,
    value_col: str,
    use_size: bool = True,
    use_industry: bool = False,
) -> pd.Series:
    residuals = pd.Series(index=panel.index, dtype=float)
    for _, group in panel.groupby("trade_date"):
        y = pd.to_numeric(group[value_col], errors="coerce")
        valid = y.notna()
        regressors = [pd.Series(1.0, index=group.index, name="intercept")]

        if use_size and "factor_size" in group.columns:
            size = pd.to_numeric(group["factor_size"], errors="coerce")
            if size.notna().sum() > 2 and size.nunique(dropna=True) > 1:
                regressors.append(size.rename("factor_size"))
                valid &= size.notna()

        if use_industry and "industry" in group.columns:
            dummies = pd.get_dummies(group["industry"], prefix="industry", dummy_na=False)
            if not dummies.empty:
                dummies = dummies.iloc[:, 1:]
                regressors.extend([dummies[col].astype(float).rename(col) for col in dummies.columns])
                valid &= group["industry"].notna()

        if valid.sum() < 3:
            residuals.loc[group.index] = y - y.mean(skipna=True)
            continue

        x = pd.concat(regressors, axis=1).loc[valid]
        y_valid = y.loc[valid]
        beta = np.linalg.pinv(x.to_numpy(dtype=float)) @ y_valid.to_numpy(dtype=float)
        fitted = x.to_numpy(dtype=float) @ beta
        residuals.loc[y_valid.index] = y_valid.to_numpy(dtype=float) - fitted
    return residuals


def calculate_factor_rank_ic_series(panel: pd.DataFrame, factor_cols: list[str], return_col: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for date, group in panel.groupby("trade_date"):
        for factor in factor_cols:
            data = group[[factor, return_col]].dropna()
            if len(data) < 3 or data[factor].nunique() < 2 or data[return_col].nunique() < 2:
                rank_ic = np.nan
            else:
                rank_ic = data[factor].corr(data[return_col], method="spearman")
            rows.append({"trade_date": date, "factor": factor, "rank_ic": rank_ic})
    return pd.DataFrame(rows)


def calculate_rolling_ic_weights(
    factor_ic_series: pd.DataFrame,
    selected_factors: list[str],
    windows: list[int],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if factor_ic_series.empty:
        return pd.DataFrame(), pd.DataFrame()
    pivot = factor_ic_series.pivot_table(index="trade_date", columns="factor", values="rank_ic", aggfunc="mean")
    pivot = pivot.sort_index().reindex(columns=selected_factors)
    all_rows: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []
    for window in windows:
        hist_mean = pivot.rolling(window, min_periods=max(20, min(window, 60))).mean().shift(1)
        weights = hist_mean.clip(lower=0)
        row_sum = weights.sum(axis=1)
        fallback = row_sum <= 0
        if selected_factors:
            weights.loc[fallback, selected_factors] = 1 / len(selected_factors)
        weights = weights.div(weights.sum(axis=1), axis=0)
        weights = weights.fillna(0)
        weights["trade_date"] = weights.index
        weights["window"] = window
        long_weights = weights.melt(id_vars=["trade_date", "window"], var_name="factor", value_name="weight")
        all_rows.append(long_weights)
        for factor in selected_factors:
            values = weights[factor]
            summary_rows.append(
                {
                    "window": window,
                    "factor": factor,
                    "avg_weight": values.mean(),
                    "median_weight": values.median(),
                    "max_weight": values.max(),
                    "active_periods": int((values > 0).sum()),
                }
            )
    return pd.concat(all_rows, ignore_index=True), pd.DataFrame(summary_rows)


def add_rolling_ic_factor(
    panel: pd.DataFrame,
    selected_factors: list[str],
    rolling_weights: pd.DataFrame,
    window: int,
) -> pd.Series:
    if rolling_weights.empty or not selected_factors:
        return panel[selected_factors].mean(axis=1) if selected_factors else pd.Series(index=panel.index, dtype=float)
    weights = (
        rolling_weights[rolling_weights["window"] == window]
        .pivot_table(index="trade_date", columns="factor", values="weight", aggfunc="mean")
        .reindex(columns=selected_factors)
        .reset_index()
    )
    weights["trade_date"] = pd.to_datetime(weights["trade_date"])
    merged = panel[["trade_date", *selected_factors]].merge(weights, on="trade_date", how="left", suffixes=("", "_weight"))
    result = pd.Series(0.0, index=panel.index, dtype=float)
    valid_any = pd.Series(False, index=panel.index)
    for factor in selected_factors:
        weight_col = f"{factor}_weight"
        if weight_col not in merged.columns:
            continue
        factor_values = pd.to_numeric(merged[factor], errors="coerce")
        factor_weights = pd.to_numeric(merged[weight_col], errors="coerce").fillna(0)
        result = result + factor_values.fillna(0).to_numpy() * factor_weights.to_numpy()
        valid_any |= factor_values.notna()
    result.loc[~valid_any] = np.nan
    return result


def calculate_pca_diagnostics(
    panel: pd.DataFrame,
    selected_factors: list[str],
    selected: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    x = panel[selected_factors].dropna().astype(float) if selected_factors else pd.DataFrame()
    if x.empty or len(selected_factors) < 2:
        return pd.DataFrame(), pd.DataFrame()
    x_centered = x - x.mean(axis=0)
    _, singular_values, vt = np.linalg.svd(x_centered.to_numpy(dtype=float), full_matrices=False)
    explained = singular_values**2
    ratio = explained / explained.sum()
    rank_ic = selected.set_index("factor")["rank_ic_mean"].reindex(selected_factors).fillna(0).to_numpy()
    component_rows: list[dict[str, object]] = []
    variance_rows: list[dict[str, object]] = []
    cumulative = 0.0
    for i, component in enumerate(vt[: min(5, len(selected_factors))], start=1):
        if np.dot(component, rank_ic) < 0:
            component = -component
        cumulative += ratio[i - 1]
        variance_rows.append(
            {
                "component": f"PC{i}",
                "explained_variance_ratio": ratio[i - 1],
                "cumulative_explained_variance_ratio": cumulative,
            }
        )
        for factor, loading in zip(selected_factors, component):
            component_rows.append({"component": f"PC{i}", "factor": factor, "loading": loading})
    return pd.DataFrame(variance_rows), pd.DataFrame(component_rows)


def add_composite_factors(
    panel: pd.DataFrame,
    selected: pd.DataFrame,
    return_col: str,
    rolling_window: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    panel = panel.copy()
    selected_rows = selected[selected["selected"]].copy()
    selected_factors = selected_rows["factor"].tolist()
    if not selected_factors:
        selected_factors = FACTOR_COLS
        selected_rows = selected[selected["factor"].isin(selected_factors)].copy()

    equal_weights = selected_rows.set_index("factor")["weight_equal"].reindex(selected_factors).fillna(0)
    ic_weights = selected_rows.set_index("factor")["weight_ic"].reindex(selected_factors).fillna(0)

    values = panel[selected_factors]
    panel["composite_equal"] = values.mul(equal_weights, axis=1).sum(axis=1, min_count=1)
    panel["composite_ic_weight"] = values.mul(ic_weights, axis=1).sum(axis=1, min_count=1)

    factor_ic_series = calculate_factor_rank_ic_series(panel, selected_factors, return_col)
    rolling_weights, rolling_weight_summary = calculate_rolling_ic_weights(
        factor_ic_series, selected_factors, ROLLING_IC_WINDOWS
    )
    panel["composite_rolling_ic_weight"] = add_rolling_ic_factor(
        panel, selected_factors, rolling_weights, rolling_window
    )

    pca_values = []
    for _, group in panel.groupby("trade_date", sort=False):
        x = group[selected_factors].astype(float)
        valid = x.notna().all(axis=1)
        scores = pd.Series(index=group.index, dtype=float)
        if valid.sum() >= 3:
            xv = x.loc[valid].to_numpy(dtype=float)
            xv = xv - xv.mean(axis=0, keepdims=True)
            _, _, vt = np.linalg.svd(xv, full_matrices=False)
            component = vt[0]
            rank_ic = selected_rows.set_index("factor")["rank_ic_mean"].reindex(selected_factors).fillna(0).to_numpy()
            if np.dot(component, rank_ic) < 0:
                component = -component
            scores.loc[x.loc[valid].index] = xv @ component
        pca_values.append(scores)
    panel["composite_pca"] = pd.concat(pca_values).sort_index()

    pca_explained, pca_components = calculate_pca_diagnostics(panel, selected_factors, selected_rows)

    for col in BASE_COMPOSITE_COLS:
        if col not in panel.columns:
            continue
        panel[f"{col}_size_neutral"] = neutralize_cross_section(panel, col, use_size=True, use_industry=False)
        panel[f"{col}_industry_size_neutral"] = neutralize_cross_section(
            panel, col, use_size=True, use_industry=True
        )

    panel["composite_equal_neutral"] = panel["composite_equal_size_neutral"]
    panel["composite_ic_weight_neutral"] = panel["composite_ic_weight_size_neutral"]
    panel["composite_pca_neutral"] = panel["composite_pca_size_neutral"]
    return panel, factor_ic_series, rolling_weights, rolling_weight_summary, pca_explained, pca_components


def safe_assign_5_groups(group: pd.DataFrame, factor_col: str) -> pd.Series:
    valid = group[factor_col].notna()
    if valid.sum() < 5:
        return pd.Series(index=group.index, dtype=float)
    ranks = group.loc[valid, factor_col].rank(method="first")
    assigned = pd.qcut(ranks, 5, labels=False, duplicates="drop") + 1
    out = pd.Series(index=group.index, dtype=float)
    out.loc[assigned.index] = assigned.astype(float)
    return out


def max_drawdown(returns: pd.Series) -> float:
    cum = (1 + returns.fillna(0)).cumprod()
    drawdown = cum / cum.cummax() - 1
    return float(drawdown.min())


def layer_backtest(panel: pd.DataFrame, factor_col: str, return_col: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    usable = panel[["trade_date", "ts_code", factor_col, return_col]].dropna().copy()
    if usable.empty:
        empty = pd.DataFrame(columns=["trade_date", "group", "period_return", "factor"])
        summary = pd.DataFrame(columns=["factor", "group", "mean_period_return", "annual_return", "annual_vol", "sharpe", "max_drawdown", "win_rate"])
        return empty, summary

    usable["group"] = usable.groupby("trade_date", group_keys=False).apply(lambda x: safe_assign_5_groups(x, factor_col))
    layer_return = (
        usable.dropna(subset=["group"])
        .groupby(["trade_date", "group"])[return_col]
        .mean()
        .reset_index(name="period_return")
    )
    layer_return["factor"] = factor_col

    rows: list[dict[str, object]] = []
    annual_scale = 252 / 20
    for group_id, group_data in layer_return.groupby("group"):
        returns = group_data.sort_values("trade_date")["period_return"]
        mean_ret = returns.mean()
        vol = returns.std()
        annual_return = (1 + mean_ret) ** annual_scale - 1 if pd.notna(mean_ret) else np.nan
        annual_vol = vol * np.sqrt(annual_scale) if pd.notna(vol) else np.nan
        rows.append(
            {
                "factor": factor_col,
                "group": int(group_id),
                "mean_period_return": mean_ret,
                "annual_return": annual_return,
                "annual_vol": annual_vol,
                "sharpe": annual_return / annual_vol if annual_vol and annual_vol != 0 else np.nan,
                "max_drawdown": max_drawdown(returns),
                "win_rate": (returns > 0).mean(),
            }
        )

    pivot = layer_return.pivot_table(index="trade_date", columns="group", values="period_return", aggfunc="mean")
    if 1.0 in pivot.columns and 5.0 in pivot.columns:
        long_short = pivot[5.0] - pivot[1.0]
        mean_ret = long_short.mean()
        vol = long_short.std()
        annual_return = (1 + mean_ret) ** annual_scale - 1 if pd.notna(mean_ret) else np.nan
        annual_vol = vol * np.sqrt(annual_scale) if pd.notna(vol) else np.nan
        rows.append(
            {
                "factor": factor_col,
                "group": "G5-G1",
                "mean_period_return": mean_ret,
                "annual_return": annual_return,
                "annual_vol": annual_vol,
                "sharpe": annual_return / annual_vol if annual_vol and annual_vol != 0 else np.nan,
                "max_drawdown": max_drawdown(long_short),
                "win_rate": (long_short > 0).mean(),
            }
        )

    return layer_return, pd.DataFrame(rows)


def calculate_composite_ic_series(panel: pd.DataFrame, return_col: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    for col in COMPOSITE_COLS:
        if col not in panel.columns:
            continue
        for date, group in panel.groupby("trade_date"):
            data = group[[col, return_col]].dropna()
            if len(data) < 3 or data[col].nunique() < 2 or data[return_col].nunique() < 2:
                rank_ic = np.nan
            else:
                rank_ic = data[col].corr(data[return_col], method="spearman")
            rows.append({"trade_date": date, "composite_factor": col, "rank_ic": rank_ic})

    ic_series = pd.DataFrame(rows)
    summary_rows: list[dict[str, object]] = []
    for factor, data in ic_series.groupby("composite_factor"):
        values = data["rank_ic"].dropna()
        summary_rows.append(
            {
                "factor": factor,
                "sample_periods": len(values),
                "rank_ic_mean": values.mean(),
                "rank_ic_std": values.std(),
                "rank_icir": values.mean() / values.std() if values.std() else np.nan,
                "rank_ic_win_rate": (values > 0).mean() if len(values) else np.nan,
            }
        )

    by_year = (
        ic_series.assign(year=lambda x: pd.to_datetime(x["trade_date"]).dt.year)
        .groupby(["year", "composite_factor"])
        .agg(
            rank_ic_mean=("rank_ic", "mean"),
            rank_ic_win_rate=("rank_ic", lambda x: (x.dropna() > 0).mean()),
            sample_periods=("rank_ic", "count"),
        )
        .reset_index()
    )
    return ic_series, pd.DataFrame(summary_rows), by_year


def calculate_layer_backtest_by_year(layer_outputs: dict[str, pd.DataFrame], composite_ic_by_year: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    annual_scale = 252 / 20
    for factor_col, layer_return in layer_outputs.items():
        if layer_return.empty:
            continue
        pivot = layer_return.pivot_table(index="trade_date", columns="group", values="period_return", aggfunc="mean")
        if 1.0 not in pivot.columns or 5.0 not in pivot.columns:
            continue
        pivot.index = pd.to_datetime(pivot.index)
        long_short = (pivot[5.0] - pivot[1.0]).rename("long_short_return")
        for year, values in long_short.groupby(long_short.index.year):
            mean_ret = values.mean()
            vol = values.std()
            annual_return = (1 + mean_ret) ** annual_scale - 1 if pd.notna(mean_ret) else np.nan
            annual_vol = vol * np.sqrt(annual_scale) if pd.notna(vol) else np.nan
            ic_match = composite_ic_by_year[
                (composite_ic_by_year["year"] == year) & (composite_ic_by_year["composite_factor"] == factor_col)
            ]
            rows.append(
                {
                    "year": year,
                    "composite_factor": factor_col,
                    "rank_ic_mean": ic_match["rank_ic_mean"].iloc[0] if not ic_match.empty else np.nan,
                    "rank_ic_win_rate": ic_match["rank_ic_win_rate"].iloc[0] if not ic_match.empty else np.nan,
                    "long_short_return": annual_return,
                    "sharpe": annual_return / annual_vol if annual_vol and annual_vol != 0 else np.nan,
                    "win_rate": (values > 0).mean(),
                }
            )
    return pd.DataFrame(rows)


def calculate_top_group_turnover(panel: pd.DataFrame, factor_col: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    usable = panel[["trade_date", "ts_code", factor_col]].dropna().copy()
    if usable.empty:
        empty = pd.DataFrame(columns=["trade_date", "model", "top_group_count", "overlap_count", "turnover"])
        summary = pd.DataFrame([{"model": factor_col, "avg_turnover": np.nan, "median_turnover": np.nan, "sample_periods": 0}])
        return empty, summary

    usable["group"] = usable.groupby("trade_date", group_keys=False).apply(lambda x: safe_assign_5_groups(x, factor_col))
    top = usable[usable["group"] == 5].copy()
    rows: list[dict[str, object]] = []
    previous: set[str] | None = None
    for date, group in top.groupby("trade_date"):
        current = set(group["ts_code"])
        if previous is None or not current:
            overlap_count = np.nan
            turnover = np.nan
        else:
            overlap_count = len(current & previous)
            turnover = 1 - overlap_count / len(current)
        rows.append(
            {
                "trade_date": date,
                "model": factor_col,
                "top_group_count": len(current),
                "overlap_count": overlap_count,
                "turnover": turnover,
            }
        )
        previous = current
    series = pd.DataFrame(rows)
    values = series["turnover"].dropna()
    summary = pd.DataFrame(
        [
            {
                "model": factor_col,
                "avg_turnover": values.mean(),
                "median_turnover": values.median(),
                "sample_periods": len(values),
            }
        ]
    )
    return series, summary


def average_size_corr(panel: pd.DataFrame, factor_col: str) -> float:
    if "factor_size" not in panel.columns or factor_col not in panel.columns:
        return np.nan
    values = []
    for _, group in panel.groupby("trade_date"):
        data = group[[factor_col, "factor_size"]].dropna()
        if len(data) < 3 or data[factor_col].nunique() < 2 or data["factor_size"].nunique() < 2:
            continue
        values.append(data[factor_col].corr(data["factor_size"], method="spearman"))
    return float(pd.Series(values).mean()) if values else np.nan


def build_model_comparison(
    composite_ic_summary: pd.DataFrame,
    layer_summary: pd.DataFrame,
    turnover_summary: pd.DataFrame,
) -> pd.DataFrame:
    long_short = layer_summary[layer_summary["group"].astype(str) == "G5-G1"].copy()
    rows: list[dict[str, object]] = []
    for factor in COMPOSITE_COLS:
        ic_match = composite_ic_summary[composite_ic_summary["factor"] == factor]
        ls_match = long_short[long_short["factor"] == factor]
        turn_match = turnover_summary[turnover_summary["model"] == factor]
        rows.append(
            {
                "model": factor,
                "neutralized": factor.endswith("_neutral")
                or factor.endswith("_size_neutral")
                or factor.endswith("_industry_size_neutral"),
                "rank_ic_mean": ic_match["rank_ic_mean"].iloc[0] if not ic_match.empty else np.nan,
                "rank_ic_ir": ic_match["rank_icir"].iloc[0] if not ic_match.empty else np.nan,
                "g5_g1_ann_return": ls_match["annual_return"].iloc[0] if not ls_match.empty else np.nan,
                "sharpe": ls_match["sharpe"].iloc[0] if not ls_match.empty else np.nan,
                "max_drawdown": ls_match["max_drawdown"].iloc[0] if not ls_match.empty else np.nan,
                "win_rate": ls_match["win_rate"].iloc[0] if not ls_match.empty else np.nan,
                "turnover": turn_match["avg_turnover"].iloc[0] if not turn_match.empty else np.nan,
            }
        )
    return pd.DataFrame(rows)


def build_neutralization_comparison(
    panel: pd.DataFrame,
    composite_ic_summary: pd.DataFrame,
    layer_summary: pd.DataFrame,
) -> pd.DataFrame:
    pairs = [
        ("equal_weight", "composite_equal", "composite_equal_size_neutral", "composite_equal_industry_size_neutral"),
        (
            "ic_weight",
            "composite_ic_weight",
            "composite_ic_weight_size_neutral",
            "composite_ic_weight_industry_size_neutral",
        ),
        ("pca", "composite_pca", "composite_pca_size_neutral", "composite_pca_industry_size_neutral"),
        (
            "rolling_ic_weight",
            "composite_rolling_ic_weight",
            "composite_rolling_ic_weight_size_neutral",
            "composite_rolling_ic_weight_industry_size_neutral",
        ),
    ]
    long_short = layer_summary[layer_summary["group"].astype(str) == "G5-G1"].copy()
    rows: list[dict[str, object]] = []
    for model, raw, size_neutral, industry_size_neutral in pairs:
        raw_ic = composite_ic_summary[composite_ic_summary["factor"] == raw]
        size_ic = composite_ic_summary[composite_ic_summary["factor"] == size_neutral]
        industry_ic = composite_ic_summary[composite_ic_summary["factor"] == industry_size_neutral]
        raw_ls = long_short[long_short["factor"] == raw]
        size_ls = long_short[long_short["factor"] == size_neutral]
        industry_ls = long_short[long_short["factor"] == industry_size_neutral]
        rows.append(
            {
                "model": model,
                "raw_rank_ic": raw_ic["rank_ic_mean"].iloc[0] if not raw_ic.empty else np.nan,
                "size_neutral_rank_ic": size_ic["rank_ic_mean"].iloc[0] if not size_ic.empty else np.nan,
                "industry_size_neutral_rank_ic": industry_ic["rank_ic_mean"].iloc[0] if not industry_ic.empty else np.nan,
                "raw_g5_g1_return": raw_ls["annual_return"].iloc[0] if not raw_ls.empty else np.nan,
                "size_neutral_g5_g1_return": size_ls["annual_return"].iloc[0] if not size_ls.empty else np.nan,
                "industry_size_neutral_g5_g1_return": industry_ls["annual_return"].iloc[0]
                if not industry_ls.empty
                else np.nan,
                "raw_size_corr": average_size_corr(panel, raw),
                "size_neutral_size_corr": average_size_corr(panel, size_neutral),
                "industry_size_neutral_size_corr": average_size_corr(panel, industry_size_neutral),
            }
        )
    return pd.DataFrame(rows)


def calculate_composite_descriptive_stats(panel: pd.DataFrame, composite_cols: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    total_rows = len(panel)
    for col in composite_cols:
        if col not in panel.columns:
            continue
        values = pd.to_numeric(panel[col], errors="coerce")
        rows.append(
            {
                "factor": col,
                "count": values.count(),
                "mean": values.mean(),
                "std": values.std(),
                "skew": values.skew(),
                "min": values.min(),
                "p1": values.quantile(0.01),
                "p25": values.quantile(0.25),
                "median": values.median(),
                "p75": values.quantile(0.75),
                "p99": values.quantile(0.99),
                "max": values.max(),
                "missing_rate": values.isna().mean() if total_rows else np.nan,
            }
        )
    return pd.DataFrame(rows)


def calculate_layer_monotonicity(layer_outputs: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    overall_rows: list[dict[str, object]] = []
    year_rows: list[dict[str, object]] = []
    for model, layer_return in layer_outputs.items():
        if layer_return.empty:
            continue
        pivot = layer_return.pivot_table(index="trade_date", columns="group", values="period_return", aggfunc="mean")
        group_cols = [group for group in [1.0, 2.0, 3.0, 4.0, 5.0] if group in pivot.columns]
        if len(group_cols) < 2:
            continue
        means = pivot[group_cols].mean()
        diffs = means.diff().dropna()
        row = {"model": model, "year": "all"}
        for group_id in range(1, 6):
            row[f"g{group_id}_return"] = means.get(float(group_id), np.nan)
        row["g5_g1"] = means.get(5.0, np.nan) - means.get(1.0, np.nan)
        row["monotonic_score"] = (diffs > 0).mean() if len(diffs) else np.nan
        overall_rows.append(row)

        pivot.index = pd.to_datetime(pivot.index)
        for year, year_data in pivot.groupby(pivot.index.year):
            year_means = year_data[group_cols].mean()
            year_diffs = year_means.diff().dropna()
            year_row = {"model": model, "year": year}
            for group_id in range(1, 6):
                year_row[f"g{group_id}_return"] = year_means.get(float(group_id), np.nan)
            year_row["g5_g1"] = year_means.get(5.0, np.nan) - year_means.get(1.0, np.nan)
            year_row["monotonic_score"] = (year_diffs > 0).mean() if len(year_diffs) else np.nan
            year_rows.append(year_row)
    return pd.DataFrame(overall_rows), pd.DataFrame(year_rows)


def estimate_turnover_costs(turnover_summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in turnover_summary.iterrows():
        avg_turnover = row.get("avg_turnover", np.nan)
        for rebalance_days in [5, 10, 20, 60]:
            annual_rebalances = 252 / rebalance_days
            for cost_rate in [0.001, 0.002, 0.003]:
                rows.append(
                    {
                        "model": row["model"],
                        "rebalance_days": rebalance_days,
                        "avg_turnover": avg_turnover,
                        "cost_rate": cost_rate,
                        "annual_cost_estimate": avg_turnover * cost_rate * annual_rebalances * 2
                        if pd.notna(avg_turnover)
                        else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def save_corr_heatmap(corr: pd.DataFrame, output_dir: Path) -> None:
    plt.figure(figsize=(7, 5.5))
    sns.heatmap(corr, cmap="RdBu_r", center=0, vmin=-1, vmax=1, annot=True, fmt=".2f")
    plt.title("Average cross-sectional Spearman correlation")
    plt.tight_layout()
    plt.savefig(output_dir / "figures" / "factor_spearman_corr_heatmap.png", dpi=160)
    plt.close()


def save_composite_figures(panel: pd.DataFrame, layer_outputs: dict[str, pd.DataFrame], output_dir: Path) -> None:
    fig_dir = output_dir / "figures"
    plt.figure(figsize=(8, 4.5))
    sns.histplot(panel["composite_equal"].dropna(), bins=60, kde=True)
    plt.title("Composite factor distribution")
    plt.tight_layout()
    plt.savefig(fig_dir / "composite_factor_distribution.png", dpi=160)
    plt.close()

    for factor_col, layer_return in layer_outputs.items():
        method = method_slug(factor_col)
        plt.figure(figsize=(8, 4.5))
        if layer_return.empty:
            plt.title(f"{factor_col} layer return")
        else:
            sns.barplot(data=layer_return, x="group", y="period_return", errorbar=None)
            plt.axhline(0, color="black", linewidth=0.8)
            plt.title(f"{factor_col} layer return")
        plt.tight_layout()
        plt.savefig(fig_dir / f"layer_return_{method}.png", dpi=160)
        plt.close()

        if layer_return.empty:
            continue
        pivot = layer_return.pivot_table(index="trade_date", columns="group", values="period_return", aggfunc="mean").sort_index()
        plt.figure(figsize=(9, 4.8))
        for group_id in sorted(pivot.columns):
            cum = (1 + pivot[group_id].fillna(0)).cumprod() - 1
            plt.plot(pd.to_datetime(cum.index), cum.values, label=f"G{int(group_id)}")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.title(f"{factor_col} layer cumulative return")
        plt.legend(ncol=5, fontsize=8)
        plt.tight_layout()
        plt.savefig(fig_dir / f"layer_cumret_{method}.png", dpi=160)
        plt.close()

        if 1.0 in pivot.columns and 5.0 in pivot.columns:
            long_short = pivot[5.0] - pivot[1.0]
            cum_ls = (1 + long_short.fillna(0)).cumprod() - 1
            plt.figure(figsize=(9, 4.8))
            plt.plot(pd.to_datetime(cum_ls.index), cum_ls.values)
            plt.axhline(0, color="black", linewidth=0.8)
            plt.title(f"{factor_col} long-short cumulative return")
            plt.tight_layout()
            plt.savefig(fig_dir / f"long_short_cumret_{method}.png", dpi=160)
            plt.close()


def save_ic_weight_bar(selected: pd.DataFrame, output_dir: Path) -> None:
    fig_dir = output_dir / "figures"
    plot_data = selected.copy()
    if plot_data.empty or "weight_ic" not in plot_data.columns:
        return
    plot_data = plot_data.sort_values("weight_ic", ascending=False)
    plt.figure(figsize=(8, 4.5))
    sns.barplot(data=plot_data, x="weight_ic", y="factor", hue="selected", dodge=False)
    plt.xlabel("IC weight")
    plt.ylabel("")
    plt.title("IC-weighted composite factor weights")
    plt.legend(title="Selected", loc="lower right")
    plt.tight_layout()
    plt.savefig(fig_dir / "ic_weight_bar.png", dpi=160)
    plt.close()


def save_composite_ic_series_figures(ic_series: pd.DataFrame, output_dir: Path) -> None:
    fig_dir = output_dir / "figures"
    if ic_series.empty:
        return

    name_map = {
        "composite_equal": "equal_weight",
        "composite_equal_neutral": "equal_weight_neutral",
        "composite_ic_weight": "ic_weight",
        "composite_ic_weight_neutral": "ic_weight_neutral",
        "composite_pca": "pca",
        "composite_pca_neutral": "pca_neutral",
    }
    plot_data = ic_series.copy()
    plot_data["trade_date"] = pd.to_datetime(plot_data["trade_date"])
    for factor_col, data in plot_data.groupby("composite_factor"):
        method = name_map.get(factor_col, method_slug(factor_col))
        data = data.sort_values("trade_date")
        rolling = data["rank_ic"].rolling(20, min_periods=5).mean()
        plt.figure(figsize=(9, 4.8))
        plt.plot(data["trade_date"], data["rank_ic"], color="#4C78A8", alpha=0.35, linewidth=1, label="Daily Rank IC")
        plt.plot(data["trade_date"], rolling, color="#F58518", linewidth=1.8, label="20-period rolling mean")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.title(f"{factor_col} Rank IC series")
        plt.legend(fontsize=8)
        plt.tight_layout()
        plt.savefig(fig_dir / f"composite_rank_ic_series_{method}.png", dpi=160)
        plt.close()


def save_turnover_figures(turnover_series: pd.DataFrame, output_dir: Path) -> None:
    fig_dir = output_dir / "figures"
    if turnover_series.empty:
        return
    plot_data = turnover_series.copy()
    plot_data["trade_date"] = pd.to_datetime(plot_data["trade_date"])
    for factor_col, data in plot_data.groupby("model"):
        method = method_slug(factor_col)
        data = data.sort_values("trade_date")
        rolling = data["turnover"].rolling(20, min_periods=5).mean()
        plt.figure(figsize=(9, 4.8))
        plt.plot(data["trade_date"], data["turnover"], color="#54A24B", alpha=0.35, linewidth=1, label="Top group turnover")
        plt.plot(data["trade_date"], rolling, color="#E45756", linewidth=1.8, label="20-period rolling mean")
        plt.ylim(0, 1.05)
        plt.title(f"{factor_col} top group turnover")
        plt.legend(fontsize=8)
        plt.tight_layout()
        plt.savefig(fig_dir / f"top_group_turnover_{method}.png", dpi=160)
        plt.close()


def save_rolling_ic_weight_plot(rolling_weights: pd.DataFrame, output_dir: Path, window: int) -> None:
    fig_dir = output_dir / "figures"
    if rolling_weights.empty:
        return
    data = rolling_weights[rolling_weights["window"] == window].copy()
    if data.empty:
        return
    pivot = data.pivot_table(index="trade_date", columns="factor", values="weight", aggfunc="mean").sort_index()
    pivot.index = pd.to_datetime(pivot.index)
    plt.figure(figsize=(10, 5))
    plt.stackplot(pivot.index, [pivot[col].fillna(0).values for col in pivot.columns], labels=pivot.columns)
    plt.ylim(0, 1)
    plt.title(f"Rolling IC weights ({window} trading days)")
    plt.legend(loc="upper left", fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(fig_dir / "rolling_ic_weights.png", dpi=160)
    plt.close()


def save_composite_explain_figures(panel: pd.DataFrame, output_dir: Path) -> None:
    fig_dir = output_dir / "figures"
    compare_cols = [
        "composite_equal",
        "composite_ic_weight",
        "composite_pca",
        "composite_rolling_ic_weight",
        "composite_ic_weight_industry_size_neutral",
    ]
    compare_cols = [col for col in compare_cols if col in panel.columns]
    if not compare_cols:
        return
    melted = panel[compare_cols].melt(var_name="factor", value_name="value").dropna()
    plt.figure(figsize=(10, 5))
    sns.kdeplot(data=melted, x="value", hue="factor", common_norm=False)
    plt.title("Composite factor distribution comparison")
    plt.tight_layout()
    plt.savefig(fig_dir / "composite_factor_distribution_compare.png", dpi=160)
    plt.close()

    ts = panel.groupby("trade_date")[compare_cols].mean().reset_index()
    ts["trade_date"] = pd.to_datetime(ts["trade_date"])
    plt.figure(figsize=(10, 5))
    for col in compare_cols:
        plt.plot(ts["trade_date"], ts[col], label=col)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.title("Composite factor cross-sectional mean over time")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(fig_dir / "composite_factor_timeseries_compare.png", dpi=160)
    plt.close()


def save_pca_figures(pca_explained: pd.DataFrame, pca_components: pd.DataFrame, output_dir: Path) -> None:
    fig_dir = output_dir / "figures"
    if not pca_explained.empty:
        plt.figure(figsize=(7, 4.5))
        sns.barplot(data=pca_explained, x="component", y="explained_variance_ratio")
        plt.title("PCA explained variance")
        plt.tight_layout()
        plt.savefig(fig_dir / "pca_explained_variance.png", dpi=160)
        plt.close()
    if not pca_components.empty:
        heatmap_data = pca_components.pivot_table(index="component", columns="factor", values="loading", aggfunc="mean")
        plt.figure(figsize=(8, 4.5))
        sns.heatmap(heatmap_data, cmap="RdBu_r", center=0, annot=True, fmt=".2f")
        plt.title("PCA component loadings")
        plt.tight_layout()
        plt.savefig(fig_dir / "pca_components_heatmap.png", dpi=160)
        plt.close()


def save_layer_monotonicity_figure(layer_monotonicity_by_year: pd.DataFrame, output_dir: Path) -> None:
    fig_dir = output_dir / "figures"
    if layer_monotonicity_by_year.empty:
        return
    focus = layer_monotonicity_by_year[
        layer_monotonicity_by_year["model"].isin(
            [
                "composite_ic_weight_industry_size_neutral",
                "composite_ic_weight_size_neutral",
                "composite_rolling_ic_weight_industry_size_neutral",
            ]
        )
    ].copy()
    if focus.empty:
        focus = layer_monotonicity_by_year.copy()
    plt.figure(figsize=(10, 5))
    sns.barplot(data=focus, x="year", y="monotonic_score", hue="model")
    plt.ylim(0, 1)
    plt.title("Layer monotonicity by year")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(fig_dir / "layer_monotonicity_by_year.png", dpi=160)
    plt.close()


def save_turnover_cost_figure(cost_estimation: pd.DataFrame, output_dir: Path) -> None:
    fig_dir = output_dir / "figures"
    if cost_estimation.empty:
        return
    focus_model = "composite_ic_weight_industry_size_neutral"
    focus = cost_estimation[cost_estimation["model"] == focus_model].copy()
    if focus.empty:
        focus = cost_estimation[cost_estimation["model"] == "composite_ic_weight_neutral"].copy()
    if focus.empty:
        focus = cost_estimation.copy()
    pivot = focus.pivot_table(index="rebalance_days", columns="cost_rate", values="annual_cost_estimate", aggfunc="mean")
    plt.figure(figsize=(7, 4.8))
    sns.heatmap(pivot, annot=True, fmt=".2%", cmap="YlOrRd")
    plt.title("Annual turnover cost estimate")
    plt.tight_layout()
    plt.savefig(fig_dir / "turnover_cost_estimation.png", dpi=160)
    plt.close()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    panel, ic_summary = read_inputs(Path(args.panel_file), Path(args.ic_file))
    panel, industry_mapping = add_learning_industry(panel)
    factor_cols = [col for col in FACTOR_COLS if col in panel.columns and panel[col].notna().sum() > 0]
    if not factor_cols:
        raise RuntimeError("No usable factors found in factor panel.")

    corr = average_cross_sectional_spearman(panel, factor_cols)
    redundancy_decision = build_redundancy_decision(corr, ic_summary, factor_cols, args.corr_threshold)
    selected = select_factors(corr, ic_summary, factor_cols, args.corr_threshold)
    selected_final = selected.copy()
    selected_final["final_selected"] = selected_final["selected"]
    (
        composite_panel,
        factor_ic_series,
        rolling_weights,
        rolling_weight_summary,
        pca_explained,
        pca_components,
    ) = add_composite_factors(panel, selected, args.return_col, args.rolling_window)

    corr.to_csv(output_dir / "factor_spearman_corr.csv", encoding="utf-8-sig")
    redundancy_decision.to_csv(output_dir / "factor_redundancy_decision.csv", index=False, encoding="utf-8-sig")
    selected.to_csv(output_dir / "selected_factors.csv", index=False, encoding="utf-8-sig")
    selected_final.to_csv(output_dir / "selected_factors_final.csv", index=False, encoding="utf-8-sig")
    industry_mapping.to_csv(output_dir / "industry_mapping.csv", index=False, encoding="utf-8-sig")
    panel.to_csv(PROJECT_ROOT / "data" / "processed" / "factor_panel_with_industry.csv", index=False, encoding="utf-8-sig")
    factor_ic_series.to_csv(output_dir / "factor_rank_ic_series.csv", index=False, encoding="utf-8-sig")
    rolling_weights.to_csv(output_dir / "rolling_ic_weights.csv", index=False, encoding="utf-8-sig")
    rolling_weight_summary.to_csv(output_dir / "rolling_ic_weight_summary.csv", index=False, encoding="utf-8-sig")
    pca_explained.to_csv(output_dir / "pca_explained_variance.csv", index=False, encoding="utf-8-sig")
    pca_components.to_csv(output_dir / "pca_components.csv", index=False, encoding="utf-8-sig")
    composite_panel.to_csv(output_dir / "composite_factor_panel.csv", index=False, encoding="utf-8-sig")

    save_corr_heatmap(corr, output_dir)

    layer_outputs: dict[str, pd.DataFrame] = {}
    summaries: list[pd.DataFrame] = []
    for col in COMPOSITE_COLS:
        if col not in composite_panel.columns:
            continue
        layer_return, summary = layer_backtest(composite_panel, col, args.return_col)
        layer_outputs[col] = layer_return
        summaries.append(summary)
        method = method_slug(col)
        layer_return.to_csv(output_dir / f"layer_return_{method}.csv", index=False, encoding="utf-8-sig")

    layer_summary = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
    layer_summary.to_csv(output_dir / "layer_backtest_summary.csv", index=False, encoding="utf-8-sig")
    layer_monotonicity, layer_monotonicity_by_year = calculate_layer_monotonicity(layer_outputs)
    layer_monotonicity.to_csv(output_dir / "layer_monotonicity_summary.csv", index=False, encoding="utf-8-sig")
    layer_monotonicity_by_year.to_csv(
        output_dir / "layer_monotonicity_by_year.csv", index=False, encoding="utf-8-sig"
    )

    composite_ic_series, composite_ic_summary, composite_ic_by_year = calculate_composite_ic_series(
        composite_panel, args.return_col
    )
    composite_ic_series.to_csv(output_dir / "composite_rank_ic_series.csv", index=False, encoding="utf-8-sig")
    composite_ic_summary.to_csv(output_dir / "composite_ic_summary.csv", index=False, encoding="utf-8-sig")
    composite_ic_by_year.to_csv(output_dir / "composite_ic_by_year.csv", index=False, encoding="utf-8-sig")

    layer_by_year = calculate_layer_backtest_by_year(layer_outputs, composite_ic_by_year)
    layer_by_year.to_csv(output_dir / "layer_backtest_by_year.csv", index=False, encoding="utf-8-sig")

    turnover_series_frames: list[pd.DataFrame] = []
    turnover_summary_frames: list[pd.DataFrame] = []
    for col in COMPOSITE_COLS:
        if col not in composite_panel.columns:
            continue
        turnover_series, turnover_summary = calculate_top_group_turnover(composite_panel, col)
        turnover_series_frames.append(turnover_series)
        turnover_summary_frames.append(turnover_summary)
    turnover_series_all = (
        pd.concat(turnover_series_frames, ignore_index=True) if turnover_series_frames else pd.DataFrame()
    )
    turnover_summary = (
        pd.concat(turnover_summary_frames, ignore_index=True) if turnover_summary_frames else pd.DataFrame()
    )
    turnover_series_all.to_csv(output_dir / "layer_turnover_series.csv", index=False, encoding="utf-8-sig")
    turnover_summary.to_csv(output_dir / "layer_turnover_summary.csv", index=False, encoding="utf-8-sig")
    turnover_cost_estimation = estimate_turnover_costs(turnover_summary)
    turnover_cost_estimation.to_csv(output_dir / "turnover_cost_estimation.csv", index=False, encoding="utf-8-sig")

    model_comparison = build_model_comparison(composite_ic_summary, layer_summary, turnover_summary)
    model_comparison.to_csv(output_dir / "composite_model_comparison.csv", index=False, encoding="utf-8-sig")

    neutralization_comparison = build_neutralization_comparison(composite_panel, composite_ic_summary, layer_summary)
    neutralization_comparison.to_csv(output_dir / "neutralization_comparison.csv", index=False, encoding="utf-8-sig")
    composite_cols = [col for col in COMPOSITE_COLS if col in composite_panel.columns]
    composite_stats = calculate_composite_descriptive_stats(composite_panel, composite_cols)
    composite_corr = composite_panel[composite_cols].corr(method="spearman")
    composite_stats.to_csv(output_dir / "composite_factor_descriptive_stats.csv", index=False, encoding="utf-8-sig")
    composite_corr.to_csv(output_dir / "composite_factor_correlation.csv", encoding="utf-8-sig")

    save_composite_figures(composite_panel, layer_outputs, output_dir)
    save_ic_weight_bar(selected, output_dir)
    save_composite_ic_series_figures(composite_ic_series, output_dir)
    save_turnover_figures(turnover_series_all, output_dir)
    save_rolling_ic_weight_plot(rolling_weights, output_dir, args.rolling_window)
    save_composite_explain_figures(composite_panel, output_dir)
    save_pca_figures(pca_explained, pca_components, output_dir)
    save_layer_monotonicity_figure(layer_monotonicity_by_year, output_dir)
    save_turnover_cost_figure(turnover_cost_estimation, output_dir)
    write_week2_report(
        output_dir,
        selected,
        redundancy_decision,
        industry_mapping,
        rolling_weight_summary,
        layer_summary,
        composite_ic_summary,
        corr,
        model_comparison,
        composite_ic_by_year,
        layer_by_year,
        turnover_summary,
        neutralization_comparison,
        layer_monotonicity,
        pca_explained,
        pca_components,
        turnover_cost_estimation,
    )
    print(f"Week 2 outputs saved to {output_dir}")


def write_week2_report(
    output_dir: Path,
    selected: pd.DataFrame,
    redundancy_decision: pd.DataFrame,
    industry_mapping: pd.DataFrame,
    rolling_weight_summary: pd.DataFrame,
    layer_summary: pd.DataFrame,
    composite_ic: pd.DataFrame,
    corr: pd.DataFrame,
    model_comparison: pd.DataFrame,
    composite_ic_by_year: pd.DataFrame,
    layer_by_year: pd.DataFrame,
    turnover_summary: pd.DataFrame,
    neutralization_comparison: pd.DataFrame,
    layer_monotonicity: pd.DataFrame,
    pca_explained: pd.DataFrame,
    pca_components: pd.DataFrame,
    turnover_cost_estimation: pd.DataFrame,
) -> None:
    selected_factors = selected.loc[selected["selected"], "factor"].tolist()
    positive_weight = selected[["factor", "weight_equal", "weight_ic", "selected"]].copy()
    ls = layer_summary[layer_summary["group"].astype(str) == "G5-G1"].copy() if not layer_summary.empty else pd.DataFrame()

    lines = [
        "# Week 2 Multi-Factor Model Report",
        "",
        "## 1. Week 2 Objective",
        "",
        "Week 2 builds on the Week 1 single-factor analysis by running factor correlation analysis, redundant factor screening, composite-factor construction, industry + size neutralization, rolling IC weighting, five-layer backtesting, turnover analysis, and transaction-cost preparation for Week 3.",
        "",
        "## 2. Candidate Factors",
        "",
        ", ".join(FACTOR_COLS),
        "",
        "ROE is not included in the v2.0 model because it remains a formal-data-source extension item.",
        "",
        "## 3. Selected Factors",
        "",
        ", ".join(selected_factors) if selected_factors else "No selected factors.",
        "",
        "## 4. Redundancy Decision",
        "",
        "A threshold of 0.7 is used for redundant-factor detection. When the absolute average cross-sectional Spearman correlation exceeds 0.7, the model keeps the factor with stronger Rank IC, ICIR, or clearer economic interpretation.",
        "",
        redundancy_decision.to_markdown(index=False)
        if not redundancy_decision.empty
        else "No redundancy decision results.",
        "",
        "## 5. Factor Weights",
        "",
        positive_weight.to_markdown(index=False),
        "",
        "## 6. Industry Mapping",
        "",
        "The current v2.1 static-sample version uses a reproducible learning-version industry mapping based on stock-code prefixes. It is used to run the industry + size neutralization pipeline and can be replaced by Wind, Shenwan, Tushare, or CSMAR industry classifications in the formal-data version.",
        "",
        industry_mapping.head(20).to_markdown(index=False)
        if not industry_mapping.empty
        else "No industry mapping results.",
        "",
        "## 7. Rolling IC Weights",
        "",
        "Rolling IC weights use only historical Rank IC information. Positive historical IC values participate in weighting; non-positive values receive zero weight; when all are non-positive, the model falls back to equal weights.",
        "",
        rolling_weight_summary.to_markdown(index=False)
        if not rolling_weight_summary.empty
        else "No rolling IC weight results.",
        "",
        "## 8. Composite Model Comparison",
        "",
        model_comparison.to_markdown(index=False) if not model_comparison.empty else "No model comparison results.",
        "",
        "## 9. Composite IC Summary",
        "",
        composite_ic.to_markdown(index=False) if not composite_ic.empty else "No composite IC results.",
        "",
        "## 10. Composite IC by Year",
        "",
        composite_ic_by_year.to_markdown(index=False) if not composite_ic_by_year.empty else "No yearly IC results.",
        "",
        "## 11. Five-Layer Long-Short Results",
        "",
        ls.to_markdown(index=False) if not ls.empty else "No layer backtest results.",
        "",
        "## 12. Five-Layer Results by Year",
        "",
        layer_by_year.to_markdown(index=False) if not layer_by_year.empty else "No yearly layer backtest results.",
        "",
        "## 13. Layer Monotonicity",
        "",
        "If G5 is materially stronger than G1 while the middle layers are not perfectly monotonic, the composite signal is still useful for top-group stock selection, but less reliable for ranking middle-quantile stocks.",
        "",
        layer_monotonicity.to_markdown(index=False)
        if not layer_monotonicity.empty
        else "No monotonicity results.",
        "",
        "## 14. Top Group Turnover",
        "",
        turnover_summary.to_markdown(index=False) if not turnover_summary.empty else "No turnover results.",
        "",
        "## 15. Transaction Cost Estimate",
        "",
        "Annual transaction cost is approximated as average turnover * one-way cost * annual rebalance count * 2. The multiplier 2 approximates round-trip buy and sell costs.",
        "",
        turnover_cost_estimation.head(30).to_markdown(index=False)
        if not turnover_cost_estimation.empty
        else "No turnover cost results.",
        "",
        "## 16. Neutralization",
        "",
        "The v2.1 model applies industry + size neutralization through cross-sectional regression on `factor_size` and industry dummy variables. The residual is used as the neutralized stock-selection signal.",
        "",
        neutralization_comparison.to_markdown(index=False)
        if not neutralization_comparison.empty
        else "No neutralization comparison results.",
        "",
        "## 17. PCA Review",
        "",
        "PCA is reviewed separately because it extracts common factor variation rather than directly optimizing future-return predictability. Weak PCA performance can occur when the first principal component captures shared style exposure or noise instead of predictive information.",
        "",
        pca_explained.to_markdown(index=False) if not pca_explained.empty else "No PCA explained variance results.",
        "",
        pca_components.to_markdown(index=False) if not pca_components.empty else "No PCA component results.",
        "",
        "## 18. Robustness Note",
        "",
        "The original full-sample IC-weighted method is kept as a benchmark, but it can contain look-ahead bias. The rolling IC-weighted factor is therefore added as a more realistic candidate because each date only uses historical IC information.",
        "",
        "## 19. Figures",
        "",
        "- `figures/factor_spearman_corr_heatmap.png`",
        "- `figures/ic_weight_bar.png`",
        "- `figures/rolling_ic_weights.png`",
        "- `figures/composite_factor_distribution.png`",
        "- `figures/composite_factor_distribution_compare.png`",
        "- `figures/composite_factor_timeseries_compare.png`",
        "- `figures/composite_rank_ic_series_ic_weight.png`",
        "- `figures/layer_cumret_equal_weight.png`",
        "- `figures/layer_cumret_ic_weight.png`",
        "- `figures/long_short_cumret_ic_weight.png`",
        "- `figures/top_group_turnover_ic_weight.png`",
        "- `figures/pca_explained_variance.png`",
        "- `figures/pca_components_heatmap.png`",
        "- `figures/layer_monotonicity_by_year.png`",
        "- `figures/turnover_cost_estimation.png`",
        "",
        "## 20. Average Cross-Sectional Correlation",
        "",
        corr.to_markdown(),
        "",
    ]
    (output_dir / "week2_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
