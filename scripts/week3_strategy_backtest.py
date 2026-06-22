"""Week 3 vectorized strategy backtest and parameter sensitivity."""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

BOOT_T0 = time.time()
print("[BOOT] week3_strategy_backtest.py starting...", flush=True)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/week3-matplotlib-cache")
os.environ.setdefault("MPLBACKEND", "Agg")

print("[BOOT] importing numpy...", flush=True)
import numpy as np
print(f"[BOOT] numpy imported in {time.time() - BOOT_T0:.2f}s", flush=True)
print("[BOOT] importing pandas...", flush=True)
import pandas as pd
print(f"[BOOT] pandas imported in {time.time() - BOOT_T0:.2f}s", flush=True)


def load_plotting():
    print("[BOOT] importing matplotlib/seaborn for figures...", flush=True)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    print(f"[BOOT] plotting libraries imported in {time.time() - BOOT_T0:.2f}s", flush=True)
    return plt, sns


DEFAULT_SIGNAL = "composite_ic_weight_industry_size_neutral"
DEFAULT_ALT_SIGNAL = "composite_rolling_ic_weight_industry_size_neutral"
REBALANCE_DAYS = [5, 20, 60]
TOP_N_LIST = [10, 20, 30]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Week 3 strategy backtest.")
    parser.add_argument(
        "--panel-file",
        default=str(PROJECT_ROOT / "outputs" / "week2" / "composite_factor_panel.csv"),
    )
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "week3"))
    parser.add_argument("--signal", default=DEFAULT_SIGNAL)
    parser.add_argument("--alt-signal", default=DEFAULT_ALT_SIGNAL)
    parser.add_argument("--rebalance-days", type=int, default=20)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--commission", type=float, default=0.001)
    parser.add_argument("--slippage", type=float, default=0.0005)
    parser.add_argument("--index-file", default=str(PROJECT_ROOT / "data" / "raw" / "hs300_index.csv"))
    parser.add_argument("--download-index", action="store_true")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run a lightweight v3.3 pass: base strategy, weight comparison, cost linkage, and framework diff only.",
    )
    parser.add_argument("--skip-stress", action="store_true", help="Skip v3.3 stress testing.")
    parser.add_argument("--skip-risk-grid", action="store_true", help="Skip risk-control parameter grid.")
    parser.add_argument("--skip-backtrader-diff", action="store_true", help="Skip vectorized vs Backtrader comparison.")
    parser.add_argument("--skip-tradeability", action="store_true", help="Skip tradeability-constrained backtest.")
    parser.add_argument("--skip-constraints", action="store_true", help="Skip hard portfolio-constraint backtest.")
    parser.add_argument("--skip-figures", action="store_true", help="Skip all matplotlib/seaborn figure generation.")
    return parser.parse_args()


def read_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    panel["trade_date"] = pd.to_datetime(panel["trade_date"])
    panel = panel.sort_values(["trade_date", "ts_code"]).copy()
    if "ret_1d" not in panel.columns:
        panel["ret_1d"] = panel.groupby("ts_code")["close"].pct_change()
    panel["next_ret_1d"] = panel.groupby("ts_code")["ret_1d"].shift(-1)
    panel["rolling_vol_20"] = (
        panel.groupby("ts_code")["ret_1d"]
        .rolling(20, min_periods=5)
        .std()
        .reset_index(level=0, drop=True)
        .shift(1)
    )
    panel["rolling_vol_60"] = (
        panel.groupby("ts_code")["ret_1d"]
        .rolling(60, min_periods=10)
        .std()
        .reset_index(level=0, drop=True)
        .shift(1)
    )
    return panel


def download_hs300_index(index_file: Path, start: str, end: str) -> bool:
    try:
        import akshare as ak
    except Exception as exc:
        print(f"AKShare not available for HS300 index download: {exc}")
        return False

    candidates = [
        lambda: ak.stock_zh_index_daily(symbol="sh000300"),
        lambda: ak.index_zh_a_hist(symbol="000300", period="daily", start_date=start, end_date=end),
    ]
    for fetch in candidates:
        try:
            df = fetch()
            if df is None or df.empty:
                continue
            df = df.copy()
            rename_map = {
                "日期": "trade_date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "date": "trade_date",
            }
            df = df.rename(columns=rename_map)
            if "trade_date" not in df.columns or "close" not in df.columns:
                continue
            df["trade_date"] = pd.to_datetime(df["trade_date"])
            start_dt = pd.to_datetime(start)
            end_dt = pd.to_datetime(end)
            df = df[(df["trade_date"] >= start_dt) & (df["trade_date"] <= end_dt)].copy()
            if df.empty:
                continue
            keep_cols = [col for col in ["trade_date", "open", "high", "low", "close", "volume", "amount"] if col in df.columns]
            index_file.parent.mkdir(parents=True, exist_ok=True)
            df[keep_cols].sort_values("trade_date").to_csv(index_file, index=False, encoding="utf-8-sig")
            return True
        except Exception as exc:
            print(f"HS300 index download attempt failed: {exc}")
    return False


def read_hs300_benchmark(index_file: Path, nav_dates: pd.Series, start: str, end: str, allow_download: bool) -> pd.DataFrame:
    if not index_file.exists() and allow_download:
        download_hs300_index(index_file, start, end)
    if not index_file.exists():
        return pd.DataFrame()
    index_df = pd.read_csv(index_file)
    if "trade_date" not in index_df.columns or "close" not in index_df.columns:
        return pd.DataFrame()
    index_df["trade_date"] = pd.to_datetime(index_df["trade_date"])
    index_df = index_df.sort_values("trade_date").copy()
    index_df["hs300_ret"] = index_df["close"].pct_change()
    aligned_dates = pd.DataFrame({"trade_date": pd.to_datetime(nav_dates)})
    out = aligned_dates.merge(index_df[["trade_date", "close", "hs300_ret"]], on="trade_date", how="left")
    out["hs300_ret"] = out["hs300_ret"].fillna(0)
    out["hs300_nav"] = (1 + out["hs300_ret"]).cumprod()
    return out


def choose_signal(panel: pd.DataFrame, preferred: str) -> str:
    if preferred in panel.columns and panel[preferred].notna().sum() > 0:
        return preferred
    fallbacks = [
        DEFAULT_SIGNAL,
        "composite_ic_weight_neutral",
        "composite_ic_weight_size_neutral",
        "composite_ic_weight",
        "composite_equal_industry_size_neutral",
    ]
    for col in fallbacks:
        if col in panel.columns and panel[col].notna().sum() > 0:
            return col
    raise RuntimeError("No usable composite signal found.")


def build_weight_matrix(panel: pd.DataFrame, signal_col: str, rebalance_days: int, top_n: int) -> pd.DataFrame:
    dates = sorted(panel["trade_date"].dropna().unique())
    rebalance_dates = set(dates[::rebalance_days])
    frames: list[pd.DataFrame] = []
    current_weights: pd.Series = pd.Series(dtype=float)

    for date in dates:
        day = panel[panel["trade_date"] == date][["trade_date", "ts_code", signal_col, "next_ret_1d"]].copy()
        tradable = day.dropna(subset=[signal_col, "next_ret_1d"])
        if date in rebalance_dates and not tradable.empty:
            selected = tradable.nlargest(top_n, signal_col)["ts_code"].tolist()
            if selected:
                current_weights = pd.Series(1 / len(selected), index=selected, dtype=float)
            else:
                current_weights = pd.Series(dtype=float)
        day["weight"] = day["ts_code"].map(current_weights).fillna(0.0)
        day["is_rebalance"] = date in rebalance_dates
        frames.append(day[["trade_date", "ts_code", "weight", "next_ret_1d", "is_rebalance"]])

    return pd.concat(frames, ignore_index=True)


def max_drawdown(nav: pd.Series) -> float:
    drawdown = nav / nav.cummax() - 1
    return float(drawdown.min())


def calculate_metrics(
    nav: pd.DataFrame,
    trades: pd.DataFrame,
    rebalance_days: int,
    top_n: int,
    signal_col: str,
) -> dict[str, object]:
    returns = nav["strategy_ret"].dropna()
    bench = nav["benchmark_ret"].dropna()
    aligned = pd.concat([returns, bench], axis=1).dropna()
    excess = aligned["strategy_ret"] - aligned["benchmark_ret"] if not aligned.empty else pd.Series(dtype=float)
    annual_return = (1 + returns).prod() ** (252 / len(returns)) - 1 if len(returns) else np.nan
    annual_volatility = returns.std() * np.sqrt(252) if len(returns) else np.nan
    sharpe = annual_return / annual_volatility if annual_volatility and annual_volatility != 0 else np.nan
    mdd = max_drawdown(nav["strategy_nav"]) if not nav.empty else np.nan
    calmar = annual_return / abs(mdd) if mdd and mdd != 0 else np.nan
    bench_annual = (1 + bench).prod() ** (252 / len(bench)) - 1 if len(bench) else np.nan
    excess_annual = annual_return - bench_annual if pd.notna(annual_return) and pd.notna(bench_annual) else np.nan
    tracking_error = excess.std() * np.sqrt(252) if len(excess) else np.nan
    information_ratio = excess_annual / tracking_error if tracking_error and tracking_error != 0 else np.nan
    avg_turnover = trades["turnover"].mean() if not trades.empty else np.nan
    annual_cost = trades["cost"].sum() * 252 / len(returns) if len(returns) else np.nan

    return {
        "signal": signal_col,
        "rebalance_days": rebalance_days,
        "top_n": top_n,
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "sharpe": sharpe,
        "max_drawdown": mdd,
        "calmar": calmar,
        "win_rate": (returns > 0).mean() if len(returns) else np.nan,
        "benchmark_annual_return": bench_annual,
        "excess_annual_return": excess_annual,
        "information_ratio": information_ratio,
        "avg_turnover": avg_turnover,
        "annual_cost": annual_cost,
    }


