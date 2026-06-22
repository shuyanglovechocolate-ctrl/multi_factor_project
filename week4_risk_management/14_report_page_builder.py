"""Build a 12-page report material index for Week 4 v4.1."""

from pathlib import Path

import pandas as pd


PAGE_PLAN = [
    (1, "Week 4 研究目标与框架", "说明风险管理与报告撰写模块如何承接 Week 1-3。"),
    (2, "数据来源与样本限制", "列出输入数据、静态样本限制和动态股票池待补事项。"),
    (3, "基础风险收益表现", "展示策略、样本等权基准和沪深300的收益风险对比。"),
    (4, "市场效应与 Beta 风险", "显性化市场效应、Alpha/Beta、滚动 Beta 和上下行捕获率。"),
    (5, "Brinson 归因方法与总结果", "解释市场、行业配置、选股和交互效应的收益拆解。"),
    (6, "年度与行业归因", "展示 Brinson 年度和行业维度结果。"),
    (7, "极端行情压力测试总览", "汇总极端事件日历、数据可用性和压力得分。"),
    (8, "2020 疫情冲击分析", "重点分析当前样本覆盖的 2020 疫情冲击阶段。"),
    (9, "2015 股灾数据限制与预留分析", "说明当前静态样本不覆盖 2015，保留事件框架等待动态数据重跑。"),
    (10, "行业暴露、集中度与换手率风险", "复盘组合风险暴露、持仓集中度和交易成本压力。"),
    (11, "风控模拟与策略改进建议", "展示止损、仓位控制、动态因子权重和改进建议评分。"),
    (12, "总结、局限性与后续优化", "总结 Week 4 发现，并连接动态股票池正式版和完整报告。"),
]


TABLE_MAP = {
    2: ["data_quality_check.csv", "extreme_event_availability.csv"],
    3: ["risk_metrics_summary.csv"],
    4: ["market_effect_summary.csv", "alpha_beta_summary.csv", "rolling_beta.csv", "up_down_capture.csv"],
    5: ["total_return_decomposition.csv", "brinson_total.csv"],
    6: ["brinson_by_year.csv", "brinson_by_industry.csv"],
    7: ["extreme_event_diagnostics.csv", "extreme_event_stress_score.csv"],
    8: ["extreme_market_test.csv"],
    9: ["extreme_event_availability.csv"],
    10: ["risk_exposure_industry.csv", "risk_exposure_holding_concentration.csv", "risk_exposure_turnover.csv"],
    11: ["risk_control_comparison.csv", "dynamic_factor_weight_proposal.csv", "improvement_priority_score.csv"],
    12: ["strategy_improvement_list_v4_1.csv"],
}


CHART_MAP = {
    3: ["nav_comparison.png", "drawdown_curve.png"],
    4: ["market_effect_decomposition.png", "rolling_beta.png", "up_down_capture.png"],
    5: ["brinson_stack_chart.png"],
    7: ["extreme_event_score_bar.png", "extreme_event_return_drawdown.png"],
    8: ["extreme_market_2020_covid_shock.png"],
    10: [],
    11: ["risk_control_nav_comparison.png", "risk_control_drawdown_comparison.png", "dynamic_factor_weight.png", "improvement_priority_matrix.png"],
}


def build_report_page_index() -> pd.DataFrame:
    rows = []
    for page, title, conclusion in PAGE_PLAN:
        rows.append(
            {
                "page": page,
                "page_title": title,
                "core_message": conclusion,
                "tables": "; ".join(TABLE_MAP.get(page, [])),
                "charts": "; ".join(CHART_MAP.get(page, [])),
            }
        )
    return pd.DataFrame(rows)


def build_material_checklist(page_index: pd.DataFrame, table_dir: Path, chart_dir: Path) -> pd.DataFrame:
    rows = []
    for _, row in page_index.iterrows():
        for table in [x.strip() for x in str(row["tables"]).split(";") if x.strip()]:
            rows.append({"page": row["page"], "material_type": "table", "material": table, "exists": (table_dir / table).exists()})
        for chart in [x.strip() for x in str(row["charts"]).split(";") if x.strip()]:
            rows.append({"page": row["page"], "material_type": "chart", "material": chart, "exists": (chart_dir / chart).exists()})
    return pd.DataFrame(rows)


def export_report_outline_md(page_index: pd.DataFrame, checklist: pd.DataFrame, report_dir: Path) -> Path:
    lines = [
        "# Week 4 12 Page Report Outline",
        "",
        "本文件不是完整 12 页报告，而是后续撰写报告或制作 PPT 的页面材料索引。",
        "",
    ]
    for _, row in page_index.iterrows():
        lines.extend(
            [
                f"## Page {int(row['page'])}: {row['page_title']}",
                "",
                f"核心结论：{row['core_message']}",
                "",
                f"建议表格：{row['tables'] or '无'}",
                "",
                f"建议图表：{row['charts'] or '无'}",
                "",
            ]
        )
    missing = checklist[checklist["exists"] == False]
    lines.extend(["## Material Gaps", ""])
    if missing.empty:
        lines.append("当前页面索引中的材料均已生成。")
    else:
        for _, row in missing.iterrows():
            lines.append(f"- Page {row['page']} 缺少 {row['material_type']}: `{row['material']}`")
    out = report_dir / "Week4_12Page_Report_Outline.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def run_report_page_builder(config) -> dict[str, pd.DataFrame | Path]:
    page_index = build_report_page_index()
    checklist = build_material_checklist(page_index, config.TABLE_DIR, config.CHART_DIR)
    outline = export_report_outline_md(page_index, checklist, config.REPORT_DIR)
    page_index.to_csv(config.REPORT_DIR / "Week4_Report_Page_Index.csv", index=False, encoding="utf-8-sig")
    checklist.to_csv(config.REPORT_DIR / "Week4_Report_Material_Checklist.csv", index=False, encoding="utf-8-sig")
    return {
        "page_index": page_index,
        "material_checklist": checklist,
        "outline_path": outline,
    }
