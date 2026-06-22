"""Build a clean factor panel from downloaded raw Tushare data."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

FACTOR_COLS = [
    "factor_momentum",
    "factor_volatility",
    "factor_roe",
    "factor_size",
    "factor_turnover",
    "factor_reversal_5d",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build static or dynamic factor panel.")
    parser.add_argument("--price-file", default=str(RAW_DIR / "price_qfq.csv"))
    parser.add_argument("--basic-file", default=str(RAW_DIR / "daily_basic.csv"))
    parser.add_argument("--fina-file", default=str(RAW_DIR / "fina_indicator.csv"))
    parser.add_argument("--members-file", default=str(RAW_DIR / "hs300_members.csv"))
    parser.add_argument("--output-csv", default=str(PROCESSED_DIR / "factor_panel.csv"))
    parser.add_argument("--output-parquet", default=str(PROCESSED_DIR / "factor_panel.parquet"))
    parser.add_argument("--universe-output", default="")
    return parser.parse_args()


def read_raw(
    price_file: Path,
    basic_file: Path,
    fina_file: Path,
    members_file: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    price = pd.read_csv(price_file)
    basic = pd.read_csv(basic_file)
    fina = pd.read_csv(fina_file)
    members = pd.read_csv(members_file)
    return price, basic, fina, members


def parse_dates(price: pd.DataFrame, basic: pd.DataFrame, fina: pd.DataFrame, members: pd.DataFrame) -> None:
    price["trade_date"] = pd.to_datetime(price["trade_date"].astype(str))
    basic["trade_date"] = pd.to_datetime(basic["trade_date"].astype(str))
    fina["ann_date"] = pd.to_datetime(fina["ann_date"].astype(str), errors="coerce")
    fina["end_date"] = pd.to_datetime(fina["end_date"].astype(str), errors="coerce")
    members["trade_date"] = pd.to_datetime(members["trade_date"].astype(str))


def add_price_features(price: pd.DataFrame) -> pd.DataFrame:
    price = price.sort_values(["ts_code", "trade_date"]).copy()
    price["ret_1d"] = price.groupby("ts_code")["close"].pct_change()
    price["ret_5d_fwd"] = price.groupby("ts_code")["close"].transform(lambda x: x.pct_change(5).shift(-5))
    price["ret_20d_fwd"] = price.groupby("ts_code")["close"].transform(lambda x: x.pct_change(20).shift(-20))
    price["return_5d"] = price.groupby("ts_code")["close"].pct_change(5)
    price["momentum_20d"] = price.groupby("ts_code")["close"].pct_change(20)
    price["volatility_20d"] = (
        price.groupby("ts_code")["ret_1d"].rolling(20).std().reset_index(level=0, drop=True)
    )
    return price


def align_financials(data: pd.DataFrame, fina: pd.DataFrame) -> pd.DataFrame:
    data = data.sort_values(["ts_code", "trade_date"]).copy()
    fina = fina.dropna(subset=["ann_date"]).sort_values(["ts_code", "ann_date"]).copy()

    frames: list[pd.DataFrame] = []
    for code, df_price in data.groupby("ts_code", sort=False):
        df_fin = fina[fina["ts_code"] == code]
        if df_fin.empty:
            frames.append(df_price)
            continue
        merged = pd.merge_asof(
            df_price.sort_values("trade_date"),
            df_fin.sort_values("ann_date"),
            left_on="trade_date",
            right_on="ann_date",
            by="ts_code",
            direction="backward",
        )
        frames.append(merged)

    return pd.concat(frames, ignore_index=True)


def add_member_filter(data: pd.DataFrame, members: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    member_cols = ["con_code", "trade_date"]
    if "weight" in members.columns:
        member_cols.append("weight")
    monthly_members = members[member_cols].drop_duplicates().copy()
    monthly_members = monthly_members.rename(columns={"con_code": "ts_code", "trade_date": "member_date"})

    frames: list[pd.DataFrame] = []
    for code, df_stock in data.groupby("ts_code", sort=False):
        df_members = monthly_members[monthly_members["ts_code"] == code]
        if df_members.empty:
            continue
        aligned = pd.merge_asof(
            df_stock.sort_values("trade_date"),
            df_members.sort_values("member_date"),
            left_on="trade_date",
            right_on="member_date",
            by="ts_code",
            direction="backward",
        )
        aligned = aligned[aligned["member_date"].notna()]
        frames.append(aligned)

    if not frames:
        raise RuntimeError("No rows left after HS300 membership filtering.")
    filtered = pd.concat(frames, ignore_index=True)
    universe = filtered[["trade_date", "ts_code"]].drop_duplicates().copy()
    universe["in_hs300"] = 1
    return filtered, universe


def add_factors(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    if "total_mv" not in data.columns:
        data["total_mv"] = np.nan
    for col in ["roe", "roa", "grossprofit_margin", "or_yoy"]:
        if col not in data.columns:
            data[col] = np.nan
    if data["total_mv"].isna().all() and "weight" in data.columns:
        data["total_mv"] = data["weight"]
    data["turnover_20d"] = (
        data.sort_values(["ts_code", "trade_date"])
        .groupby("ts_code")["turnover_rate"]
        .rolling(20)
        .mean()
        .reset_index(level=0, drop=True)
    )
    data["factor_momentum"] = data["momentum_20d"]
    data["factor_volatility"] = -data["volatility_20d"]
    data["factor_roe"] = data["roe"]
    data["factor_size"] = -np.log(data["total_mv"].where(data["total_mv"] > 0))
    data["factor_turnover"] = -data["turnover_20d"]
    data["factor_reversal_5d"] = -data["return_5d"]
    return data


def winsorize_zscore(group: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    group = group.copy()
    for col in cols:
        values = group[col]
        mean = values.mean(skipna=True)
        std = values.std(skipna=True)
        if pd.isna(std) or std == 0:
            group[col] = np.nan
            continue
        clipped = values.clip(mean - 3 * std, mean + 3 * std)
        group[col] = (clipped - clipped.mean(skipna=True)) / clipped.std(skipna=True)
    return group


def build_factor_panel(
    price_file: Path = RAW_DIR / "price_qfq.csv",
    basic_file: Path = RAW_DIR / "daily_basic.csv",
    fina_file: Path = RAW_DIR / "fina_indicator.csv",
    members_file: Path = RAW_DIR / "hs300_members.csv",
    output_csv: Path = PROCESSED_DIR / "factor_panel.csv",
    output_parquet: Path = PROCESSED_DIR / "factor_panel.parquet",
    universe_output: Path | None = None,
) -> pd.DataFrame:
    price, basic, fina, members = read_raw(price_file, basic_file, fina_file, members_file)
    parse_dates(price, basic, fina, members)

    price = add_price_features(price)
    data = price.merge(basic, on=["ts_code", "trade_date"], how="left")
    if "turnover_rate" not in data.columns:
        turnover_candidates = [col for col in ["turnover_rate_y", "turnover_rate_x"] if col in data.columns]
        if turnover_candidates:
            data["turnover_rate"] = data[turnover_candidates].bfill(axis=1).iloc[:, 0]
    data = align_financials(data, fina)
    data, universe = add_member_filter(data, members)
    data = add_factors(data)

    data = pd.concat(
        [winsorize_zscore(group, FACTOR_COLS) for _, group in data.groupby("trade_date", sort=False)],
        ignore_index=True,
    )
    data = data.sort_values(["trade_date", "ts_code"]).reset_index(drop=True)

    keep_cols = [
        "trade_date",
        "ts_code",
        "close",
        "ret_1d",
        "ret_5d_fwd",
        "ret_20d_fwd",
        "return_5d",
        "momentum_20d",
        "volatility_20d",
        "roe",
        "roa",
        "grossprofit_margin",
        "or_yoy",
        "pe",
        "pb",
        "total_mv",
        "circ_mv",
        "turnover_rate",
        "turnover_20d",
        *FACTOR_COLS,
    ]
    data = data[[col for col in keep_cols if col in data.columns]]

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output_csv, index=False, encoding="utf-8-sig")
    data.to_parquet(output_parquet, index=False)
    if universe_output:
        universe_output.parent.mkdir(parents=True, exist_ok=True)
        universe.to_csv(universe_output, index=False, encoding="utf-8-sig")
    return data


def main() -> None:
    args = parse_args()
    universe_output = Path(args.universe_output) if args.universe_output else None
    panel = build_factor_panel(
        price_file=Path(args.price_file),
        basic_file=Path(args.basic_file),
        fina_file=Path(args.fina_file),
        members_file=Path(args.members_file),
        output_csv=Path(args.output_csv),
        output_parquet=Path(args.output_parquet),
        universe_output=universe_output,
    )
    print(f"Factor panel rows: {len(panel):,}")
    print(f"Saved to {args.output_csv}")


if __name__ == "__main__":
    main()