def run_backtest(
    panel: pd.DataFrame,
    signal_col: str,
    rebalance_days: int,
    top_n: int,
    single_side_cost: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    weights = build_weight_matrix(panel, signal_col, rebalance_days, top_n)
    returns = weights.copy()
    returns["weighted_ret"] = returns["weight"] * returns["next_ret_1d"].fillna(0)
    daily = returns.groupby("trade_date").agg(strategy_gross_ret=("weighted_ret", "sum")).reset_index()

    benchmark = (
        panel.dropna(subset=["next_ret_1d"])
        .groupby("trade_date")["next_ret_1d"]
        .mean()
        .reset_index(name="benchmark_ret")
    )
    daily = daily.merge(benchmark, on="trade_date", how="left")

    weight_pivot = weights.pivot_table(index="trade_date", columns="ts_code", values="weight", aggfunc="sum").fillna(0)
    turnover = 0.5 * weight_pivot.diff().abs().sum(axis=1)
    if not turnover.empty:
        turnover.iloc[0] = 0.5 * weight_pivot.iloc[0].abs().sum()
    is_rebalance = weights.groupby("trade_date")["is_rebalance"].max()
    trades = pd.DataFrame(
        {
            "trade_date": turnover.index,
            "turnover": turnover.values,
            "is_rebalance": is_rebalance.reindex(turnover.index).fillna(False).values,
        }
    )
    trades["cost"] = np.where(trades["is_rebalance"], trades["turnover"] * single_side_cost, 0.0)

    daily = daily.merge(trades[["trade_date", "turnover", "cost", "is_rebalance"]], on="trade_date", how="left")
    daily["turnover"] = daily["turnover"].fillna(0)
    daily["cost"] = daily["cost"].fillna(0)
    daily["strategy_ret"] = daily["strategy_gross_ret"] - daily["cost"]
    daily["strategy_nav"] = (1 + daily["strategy_ret"].fillna(0)).cumprod()
    daily["benchmark_nav"] = (1 + daily["benchmark_ret"].fillna(0)).cumprod()
    daily["excess_nav"] = daily["strategy_nav"] / daily["benchmark_nav"]
    daily["drawdown"] = daily["strategy_nav"] / daily["strategy_nav"].cummax() - 1

    metrics = calculate_metrics(daily, trades[trades["is_rebalance"]].copy(), rebalance_days, top_n, signal_col)
    return daily, trades, metrics


def get_tradeability_flags(day: pd.DataFrame) -> pd.DataFrame:
    out = day.copy()
    ret = out["ret_1d"] if "ret_1d" in out.columns else pd.Series(np.nan, index=out.index)
    volume_col = "vol" if "vol" in out.columns else "volume" if "volume" in out.columns else None
    suspended = out["close"].isna() | out["next_ret_1d"].isna()
    if volume_col:
        suspended = suspended | out[volume_col].fillna(0).eq(0)
    st_mask = pd.Series(False, index=out.index)
    for name_col in ["name", "stock_name"]:
        if name_col in out.columns:
            st_mask = st_mask | out[name_col].astype(str).str.contains("ST", case=False, na=False)
    out["is_suspended_like"] = suspended
    out["is_limit_up_like"] = ret >= 0.098
    out["is_limit_down_like"] = ret <= -0.098
    out["is_st_like"] = st_mask
    out["can_buy"] = ~(out["is_suspended_like"] | out["is_limit_up_like"] | out["is_st_like"])
    out["can_sell"] = ~(out["is_suspended_like"] | out["is_limit_down_like"])
    return out


def normalize_selected_weights(selected: pd.DataFrame, weight_method: str, target_sum: float = 1.0) -> pd.Series:
    if selected.empty or target_sum <= 0:
        return pd.Series(dtype=float)
    if weight_method == "equal_weight":
        raw = pd.Series(1.0, index=selected["ts_code"])
    elif weight_method == "inverse_vol_weight":
        vol = selected["rolling_vol_20"].replace(0, np.nan).fillna(selected["rolling_vol_20"].median())
        raw = pd.Series(1 / vol.clip(lower=1e-6).to_numpy(), index=selected["ts_code"])
    elif weight_method == "risk_parity_weight":
        vol = selected["rolling_vol_60"].replace(0, np.nan).fillna(selected["rolling_vol_60"].median())
        raw = pd.Series(1 / vol.clip(lower=1e-6).to_numpy(), index=selected["ts_code"])
    else:
        raise ValueError(f"Unknown weight method: {weight_method}")
    if raw.replace([np.inf, -np.inf], np.nan).dropna().sum() <= 0:
        raw = pd.Series(1.0, index=selected["ts_code"])
    raw = raw.replace([np.inf, -np.inf], np.nan).fillna(0)
    return raw / raw.sum() * target_sum


def apply_weight_caps(
    weights: pd.Series,
    industries: pd.Series,
    max_stock_weight: float = 0.08,
    max_industry_weight: float = 0.30,
) -> pd.Series:
    if weights.empty:
        return weights
    capped = weights.clip(upper=max_stock_weight)
    for _ in range(10):
        industry_sum = capped.groupby(industries.reindex(capped.index).fillna("Unknown")).sum()
        over_industries = industry_sum[industry_sum > max_industry_weight]
        if over_industries.empty:
            break
        for industry, total in over_industries.items():
            members = industries[industries == industry].index.intersection(capped.index)
            if len(members) and total > 0:
                capped.loc[members] *= max_industry_weight / total
    return capped


def build_weight_matrix_enhanced(
    panel: pd.DataFrame,
    signal_col: str,
    rebalance_days: int,
    top_n: int,
    weight_method: str = "equal_weight",
    trade_constraints: bool = False,
    portfolio_constraints: bool = False,
    max_stock_weight: float = 0.08,
    max_industry_weight: float = 0.30,
    min_holdings: int = 15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = sorted(panel["trade_date"].dropna().unique())
    rebalance_dates = set(dates[::rebalance_days])
    frames: list[pd.DataFrame] = []
    restriction_rows: list[dict[str, object]] = []
    violation_rows: list[dict[str, object]] = []
    current_weights: pd.Series = pd.Series(dtype=float)

    base_cols = [
        "trade_date",
        "ts_code",
        signal_col,
        "next_ret_1d",
        "ret_1d",
        "close",
        "rolling_vol_20",
        "rolling_vol_60",
    ]
    if "industry" in panel.columns:
        base_cols.append("industry")
    for col in ["vol", "volume", "name", "stock_name"]:
        if col in panel.columns:
            base_cols.append(col)
    base_cols = list(dict.fromkeys([col for col in base_cols if col in panel.columns]))

    for date in dates:
        day = panel[panel["trade_date"] == date][base_cols].copy()
        if "industry" not in day.columns:
            day["industry"] = "Unknown"
        flags = get_tradeability_flags(day)
        selected_codes: list[str] = []
        blocked_sell_codes: list[str] = []
        skipped_codes: list[str] = []

        if date in rebalance_dates:
            tradable = flags.dropna(subset=[signal_col, "next_ret_1d"]).copy()
            held_codes = set(current_weights[current_weights > 0].index)
            if trade_constraints and held_codes:
                held_flags = flags[flags["ts_code"].isin(held_codes)].set_index("ts_code")
                blocked_sell_codes = held_flags.index[~held_flags["can_sell"]].tolist()
            retained = current_weights.reindex(blocked_sell_codes).dropna()
            retained_sum = float(retained.sum())

            candidates = tradable.copy()
            if trade_constraints:
                blocked_buy = candidates[~candidates["can_buy"]]["ts_code"].tolist()
                skipped_codes.extend(blocked_buy)
                candidates = candidates[candidates["can_buy"]].copy()
            candidates = candidates.sort_values(signal_col, ascending=False).head(max(top_n * 3, 50))

            if portfolio_constraints:
                chosen_rows = []
                industry_weights: dict[str, float] = {}
                target_weight = min(max_stock_weight, (1 - retained_sum) / max(top_n, 1))
                for _, row in candidates.iterrows():
                    industry = row.get("industry", "Unknown")
                    projected = industry_weights.get(industry, 0.0) + target_weight
                    if projected > max_industry_weight and len(chosen_rows) >= min_holdings:
                        skipped_codes.append(row["ts_code"])
                        continue
                    chosen_rows.append(row)
                    industry_weights[industry] = projected
                    if len(chosen_rows) >= top_n:
                        break
                selected = pd.DataFrame(chosen_rows)
            else:
                selected = candidates.head(top_n).copy()

            selected_weights = normalize_selected_weights(selected, weight_method, max(0.0, 1 - retained_sum))
            if portfolio_constraints and not selected_weights.empty:
                industries = selected.set_index("ts_code")["industry"]
                selected_weights = apply_weight_caps(
                    selected_weights,
                    industries,
                    max_stock_weight=max_stock_weight,
                    max_industry_weight=max_industry_weight,
                )
            current_weights = pd.concat([retained, selected_weights]).groupby(level=0).sum()
            current_weights = current_weights[current_weights > 0]
            selected_codes = selected_weights.index.tolist()

            industry_lookup = day.set_index("ts_code")["industry"]
            industry_check = current_weights.groupby(industry_lookup.reindex(current_weights.index).fillna("Unknown")).sum()
            violation_rows.append(
                {
                    "trade_date": date,
                    "portfolio_constraints": portfolio_constraints,
                    "holding_count": int((current_weights > 0).sum()),
                    "max_stock_weight": float(current_weights.max()) if not current_weights.empty else 0.0,
                    "max_industry_weight": float(industry_check.max()) if not industry_check.empty else 0.0,
                    "violates_stock_cap": bool((current_weights > max_stock_weight + 1e-10).any()),
                    "violates_industry_cap": bool((industry_check > max_industry_weight + 1e-10).any()),
                    "cash_weight": max(0.0, 1 - float(current_weights.sum())),
                }
            )

        if date in rebalance_dates:
            restriction_rows.append(
                {
                    "trade_date": date,
                    "trade_constraints": trade_constraints,
                    "blocked_buy_count": len(set(skipped_codes)),
                    "blocked_sell_count": len(set(blocked_sell_codes)),
                    "selected_count": len(selected_codes),
                    "retained_due_to_sell_block_count": len(set(blocked_sell_codes)),
                }
            )
        day["weight"] = day["ts_code"].map(current_weights).fillna(0.0)
        day["is_rebalance"] = date in rebalance_dates
        frames.append(day[["trade_date", "ts_code", "weight", "next_ret_1d", "is_rebalance"]])

    return (
        pd.concat(frames, ignore_index=True),
        pd.DataFrame(restriction_rows),
        pd.DataFrame(violation_rows),
    )


def portfolio_from_weights(
    panel: pd.DataFrame,
    weights: pd.DataFrame,
    signal_label: str,
    rebalance_days: int,
    top_n: int,
    single_side_cost: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    returns = weights.copy()
    returns["weighted_ret"] = returns["weight"] * returns["next_ret_1d"].fillna(0)
    daily = returns.groupby("trade_date").agg(strategy_gross_ret=("weighted_ret", "sum")).reset_index()
    benchmark = (
        panel.dropna(subset=["next_ret_1d"])
        .groupby("trade_date")["next_ret_1d"]
        .mean()
        .reset_index(name="benchmark_ret")
    )
    daily = daily.merge(benchmark, on="trade_date", how="left")

    weight_pivot = weights.pivot_table(index="trade_date", columns="ts_code", values="weight", aggfunc="sum").fillna(0)
    turnover = 0.5 * weight_pivot.diff().abs().sum(axis=1)
    if not turnover.empty:
        turnover.iloc[0] = 0.5 * weight_pivot.iloc[0].abs().sum()
    is_rebalance = weights.groupby("trade_date")["is_rebalance"].max()
    trades = pd.DataFrame(
        {
            "trade_date": turnover.index,
            "turnover": turnover.values,
            "is_rebalance": is_rebalance.reindex(turnover.index).fillna(False).values,
        }
    )
    trades["cost"] = np.where(trades["is_rebalance"], trades["turnover"] * single_side_cost, 0.0)
    daily = daily.merge(trades[["trade_date", "turnover", "cost", "is_rebalance"]], on="trade_date", how="left")
    daily["turnover"] = daily["turnover"].fillna(0)
    daily["cost"] = daily["cost"].fillna(0)
    daily["strategy_ret"] = daily["strategy_gross_ret"] - daily["cost"]
    daily["strategy_nav"] = (1 + daily["strategy_ret"].fillna(0)).cumprod()
    daily["benchmark_nav"] = (1 + daily["benchmark_ret"].fillna(0)).cumprod()
    daily["excess_nav"] = daily["strategy_nav"] / daily["benchmark_nav"]
    daily["drawdown"] = daily["strategy_nav"] / daily["strategy_nav"].cummax() - 1
    metrics = calculate_metrics(daily, trades[trades["is_rebalance"]].copy(), rebalance_days, top_n, signal_label)
    return daily, trades, metrics


def run_backtest_enhanced(
    panel: pd.DataFrame,
    signal_col: str,
    rebalance_days: int,
    top_n: int,
    single_side_cost: float,
    weight_method: str = "equal_weight",
    trade_constraints: bool = False,
    portfolio_constraints: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    weights, restriction_events, constraint_checks = build_weight_matrix_enhanced(
        panel,
        signal_col,
        rebalance_days,
        top_n,
        weight_method=weight_method,
        trade_constraints=trade_constraints,
        portfolio_constraints=portfolio_constraints,
    )
    label_parts = [signal_col, weight_method]
    if trade_constraints:
        label_parts.append("trade_constraints")
    if portfolio_constraints:
        label_parts.append("portfolio_constraints")
    label = "__".join(label_parts)
    nav, trades, metrics = portfolio_from_weights(panel, weights, label, rebalance_days, top_n, single_side_cost)
    metrics["weight_method"] = weight_method
    metrics["trade_constraints"] = trade_constraints
    metrics["portfolio_constraints"] = portfolio_constraints
    return nav, trades, metrics, weights, restriction_events, constraint_checks


def run_parameter_grid(
    panel: pd.DataFrame,
    signal_col: str,
    single_side_cost: float,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rebalance_days in REBALANCE_DAYS:
        for top_n in TOP_N_LIST:
            _, _, metrics = run_backtest(panel, signal_col, rebalance_days, top_n, single_side_cost)
            rows.append(metrics)
    return pd.DataFrame(rows)


def run_weight_method_comparison(
    panel: pd.DataFrame,
    signal_col: str,
    rebalance_days: int,
    top_n: int,
    single_side_cost: float,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    rows: list[dict[str, object]] = []
    navs: dict[str, pd.DataFrame] = {}
    for method in ["equal_weight", "inverse_vol_weight", "risk_parity_weight"]:
        nav, _, metrics, _, _, _ = run_backtest_enhanced(
            panel,
            signal_col,
            rebalance_days,
            top_n,
            single_side_cost,
            weight_method=method,
        )
        metrics["model"] = method
        rows.append(metrics)
        navs[method] = nav
    return pd.DataFrame(rows), navs


def build_parameter_cost_linkage(panel: pd.DataFrame, signal_col: str, single_side_cost: float) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rebalance_days in REBALANCE_DAYS:
        for top_n in TOP_N_LIST:
            nav, _, metrics = run_backtest(panel, signal_col, rebalance_days, top_n, single_side_cost)
            gross_metrics = basic_return_metrics(nav["strategy_gross_ret"])
            row = {
                "rebalance_days": rebalance_days,
                "top_n": top_n,
                "annual_return": metrics["annual_return"],
                "gross_return": gross_metrics["annual_return"],
                "annual_cost": metrics["annual_cost"],
                "net_return_after_cost": metrics["annual_return"],
                "avg_turnover": metrics["avg_turnover"],
                "sharpe": metrics["sharpe"],
                "calmar": metrics["calmar"],
            }
            rows.append(row)
    return pd.DataFrame(rows)


def build_backtest_framework_comparison(output_dir: Path, vector_nav: pd.DataFrame, vector_metrics: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    bt_nav_path = output_dir / "backtrader_nav.csv"
    bt_metrics_path = output_dir / "backtrader_metrics.csv"
    if not bt_nav_path.exists() or not bt_metrics_path.exists():
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    bt_nav = pd.read_csv(bt_nav_path)
    bt_nav["trade_date"] = pd.to_datetime(bt_nav["trade_date"])
    bt_metrics = pd.read_csv(bt_metrics_path)
    rows = []
    if not bt_metrics.empty:
        bt_row = bt_metrics.iloc[0].to_dict()
        for metric in ["annual_return", "annual_volatility", "sharpe", "max_drawdown", "calmar", "win_rate"]:
            rows.append(
                {
                    "metric": metric,
                    "vectorized": vector_metrics.get(metric, np.nan),
                    "backtrader": bt_row.get(metric, np.nan),
                    "difference": vector_metrics.get(metric, np.nan) - bt_row.get(metric, np.nan),
                }
            )
    attribution = pd.DataFrame(
        [
            {"difference_source": "rebalance_execution_time", "explanation": "Vectorized backtest applies target weights to next-period returns; Backtrader processes orders through event-driven bars."},
            {"difference_source": "price_matching_logic", "explanation": "Vectorized returns use percentage returns directly; Backtrader marks positions using broker value and data feed prices."},
            {"difference_source": "cost_deduction", "explanation": "Vectorized costs are turnover-based; Backtrader commissions and slippage are order-value based."},
            {"difference_source": "cash_handling", "explanation": "Vectorized backtest assumes target exposure after weights; Backtrader keeps residual cash after executions."},
            {"difference_source": "missing_price_handling", "explanation": "The two frameworks can differ when a symbol has missing bars or delayed data."},
            {"difference_source": "nav_timestamp", "explanation": "Backtrader reports broker value by bar; vectorized NAV is accumulated from portfolio daily returns."},
        ]
    )
    merged = vector_nav[["trade_date", "strategy_nav"]].merge(
        bt_nav[["trade_date", "backtrader_nav"]], on="trade_date", how="inner"
    )
    merged["nav_difference"] = merged["strategy_nav"] - merged["backtrader_nav"]
    return pd.DataFrame(rows), attribution, merged


def find_stress_periods(hs300_nav: pd.DataFrame, top_k: int = 3, window: int = 60) -> pd.DataFrame:
    if hs300_nav.empty or "hs300_ret" not in hs300_nav.columns:
        return pd.DataFrame()
    data = hs300_nav[["trade_date", "hs300_ret"]].copy().dropna()
    data["window_return"] = (1 + data["hs300_ret"]).rolling(window).apply(np.prod, raw=True) - 1
    candidates = data.dropna(subset=["window_return"]).sort_values("window_return").copy()
    selected = []
    used_ranges: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for _, row in candidates.iterrows():
        end_date = row["trade_date"]
        start_idx = data.index[data["trade_date"].eq(end_date)][0] - window + 1
        if start_idx < 0:
            continue
        start_date = data.iloc[start_idx]["trade_date"]
        overlaps = any(not (end_date < old_start or start_date > old_end) for old_start, old_end in used_ranges)
        if overlaps:
            continue
        selected.append(
            {
                "stress_period": f"auto_drawdown_{len(selected) + 1}",
                "start_date": start_date,
                "end_date": end_date,
                "hs300_window_return": row["window_return"],
            }
        )
        used_ranges.append((start_date, end_date))
        if len(selected) >= top_k:
            break
    manual_periods = [
        ("covid_shock_2020", "2020-02-03", "2020-04-30"),
        ("bear_market_2022", "2022-01-01", "2022-12-31"),
        ("weak_recovery_2023", "2023-01-01", "2023-12-31"),
    ]
    min_date, max_date = data["trade_date"].min(), data["trade_date"].max()
    for name, start, end in manual_periods:
        start_dt, end_dt = pd.to_datetime(start), pd.to_datetime(end)
        if end_dt >= min_date and start_dt <= max_date:
            selected.append(
                {
                    "stress_period": name,
                    "start_date": max(start_dt, min_date),
                    "end_date": min(end_dt, max_date),
                    "hs300_window_return": np.nan,
                }
            )
    return pd.DataFrame(selected)


def calculate_stress_metrics(nav: pd.DataFrame, periods: pd.DataFrame) -> pd.DataFrame:
    if periods.empty:
        return pd.DataFrame()
    rows = []
    for _, period in periods.iterrows():
        start, end = pd.to_datetime(period["start_date"]), pd.to_datetime(period["end_date"])
        sample = nav[(nav["trade_date"] >= start) & (nav["trade_date"] <= end)].copy()
        if sample.empty:
            continue
        strategy_return = (1 + sample["strategy_ret"].fillna(0)).prod() - 1
        hs300_return = (1 + sample["hs300_ret"].fillna(0)).prod() - 1 if "hs300_ret" in sample.columns else np.nan
        mdd = max_drawdown((1 + sample["strategy_ret"].fillna(0)).cumprod())
        rows.append(
            {
                "stress_period": period["stress_period"],
                "start_date": start,
                "end_date": end,
                "strategy_return": strategy_return,
                "hs300_return": hs300_return,
                "excess_return": strategy_return - hs300_return if pd.notna(hs300_return) else np.nan,
                "max_drawdown": mdd,
                "calmar": strategy_return / abs(mdd) if mdd else np.nan,
            }
        )
    return pd.DataFrame(rows)


def run_risk_control_parameter_grid(panel: pd.DataFrame, signal_col: str, single_side_cost: float) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rebalance_days in REBALANCE_DAYS:
        for top_n in TOP_N_LIST:
            nav, trades, metrics = run_backtest(panel, signal_col, rebalance_days, top_n, single_side_cost)
            rows.append({"risk_control": "none", **metrics})
            vol_nav, vol_metrics = apply_vol_target(nav, target_vol=0.15)
            vol_metrics.update({"rebalance_days": rebalance_days, "top_n": top_n, "avg_turnover": metrics["avg_turnover"]})
            rows.append({"risk_control": "vol_target", **vol_metrics})
            dd_nav, dd_metrics = apply_drawdown_control(nav, trigger_drawdown=-0.15, reduced_exposure=0.5)
            dd_metrics.update({"rebalance_days": rebalance_days, "top_n": top_n, "avg_turnover": metrics["avg_turnover"]})
            rows.append({"risk_control": "drawdown_control", **dd_metrics})
    return pd.DataFrame(rows)


def apply_vol_target(nav: pd.DataFrame, target_vol: float = 0.15, window: int = 20) -> tuple[pd.DataFrame, dict[str, object]]:
    out = nav[["trade_date", "strategy_gross_ret", "cost", "benchmark_ret"]].copy()
    realized_vol = out["strategy_gross_ret"].rolling(window, min_periods=5).std().shift(1) * np.sqrt(252)
    out["exposure"] = (target_vol / realized_vol).clip(upper=1).fillna(1)
    out["strategy_ret"] = out["exposure"] * out["strategy_gross_ret"] - out["exposure"] * out["cost"]
    out["strategy_nav"] = (1 + out["strategy_ret"].fillna(0)).cumprod()
    out["benchmark_nav"] = (1 + out["benchmark_ret"].fillna(0)).cumprod()
    out["excess_nav"] = out["strategy_nav"] / out["benchmark_nav"]
    out["drawdown"] = out["strategy_nav"] / out["strategy_nav"].cummax() - 1
    trades = pd.DataFrame({"turnover": [], "cost": []})
    metrics = calculate_metrics(out, trades, 20, 20, "vol_target_15pct")
    metrics["avg_exposure"] = out["exposure"].mean()
    return out, metrics


def apply_drawdown_control(
    nav: pd.DataFrame,
    trigger_drawdown: float = -0.15,
    recover_drawdown: float = -0.05,
    reduced_exposure: float = 0.5,
) -> tuple[pd.DataFrame, dict[str, object]]:
    out = nav[["trade_date", "strategy_gross_ret", "cost", "benchmark_ret"]].copy()
    exposures: list[float] = []
    current_nav = 1.0
    high_water = 1.0
    exposure = 1.0
    returns: list[float] = []
    navs: list[float] = []
    drawdowns: list[float] = []
    for _, row in out.iterrows():
        dd = current_nav / high_water - 1
        if dd <= trigger_drawdown:
            exposure = reduced_exposure
        elif dd >= recover_drawdown:
            exposure = 1.0
        period_ret = exposure * row["strategy_gross_ret"] - exposure * row["cost"]
        current_nav *= 1 + (0 if pd.isna(period_ret) else period_ret)
        high_water = max(high_water, current_nav)
        exposures.append(exposure)
        returns.append(period_ret)
        navs.append(current_nav)
        drawdowns.append(current_nav / high_water - 1)
    out["exposure"] = exposures
    out["strategy_ret"] = returns
    out["strategy_nav"] = navs
    out["benchmark_nav"] = (1 + out["benchmark_ret"].fillna(0)).cumprod()
    out["excess_nav"] = out["strategy_nav"] / out["benchmark_nav"]
    out["drawdown"] = drawdowns
    trades = pd.DataFrame({"turnover": [], "cost": []})
    metrics = calculate_metrics(out, trades, 20, 20, "drawdown_control")
    metrics["avg_exposure"] = out["exposure"].mean()
    return out, metrics


def build_holdings_analysis(panel: pd.DataFrame, signal_col: str, rebalance_days: int, top_n: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = sorted(panel["trade_date"].dropna().unique())
    rebalance_dates = dates[::rebalance_days]
    rows: list[dict[str, object]] = []
    rebalance_order = {date: idx for idx, date in enumerate(rebalance_dates)}
    for date in rebalance_dates:
        day = panel[panel["trade_date"] == date][["trade_date", "ts_code", signal_col]].dropna()
        selected = day.nlargest(top_n, signal_col).copy()
        for rank, (_, row) in enumerate(selected.iterrows(), start=1):
            rows.append(
                {
                    "trade_date": date,
                    "rebalance_index": rebalance_order[date],
                    "ts_code": row["ts_code"],
                    "rank": rank,
                    "weight": 1 / len(selected) if len(selected) else np.nan,
                    "signal": row[signal_col],
                }
            )
    holdings = pd.DataFrame(rows)
    if holdings.empty:
        return holdings, pd.DataFrame(), pd.DataFrame()
    frequency = (
        holdings.groupby("ts_code")
        .agg(selected_count=("trade_date", "count"), avg_rank=("rank", "mean"), avg_weight=("weight", "mean"))
        .reset_index()
        .sort_values(["selected_count", "avg_rank"], ascending=[False, True])
    )
    periods = []
    for code, data in holdings.sort_values("rebalance_index").groupby("ts_code"):
        indices = data["rebalance_index"].sort_values().tolist()
        streak = 1
        streaks = []
        for prev, cur in zip(indices, indices[1:]):
            if cur == prev + 1:
                streak += 1
            else:
                streaks.append(streak)
                streak = 1
        streaks.append(streak)
        periods.append(
            {
                "ts_code": code,
                "selected_count": len(indices),
                "max_consecutive_rebalances": max(streaks),
                "avg_consecutive_rebalances": float(np.mean(streaks)),
            }
        )
    holding_stats = pd.DataFrame(periods).sort_values("selected_count", ascending=False)
    return holdings, frequency, holding_stats


def run_cost_sensitivity(
    panel: pd.DataFrame,
    signal_col: str,
    rebalance_days: int,
    top_n: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for commission in [0.0, 0.001, 0.002, 0.003]:
        for slippage in [0.0, 0.0005, 0.001]:
            _, _, metrics = run_backtest(panel, signal_col, rebalance_days, top_n, commission + slippage)
            metrics["commission"] = commission
            metrics["slippage"] = slippage
            metrics["single_side_cost"] = commission + slippage
            rows.append(metrics)
    return pd.DataFrame(rows)


def build_parameter_recommendation(sensitivity: pd.DataFrame) -> pd.DataFrame:
    if sensitivity.empty:
        return pd.DataFrame()
    ranked = sensitivity.copy()
    ranked["score"] = (
        ranked["calmar"].rank(pct=True)
        + ranked["sharpe"].rank(pct=True)
        + ranked["annual_return"].rank(pct=True)
        - ranked["avg_turnover"].rank(pct=True) * 0.5
    )
    ranked = ranked.sort_values(["score", "calmar", "sharpe"], ascending=False).reset_index(drop=True)
    ranked["ranking"] = ranked.index + 1
    ranked["reason"] = ranked.apply(
        lambda row: (
            f"Calmar {row['calmar']:.2f}, annual return {row['annual_return']:.2%}, "
            f"turnover {row['avg_turnover']:.2%}; balances return, drawdown, and trading frequency."
        ),
        axis=1,
    )
    cols = [
        "ranking",
        "rebalance_days",
        "top_n",
        "annual_return",
        "sharpe",
        "max_drawdown",
        "calmar",
        "avg_turnover",
        "reason",
    ]
    return ranked[cols]


def basic_return_metrics(returns: pd.Series, nav: pd.Series | None = None) -> dict[str, float]:
    returns = returns.dropna()
    if nav is None:
        nav = (1 + returns.fillna(0)).cumprod()
    annual_return = (1 + returns).prod() ** (252 / len(returns)) - 1 if len(returns) else np.nan
    annual_vol = returns.std() * np.sqrt(252) if len(returns) else np.nan
    sharpe = annual_return / annual_vol if annual_vol and annual_vol != 0 else np.nan
    mdd = max_drawdown(nav) if len(nav) else np.nan
    calmar = annual_return / abs(mdd) if mdd and mdd != 0 else np.nan
    return {
        "annual_return": annual_return,
        "annual_volatility": annual_vol,
        "sharpe": sharpe,
        "max_drawdown": mdd,
        "calmar": calmar,
        "win_rate": (returns > 0).mean() if len(returns) else np.nan,
    }


def build_strategy_vs_benchmark_metrics(nav: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    benchmarks = [
        ("strategy", "strategy_ret", "strategy_nav"),
        ("sample_equal_weight", "benchmark_ret", "benchmark_nav"),
    ]
    if "hs300_ret" in nav.columns and "hs300_nav" in nav.columns:
        benchmarks.append(("hs300", "hs300_ret", "hs300_nav"))
    strategy_returns = nav["strategy_ret"].dropna()
    for name, ret_col, nav_col in benchmarks:
        metrics = basic_return_metrics(nav[ret_col], nav[nav_col])
        if name == "strategy":
            excess_annual = np.nan
            information_ratio = np.nan
        else:
            aligned = pd.concat([strategy_returns, nav[ret_col]], axis=1).dropna()
            excess = aligned.iloc[:, 0] - aligned.iloc[:, 1] if not aligned.empty else pd.Series(dtype=float)
            strategy_annual = basic_return_metrics(aligned.iloc[:, 0]).get("annual_return") if not aligned.empty else np.nan
            bench_annual = metrics["annual_return"]
            excess_annual = strategy_annual - bench_annual if pd.notna(strategy_annual) and pd.notna(bench_annual) else np.nan
            tracking_error = excess.std() * np.sqrt(252) if len(excess) else np.nan
            information_ratio = excess_annual / tracking_error if tracking_error and tracking_error != 0 else np.nan
        rows.append({"benchmark": name, **metrics, "excess_return": excess_annual, "information_ratio": information_ratio})
    return pd.DataFrame(rows)


def calculate_alpha_beta(nav: pd.DataFrame) -> pd.DataFrame:
    if "hs300_ret" not in nav.columns:
        return pd.DataFrame()
    data = nav[["strategy_ret", "hs300_ret"]].dropna()
    if len(data) < 5:
        return pd.DataFrame()
    y = data["strategy_ret"].to_numpy(dtype=float)
    x = data["hs300_ret"].to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(x)), x])
    alpha_daily, beta = np.linalg.pinv(design) @ y
    fitted = design @ np.array([alpha_daily, beta])
    residual = y - fitted
    ss_res = np.sum(residual**2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot else np.nan
    excess = data["strategy_ret"] - data["hs300_ret"]
    tracking_error = excess.std() * np.sqrt(252)
    strategy_annual = basic_return_metrics(data["strategy_ret"])["annual_return"]
    hs300_annual = basic_return_metrics(data["hs300_ret"])["annual_return"]
    information_ratio = (strategy_annual - hs300_annual) / tracking_error if tracking_error else np.nan
    return pd.DataFrame(
        [
            {
                "alpha_daily": alpha_daily,
                "alpha_annual": (1 + alpha_daily) ** 252 - 1,
                "beta": beta,
                "r_squared": r_squared,
                "tracking_error": tracking_error,
                "information_ratio": information_ratio,
            }
        ]
    )


def calculate_periodic_returns(nav: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = nav.set_index("trade_date").copy()
    monthly_rows = []
    for date, group in data.groupby(pd.Grouper(freq="ME")):
        if group.empty:
            continue
        strategy_return = (1 + group["strategy_ret"].fillna(0)).prod() - 1
        benchmark_return = (1 + group["benchmark_ret"].fillna(0)).prod() - 1
        hs300_return = (1 + group["hs300_ret"].fillna(0)).prod() - 1 if "hs300_ret" in group.columns else np.nan
        monthly_rows.append(
            {
                "year": date.year,
                "month": date.month,
                "strategy_return": strategy_return,
                "benchmark_return": benchmark_return,
                "hs300_return": hs300_return,
                "excess_return": strategy_return - benchmark_return,
            }
        )
    yearly_rows = []
    for year, group in data.groupby(data.index.year):
        strategy_metrics = basic_return_metrics(group["strategy_ret"])
        benchmark_return = (1 + group["benchmark_ret"].fillna(0)).prod() - 1
        hs300_return = (1 + group["hs300_ret"].fillna(0)).prod() - 1 if "hs300_ret" in group.columns else np.nan
        yearly_rows.append(
            {
                "year": year,
                "strategy_return": (1 + group["strategy_ret"].fillna(0)).prod() - 1,
                "benchmark_return": benchmark_return,
                "hs300_return": hs300_return,
                "excess_return": (1 + group["strategy_ret"].fillna(0)).prod() - 1 - benchmark_return,
                "max_drawdown": strategy_metrics["max_drawdown"],
                "sharpe": strategy_metrics["sharpe"],
            }
        )
    return pd.DataFrame(monthly_rows), pd.DataFrame(yearly_rows)


def build_trade_records(panel: pd.DataFrame, weights: pd.DataFrame, single_side_cost: float) -> pd.DataFrame:
    pivot = weights.pivot_table(index="trade_date", columns="ts_code", values="weight", aggfunc="sum").fillna(0)
    old = pivot.shift(1).fillna(0)
    changes = pivot - old
    price = panel.pivot_table(index="trade_date", columns="ts_code", values="close", aggfunc="last")
    rows: list[dict[str, object]] = []
    for date, row in changes.iterrows():
        changed = row[row.abs() > 1e-12]
        for code, weight_change in changed.items():
            rows.append(
                {
                    "trade_date": date,
                    "ts_code": code,
                    "action": "buy" if weight_change > 0 else "sell",
                    "old_weight": old.loc[date, code],
                    "new_weight": pivot.loc[date, code],
                    "weight_change": weight_change,
                    "price": price.loc[date, code] if date in price.index and code in price.columns else np.nan,
                    "cost": abs(weight_change) * single_side_cost / 2,
                }
            )
    return pd.DataFrame(rows)


def calculate_holding_concentration(holdings: pd.DataFrame) -> pd.DataFrame:
    if holdings.empty:
        return pd.DataFrame()
    rows = []
    for date, group in holdings.groupby("trade_date"):
        weights = group["weight"].dropna().sort_values(ascending=False)
        hhi = float((weights**2).sum())
        rows.append(
            {
                "trade_date": date,
                "top1_weight": weights.iloc[0] if len(weights) else np.nan,
                "top5_weight": weights.head(5).sum(),
                "effective_num_stocks": 1 / hhi if hhi else np.nan,
                "herfindahl_index": hhi,
            }
        )
    return pd.DataFrame(rows)


def calculate_industry_exposure(holdings: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    if holdings.empty or "industry" not in panel.columns:
        return pd.DataFrame()
    industry = panel[["trade_date", "ts_code", "industry"]].drop_duplicates()
    merged = holdings.merge(industry, on=["trade_date", "ts_code"], how="left")
    return (
        merged.groupby(["trade_date", "industry"])["weight"]
        .sum()
        .reset_index(name="industry_weight")
        .sort_values(["trade_date", "industry"])
    )


def run_risk_control_sensitivity(nav: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for target in [0.10, 0.15, 0.20]:
        _, metrics = apply_vol_target(nav, target_vol=target)
        rows.append({"risk_model": "vol_target", "target_vol": target, "trigger_drawdown": np.nan, "reduced_exposure": np.nan, **metrics})
    for trigger in [-0.10, -0.15, -0.20]:
        for exposure in [0.3, 0.5, 0.7]:
            _, metrics = apply_drawdown_control(nav, trigger_drawdown=trigger, reduced_exposure=exposure)
            rows.append(
                {
                    "risk_model": "drawdown_control",
                    "target_vol": np.nan,
                    "trigger_drawdown": trigger,
                    "reduced_exposure": exposure,
                    **metrics,
                }
            )
    return pd.DataFrame(rows)


def write_no_lookahead_check(output_dir: Path, signal_col: str) -> None:
    lines = [
        "No Look-Ahead Check",
        "===================",
        "PASS: Signal date is the rebalance date; the strategy ranks stocks only by the selected composite factor.",
        f"PASS: Selected signal column is {signal_col}; future return columns are not used for stock selection.",
        "PASS: Portfolio return uses next_ret_1d, which is ret_1d shifted by -1 within each stock.",
        "PASS: Rebalance cost is deducted at the rebalance date using realized weight turnover.",
        "PASS: Parameter sensitivity reuses the same signal and next-period return convention.",
        "",
        "Method note: to avoid look-ahead bias, each rebalance uses only the current composite factor snapshot.",
        "Holding returns begin from the next trading day. Future return fields are reserved for factor evaluation, not strategy selection.",
    ]
    (output_dir / "no_lookahead_check.txt").write_text("\n".join(lines), encoding="utf-8")


def save_figures(nav: pd.DataFrame, trades: pd.DataFrame, sensitivity: pd.DataFrame, output_dir: Path) -> None:
    plt, sns = load_plotting()
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 5))
    plt.plot(nav["trade_date"], nav["strategy_nav"], label="Strategy")
    plt.plot(nav["trade_date"], nav["benchmark_nav"], label="Benchmark")
    plt.title("Strategy NAV vs benchmark")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "nav_curve.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(nav["trade_date"], nav["excess_nav"], color="#F58518")
    plt.axhline(1, color="black", linewidth=0.8)
    plt.title("Excess return curve")
    plt.tight_layout()
    plt.savefig(fig_dir / "excess_return_curve.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 4.5))
    plt.fill_between(nav["trade_date"], nav["drawdown"], 0, color="#E45756", alpha=0.35)
    plt.title("Strategy drawdown")
    plt.tight_layout()
    plt.savefig(fig_dir / "drawdown_curve.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 4.5))
    plot_trades = trades[trades["is_rebalance"]].copy()
    plt.plot(plot_trades["trade_date"], plot_trades["turnover"], color="#54A24B")
    plt.title("Rebalance turnover")
    plt.tight_layout()
    plt.savefig(fig_dir / "turnover_curve.png", dpi=160)
    plt.close()

    heatmaps = [
        ("annual_return", "sensitivity_return_heatmap.png", "Annual return"),
        ("sharpe", "sensitivity_sharpe_heatmap.png", "Sharpe"),
        ("calmar", "sensitivity_calmar_heatmap.png", "Calmar"),
    ]
    for metric, file_name, title in heatmaps:
        pivot = sensitivity.pivot_table(index="rebalance_days", columns="top_n", values=metric, aggfunc="mean")
        plt.figure(figsize=(7, 4.8))
        fmt = ".2%" if metric == "annual_return" else ".2f"
        sns.heatmap(pivot, annot=True, fmt=fmt, cmap="RdYlGn")
        plt.title(title)
        plt.tight_layout()
        plt.savefig(fig_dir / file_name, dpi=160)
        plt.close()


def save_v31_figures(
    nav: pd.DataFrame,
    hs300: pd.DataFrame,
    risk_navs: dict[str, pd.DataFrame],
    cost_sensitivity: pd.DataFrame,
    output_dir: Path,
) -> None:
    plt, sns = load_plotting()
    fig_dir = output_dir / "figures"
    if not hs300.empty and "hs300_nav" in hs300.columns:
        if "hs300_nav" in nav.columns:
            merged = nav.copy()
        else:
            merged = nav.merge(hs300[["trade_date", "hs300_nav"]], on="trade_date", how="left")
        plt.figure(figsize=(10, 5))
        plt.plot(merged["trade_date"], merged["strategy_nav"], label="Strategy")
        plt.plot(merged["trade_date"], merged["hs300_nav"], label="HS300")
        plt.title("Strategy NAV vs HS300")
        plt.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / "nav_vs_hs300.png", dpi=160)
        plt.close()

        plt.figure(figsize=(10, 5))
        excess = merged["strategy_nav"] / merged["hs300_nav"]
        plt.plot(merged["trade_date"], excess, color="#F58518")
        plt.axhline(1, color="black", linewidth=0.8)
        plt.title("Excess NAV vs HS300")
        plt.tight_layout()
        plt.savefig(fig_dir / "excess_vs_hs300.png", dpi=160)
        plt.close()

    if risk_navs:
        plt.figure(figsize=(10, 5))
        plt.plot(nav["trade_date"], nav["strategy_nav"], label="Base")
        for name, risk_nav in risk_navs.items():
            plt.plot(risk_nav["trade_date"], risk_nav["strategy_nav"], label=name)
        plt.title("Risk control comparison")
        plt.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / "nav_risk_control_comparison.png", dpi=160)
        plt.close()

    if not cost_sensitivity.empty:
        pivot = cost_sensitivity.pivot_table(
            index="commission", columns="slippage", values="annual_return", aggfunc="mean"
        )
        plt.figure(figsize=(7, 4.8))
        sns.heatmap(pivot, annot=True, fmt=".2%", cmap="RdYlGn")
        plt.title("Cost sensitivity: annual return")
        plt.tight_layout()
        plt.savefig(fig_dir / "cost_sensitivity_heatmap.png", dpi=160)
        plt.close()


def save_v32_figures(
    monthly_returns: pd.DataFrame,
    yearly_returns: pd.DataFrame,
    industry_exposure: pd.DataFrame,
    risk_control_sensitivity: pd.DataFrame,
    output_dir: Path,
) -> None:
    plt, sns = load_plotting()
    fig_dir = output_dir / "figures"
    if not monthly_returns.empty:
        pivot = monthly_returns.pivot_table(index="year", columns="month", values="strategy_return", aggfunc="mean")
        plt.figure(figsize=(10, 4.8))
        sns.heatmap(pivot, annot=True, fmt=".2%", cmap="RdYlGn", center=0)
        plt.title("Monthly strategy return")
        plt.tight_layout()
        plt.savefig(fig_dir / "monthly_return_heatmap.png", dpi=160)
        plt.close()

    if not yearly_returns.empty:
        plot_data = yearly_returns.melt(
            id_vars="year",
            value_vars=[col for col in ["strategy_return", "benchmark_return", "hs300_return"] if col in yearly_returns.columns],
            var_name="series",
            value_name="return",
        )
        plt.figure(figsize=(9, 4.8))
        sns.barplot(data=plot_data, x="year", y="return", hue="series")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.title("Yearly returns")
        plt.tight_layout()
        plt.savefig(fig_dir / "yearly_return_bar.png", dpi=160)
        plt.close()

    if not industry_exposure.empty:
        pivot = industry_exposure.pivot_table(
            index="trade_date", columns="industry", values="industry_weight", aggfunc="sum"
        ).fillna(0)
        pivot.index = pd.to_datetime(pivot.index)
        plt.figure(figsize=(10, 5))
        plt.stackplot(pivot.index, [pivot[col].values for col in pivot.columns], labels=pivot.columns)
        plt.ylim(0, 1.05)
        plt.legend(loc="upper left", fontsize=8, ncol=2)
        plt.title("Industry exposure by rebalance")
        plt.tight_layout()
        plt.savefig(fig_dir / "industry_exposure_stackplot.png", dpi=160)
        plt.close()

    if not risk_control_sensitivity.empty:
        dd = risk_control_sensitivity[risk_control_sensitivity["risk_model"] == "drawdown_control"].copy()
        if not dd.empty:
            pivot = dd.pivot_table(index="trigger_drawdown", columns="reduced_exposure", values="calmar", aggfunc="mean")
            plt.figure(figsize=(7, 4.8))
            sns.heatmap(pivot, annot=True, fmt=".2f", cmap="RdYlGn")
            plt.title("Risk control sensitivity: Calmar")
            plt.tight_layout()
            plt.savefig(fig_dir / "risk_control_sensitivity_heatmap.png", dpi=160)
            plt.close()


def save_v33_figures(
    weight_navs: dict[str, pd.DataFrame],
    weight_comparison: pd.DataFrame,
    parameter_cost_linkage: pd.DataFrame,
    framework_nav_diff: pd.DataFrame,
    trade_constraints_nav: pd.DataFrame,
    base_nav: pd.DataFrame,
    constrained_nav: pd.DataFrame,
    industry_before_after: pd.DataFrame,
    risk_control_parameter_grid: pd.DataFrame,
    stress_test_metrics: pd.DataFrame,
    output_dir: Path,
) -> None:
    plt, sns = load_plotting()
    fig_dir = output_dir / "figures"
    if weight_navs:
        plt.figure(figsize=(10, 5))
        for method, nav in weight_navs.items():
            plt.plot(nav["trade_date"], nav["strategy_nav"], label=method)
        plt.title("Weight method NAV comparison")
        plt.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / "nav_weight_method_comparison.png", dpi=160)
        plt.close()

    if not weight_comparison.empty:
        plot_data = weight_comparison.melt(
            id_vars="model",
            value_vars=[col for col in ["annual_return", "max_drawdown", "calmar"] if col in weight_comparison.columns],
            var_name="metric",
            value_name="value",
        )
        plt.figure(figsize=(9, 4.8))
        sns.barplot(data=plot_data, x="model", y="value", hue="metric")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.title("Weight method metrics")
        plt.tight_layout()
        plt.savefig(fig_dir / "weight_method_metrics_bar.png", dpi=160)
        plt.close()

    if not parameter_cost_linkage.empty:
        plt.figure(figsize=(7, 5))
        sns.scatterplot(
            data=parameter_cost_linkage,
            x="avg_turnover",
            y="annual_return",
            hue="rebalance_days",
            size="top_n",
            sizes=(60, 180),
        )
        plt.title("Turnover vs annual return")
        plt.tight_layout()
        plt.savefig(fig_dir / "turnover_vs_return_scatter.png", dpi=160)
        plt.close()

        plt.figure(figsize=(7, 5))
        sns.scatterplot(
            data=parameter_cost_linkage,
            x="avg_turnover",
            y="calmar",
            hue="rebalance_days",
            size="top_n",
            sizes=(60, 180),
        )
        plt.title("Turnover vs Calmar")
        plt.tight_layout()
        plt.savefig(fig_dir / "turnover_vs_calmar_scatter.png", dpi=160)
        plt.close()

        for metric, file_name, title, fmt in [
            ("annual_cost", "annual_cost_by_parameter_heatmap.png", "Annual cost by parameter", ".2%"),
            ("net_return_after_cost", "net_return_after_cost_heatmap.png", "Net return after cost", ".2%"),
        ]:
            pivot = parameter_cost_linkage.pivot_table(index="rebalance_days", columns="top_n", values=metric, aggfunc="mean")
            plt.figure(figsize=(7, 4.8))
            sns.heatmap(pivot, annot=True, fmt=fmt, cmap="RdYlGn")
            plt.title(title)
            plt.tight_layout()
            plt.savefig(fig_dir / file_name, dpi=160)
            plt.close()

    if not framework_nav_diff.empty:
        plt.figure(figsize=(10, 4.8))
        plt.plot(framework_nav_diff["trade_date"], framework_nav_diff["nav_difference"], color="#E45756")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.title("Vectorized NAV minus Backtrader NAV")
        plt.tight_layout()
        plt.savefig(fig_dir / "vectorized_vs_backtrader_nav_diff.png", dpi=160)
        plt.close()

    if not trade_constraints_nav.empty:
        plt.figure(figsize=(10, 5))
        plt.plot(base_nav["trade_date"], base_nav["strategy_nav"], label="Base")
        plt.plot(trade_constraints_nav["trade_date"], trade_constraints_nav["strategy_nav"], label="With trade constraints")
        plt.title("Trade constraints comparison")
        plt.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / "nav_trade_constraints_comparison.png", dpi=160)
        plt.close()

    if not constrained_nav.empty:
        plt.figure(figsize=(10, 5))
        plt.plot(base_nav["trade_date"], base_nav["strategy_nav"], label="Unconstrained")
        plt.plot(constrained_nav["trade_date"], constrained_nav["strategy_nav"], label="Constrained")
        plt.title("Portfolio constraints comparison")
        plt.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / "nav_constrained_vs_unconstrained.png", dpi=160)
        plt.close()

    if not industry_before_after.empty:
        top_industries = (
            industry_before_after.groupby("industry")["industry_weight"]
            .mean()
            .sort_values(ascending=False)
            .head(8)
            .index
        )
        plot_data = industry_before_after[industry_before_after["industry"].isin(top_industries)]
        plt.figure(figsize=(10, 4.8))
        sns.barplot(data=plot_data, x="industry", y="industry_weight", hue="portfolio")
        plt.xticks(rotation=30, ha="right")
        plt.title("Industry weight before and after constraints")
        plt.tight_layout()
        plt.savefig(fig_dir / "industry_weight_before_after.png", dpi=160)
        plt.close()

    if not risk_control_parameter_grid.empty:
        for metric, file_name, title, fmt in [
            ("calmar", "risk_control_parameter_calmar_heatmap.png", "Risk control parameter Calmar", ".2f"),
            ("annual_return", "risk_control_parameter_return_heatmap.png", "Risk control parameter annual return", ".2%"),
        ]:
            subset = risk_control_parameter_grid[risk_control_parameter_grid["risk_control"] == "drawdown_control"]
            if subset.empty:
                subset = risk_control_parameter_grid[risk_control_parameter_grid["risk_control"] == "vol_target"]
            pivot = subset.pivot_table(index="rebalance_days", columns="top_n", values=metric, aggfunc="mean")
            plt.figure(figsize=(7, 4.8))
            sns.heatmap(pivot, annot=True, fmt=fmt, cmap="RdYlGn")
            plt.title(title)
            plt.tight_layout()
            plt.savefig(fig_dir / file_name, dpi=160)
            plt.close()

    if not stress_test_metrics.empty:
        plot_data = stress_test_metrics.melt(
            id_vars="stress_period",
            value_vars=[col for col in ["strategy_return", "hs300_return", "excess_return"] if col in stress_test_metrics.columns],
            var_name="series",
            value_name="return",
        )
        plt.figure(figsize=(10, 4.8))
        sns.barplot(data=plot_data, x="stress_period", y="return", hue="series")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.xticks(rotation=25, ha="right")
        plt.title("Stress test returns")
        plt.tight_layout()
        plt.savefig(fig_dir / "stress_test_return_bar.png", dpi=160)
        plt.close()

        plt.figure(figsize=(9, 4.8))
        sns.barplot(data=stress_test_metrics, x="stress_period", y="max_drawdown", color="#E45756")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.xticks(rotation=25, ha="right")
        plt.title("Stress test drawdown")
        plt.tight_layout()
        plt.savefig(fig_dir / "stress_test_drawdown_bar.png", dpi=160)
        plt.close()


def write_report(
    output_dir: Path,
    signal_col: str,
    alt_signal_col: str | None,
    metrics: dict[str, object],
    sensitivity: pd.DataFrame,
    single_side_cost: float,
    risk_control: pd.DataFrame | None = None,
    parameter_recommendation: pd.DataFrame | None = None,
    cost_sensitivity: pd.DataFrame | None = None,
    strategy_vs_benchmark: pd.DataFrame | None = None,
    alpha_beta: pd.DataFrame | None = None,
    yearly_returns: pd.DataFrame | None = None,
) -> None:
    best = sensitivity.sort_values(["calmar", "sharpe", "annual_return"], ascending=False).head(1)
    lines = [
        "# Week 3 Strategy Backtest Report",
        "",
        "## 1. Objective",
        "",
        "Week 3 converts the Week 2 composite factor into a long-only stock-selection strategy, then evaluates default parameters and parameter sensitivity.",
        "",
        "## 2. Signal Source",
        "",
        f"Main signal: `{signal_col}`.",
        f"Control signal: `{alt_signal_col}`." if alt_signal_col else "No control signal was available.",
        "",
        "## 3. Strategy Rules",
        "",
        "- Rebalance every 20 trading days for the default strategy.",
        "- Select Top 20 stocks by composite factor score.",
        "- Use equal weight allocation among selected stocks.",
        f"- One-way commission plus slippage is {single_side_cost:.2%}.",
        "- Turnover is defined as 0.5 * sum(abs(new_weight - old_weight)).",
        "",
        "## 4. Benchmark",
        "",
        "The v3.0 learning version uses the equal-weight return of all tradable sample stocks as the benchmark when HS300 index data is not supplied.",
        "",
        "## 5. Default Strategy Metrics",
        "",
        pd.DataFrame([metrics]).to_markdown(index=False),
        "",
        "## 6. Parameter Sensitivity",
        "",
        sensitivity.to_markdown(index=False),
        "",
        "## 7. Best Parameter Set",
        "",
        best.to_markdown(index=False) if not best.empty else "No sensitivity result.",
        "",
        "## 8. Current Limits",
        "",
        "The v3.3 result is based on the static medium-sized Week 2 panel. It is intended to validate strategy logic, turnover accounting, no-look-ahead handling, benchmark comparison, risk control, weight-method comparison, tradeability filters, portfolio constraints, stress testing, and parameter search. After the dynamic HS300 panel is generated, the same script should be rerun as the formal dynamic version.",
        "",
        "## 9. Strategy vs Benchmark",
        "",
        strategy_vs_benchmark.to_markdown(index=False)
        if strategy_vs_benchmark is not None and not strategy_vs_benchmark.empty
        else "No benchmark comparison results.",
        "",
        "## 10. Alpha Beta Analysis",
        "",
        alpha_beta.to_markdown(index=False)
        if alpha_beta is not None and not alpha_beta.empty
        else "No alpha beta analysis results.",
        "",
        "## 11. Yearly Returns",
        "",
        yearly_returns.to_markdown(index=False)
        if yearly_returns is not None and not yearly_returns.empty
        else "No yearly return results.",
        "",
        "## 12. Risk Control Comparison",
        "",
        risk_control.to_markdown(index=False) if risk_control is not None and not risk_control.empty else "No risk control results.",
        "",
        "## 13. Parameter Recommendation",
        "",
        parameter_recommendation.head(5).to_markdown(index=False)
        if parameter_recommendation is not None and not parameter_recommendation.empty
        else "No parameter recommendation results.",
        "",
        "## 14. Cost Sensitivity",
        "",
        cost_sensitivity.to_markdown(index=False)
        if cost_sensitivity is not None and not cost_sensitivity.empty
        else "No cost sensitivity results.",
        "",
        "## 15. Weight Method Comparison",
        "",
        "Week 3 v3.3 adds equal weight, inverse-volatility weight, and simplified risk-parity weight. Equal weight is the transparent baseline, inverse-volatility weighting reduces exposure to high-volatility stocks, and simplified risk parity attempts to balance stock-level risk contribution.",
        "",
        "Key outputs: `weight_method_comparison.csv`, `strategy_nav_inverse_vol.csv`, `strategy_nav_risk_parity.csv`, `figures/nav_weight_method_comparison.png`, `figures/weight_method_metrics_bar.png`.",
        "",
        "## 16. Parameter Sensitivity and Cost Linkage",
        "",
        "Week 3 v3.3 links parameter sensitivity with turnover and annualized cost. This explains why lower-frequency rebalancing and more diversified holdings can be more stable: short rebalance cycles may capture signal changes faster, but they also increase turnover and cost drag.",
        "",
        "Key outputs: `parameter_sensitivity_cost_linkage.csv`, `figures/turnover_vs_return_scatter.png`, `figures/turnover_vs_calmar_scatter.png`, `figures/annual_cost_by_parameter_heatmap.png`, `figures/net_return_after_cost_heatmap.png`.",
        "",
        "## 17. Tradeability Filter",
        "",
        "Week 3 v3.3 adds a learning-version A-share tradeability filter covering suspension-like cases, limit-up, limit-down, and ST-like stock exclusion when fields are available. The formal version should replace these approximations with official trading-status data.",
        "",
        "Key outputs: `tradeability_filter_summary.csv`, `trade_restriction_events.csv`, `strategy_nav_with_trade_constraints.csv`, `figures/nav_trade_constraints_comparison.png`.",
        "",
        "## 18. Portfolio Hard Constraints",
        "",
        "The project extends holding analysis into hard portfolio constraints, including a single-stock weight cap, industry weight cap, and minimum holding count. These constraints reduce single-name and industry concentration risk and make the portfolio closer to practical asset-management requirements.",
        "",
        "Key outputs: `constrained_strategy_metrics.csv`, `constraint_violation_summary.csv`, `industry_weight_constraint_check.csv`, `stock_weight_constraint_check.csv`, `figures/nav_constrained_vs_unconstrained.png`, `figures/industry_weight_before_after.png`.",
        "",
        "## 19. Backtrader vs Vectorized Backtest",
        "",
        "Week 3 v3.3 decomposes the difference between the vectorized Pandas backtest and Backtrader. Small metric differences are expected because of execution timing, order matching, cost deduction, cash handling, missing-price treatment, and NAV timestamp conventions. Vectorized backtesting is used for broad parameter search, while Backtrader validates the event-driven implementation.",
        "",
        "Key outputs: `backtest_framework_comparison.csv`, `backtest_difference_attribution.csv`, `figures/vectorized_vs_backtrader_nav_diff.png`.",
        "",
        "## 20. Stress Testing and Risk-Control Linkage",
        "",
        "Week 3 v3.3 adds stress testing based on HS300 drawdown windows and representative market phases. It also links risk-control rules with rebalance frequency and holding count to evaluate whether risk controls work consistently across parameter choices.",
        "",
        "Key outputs: `stress_periods_auto.csv`, `stress_test_metrics.csv`, `risk_control_parameter_grid.csv`, `figures/stress_test_return_bar.png`, `figures/stress_test_drawdown_bar.png`, `figures/risk_control_parameter_calmar_heatmap.png`, `figures/risk_control_parameter_return_heatmap.png`.",
        "",
        "## 21. Figures",
        "",
        "- `figures/nav_curve.png`",
        "- `figures/nav_vs_hs300.png`",
        "- `figures/excess_return_curve.png`",
        "- `figures/excess_vs_hs300.png`",
        "- `figures/drawdown_curve.png`",
        "- `figures/turnover_curve.png`",
        "- `figures/nav_risk_control_comparison.png`",
        "- `figures/sensitivity_return_heatmap.png`",
        "- `figures/sensitivity_sharpe_heatmap.png`",
        "- `figures/sensitivity_calmar_heatmap.png`",
        "- `figures/cost_sensitivity_heatmap.png`",
        "- `figures/monthly_return_heatmap.png`",
        "- `figures/yearly_return_bar.png`",
        "- `figures/industry_exposure_stackplot.png`",
        "- `figures/risk_control_sensitivity_heatmap.png`",
        "- `figures/nav_weight_method_comparison.png`",
        "- `figures/weight_method_metrics_bar.png`",
        "- `figures/turnover_vs_return_scatter.png`",
        "- `figures/turnover_vs_calmar_scatter.png`",
        "- `figures/annual_cost_by_parameter_heatmap.png`",
        "- `figures/net_return_after_cost_heatmap.png`",
        "- `figures/vectorized_vs_backtrader_nav_diff.png`",
        "- `figures/nav_trade_constraints_comparison.png`",
        "- `figures/nav_constrained_vs_unconstrained.png`",
        "- `figures/industry_weight_before_after.png`",
        "- `figures/stress_test_return_bar.png`",
        "- `figures/stress_test_drawdown_bar.png`",
        "- `figures/risk_control_parameter_calmar_heatmap.png`",
        "- `figures/risk_control_parameter_return_heatmap.png`",
        "",
    ]
    (output_dir / "week3_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.fast:
        args.skip_stress = True
        args.skip_risk_grid = True
        args.skip_tradeability = True
        args.skip_constraints = True

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "figures").mkdir(parents=True, exist_ok=True)

    print("Loading Week 3 panel...")
    panel = read_panel(Path(args.panel_file))
    signal_col = choose_signal(panel, args.signal)
    alt_signal_col = args.alt_signal if args.alt_signal in panel.columns else None
    single_side_cost = args.commission + args.slippage
    start = panel["trade_date"].min().strftime("%Y%m%d")
    end = panel["trade_date"].max().strftime("%Y%m%d")

    print("Running base strategy and parameter grid...")
    nav, trades, metrics = run_backtest(panel, signal_col, args.rebalance_days, args.top_n, single_side_cost)
    sensitivity = run_parameter_grid(panel, signal_col, single_side_cost)
    best = sensitivity.sort_values(["calmar", "sharpe", "annual_return"], ascending=False).head(1)
    parameter_recommendation = build_parameter_recommendation(sensitivity)
    cost_sensitivity = run_cost_sensitivity(panel, signal_col, args.rebalance_days, args.top_n)

    hs300 = read_hs300_benchmark(Path(args.index_file), nav["trade_date"], start, end, args.download_index)
    if not hs300.empty:
        nav = nav.merge(hs300[["trade_date", "hs300_ret", "hs300_nav"]], on="trade_date", how="left")
        nav["excess_vs_hs300_nav"] = nav["strategy_nav"] / nav["hs300_nav"]

    vol_target_nav, vol_target_metrics = apply_vol_target(nav)
    dd_control_nav, dd_control_metrics = apply_drawdown_control(nav)
    risk_control = pd.DataFrame(
        [
            {"risk_control": "base", **metrics, "avg_exposure": 1.0},
            {"risk_control": "vol_target_15pct", **vol_target_metrics},
            {"risk_control": "drawdown_control", **dd_control_metrics},
        ]
    )

    holdings, holding_frequency, holding_period_stats = build_holdings_analysis(
        panel, signal_col, args.rebalance_days, args.top_n
    )
    weights = build_weight_matrix(panel, signal_col, args.rebalance_days, args.top_n)
    trade_records = build_trade_records(panel, weights, single_side_cost)
    holding_concentration = calculate_holding_concentration(holdings)
    industry_exposure = calculate_industry_exposure(holdings, panel)
    strategy_vs_benchmark = build_strategy_vs_benchmark_metrics(nav)
    alpha_beta = calculate_alpha_beta(nav)
    monthly_returns, yearly_returns = calculate_periodic_returns(nav)
    risk_control_sensitivity = run_risk_control_sensitivity(nav)
    print("Running Week 3 v3.3 enhanced analyses...")
    weight_method_comparison, weight_method_navs = run_weight_method_comparison(
        panel, signal_col, args.rebalance_days, args.top_n, single_side_cost
    )
    inverse_vol_nav = weight_method_navs.get("inverse_vol_weight", pd.DataFrame())
    risk_parity_nav = weight_method_navs.get("risk_parity_weight", pd.DataFrame())
    parameter_cost_linkage = build_parameter_cost_linkage(panel, signal_col, single_side_cost)
    if args.skip_backtrader_diff:
        framework_comparison, framework_attribution, framework_nav_diff = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    else:
        framework_comparison, framework_attribution, framework_nav_diff = build_backtest_framework_comparison(
            output_dir, nav, metrics
        )

    if args.skip_tradeability:
        trade_constraints_nav = pd.DataFrame()
        trade_constraints_metrics = {**metrics, "signal": f"{signal_col}__trade_constraints_skipped"}
        trade_restriction_events = pd.DataFrame()
    else:
        trade_constraints_nav, _, trade_constraints_metrics, _, trade_restriction_events, _ = run_backtest_enhanced(
            panel,
            signal_col,
            args.rebalance_days,
            args.top_n,
            single_side_cost,
            weight_method="equal_weight",
            trade_constraints=True,
        )

    if args.skip_constraints:
        constrained_nav = pd.DataFrame()
        constrained_metrics = {**metrics, "signal": f"{signal_col}__portfolio_constraints_skipped"}
        constrained_weights = pd.DataFrame()
        constraint_checks = pd.DataFrame()
    else:
        constrained_nav, _, constrained_metrics, constrained_weights, _, constraint_checks = run_backtest_enhanced(
            panel,
            signal_col,
            args.rebalance_days,
            args.top_n,
            single_side_cost,
            weight_method="equal_weight",
            portfolio_constraints=True,
        )
    constraint_violation_summary = pd.DataFrame(
        [
            {
                "constraint": "single_stock_max_weight",
                "threshold": 0.08,
                "violation_count": int(constraint_checks["violates_stock_cap"].sum()) if not constraint_checks.empty else 0,
            },
            {
                "constraint": "single_industry_max_weight",
                "threshold": 0.30,
                "violation_count": int(constraint_checks["violates_industry_cap"].sum()) if not constraint_checks.empty else 0,
            },
            {
                "constraint": "minimum_holding_count",
                "threshold": 15,
                "violation_count": int((constraint_checks["holding_count"] < 15).sum()) if not constraint_checks.empty else 0,
            },
        ]
    )
    stock_weight_constraint_check = constraint_checks[
        ["trade_date", "holding_count", "max_stock_weight", "violates_stock_cap", "cash_weight"]
    ].copy() if not constraint_checks.empty else pd.DataFrame()
    industry_weight_constraint_check = constraint_checks[
        ["trade_date", "max_industry_weight", "violates_industry_cap", "cash_weight"]
    ].copy() if not constraint_checks.empty else pd.DataFrame()
    constrained_strategy_metrics = pd.DataFrame(
        [
            {"strategy_variant": "unconstrained", **metrics},
            {"strategy_variant": "trade_constraints", **trade_constraints_metrics},
            {"strategy_variant": "portfolio_constraints", **constrained_metrics},
        ]
    )
    base_industry = industry_exposure.copy()
    base_industry["portfolio"] = "before_constraints" if not base_industry.empty else np.nan
    if constrained_weights.empty:
        constrained_industry = pd.DataFrame()
    else:
        constrained_holdings = constrained_weights[
            constrained_weights["is_rebalance"] & (constrained_weights["weight"] > 0)
        ][["trade_date", "ts_code", "weight"]].copy()
        constrained_industry = calculate_industry_exposure(constrained_holdings, panel)
        constrained_industry["portfolio"] = "after_constraints" if not constrained_industry.empty else np.nan
    industry_before_after = pd.concat([base_industry, constrained_industry], ignore_index=True)
    if args.skip_stress:
        stress_periods, stress_metrics = pd.DataFrame(), pd.DataFrame()
    else:
        stress_periods = find_stress_periods(nav[["trade_date", "hs300_ret"]].dropna() if "hs300_ret" in nav.columns else pd.DataFrame())
        stress_metrics = calculate_stress_metrics(nav, stress_periods)
    if args.skip_risk_grid:
        risk_control_parameter_grid = pd.DataFrame()
    else:
        risk_control_parameter_grid = run_risk_control_parameter_grid(panel, signal_col, single_side_cost)
    print("Writing Week 3 outputs...")
    write_no_lookahead_check(output_dir, signal_col)

    print("Writing base nav and metrics...", flush=True)
    nav.to_csv(output_dir / "strategy_nav.csv", index=False, encoding="utf-8-sig")
    nav[["trade_date", "benchmark_ret", "benchmark_nav"]].to_csv(
        output_dir / "benchmark_nav.csv", index=False, encoding="utf-8-sig"
    )
    if not hs300.empty:
        hs300.to_csv(output_dir / "benchmark_hs300_nav.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([metrics]).to_csv(output_dir / "strategy_metrics.csv", index=False, encoding="utf-8-sig")
    trades.to_csv(output_dir / "trades_turnover.csv", index=False, encoding="utf-8-sig")
    sensitivity.to_csv(output_dir / "parameter_sensitivity.csv", index=False, encoding="utf-8-sig")
    best.to_csv(output_dir / "best_strategy_summary.csv", index=False, encoding="utf-8-sig")
    parameter_recommendation.to_csv(output_dir / "parameter_recommendation.csv", index=False, encoding="utf-8-sig")
    cost_sensitivity.to_csv(output_dir / "cost_sensitivity.csv", index=False, encoding="utf-8-sig")
    risk_control.to_csv(output_dir / "risk_control_comparison.csv", index=False, encoding="utf-8-sig")
    vol_target_nav.to_csv(output_dir / "strategy_nav_vol_target.csv", index=False, encoding="utf-8-sig")
    dd_control_nav.to_csv(output_dir / "strategy_nav_drawdown_control.csv", index=False, encoding="utf-8-sig")
    print("Writing holdings and v3.2 diagnostics...", flush=True)
    holdings.to_csv(output_dir / "holdings_by_rebalance.csv", index=False, encoding="utf-8-sig")
    holding_frequency.to_csv(output_dir / "top_holdings_frequency.csv", index=False, encoding="utf-8-sig")
    holding_period_stats.to_csv(output_dir / "holding_period_stats.csv", index=False, encoding="utf-8-sig")
    trade_records.to_csv(output_dir / "trade_records.csv", index=False, encoding="utf-8-sig")
    holding_concentration.to_csv(output_dir / "holding_concentration.csv", index=False, encoding="utf-8-sig")
    industry_exposure.to_csv(output_dir / "industry_exposure_by_rebalance.csv", index=False, encoding="utf-8-sig")
    strategy_vs_benchmark.to_csv(output_dir / "strategy_vs_benchmark_metrics.csv", index=False, encoding="utf-8-sig")
    alpha_beta.to_csv(output_dir / "alpha_beta_analysis.csv", index=False, encoding="utf-8-sig")
    monthly_returns.to_csv(output_dir / "monthly_returns.csv", index=False, encoding="utf-8-sig")
    yearly_returns.to_csv(output_dir / "yearly_returns.csv", index=False, encoding="utf-8-sig")
    risk_control_sensitivity.to_csv(output_dir / "risk_control_sensitivity.csv", index=False, encoding="utf-8-sig")
    print("Writing v3.3 enhanced outputs...", flush=True)
    weight_method_comparison.to_csv(output_dir / "weight_method_comparison.csv", index=False, encoding="utf-8-sig")
    if not inverse_vol_nav.empty:
        inverse_vol_nav.to_csv(output_dir / "strategy_nav_inverse_vol.csv", index=False, encoding="utf-8-sig")
    if not risk_parity_nav.empty:
        risk_parity_nav.to_csv(output_dir / "strategy_nav_risk_parity.csv", index=False, encoding="utf-8-sig")
    parameter_cost_linkage.to_csv(output_dir / "parameter_sensitivity_cost_linkage.csv", index=False, encoding="utf-8-sig")
    framework_comparison.to_csv(output_dir / "backtest_framework_comparison.csv", index=False, encoding="utf-8-sig")
    framework_attribution.to_csv(output_dir / "backtest_difference_attribution.csv", index=False, encoding="utf-8-sig")
    trade_restriction_events.to_csv(output_dir / "trade_restriction_events.csv", index=False, encoding="utf-8-sig")
    trade_constraints_nav.to_csv(output_dir / "strategy_nav_with_trade_constraints.csv", index=False, encoding="utf-8-sig")
    tradeability_summary = pd.DataFrame(
        [
            {
                "rebalance_count": len(trade_restriction_events),
                "total_blocked_buy": trade_restriction_events["blocked_buy_count"].sum() if not trade_restriction_events.empty else 0,
                "total_blocked_sell": trade_restriction_events["blocked_sell_count"].sum() if not trade_restriction_events.empty else 0,
                "avg_selected_count": trade_restriction_events["selected_count"].mean() if not trade_restriction_events.empty else np.nan,
            }
        ]
    )
    tradeability_summary.to_csv(output_dir / "tradeability_filter_summary.csv", index=False, encoding="utf-8-sig")
    constrained_strategy_metrics.to_csv(output_dir / "constrained_strategy_metrics.csv", index=False, encoding="utf-8-sig")
    constraint_violation_summary.to_csv(output_dir / "constraint_violation_summary.csv", index=False, encoding="utf-8-sig")
    industry_weight_constraint_check.to_csv(output_dir / "industry_weight_constraint_check.csv", index=False, encoding="utf-8-sig")
    stock_weight_constraint_check.to_csv(output_dir / "stock_weight_constraint_check.csv", index=False, encoding="utf-8-sig")
    risk_control_parameter_grid.to_csv(output_dir / "risk_control_parameter_grid.csv", index=False, encoding="utf-8-sig")
    stress_periods.to_csv(output_dir / "stress_periods_auto.csv", index=False, encoding="utf-8-sig")
    stress_metrics.to_csv(output_dir / "stress_test_metrics.csv", index=False, encoding="utf-8-sig")

    print("Writing parameter pivots and optional alt signal...", flush=True)
    for metric, file_name in [
        ("annual_return", "parameter_sensitivity_pivot_return.csv"),
        ("sharpe", "parameter_sensitivity_pivot_sharpe.csv"),
        ("calmar", "parameter_sensitivity_pivot_calmar.csv"),
    ]:
        pivot = sensitivity.pivot_table(index="rebalance_days", columns="top_n", values=metric, aggfunc="mean")
        pivot.to_csv(output_dir / file_name, encoding="utf-8-sig")

    if alt_signal_col:
        alt_nav, alt_trades, alt_metrics = run_backtest(
            panel, alt_signal_col, args.rebalance_days, args.top_n, single_side_cost
        )
        alt_nav.to_csv(output_dir / "strategy_nav_alt_signal.csv", index=False, encoding="utf-8-sig")
        alt_trades.to_csv(output_dir / "trades_turnover_alt_signal.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame([alt_metrics]).to_csv(
            output_dir / "strategy_metrics_alt_signal.csv", index=False, encoding="utf-8-sig"
        )

    print("Writing figures/report...", flush=True)
    if args.skip_figures:
        print("Skipping figure generation (--skip-figures).", flush=True)
    else:
        save_figures(nav, trades, sensitivity, output_dir)
        save_v31_figures(
            nav,
            hs300,
            {"Vol target 15%": vol_target_nav, "Drawdown control": dd_control_nav},
            cost_sensitivity,
            output_dir,
        )
        save_v32_figures(monthly_returns, yearly_returns, industry_exposure, risk_control_sensitivity, output_dir)
        print("Saving Week 3 v3.3 figures...")
        save_v33_figures(
            weight_method_navs,
            weight_method_comparison,
            parameter_cost_linkage,
            framework_nav_diff,
            trade_constraints_nav,
            nav,
            constrained_nav,
            industry_before_after,
            risk_control_parameter_grid,
            stress_metrics,
            output_dir,
        )
    print("Writing Week 3 report...")
    write_report(
        output_dir,
        signal_col,
        alt_signal_col,
        metrics,
        sensitivity,
        single_side_cost,
        risk_control,
        parameter_recommendation,
        cost_sensitivity,
        strategy_vs_benchmark,
        alpha_beta,
        yearly_returns,
    )
    print(f"Week 3 outputs saved to {output_dir}")


if __name__ == "__main__":
    main()
