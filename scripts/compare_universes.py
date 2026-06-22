"""Compare Week 1 static and dynamic universe results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "week1"


CONFIGS = [
    {
        "version": "v1.0",
        "universe_type": "static_46",
        "panel": PROCESSED_DIR / "factor_panel.csv",
        "output": OUTPUT_DIR,
    },
    {
        "version": "v1.1",
        "universe_type": "dynamic_hs300",
        "panel": PROCESSED_DIR / "factor_panel_dynamic.csv",
        "output": OUTPUT_DIR / "dynamic_universe",
    },
]


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def summarize_config(config: dict[str, object]) -> pd.DataFrame:
    panel_path = config["panel"]
    output_dir = config["output"]
    panel = load_csv(panel_path)
    ic = load_csv(output_dir / "factor_ic_summary.csv")
    group = load_csv(output_dir / "decile_group_summary.csv")
    if group.empty:
        group = load_csv(output_dir / "factor_group_summary.csv")

    if panel.empty or ic.empty:
        return pd.DataFrame()

    panel["trade_date"] = pd.to_datetime(panel["trade_date"])
    base = {
        "version": config["version"],
        "universe_type": config["universe_type"],
        "start_date": panel["trade_date"].min().date(),
        "end_date": panel["trade_date"].max().date(),
        "stock_count": panel["ts_code"].nunique(),
        "rows": len(panel),
    }

    rows: list[dict[str, object]] = []
    for _, ic_row in ic.iterrows():
        factor = ic_row["factor"]
        group_match = group[group["factor"] == factor] if not group.empty else pd.DataFrame()
        long_short = group_match["long_short_mean"].iloc[0] if "long_short_mean" in group_match and not group_match.empty else None
        rows.append(
            {
                **base,
                "factor": factor,
                "rank_ic_mean": ic_row.get("rank_ic_mean"),
                "rank_ic_ir": ic_row.get("rank_icir"),
                "long_short_mean": long_short,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    frames = [summarize_config(config) for config in CONFIGS]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        raise RuntimeError("No universe results found to compare.")
    summary = pd.concat(frames, ignore_index=True)
    out = OUTPUT_DIR / "universe_comparison_summary.csv"
    summary.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"Saved comparison summary to {out}")


if __name__ == "__main__":
    main()
