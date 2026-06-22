"""Download a learning-version dataset with AKShare.

This fallback is useful when Tushare token permissions do not include daily
market data. It reuses ``data/raw/hs300_members.csv`` from Tushare if present.

Limitations:
- AKShare financial data used here has report dates, not actual announcement
  dates. ``ann_date`` is approximated as report date + 90 days.
- Historical PE/PB and market cap are not included. ``total_mv`` is proxied by
  HS300 constituent weight so the size factor can run for learning purposes.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import akshare as ak
import pandas as pd
from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download learning-version data with AKShare.")
    parser.add_argument("--start", default="20200101", help="Start date, YYYYMMDD.")
    parser.add_argument("--end", default="20231231", help="End date, YYYYMMDD.")
    parser.add_argument("--max-stocks", "--max_stocks", dest="max_stocks", type=int, default=50, help="Limit stock count; use 0 for all.")
    parser.add_argument("--stock-list", default="", help="CSV with a ts_code column. Overrides member-derived stock list.")
    parser.add_argument("--members-file", default=str(RAW_DIR / "hs300_members.csv"), help="Members CSV used for weight proxy.")
    parser.add_argument("--by-stock-dir", default=str(RAW_DIR / "price_qfq_by_stock"), help="Directory for per-stock qfq files.")
    parser.add_argument("--combine-only", action="store_true", help="Only combine existing per-stock files.")
    parser.add_argument("--refresh", action="store_true", help="Re-download existing per-stock files.")
    parser.add_argument("--sleep", type=float, default=0.2, help="Pause between requests.")
    parser.add_argument("--retries", "--retry", dest="retries", type=int, default=3, help="Retries per AKShare request.")
    parser.add_argument("--timeout", type=float, default=10, help="Request timeout in seconds.")
    parser.add_argument("--with-financial", action="store_true", help="Also download AKShare financial indicators.")
    return parser.parse_args()


def tushare_to_ak_symbol(ts_code: str) -> str:
    return ts_code.split(".")[0]


def tushare_to_prefixed_symbol(ts_code: str) -> str:
    code, exchange = ts_code.split(".")
    prefix = "sh" if exchange == "SH" else "sz"
    return f"{prefix}{code}"


def load_members(path: Path, max_stocks: int) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing members file: {path}")
    members = pd.read_csv(path)
    members["trade_date"] = pd.to_datetime(members["trade_date"].astype(str))
    stock_list = members["con_code"].dropna().drop_duplicates().sort_values().tolist()
    if max_stocks and max_stocks > 0:
        stock_list = stock_list[:max_stocks]
    return members[members["con_code"].isin(stock_list)].copy()


def load_stock_list(args: argparse.Namespace, members: pd.DataFrame) -> list[str]:
    if args.stock_list:
        stock_path = Path(args.stock_list)
        stock_df = pd.read_csv(stock_path)
        if "ts_code" not in stock_df.columns:
            raise ValueError(f"{stock_path} must contain a ts_code column.")
        stock_list = stock_df["ts_code"].dropna().drop_duplicates().sort_values().tolist()
    else:
        stock_list = members["con_code"].dropna().drop_duplicates().sort_values().tolist()

    if args.max_stocks and args.max_stocks > 0:
        stock_list = stock_list[: args.max_stocks]
    return stock_list


def normalize_price_frame(df: pd.DataFrame, ts_code: str) -> pd.DataFrame:
    df = df.rename(
        columns={
            "date": "trade_date",
            "volume": "vol",
            "turnover": "turnover_rate",
        }
    )
    df["turnover_rate"] = pd.to_numeric(df["turnover_rate"], errors="coerce") * 100
    df["ts_code"] = ts_code
    out = df[["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount", "turnover_rate"]].copy()
    out["trade_date"] = pd.to_datetime(out["trade_date"]).dt.strftime("%Y%m%d")
    return out


def combine_price_files(by_stock_dir: Path, stock_list: list[str] | None = None) -> pd.DataFrame:
    files = sorted(by_stock_dir.glob("*.csv"))
    if stock_list is not None:
        wanted = set(stock_list)
        files = [path for path in files if path.stem in wanted]
    frames = [pd.read_csv(path) for path in files if path.stat().st_size > 0]
    if not frames:
        raise RuntimeError(f"No per-stock price files found in {by_stock_dir}")
    price = pd.concat(frames, ignore_index=True)
    price = price.drop_duplicates(["ts_code", "trade_date"]).sort_values(["ts_code", "trade_date"])
    price.to_csv(RAW_DIR / "price_qfq.csv", index=False, encoding="utf-8-sig")
    return price


def download_price(
    stock_list: list[str],
    start: str,
    end: str,
    sleep: float,
    retries: int,
    timeout: float,
    by_stock_dir: Path,
    refresh: bool,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    by_stock_dir.mkdir(parents=True, exist_ok=True)
    for ts_code in tqdm(stock_list, desc="akshare price"):
        output_path = by_stock_dir / f"{ts_code}.csv"
        if output_path.exists() and not refresh:
            try:
                frames.append(pd.read_csv(output_path))
            except Exception as exc:
                print(f"[read cached price] {ts_code}: {exc}")
            continue

        symbol = tushare_to_prefixed_symbol(ts_code)
        df = pd.DataFrame()
        for attempt in range(1, retries + 1):
            try:
                df = ak.stock_zh_a_daily(
                    symbol=symbol,
                    start_date=start,
                    end_date=end,
                    adjust="qfq",
                )
                break
            except Exception as exc:
                print(f"[ak price] {ts_code} attempt {attempt}/{retries}: {exc}")
                time.sleep(sleep * attempt)
        if df is None or df.empty:
            time.sleep(sleep)
            continue

        normalized = normalize_price_frame(df, ts_code)
        normalized.to_csv(output_path, index=False, encoding="utf-8-sig")
        frames.append(normalized)
        time.sleep(sleep)

    if not frames:
        raise RuntimeError("No AKShare price data downloaded.")
    price = pd.concat(frames, ignore_index=True).drop_duplicates(["ts_code", "trade_date"])
    price = price.sort_values(["ts_code", "trade_date"])
    price.to_csv(RAW_DIR / "price_qfq.csv", index=False, encoding="utf-8-sig")
    return price


def build_daily_basic(price: pd.DataFrame, members: pd.DataFrame) -> pd.DataFrame:
    basic = price[["ts_code", "trade_date", "turnover_rate"]].copy()
    basic["trade_date_dt"] = pd.to_datetime(basic["trade_date"].astype(str))

    member_weight = members[["con_code", "trade_date", "weight"]].rename(
        columns={"con_code": "ts_code", "trade_date": "member_date"}
    )
    frames: list[pd.DataFrame] = []
    for code, df_basic in basic.groupby("ts_code", sort=False):
        df_weight = member_weight[member_weight["ts_code"] == code].sort_values("member_date")
        merged = pd.merge_asof(
            df_basic.sort_values("trade_date_dt"),
            df_weight,
            left_on="trade_date_dt",
            right_on="member_date",
            by="ts_code",
            direction="backward",
        )
        frames.append(merged)

    daily_basic = pd.concat(frames, ignore_index=True)
    daily_basic["total_mv"] = daily_basic["weight"]
    daily_basic["circ_mv"] = daily_basic["weight"]
    daily_basic["pe"] = pd.NA
    daily_basic["pb"] = pd.NA
    daily_basic = daily_basic[["ts_code", "trade_date", "turnover_rate", "pe", "pb", "total_mv", "circ_mv"]]
    daily_basic.to_csv(RAW_DIR / "daily_basic.csv", index=False, encoding="utf-8-sig")
    return daily_basic


def download_financial(stock_list: list[str], start: str, sleep: float, retries: int) -> pd.DataFrame:
    start_year = str(pd.to_datetime(start).year - 1)
    frames: list[pd.DataFrame] = []
    for ts_code in tqdm(stock_list, desc="akshare financial"):
        symbol = tushare_to_ak_symbol(ts_code)
        df = pd.DataFrame()
        for attempt in range(1, retries + 1):
            try:
                df = ak.stock_financial_analysis_indicator(symbol=symbol, start_year=start_year)
                break
            except Exception as exc:
                print(f"[ak financial] {ts_code} attempt {attempt}/{retries}: {exc}")
                time.sleep(sleep * attempt)
        if df is None or df.empty:
            time.sleep(sleep)
            continue

        out = pd.DataFrame()
        out["ts_code"] = ts_code
        out["end_date"] = pd.to_datetime(df["日期"], errors="coerce")
        out["ann_date"] = out["end_date"] + pd.Timedelta(days=90)
        out["roe"] = pd.to_numeric(df.get("净资产收益率(%)"), errors="coerce")
        out["roa"] = pd.to_numeric(df.get("总资产净利润率(%)"), errors="coerce")
        out["grossprofit_margin"] = pd.to_numeric(df.get("销售毛利率(%)"), errors="coerce")
        out["or_yoy"] = pd.to_numeric(df.get("主营业务收入增长率(%)"), errors="coerce")
        frames.append(out.dropna(subset=["end_date"]))
        time.sleep(sleep)

    if not frames:
        raise RuntimeError("No AKShare financial data downloaded.")
    fina = pd.concat(frames, ignore_index=True)
    fina["ann_date"] = fina["ann_date"].dt.strftime("%Y%m%d")
    fina["end_date"] = fina["end_date"].dt.strftime("%Y%m%d")
    fina.to_csv(RAW_DIR / "fina_indicator.csv", index=False, encoding="utf-8-sig")
    return fina


def main() -> None:
    args = parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    members = load_members(Path(args.members_file), 0 if args.stock_list else args.max_stocks)
    stock_list = load_stock_list(args, members)
    by_stock_dir = Path(args.by_stock_dir)
    if args.combine_only:
        price = combine_price_files(by_stock_dir, stock_list)
    else:
        price = download_price(
            stock_list,
            args.start,
            args.end,
            args.sleep,
            args.retries,
            args.timeout,
            by_stock_dir,
            args.refresh,
        )
    build_daily_basic(price, members)
    if args.with_financial:
        successful_stocks = price["ts_code"].drop_duplicates().tolist()
        download_financial(successful_stocks, args.start, args.sleep, args.retries)
    elif not (RAW_DIR / "fina_indicator.csv").exists():
        pd.DataFrame(columns=["ts_code", "ann_date", "end_date", "roe", "roa", "grossprofit_margin", "or_yoy"]).to_csv(
            RAW_DIR / "fina_indicator.csv",
            index=False,
            encoding="utf-8-sig",
        )
    print(f"Done. AKShare learning-version files saved to {RAW_DIR}")


if __name__ == "__main__":
    main()
