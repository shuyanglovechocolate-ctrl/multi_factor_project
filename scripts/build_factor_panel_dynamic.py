"""Build factor panel for the dynamic HS300 universe."""

from __future__ import annotations

from pathlib import Path

from build_factor_panel import PROJECT_ROOT, build_factor_panel


RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def main() -> None:
    panel = build_factor_panel(
        price_file=RAW_DIR / "price_qfq.csv",
        basic_file=RAW_DIR / "daily_basic.csv",
        fina_file=RAW_DIR / "fina_indicator.csv",
        members_file=RAW_DIR / "hs300_members_dynamic.csv",
        output_csv=PROCESSED_DIR / "factor_panel_dynamic.csv",
        output_parquet=PROCESSED_DIR / "factor_panel_dynamic.parquet",
        universe_output=PROCESSED_DIR / "dynamic_universe.csv",
    )
    print(f"Dynamic factor panel rows: {len(panel):,}")
    print(f"Saved to {PROCESSED_DIR / 'factor_panel_dynamic.csv'}")


if __name__ == "__main__":
    main()
