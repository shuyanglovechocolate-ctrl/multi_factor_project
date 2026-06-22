"""Week 4 risk management configuration.

This module keeps paths and research assumptions in one place.  The filenames
keep the week-order prefix for report readability, so main_week4.py loads
modules with importlib instead of normal Python imports.
"""

from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parent

WEEK2_DIR = PROJECT_ROOT / "outputs" / "week2"
WEEK3_DIR = PROJECT_ROOT / "outputs" / "week3"

OUTPUT_DIR = MODULE_DIR / "output"
TABLE_DIR = OUTPUT_DIR / "tables"
CHART_DIR = OUTPUT_DIR / "charts"
REPORT_DIR = OUTPUT_DIR / "report_materials"

WEEK2_PANEL_FILE = WEEK2_DIR / "composite_factor_panel.csv"
STRATEGY_NAV_FILE = WEEK3_DIR / "strategy_nav.csv"
BENCHMARK_NAV_FILE = WEEK3_DIR / "benchmark_nav.csv"
HS300_NAV_FILE = WEEK3_DIR / "benchmark_hs300_nav.csv"
HOLDINGS_FILE = WEEK3_DIR / "holdings_by_rebalance.csv"
INDUSTRY_EXPOSURE_FILE = WEEK3_DIR / "industry_exposure_by_rebalance.csv"
TURNOVER_FILE = WEEK3_DIR / "trades_turnover.csv"
TRADE_RECORDS_FILE = WEEK3_DIR / "trade_records.csv"

RISK_FREE_RATE = 0.02
TRADING_DAYS = 252

EXTREME_PERIODS = {
    "2015_stock_market_crash": ("2015-06-12", "2015-08-26"),
    "2016_circuit_breaker": ("2016-01-04", "2016-02-29"),
    "2018_bear_market": ("2018-01-29", "2018-12-31"),
    "2020_covid_shock": ("2020-02-03", "2020-03-23"),
    "2021_2022_growth_adjustment": ("2021-02-18", "2022-04-26"),
    "2023_style_rotation": ("2023-01-01", "2023-12-31"),
}

IMPROVEMENT_TOPICS = [
    "dynamic_factor_weight",
    "stop_loss_control",
    "volatility_target_position",
    "industry_weight_constraint",
    "single_stock_weight_constraint",
    "turnover_cost_control",
    "liquidity_and_tradeability_filter",
]

# =========================
# Week 4 v4.1 Enhanced Config
# =========================

ENABLE_MARKET_EFFECT_ANALYSIS = True
ENABLE_EXTREME_EVENT_DIAGNOSTICS = True
ENABLE_FACTOR_DYNAMIC_WEIGHT = True
ENABLE_RISK_CONTROL_SIMULATION = True
ENABLE_IMPROVEMENT_SCORING = True
ENABLE_REPORT_PAGE_BUILDER = True

ROLLING_BETA_WINDOW = 60
ROLLING_IC_WINDOW = 60

FACTOR_COLS = [
    "factor_momentum",
    "factor_volatility",
    "factor_turnover",
    "factor_size",
    "factor_reversal_5d",
]
FUTURE_RETURN_COL = "ret_20d_fwd"

STOP_LOSS_LEVELS = [-0.05, -0.08, -0.10, -0.15]
REDUCE_POSITION_LEVELS = [0.3, 0.5, 0.8]
POSITION_LEVELS = [1.0, 0.8, 0.6, 0.4]
MA_WINDOWS = [20, 60, 120]

STRESS_SCORE_WEIGHTS = {
    "drawdown": 0.40,
    "volatility": 0.25,
    "loss": 0.25,
    "recovery_days": 0.10,
}

IMPROVEMENT_SCORE_WEIGHTS = {
    "impact": 0.40,
    "urgency": 0.30,
    "feasibility": 0.30,
}


def ensure_output_dirs() -> None:
    for path in (OUTPUT_DIR, TABLE_DIR, CHART_DIR, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
