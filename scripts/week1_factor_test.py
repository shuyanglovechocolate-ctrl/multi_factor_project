"""Run Week 1 IC analysis, flexible grouping, and visualizations."""

from __future__ import annotations

import os
import argparse
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
from scipy.stats import pearsonr, spearmanr, ttest_1samp


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "week1"
FIGURE_DIR = OUTPUT_DIR / "figures"

FACTOR_COLS = [
    "factor_momentum",
    "factor_volatility",
    "factor_roe",
    "factor_size",
    "factor_turnover",
    "factor_reversal_5d",
]
WINDOWS = [1, 5, 10, 20, 60]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Week 1 factor analysis.")
    parser.add_argument("--panel-file", default=str(PROCESSED_DIR / "factor_panel.csv"))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--return-col", default="ret_20d_fwd")
    parser.add_argument("--group-mode", choices=["adaptive", "decile", "both"], default="adaptive")
    return parser.parse_args()


def load_panel(panel_file: Path | None = None) -> pd.DataFrame:
    csv_path = panel_file or (PROCESSED_DIR / "factor_panel.csv")
    parquet_path = csv_path.with_suffix(".parquet") if panel_file else (PROCESSED_DIR / "factor_panel.parquet")
    if csv_path.exists():
        panel = pd.read_csv(csv_path)
    elif parquet_path.exists():
        panel = pd.read_parquet(parquet_path)
    else:
        raise FileNotFoundError(f"Missing panel file: {csv_path}")
    panel["trade_date"] = pd.to_datetime(panel["trade_date"])
    return panel.sort_values(["ts_code", "trade_date"])


def add_forward_returns(panel: pd.DataFrame, windows: list[int]) -> pd.DataFrame:
    panel = panel.copy()
    for window in windows:
        col = f"ret_{window}d_fwd"
        if col not in panel.columns:
            panel[col] = panel.groupby("ts_code")["close"].transform(lambda x: x.pct_change(window).shift(-window))
    return panel


def safe_corr(x: pd.Series, y: pd.Series, method: str) -> float:
    data = pd.concat([x, y], axis=1).dropna()
    if len(data) < 2 or data.iloc[:, 0].nunique() < 2 or data.iloc[:, 1].nunique() < 2:
        return float("nan")
    if method == "pearson":
        return pearsonr(data.iloc[:, 0], data.iloc[:, 1])[0]
    return spearmanr(data.iloc[:, 0], data.iloc[:, 1])[0]


def calculate_ic(panel: pd.DataFrame, return_col: str = "ret_20d_fwd") -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    for date, group in panel.groupby("trade_date"):
        for factor in FACTOR_COLS:
            rows.append(
                {
                    "trade_date": date,
                    "factor": factor,
                    "ic": safe_corr(group[factor], group[return_col], "pearson"),
                    "rank_ic": safe_corr(group[factor], group[return_col], "spearman"),
                }
            )
    ic_series = pd.DataFrame(rows)

    summary = (
        ic_series.groupby("factor")
        .agg(
            sample_periods=("ic", "count"),
            ic_mean=("ic", "mean"),
            ic_std=("ic", "std"),
            rank_ic_mean=("rank_ic", "mean"),
            rank_ic_std=("rank_ic", "std"),
            ic_win_rate=("ic", lambda x: (x > 0).mean()),
            rank_ic_win_rate=("rank_ic", lambda x: (x > 0).mean()),
        )
        .reset_index()
    )
    summary["icir"] = summary["ic_mean"] / summary["ic_std"]
    summary["rank_icir"] = summary["rank_ic_mean"] / summary["rank_ic_std"]
    t_rows: list[dict[str, float | str]] = []
    for factor, factor_ic in ic_series.groupby("factor"):
        ic_values = factor_ic["ic"].dropna()
        rank_ic_values = factor_ic["rank_ic"].dropna()
        ic_test = ttest_1samp(ic_values, 0, nan_policy="omit") if len(ic_values) > 1 else None
        rank_test = ttest_1samp(rank_ic_values, 0, nan_policy="omit") if len(rank_ic_values) > 1 else None
        t_rows.append(
            {
                "factor": factor,
                "ic_t_stat": ic_test.statistic if ic_test is not None else np.nan,
                "ic_p_value": ic_test.pvalue if ic_test is not None else np.nan,
                "rank_ic_t_stat": rank_test.statistic if rank_test is not None else np.nan,
                "rank_ic_p_value": rank_test.pvalue if rank_test is not None else np.nan,
            }
        )
    summary = summary.merge(pd.DataFrame(t_rows), on="factor", how="left")
    return ic_series, summary


