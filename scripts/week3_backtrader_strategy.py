"""Backtrader demo for the Week 3 Top-N factor strategy."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".matplotlib-cache"))
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DEFAULT_SIGNAL = "composite_ic_weight_industry_size_neutral"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Week 3 Backtrader demo strategy.")
    parser.add_argument("--panel-file", default=str(PROJECT_ROOT / "outputs" / "week2" / "composite_factor_panel.csv"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "week3"))
    parser.add_argument("--signal", default=DEFAULT_SIGNAL)
    parser.add_argument("--rebalance-days", type=int, default=20)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--commission", type=float, default=0.001)
    parser.add_argument("--slippage", type=float, default=0.0005)
    return parser.parse_args()


def basic_metrics(nav: pd.DataFrame) -> dict[str, float]:
    ret = nav["backtrader_ret"].dropna()
    annual_return = (1 + ret).prod() ** (252 / len(ret)) - 1 if len(ret) else np.nan
    annual_vol = ret.std() * np.sqrt(252) if len(ret) else np.nan
    drawdown = nav["backtrader_nav"] / nav["backtrader_nav"].cummax() - 1
    max_drawdown = drawdown.min()
    return {
        "annual_return": annual_return,
        "annual_volatility": annual_vol,
        "sharpe": annual_return / annual_vol if annual_vol and annual_vol != 0 else np.nan,
        "max_drawdown": max_drawdown,
        "calmar": annual_return / abs(max_drawdown) if max_drawdown and max_drawdown != 0 else np.nan,
        "win_rate": (ret > 0).mean() if len(ret) else np.nan,
    }


def prepare_inputs(panel_file: Path, signal: str, rebalance_days: int) -> tuple[pd.DataFrame, dict[pd.Timestamp, dict[str, float]], set[pd.Timestamp]]:
    panel = pd.read_csv(panel_file)
    panel["trade_date"] = pd.to_datetime(panel["trade_date"])
    panel = panel.sort_values(["trade_date", "ts_code"]).copy()
    if signal not in panel.columns:
        raise RuntimeError(f"Signal column not found: {signal}")
    dates = sorted(panel["trade_date"].dropna().unique())
    rebalance_dates = set(pd.to_datetime(dates[::rebalance_days]))
    signal_map: dict[pd.Timestamp, dict[str, float]] = {}
    for date, group in panel[panel["trade_date"].isin(rebalance_dates)].groupby("trade_date"):
        signal_map[pd.Timestamp(date)] = group.set_index("ts_code")[signal].dropna().to_dict()
    return panel, signal_map, rebalance_dates


def run_backtrader(
    panel: pd.DataFrame,
    signal_map: dict[pd.Timestamp, dict[str, float]],
    rebalance_dates: set[pd.Timestamp],
    top_n: int,
    commission: float,
    slippage: float,
) -> pd.DataFrame:
    try:
        import backtrader as bt
    except Exception as exc:
        raise RuntimeError("Backtrader is not installed. Run `.venv/bin/pip install backtrader`.") from exc

    class TopNFactorStrategy(bt.Strategy):
        params = dict(signal_map=signal_map, rebalance_dates=rebalance_dates, top_n=top_n)

        def __init__(self) -> None:
            self.nav_records: list[dict[str, object]] = []

        def next(self) -> None:
            current_date = pd.Timestamp(self.datas[0].datetime.date(0))
            if current_date in self.p.rebalance_dates:
                scores = {}
                day_scores = self.p.signal_map.get(current_date, {})
                for data in self.datas:
                    score = day_scores.get(data._name)
                    if score is not None and pd.notna(score):
                        scores[data] = score
                selected = {data for data, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)[: self.p.top_n]}
                target = 1 / len(selected) if selected else 0
                for data in self.datas:
                    self.order_target_percent(data=data, target=target if data in selected else 0)
            self.nav_records.append({"trade_date": current_date, "portfolio_value": self.broker.getvalue()})

    cerebro = bt.Cerebro()
    cerebro.broker.setcash(1_000_000)
    cerebro.broker.setcommission(commission=commission)
    cerebro.broker.set_slippage_perc(perc=slippage)

    for code, group in panel.groupby("ts_code"):
        data = group[["trade_date", "close"]].dropna().copy()
        if data.empty:
            continue
        data = data.set_index("trade_date").sort_index()
        feed_df = pd.DataFrame(index=data.index)
        feed_df["open"] = data["close"]
        feed_df["high"] = data["close"]
        feed_df["low"] = data["close"]
        feed_df["close"] = data["close"]
        feed_df["volume"] = 0
        feed_df["openinterest"] = 0
        cerebro.adddata(bt.feeds.PandasData(dataname=feed_df), name=code)

    cerebro.addstrategy(TopNFactorStrategy)
    results = cerebro.run()
    strategy = results[0]
    nav = pd.DataFrame(strategy.nav_records).drop_duplicates("trade_date").sort_values("trade_date")
    nav["backtrader_nav"] = nav["portfolio_value"] / nav["portfolio_value"].iloc[0]
    nav["backtrader_ret"] = nav["backtrader_nav"].pct_change().fillna(0)
    return nav


def save_outputs(nav: pd.DataFrame, output_dir: Path, signal: str, rebalance_days: int, top_n: int) -> None:
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    nav.to_csv(output_dir / "backtrader_nav.csv", index=False, encoding="utf-8-sig")
    metrics = {"signal": signal, "rebalance_days": rebalance_days, "top_n": top_n, **basic_metrics(nav)}
    pd.DataFrame([metrics]).to_csv(output_dir / "backtrader_metrics.csv", index=False, encoding="utf-8-sig")
    plt.figure(figsize=(10, 5))
    plt.plot(nav["trade_date"], nav["backtrader_nav"], label="Backtrader")
    plt.title("Backtrader strategy NAV")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "backtrader_nav_curve.png", dpi=160)
    plt.close()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    panel, signal_map, rebalance_dates = prepare_inputs(Path(args.panel_file), args.signal, args.rebalance_days)
    nav = run_backtrader(panel, signal_map, rebalance_dates, args.top_n, args.commission, args.slippage)
    save_outputs(nav, output_dir, args.signal, args.rebalance_days, args.top_n)
    print(f"Backtrader outputs saved to {output_dir}")


if __name__ == "__main__":
    main()
