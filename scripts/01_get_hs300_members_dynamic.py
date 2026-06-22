"""Download monthly HS300 historical constituents with resumable Tushare calls."""

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
MONTH_DIR = RAW_DIR / "hs300_members_dynamic_by_month"
OUTPUT_FILE = RAW_DIR / "hs300_members_dynamic.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download dynamic HS300 monthly members from Tushare.")
    parser.add_argument("--start", default="20150101", help="Start date, YYYYMMDD.")
    parser.add_argument("--end", default="20231231", help="End date, YYYYMMDD.")
    parser.add_argument("--index-code", default="399300.SZ", help="HS300 index code.")
    parser.add_argument("--sleep", type=float, default=65.0, help="Sleep seconds between index_weight calls.")
    parser.add_argument("--token", default=os.getenv("TUSHARE_TOKEN"), help="Tushare token.")
    parser.add_argument("--refresh", action="store_true", help="Re-download existing month files.")
    return parser.parse_args()


def month_file(month: pd.Timestamp) -> Path:
    return MONTH_DIR / f"{month.strftime('%Y%m')}.csv"


def combine_month_files() -> pd.DataFrame:
    files = sorted(MONTH_DIR.glob("*.csv"))
    frames = [pd.read_csv(path) for path in files if path.stat().st_size > 0]
    if not frames:
        return pd.DataFrame(columns=["index_code", "con_code", "trade_date", "weight"])
    members = pd.concat(frames, ignore_index=True).drop_duplicates()
    members = members.sort_values(["trade_date", "con_code"]).reset_index(drop=True)
    members.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    return members


def main() -> None:
    args = parse_args()
    if not args.token:
        raise SystemExit("Please set TUSHARE_TOKEN or pass --token.")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    MONTH_DIR.mkdir(parents=True, exist_ok=True)

    pro = ts.pro_api(args.token)
    months = pd.date_range(start=args.start, end=args.end, freq="MS")

    for month in tqdm(months, desc="index_weight monthly"):
        path = month_file(month)
        if path.exists() and not args.refresh:
            continue

        start_date = month.strftime("%Y%m%d")
        end_date = (month + pd.offsets.MonthEnd(0)).strftime("%Y%m%d")
        try:
            df = pro.index_weight(index_code=args.index_code, start_date=start_date, end_date=end_date)
            if df is None:
                df = pd.DataFrame(columns=["index_code", "con_code", "trade_date", "weight"])
            df.to_csv(path, index=False, encoding="utf-8-sig")
        except Exception as exc:
            print(f"[index_weight] {start_date}-{end_date}: {exc}")
            if not path.exists():
                pd.DataFrame(columns=["index_code", "con_code", "trade_date", "weight"]).to_csv(
                    path,
                    index=False,
                    encoding="utf-8-sig",
                )
        time.sleep(args.sleep)

    members = combine_month_files()
    print(f"Saved {len(members):,} member rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
