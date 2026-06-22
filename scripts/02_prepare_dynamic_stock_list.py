"""Prepare a unique stock list from dynamic HS300 constituents."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract dynamic HS300 stock list.")
    parser.add_argument("--members", default=str(RAW_DIR / "hs300_members_dynamic.csv"), help="Dynamic members CSV.")
    parser.add_argument(
        "--output",
        default=str(PROCESSED_DIR / "hs300_dynamic_stock_list.csv"),
        help="Output stock list CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    members_path = Path(args.members)
    output_path = Path(args.output)
    if not members_path.exists():
        raise FileNotFoundError(f"Missing dynamic members file: {members_path}")

    members = pd.read_csv(members_path)
    stock_list = (
        members["con_code"]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .rename("ts_code")
        .to_frame()
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stock_list.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Saved {len(stock_list):,} stocks to {output_path}")


if __name__ == "__main__":
    main()
