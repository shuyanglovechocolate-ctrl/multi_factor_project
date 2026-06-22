"""Run the Week 4 risk management research scaffold."""

from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent


def load_module(file_stem: str):
    path = MODULE_DIR / f"{file_stem}.py"
    spec = importlib.util.spec_from_file_location(file_stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    config = load_module("00_config")
    data_loader = load_module("01_data_loader")
    risk_metrics = load_module("02_risk_metrics")
    brinson = load_module("03_brinson_attribution")
    extreme = load_module("04_extreme_market_test")
    exposure = load_module("05_risk_exposure")
    improvement = load_module("06_strategy_improvement")
    visualization = load_module("07_visualization")
    exporter = load_module("08_report_data_export")
    market_effect = load_module("09_market_effect_analysis")
    event_diagnostics = load_module("10_extreme_event_diagnostics")
    factor_dynamic_weight = load_module("11_factor_dynamic_weight_analysis")
    risk_control = load_module("12_risk_control_simulator")
    improvement_scoring = load_module("13_improvement_scoring")
    report_page_builder = load_module("14_report_page_builder")

    config.ensure_output_dirs()

    data = data_loader.load_all_data(config)
    return_frame = data_loader.build_return_frame(data)

    risk_metrics_summary = risk_metrics.run_risk_metrics(return_frame, config)
    extreme_market_test = extreme.run_extreme_market_test(return_frame, config)

    tables = {
        "data_quality_check": data_loader.check_data_quality(data),
        "risk_metrics_summary": risk_metrics_summary,
        "extreme_market_test": extreme_market_test,
        "strategy_improvement_list": improvement.build_strategy_improvement_list(),
    }

    brinson_outputs = brinson.run_brinson_attribution(data)
    tables.update(
        {
            "brinson_total": brinson_outputs.get("brinson_total"),
            "brinson_by_year": brinson_outputs.get("brinson_by_year"),
            "brinson_by_industry": brinson_outputs.get("brinson_by_industry"),
        }
    )

    exposure_outputs = exposure.run_risk_exposure(data)
    tables.update(
        {
            "risk_exposure_industry": exposure_outputs.get("industry_exposure_summary"),
            "risk_exposure_holding_concentration": exposure_outputs.get("holding_concentration_summary"),
            "risk_exposure_turnover": exposure_outputs.get("turnover_summary"),
        }
    )

    chart_paths = []

    if config.ENABLE_MARKET_EFFECT_ANALYSIS:
        market_effect_outputs, market_charts = market_effect.run_market_effect_analysis(return_frame, brinson_outputs, config)
        tables.update(market_effect_outputs)
        chart_paths.extend(market_charts)
    else:
        market_effect_outputs = {}

    if config.ENABLE_EXTREME_EVENT_DIAGNOSTICS:
        extreme_diag_outputs, extreme_diag_charts = event_diagnostics.run_extreme_event_diagnostics(return_frame, config)
        tables.update(extreme_diag_outputs)
        chart_paths.extend(extreme_diag_charts)
    else:
        extreme_diag_outputs = {}

    if config.ENABLE_FACTOR_DYNAMIC_WEIGHT:
        factor_outputs, factor_charts = factor_dynamic_weight.run_factor_dynamic_weight_analysis(
            data.get("factor_panel"),
            config,
        )
        tables.update(factor_outputs)
        chart_paths.extend(factor_charts)
    else:
        factor_outputs = {}

    if config.ENABLE_RISK_CONTROL_SIMULATION:
        risk_control_outputs, risk_control_charts = risk_control.run_risk_control_simulation(return_frame, config)
        tables.update(risk_control_outputs)
        chart_paths.extend(risk_control_charts)
    else:
        risk_control_outputs = {}

    if config.ENABLE_IMPROVEMENT_SCORING:
        scored_outputs, scored_charts = improvement_scoring.run_improvement_scoring(
            risk_metrics_summary,
            market_effect_outputs,
            extreme_diag_outputs,
            exposure_outputs,
            factor_outputs,
            risk_control_outputs,
            config,
        )
        tables.update(scored_outputs)
        chart_paths.extend(scored_charts)

    chart_paths.extend(
        visualization.run_visualizations(
            return_frame,
            brinson_outputs,
            tables["extreme_market_test"],
            config,
        )
    )
    table_paths = exporter.save_tables(tables, config.TABLE_DIR)

    if config.ENABLE_REPORT_PAGE_BUILDER:
        report_page_builder.run_report_page_builder(config)

    summary_path = exporter.write_summary_md(table_paths, chart_paths, config.REPORT_DIR)

    print(f"Week 4 tables: {len(table_paths)}")
    print(f"Week 4 charts: {len(chart_paths)}")
    print(f"Week 4 summary: {summary_path}")


if __name__ == "__main__":
    main()
