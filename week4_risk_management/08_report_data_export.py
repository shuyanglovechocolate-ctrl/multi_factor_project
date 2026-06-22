"""Export Week 4 tables and a concise report-material summary."""

from pathlib import Path

import pandas as pd


def save_tables(tables: dict[str, pd.DataFrame], table_dir: Path) -> list[Path]:
    paths = []
    for name, df in tables.items():
        if df is None or df.empty:
            continue
        path = table_dir / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        paths.append(path)
    return paths


def write_summary_md(table_paths: list[Path], chart_paths: list[Path], report_dir: Path) -> Path:
    lines = [
        "# Week 4 Analysis Summary",
        "",
        "本文件用于汇总 Week 4 风险管理与报告撰写模块的可交付材料。",
        "",
        "## 研究覆盖范围",
        "",
        "- 基础风险指标复盘：收益、波动、Sharpe、最大回撤、Calmar、胜率。",
        "- Brinson 收益归因：配置效应、选择效应、交互效应。",
        "- 市场效应分析：市场收益贡献、Alpha/Beta、滚动 Beta、上下行捕获率。",
        "- 极端行情压力测试：2015 股灾、2020 疫情冲击，并预留 2016、2018、2021-2022、2023 阶段。",
        "- 极端事件诊断：事件可用性、压力得分、自动文字解读和数据限制说明。",
        "- 动态因子权重：基于 Rank IC / ICIR 生成权重建议。",
        "- 风控模拟：组合止损、波动率目标、均线择时、固定仓位对照。",
        "- 风险暴露分析：行业暴露、持仓集中度、换手率。",
        "- 策略改进建议：风险发现映射、优先级评分、12 页报告材料索引。",
        "",
        "## 输出表格",
        "",
    ]
    if table_paths:
        lines.extend([f"- `{path.name}`" for path in table_paths])
    else:
        lines.append("- 暂无表格输出。")

    lines.extend(["", "## 输出图表", ""])
    if chart_paths:
        lines.extend([f"- `{path.name}`" for path in chart_paths])
    else:
        lines.append("- 暂无图表输出。")

    lines.extend(
        [
            "",
            "## 报告写作提示",
            "",
            "当前 Week 4 模块先作为研究步骤与代码框架，不展开完整 12 页报告。",
            "后续正式报告可以直接引用本目录生成的表格、图表和策略改进清单。",
            "",
        ]
    )
    out = report_dir / "Week4_Analysis_Summary.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
