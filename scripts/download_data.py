"""Download HS300 raw data from Tushare Pro.

Default settings produce a smaller learning dataset:
2020-2023 and the first 50 historical HS300 constituents.

Set your token before running:
    export TUSHARE_TOKEN="your token"
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import pandas as pd
import tushare as ts
from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download HS300 data from Tushare Pro.")
    parser.add_argument("--start", default="20200101", help="Start date, YYYYMMDD.")
    parser.add_argument("--end", default="20231231", help="End date, YYYYMMDD.")
    parser.add_argument("--index-code", default="399300.SZ", help="HS300 index code.")
    parser.add_argument("--max-stocks", type=int, default=50, help="Limit stock count; use 0 for all.")
    parser.add_argument("--sleep", type=float, default=0.35, help="Pause between API calls.")
    parser.add_argument("--token", default=os.getenv("TUSHARE_TOKEN"), help="Tushare token.")
    parser.add_argument("--refresh", action="store_true", help="Re-download files that already exist.")
    return parser.parse_args()


def save_csv(df: pd.DataFrame, filename: str) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_DIR / filename, index=False, encoding="utf-8-sig")


def require_non_empty(frames: list[pd.DataFrame], name: str) -> pd.DataFrame:
    if not frames:
        raise RuntimeError(f"No data downloaded for {name}. Check token permissions and date range.")
    return pd.concat(frames, ignore_index=True)


def get_hs300_members(pro: ts.pro_api, start: str, end: str, index_code: str, sleep: float) -> pd.DataFrame:
    months = pd.date_range(start=start, end=end, freq="MS")
    frames: list[pd.DataFrame] = []

    for d in tqdm(months, desc="index_weight"):
        start_date = d.strftime("%Y%m%d")
        end_date = (d + pd.offsets.MonthEnd(0)).strftime("%Y%m%d")
        try:
            df = pro.index_weight(index_code=index_code, start_date=start_date, end_date=end_date)
            if df is not None and not df.empty:
                frames.append(df)
        except Exception as exc:  # Tushare returns permission/rate-limit messages as exceptions.
            print(f"[index_weight] {start_date}: {exc}")
        time.sleep(sleep)

    members = require_non_empty(frames, "hs300 members")
    members = members.drop_duplicates()
    save_csv(members, "hs300_members.csv")
    return members


def get_trade_dates(pro: ts.pro_api, start: str, end: str) -> list[str]:
    try:
        cal = pro.trade_cal(exchange="SSE", start_date=start, end_date=end, is_open="1")
    except Exception as exc:
        print(f"[trade_cal] fallback to business days: {exc}")
        cal = pd.DataFrame()
    if cal is None or cal.empty:
        return [d.strftime("%Y%m%d") for d in pd.date_range(start=start, end=end, freq="B")]
    return cal.sort_values("cal_date")["cal_date"].astype(str).tolist()


def get_price_data(pro: ts.pro_api, stock_list: list[str], start: str, end: str, sleep: float) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    for code in tqdm(stock_list, desc="pro_bar qfq"):
        try:
            df = ts.pro_bar(api=pro, ts_code=code, adj="qfq", start_date=start, end_date=end)
            if df is not None and not df.empty:
                frames.append(df)
        except Exception as exc:
            print(f"[pro_bar] {code}: {exc}")
        time.sleep(sleep)

    price = require_non_empty(frames, "price_qfq")
    price = price.drop_duplicates(["ts_code", "trade_date"])
    save_csv(price, "price_qfq.csv")
    return price


def get_daily_basic(pro: ts.pro_api, trade_dates: list[str], sleep: float) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    fields = "ts_code,trade_date,turnover_rate,pe,pb,total_mv,circ_mv"

    for date in tqdm(trade_dates, desc="daily_basic"):
        try:
            df = pro.daily_basic(ts_code="", trade_date=date, fields=fields)
            if df is not None and not df.empty:
                frames.append(df)
        except Exception as exc:
            print(f"[daily_basic] {date}: {exc}")
        time.sleep(sleep)

    basic = require_non_empty(frames, "daily_basic")
    basic = basic.drop_duplicates(["ts_code", "trade_date"])
    save_csv(basic, "daily_basic.csv")
    return basic


def get_fina_indicator(pro: ts.pro_api, stock_list: list[str], start: str, end: str, sleep: float) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    fields = "ts_code,ann_date,end_date,roe,roa,grossprofit_margin,or_yoy"

    for code in tqdm(stock_list, desc="fina_indicator"):
        try:
            df = pro.fina_indicator(ts_code=code, start_date=start, end_date=end, fields=fields)
            if df is not None and not df.empty:
                frames.append(df)
        except Exception as exc:
            print(f"[fina_indicator] {code}: {exc}")
        time.sleep(sleep)

    fina = require_non_empty(frames, "fina_indicator")
    fina = fina.drop_duplicates(["ts_code", "ann_date", "end_date"])
    save_csv(fina, "fina_indicator.csv")
    return fina


def main() -> None:
    args = parse_args()
    if not args.token:
        raise SystemExit("Please set TUSHARE_TOKEN or pass --token.")

    pro = ts.pro_api(args.token)

    members_path = RAW_DIR / "hs300_members.csv"
    if members_path.exists() and not args.refresh:
        print(f"Reuse existing {members_path}")
        members = pd.read_csv(members_path)
    else:
        members = get_hs300_members(pro, args.start, args.end, args.index_code, args.sleep)
    stock_list = members["con_code"].dropna().drop_duplicates().sort_values().tolist()
    if args.max_stocks and args.max_stocks > 0:
        stock_list = stock_list[: args.max_stocks]

    trade_dates = get_trade_dates(pro, args.start, args.end)
    if (RAW_DIR / "price_qfq.csv").exists() and not args.refresh:
        print(f"Reuse existing {RAW_DIR / 'price_qfq.csv'}")
    else:
        get_price_data(pro, stock_list, args.start, args.end, args.sleep)

    if (RAW_DIR / "daily_basic.csv").exists() and not args.refresh:
        print(f"Reuse existing {RAW_DIR / 'daily_basic.csv'}")
    else:
        get_daily_basic(pro, trade_dates, args.sleep)

    if (RAW_DIR / "fina_indicator.csv").exists() and not args.refresh:
        print(f"Reuse existing {RAW_DIR / 'fina_indicator.csv'}")
    else:
        get_fina_indicator(pro, stock_list, args.start, args.end, args.sleep)

    print(f"Done. Raw files saved to {RAW_DIR}")


if __name__ == "__main__":
    main()