def calculate_ic_by_year(ic_series: pd.DataFrame) -> pd.DataFrame:
    data = ic_series.copy()
    data["year"] = pd.to_datetime(data["trade_date"]).dt.year
    return (
        data.groupby(["year", "factor"])
        .agg(
            ic_mean=("ic", "mean"),
            rank_ic_mean=("rank_ic", "mean"),
            ic_win_rate=("ic", lambda x: (x > 0).mean()),
            sample_periods=("ic", "count"),
        )
        .reset_index()
    )


def calculate_descriptive_stats(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    total_rows = len(panel)
    for factor in FACTOR_COLS:
        values = panel[factor] if factor in panel.columns else pd.Series(dtype=float)
        non_null = values.dropna()
        quantiles = non_null.quantile([0.01, 0.25, 0.5, 0.75, 0.99]) if not non_null.empty else pd.Series(dtype=float)
        rows.append(
            {
                "factor": factor,
                "count": int(non_null.count()),
                "mean": non_null.mean(),
                "std": non_null.std(),
                "min": non_null.min(),
                "p1": quantiles.get(0.01, np.nan),
                "p25": quantiles.get(0.25, np.nan),
                "median": quantiles.get(0.5, np.nan),
                "p75": quantiles.get(0.75, np.nan),
                "p99": quantiles.get(0.99, np.nan),
                "max": non_null.max(),
                "missing_rate": 1 - (len(non_null) / total_rows if total_rows else 0),
            }
        )
    return pd.DataFrame(rows)


def calculate_ic_decay(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for window in WINDOWS:
        return_col = f"ret_{window}d_fwd"
        for factor in FACTOR_COLS:
            daily_ic = [
                safe_corr(group[factor], group[return_col], "spearman")
                for _, group in panel.groupby("trade_date")
            ]
            rows.append({"factor": factor, "window": window, "rank_ic_mean": pd.Series(daily_ic).mean()})
    return pd.DataFrame(rows)


def calculate_group_returns(
    panel: pd.DataFrame,
    return_col: str = "ret_20d_fwd",
    mode: str = "adaptive",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    for factor in FACTOR_COLS:
        usable = panel[["trade_date", "ts_code", factor, return_col]].dropna().copy()
        if usable.empty:
            continue

        def assign_groups(group: pd.DataFrame) -> pd.Series:
            n = group[factor].notna().sum()
            if n == 0:
                return pd.Series(index=group.index, dtype="float64")
            if n == 1:
                return pd.Series(1, index=group.index, dtype="int64")
            if mode == "decile" and n < 10:
                return pd.Series(index=group.index, dtype="float64")
            group_count = 10 if mode == "decile" else min(10, n)
            ranks = group[factor].rank(method="first")
            return pd.qcut(ranks, group_count, labels=False, duplicates="drop") + 1

        usable["group"] = usable.groupby("trade_date", group_keys=False).apply(assign_groups)
        grouped = usable.groupby(["trade_date", "group"])[return_col].mean().reset_index()
        grouped["factor"] = factor
        rows.append(grouped)

    if rows:
        group_returns = pd.concat(rows, ignore_index=True)
    else:
        group_returns = pd.DataFrame(columns=["trade_date", "group", return_col, "factor"])

    summary_rows: list[dict[str, object]] = []
    for factor in FACTOR_COLS:
        factor_groups = group_returns[group_returns["factor"] == factor]
        if factor_groups.empty:
            summary_rows.append(
                {
                    "factor": factor,
                    "lowest_group": np.nan,
                    "highest_group": np.nan,
                    "lowest_group_return": np.nan,
                    "highest_group_return": np.nan,
                    "high_minus_low": np.nan,
                    "long_short_mean": np.nan,
                    "available_groups": 0,
                    "sample_periods": 0,
                }
            )
            continue

        grouped_mean = factor_groups.groupby("group")[return_col].mean().sort_index()
        lowest_group = grouped_mean.index.min()
        highest_group = grouped_mean.index.max()
        high_minus_low = grouped_mean.loc[highest_group] - grouped_mean.loc[lowest_group]
        summary_rows.append(
            {
                "factor": factor,
                "lowest_group": lowest_group,
                "highest_group": highest_group,
                "lowest_group_return": grouped_mean.loc[lowest_group],
                "highest_group_return": grouped_mean.loc[highest_group],
                "high_minus_low": high_minus_low,
                "long_short_mean": high_minus_low,
                "available_groups": factor_groups["group"].nunique(),
                "sample_periods": factor_groups["trade_date"].nunique(),
            }
        )

    return group_returns, pd.DataFrame(summary_rows)


def calculate_group_monotonicity(group_returns: pd.DataFrame, return_col: str = "ret_20d_fwd") -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for factor in FACTOR_COLS:
        factor_groups = group_returns[group_returns["factor"] == factor]
        if factor_groups.empty:
            rows.append(
                {
                    "factor": factor,
                    "available_groups": 0,
                    "bottom_return": np.nan,
                    "top_return": np.nan,
                    "top_bottom_spread": np.nan,
                    "monotonic_score": np.nan,
                }
            )
            continue

        grouped_mean = factor_groups.groupby("group")[return_col].mean().sort_index()
        diffs = grouped_mean.diff().dropna()
        rows.append(
            {
                "factor": factor,
                "available_groups": int(grouped_mean.count()),
                "bottom_return": grouped_mean.iloc[0],
                "top_return": grouped_mean.iloc[-1],
                "top_bottom_spread": grouped_mean.iloc[-1] - grouped_mean.iloc[0],
                "monotonic_score": (diffs > 0).mean() if len(diffs) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def add_no_data_message(title: str) -> None:
    plt.title(title)
    plt.text(0.5, 0.5, "No valid data in current sample", ha="center", va="center")
    plt.xticks([])
    plt.yticks([])


def save_figures(panel: pd.DataFrame, ic_series: pd.DataFrame, ic_decay: pd.DataFrame, group_returns: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    for factor in FACTOR_COLS:
        plt.figure(figsize=(8, 4.5))
        factor_values = panel[factor].dropna()
        if factor_values.empty:
            add_no_data_message(f"{factor} distribution")
        else:
            sns.histplot(factor_values, bins=min(60, max(5, len(factor_values))), kde=len(factor_values) > 2)
            plt.title(f"{factor} distribution")
        plt.tight_layout()
        plt.savefig(FIGURE_DIR / f"distribution_{factor}.png", dpi=160)
        plt.close()

        factor_ic = ic_series[ic_series["factor"] == factor].sort_values("trade_date")
        factor_ic = factor_ic.assign(rank_ic_20d=factor_ic["rank_ic"].rolling(20).mean())
        plt.figure(figsize=(10, 4.5))
        if factor_ic["rank_ic"].dropna().empty:
            add_no_data_message(f"{factor} Rank IC")
        else:
            sns.lineplot(data=factor_ic, x="trade_date", y="rank_ic", label="Rank IC")
            sns.lineplot(data=factor_ic, x="trade_date", y="rank_ic_20d", label="20D mean")
            plt.axhline(0, color="black", linewidth=0.8)
            plt.title(f"{factor} Rank IC")
        plt.tight_layout()
        plt.savefig(FIGURE_DIR / f"rank_ic_{factor}.png", dpi=160)
        plt.close()

        factor_groups = group_returns[group_returns["factor"] == factor]
        plt.figure(figsize=(8, 4.5))
        if factor_groups.empty:
            add_no_data_message(f"{factor} group return")
        else:
            sns.barplot(data=factor_groups, x="group", y="ret_20d_fwd", errorbar=None)
            plt.axhline(0, color="black", linewidth=0.8)
            plt.title(f"{factor} group return")
        plt.tight_layout()
        plt.savefig(FIGURE_DIR / f"group_return_{factor}.png", dpi=160)
        plt.close()

        plt.figure(figsize=(9, 4.5))
        if factor_groups.empty:
            add_no_data_message(f"{factor} long-short cumulative return")
        else:
            pivot = factor_groups.pivot_table(index="trade_date", columns="group", values="ret_20d_fwd", aggfunc="mean")
            if pivot.empty or pivot.shape[1] < 2:
                add_no_data_message(f"{factor} long-short cumulative return")
            else:
                long_short = pivot[pivot.columns.max()] - pivot[pivot.columns.min()]
                cumret = (1 + long_short.fillna(0)).cumprod() - 1
                sns.lineplot(x=pd.to_datetime(cumret.index), y=cumret.values)
                plt.axhline(0, color="black", linewidth=0.8)
                plt.title(f"{factor} long-short cumulative return")
        plt.tight_layout()
        plt.savefig(FIGURE_DIR / f"long_short_cumret_{factor}.png", dpi=160)
        plt.close()

    plt.figure(figsize=(8, 4.5))
    if ic_decay["rank_ic_mean"].dropna().empty:
        add_no_data_message("IC decay")
    else:
        sns.lineplot(data=ic_decay, x="window", y="rank_ic_mean", hue="factor", marker="o")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.title("IC decay")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "ic_decay.png", dpi=160)
    plt.close()

    yearly = group_returns.copy()
    if yearly.empty:
        return
    yearly["year"] = pd.to_datetime(yearly["trade_date"]).dt.year
    for factor in FACTOR_COLS:
        table = (
            yearly[yearly["factor"] == factor]
            .pivot_table(index="group", columns="year", values="ret_20d_fwd", aggfunc="mean")
            .sort_index(ascending=False)
        )
        plt.figure(figsize=(8, 5))
        if table.empty or table.dropna(how="all").empty:
            add_no_data_message(f"{factor} group return heatmap")
        else:
            sns.heatmap(table, cmap="RdYlGn", center=0, annot=False)
            plt.title(f"{factor} group return heatmap")
        plt.tight_layout()
        plt.savefig(FIGURE_DIR / f"group_heatmap_{factor}.png", dpi=160)
        plt.close()


def save_overview_figures(panel: pd.DataFrame, ic_by_year: pd.DataFrame) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    coverage = pd.DataFrame(
        {
            "factor": FACTOR_COLS,
            "coverage_rate": [panel[factor].notna().mean() if factor in panel.columns else 0 for factor in FACTOR_COLS],
        }
    )
    plt.figure(figsize=(9, 4.5))
    sns.barplot(data=coverage, x="factor", y="coverage_rate")
    plt.xticks(rotation=30, ha="right")
    plt.ylim(0, 1)
    plt.title("Factor coverage")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "factor_coverage_bar.png", dpi=160)
    plt.close()

    corr = panel[FACTOR_COLS].corr()
    plt.figure(figsize=(7, 5.5))
    if corr.dropna(how="all").empty:
        add_no_data_message("Factor correlation")
    else:
        sns.heatmap(corr, cmap="RdBu_r", center=0, annot=True, fmt=".2f", vmin=-1, vmax=1)
        plt.title("Factor correlation")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "factor_correlation_heatmap.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 5))
    valid = ic_by_year.dropna(subset=["rank_ic_mean"])
    if valid.empty:
        add_no_data_message("Rank IC by year")
    else:
        sns.barplot(data=valid, x="year", y="rank_ic_mean", hue="factor")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.title("Rank IC by year")
        plt.legend(loc="best", fontsize=8)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "rank_ic_by_year.png", dpi=160)
    plt.close()


def write_week1_report(
    panel: pd.DataFrame,
    ic_summary: pd.DataFrame,
    group_summary: pd.DataFrame,
    descriptive_stats: pd.DataFrame,
    group_monotonicity: pd.DataFrame,
) -> None:
    price_rows = len(panel)
    stock_count = panel["ts_code"].nunique()
    start_date = panel["trade_date"].min().date()
    end_date = panel["trade_date"].max().date()
    coverage = descriptive_stats[["factor", "count", "missing_rate"]].copy()
    usable_factors = coverage.loc[coverage["missing_rate"] < 0.5, "factor"].tolist()

    report = [
        "# Week 1 Factor Exploration Report",
        "",
        "## 1. Data Sample",
        "",
        f"- Rows: {price_rows:,}",
        f"- Stocks: {stock_count}",
        f"- Period: {start_date} to {end_date}",
        "- Data source: AKShare qfq price data; HS300 membership from Tushare index_weight.",
        "",
        "## 2. Factor Coverage",
        "",
        coverage.to_markdown(index=False),
        "",
        "## 3. IC Summary",
        "",
        ic_summary.sort_values("rank_ic_mean", ascending=False).to_markdown(index=False),
        "",
        "## 4. Group Return Summary",
        "",
        group_summary.sort_values("long_short_mean", ascending=False).to_markdown(index=False),
        "",
        "## 5. Monotonicity",
        "",
        group_monotonicity.sort_values("monotonic_score", ascending=False).to_markdown(index=False),
        "",
        "## 6. Figures",
        "",
        "- `figures/ic_decay.png`",
        "- `figures/factor_correlation_heatmap.png`",
        "- `figures/factor_coverage_bar.png`",
        "- `figures/rank_ic_by_year.png`",
        "- `figures/rank_ic_factor_*.png`",
        "- `figures/distribution_factor_*.png`",
        "- `figures/group_return_factor_*.png`",
        "- `figures/long_short_cumret_factor_*.png`",
        "",
        "## 7. Current Limitations",
        "",
        "- ROE remains unavailable in the learning version because financial indicators are not reliably aligned by stock code and announcement date.",
        "- `factor_size` uses HS300 constituent weight as a market-cap proxy because historical market-cap data is unavailable without higher Tushare permissions.",
        "- The current analysis is suitable for Week 1 workflow validation and preliminary factor exploration.",
        "",
        "## 8. Week 2 Candidate Factors",
        "",
        ", ".join(usable_factors) if usable_factors else "No usable factors yet.",
        "",
    ]
    (OUTPUT_DIR / "week1_report.md").write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    global OUTPUT_DIR, FIGURE_DIR
    args = parse_args()
    OUTPUT_DIR = Path(args.output_dir)
    FIGURE_DIR = OUTPUT_DIR / "figures"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = add_forward_returns(load_panel(Path(args.panel_file)), WINDOWS)

    ic_series, ic_summary = calculate_ic(panel, args.return_col)
    ic_by_year = calculate_ic_by_year(ic_series)
    ic_decay = calculate_ic_decay(panel)
    group_returns, group_summary = calculate_group_returns(panel, args.return_col, mode="adaptive")
    decile_group_returns, decile_group_summary = calculate_group_returns(panel, args.return_col, mode="decile")
    descriptive_stats = calculate_descriptive_stats(panel)
    group_monotonicity = calculate_group_monotonicity(group_returns)
    decile_group_monotonicity = calculate_group_monotonicity(decile_group_returns)

    ic_series.to_csv(OUTPUT_DIR / "ic_series.csv", index=False, encoding="utf-8-sig")
    ic_summary.to_csv(OUTPUT_DIR / "factor_ic_summary.csv", index=False, encoding="utf-8-sig")
    ic_by_year.to_csv(OUTPUT_DIR / "factor_ic_by_year.csv", index=False, encoding="utf-8-sig")
    ic_decay.to_csv(OUTPUT_DIR / "ic_decay.csv", index=False, encoding="utf-8-sig")
    group_returns.to_csv(OUTPUT_DIR / "group_returns.csv", index=False, encoding="utf-8-sig")
    group_summary.to_csv(OUTPUT_DIR / "group_return_summary.csv", index=False, encoding="utf-8-sig")
    group_summary.to_csv(OUTPUT_DIR / "factor_group_summary.csv", index=False, encoding="utf-8-sig")
    group_returns.to_csv(OUTPUT_DIR / "adaptive_group_returns.csv", index=False, encoding="utf-8-sig")
    group_summary.to_csv(OUTPUT_DIR / "adaptive_group_summary.csv", index=False, encoding="utf-8-sig")
    decile_group_returns.to_csv(OUTPUT_DIR / "decile_group_returns.csv", index=False, encoding="utf-8-sig")
    decile_group_summary.to_csv(OUTPUT_DIR / "decile_group_summary.csv", index=False, encoding="utf-8-sig")
    descriptive_stats.to_csv(OUTPUT_DIR / "factor_descriptive_stats.csv", index=False, encoding="utf-8-sig")
    group_monotonicity.to_csv(OUTPUT_DIR / "factor_group_monotonicity.csv", index=False, encoding="utf-8-sig")
    decile_group_monotonicity.to_csv(OUTPUT_DIR / "decile_group_monotonicity.csv", index=False, encoding="utf-8-sig")
    for factor in FACTOR_COLS:
        ic_series[ic_series["factor"] == factor].to_csv(
            OUTPUT_DIR / f"ic_series_{factor}.csv",
            index=False,
            encoding="utf-8-sig",
        )
        group_returns[group_returns["factor"] == factor].to_csv(
            OUTPUT_DIR / f"group_return_{factor}.csv",
            index=False,
            encoding="utf-8-sig",
        )
        group_returns[group_returns["factor"] == factor].to_csv(
            OUTPUT_DIR / f"adaptive_group_return_{factor}.csv",
            index=False,
            encoding="utf-8-sig",
        )
        decile_group_returns[decile_group_returns["factor"] == factor].to_csv(
            OUTPUT_DIR / f"decile_group_return_{factor}.csv",
            index=False,
            encoding="utf-8-sig",
        )
    save_figures(panel, ic_series, ic_decay, group_returns)
    save_overview_figures(panel, ic_by_year)
    write_week1_report(panel, ic_summary, group_summary, descriptive_stats, group_monotonicity)

    print(f"Week 1 outputs saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
