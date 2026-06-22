"""Data loading helpers for Week 4 risk analysis."""

from pathlib import Path

import pandas as pd


def read_csv_safe(path: Path, parse_dates: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    for col in parse_dates or []:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df


def load_all_data(config) -> dict[str, pd.DataFrame]:
    """Load all Week 2/3 outputs needed by Week 4."""
    return {
        "strategy_nav": read_csv_safe(config.STRATEGY_NAV_FILE, ["trade_date"]),
        "benchmark_nav": read_csv_safe(config.BENCHMARK_NAV_FILE, ["trade_date"]),
        "hs300_nav": read_csv_safe(config.HS300_NAV_FILE, ["trade_date"]),
        "holdings": read_csv_safe(config.HOLDINGS_FILE, ["trade_date"]),
        "industry_exposure": read_csv_safe(config.INDUSTRY_EXPOSURE_FILE, ["trade_date"]),
        "turnover": read_csv_safe(config.TURNOVER_FILE, ["trade_date"]),
        "trade_records": read_csv_safe(config.TRADE_RECORDS_FILE, ["trade_date"]),
        "factor_panel": read_csv_safe(config.WEEK2_PANEL_FILE, ["trade_date"]),
    }


def check_data_quality(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in data.items():
        date_min = df["trade_date"].min() if "trade_date" in df.columns and not df.empty else None
        date_max = df["trade_date"].max() if "trade_date" in df.columns and not df.empty else None
        rows.append(
            {
                "dataset": name,
                "rows": len(df),
                "columns": len(df.columns),
                "date_min": date_min,
                "date_max": date_max,
                "is_available": not df.empty,
            }
        )
    return pd.DataFrame(rows)


def build_return_frame(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    nav = data.get("strategy_nav", pd.DataFrame()).copy()
    if nav.empty:
        return pd.DataFrame()

    keep_cols = [
        "trade_date",
        "strategy_ret",
        "benchmark_ret",
        "hs300_ret",
        "strategy_nav",
        "benchmark_nav",
        "hs300_nav",
        "drawdown",
    ]
    keep_cols = [col for col in keep_cols if col in nav.columns]
    return nav[keep_cols].sort_values("trade_date").reset_index(drop=True)
