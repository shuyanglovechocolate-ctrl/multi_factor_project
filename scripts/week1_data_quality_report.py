"""Generate Week 1 data quality reports."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "week1"

FACTOR_COLS = [
    "factor_momentum",
    "factor_volatility",
    "factor_roe",
    "factor_size",
    "factor_turnover",
    "factor_reversal_5d",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Week 1 data quality reports.")
    parser.add_argument("--price-file", default=str(RAW_DIR / "price_qfq.csv"))
    parser.add_argument("--panel-file", default=str(PROCESSED_DIR / "factor_panel.csv"))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    return parser.parse_args()


def load_data(price_file: Path, panel_file: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    price = pd.read_csv(price_file)
    panel = pd.read_csv(panel_file)
    price["trade_date"] = pd.to_datetime(price["trade_date"].astype(str))
    panel["trade_date"] = pd.to_datetime(panel["trade_date"].astype(str))
    return price, panel


def count_3sigma_outliers(values: pd.Series) -> int:
    values = pd.to_numeric(values, errors="coerce").dropna()
    if values.empty:
        return 0
    std = values.std()
    if pd.isna(std) or std == 0:
        return 0
    mean = values.mean()
    return int(((values < mean - 3 * std) | (values > mean + 3 * std)).sum())


def build_quality_report(price: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    rows.extend(
        [
            {"section": "sample", "item": "price_rows", "value": len(price), "note": "Rows in raw qfq price data"},
            {"section": "sample", "item": "factor_panel_rows", "value": len(panel), "note": "Rows in processed factor panel"},
            {"section": "sample", "item": "stock_count", "value": price["ts_code"].nunique(), "note": "Unique stocks"},
            {"section": "sample", "item": "start_date", "value": price["trade_date"].min().date(), "note": "Earliest price date"},
            {"section": "sample", "item": "end_date", "value": price["trade_date"].max().date(), "note": "Latest price date"},
        ]
    )

    stock_counts = price.groupby("ts_code")["trade_date"].count()
    rows.extend(
        [
            {"section": "stock_rows", "item": "min_rows_per_stock", "value": int(stock_counts.min()), "note": "Minimum rows by stock"},
            {"section": "stock_rows", "item": "median_rows_per_stock", "value": float(stock_counts.median()), "note": "Median rows by stock"},
            {"section": "stock_rows", "item": "max_rows_per_stock", "value": int(stock_counts.max()), "note": "Maximum rows by stock"},
            {
                "section": "stock_rows",
                "item": "stocks_with_less_than_200_rows",
                "value": int((stock_counts < 200).sum()),
                "note": "Potentially incomplete stocks",
            },
        ]
    )

    for col in ["open", "high", "low", "close", "vol", "amount", "turnover_rate"]:
        if col in price.columns:
            rows.append(
                {
                    "section": "raw_missing",
                    "item": f"{col}_missing_rate",
                    "value": float(price[col].isna().mean()),
                    "note": "Missing rate in raw price data",
                }
            )

    for col in FACTOR_COLS:
        if col in panel.columns:
            rows.append(
                {
                    "section": "factor_quality",
                    "item": f"{col}_non_null_rate",
                    "value": float(panel[col].notna().mean()),
                    "note": "Factor coverage rate",
                }
            )
            rows.append(
                {
                    "section": "factor_quality",
                    "item": f"{col}_3sigma_outliers",
                    "value": count_3sigma_outliers(panel[col]),
                    "note": "Outliers after cross-sectional winsorization/z-score",
                }
            )

    if "vol" in price.columns:
        rows.append(
            {
                "section": "trading_quality",
                "item": "zero_volume_rows",
                "value": int((pd.to_numeric(price["vol"], errors="coerce").fillna(0) <= 0).sum()),
                "note": "Possible suspended or invalid trading rows",
            }
        )

    trading_days = price.groupby("trade_date")["ts_code"].nunique()
    rows.append(
        {
            "section": "trading_quality",
            "item": "median_stocks_per_day",
            "value": float(trading_days.median()),
            "note": "Cross-sectional breadth by trading date",
        }
    )

    return pd.DataFrame(rows)


def write_summary(report: pd.DataFrame) -> None:
    def value(item: str) -> object:
        match = report.loc[report["item"] == item, "value"]
        return match.iloc[0] if not match.empty else "NA"

    lines = [
        "Week 1 Data Quality Summary",
        "",
        f"Raw price rows: {value('price_rows')}",
        f"Factor panel rows: {value('factor_panel_rows')}",
        f"Stock count: {value('stock_count')}",
        f"Date range: {value('start_date')} to {value('end_date')}",
        f"Rows per stock: min={value('min_rows_per_stock')}, median={value('median_rows_per_stock')}, max={value('max_rows_per_stock')}",
        f"Stocks with <200 rows: {value('stocks_with_less_than_200_rows')}",
        f"Zero-volume rows: {value('zero_volume_rows')}",
        "",
        "Factor non-null rates:",
    ]
    for col in FACTOR_COLS:
        item = f"{col}_non_null_rate"
        if item in set(report["item"]):
            lines.append(f"- {col}: {value(item)}")

    (OUTPUT_DIR / "data_quality_summary.txt").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    global OUTPUT_DIR
    args = parse_args()
    OUTPUT_DIR = Path(args.output_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    price, panel = load_data(Path(args.price_file), Path(args.panel_file))
    report = build_quality_report(price, panel)
    report.to_csv(OUTPUT_DIR / "data_quality_report.csv", index=False, encoding="utf-8-sig")
    write_summary(report)
    print(f"Data quality reports saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
