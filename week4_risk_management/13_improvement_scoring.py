"""Score and rank Week 4 strategy improvement proposals."""

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def map_risk_findings_to_improvements(
    risk_metrics: pd.DataFrame,
    market_effect: dict[str, pd.DataFrame],
    extreme_diagnostics: dict[str, pd.DataFrame],
    exposure_results: dict[str, pd.DataFrame],
    factor_results: dict[str, pd.DataFrame],
    risk_control_results: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    strategy_row = risk_metrics[risk_metrics.get("series", "") == "strategy"].head(1)
    max_dd = strategy_row["max_drawdown"].iloc[0] if not strategy_row.empty and "max_drawdown" in strategy_row else np.nan
    beta = np.nan
    alpha_beta = market_effect.get("alpha_beta_summary", pd.DataFrame())
    if not alpha_beta.empty and "beta" in alpha_beta:
        beta = alpha_beta["beta"].iloc[0]
    factor_weights = factor_results.get("dynamic_factor_weight_proposal", pd.DataFrame())
    top_factor = factor_weights["factor"].iloc[0] if not factor_weights.empty else "N/A"

    rows = [
        {
            "improvement_id": "IMP001",
            "improvement_name": "动态因子权重",
            "risk_evidence": f"滚动 IC 显示因子有效性阶段性变化，当前建议最高权重因子为 {top_factor}。",
            "related_module": "11_factor_dynamic_weight_analysis",
            "current_problem": "固定权重难以适应因子阶段性失效。",
            "proposed_method": "使用滚动 Rank IC / ICIR 调整因子权重。",
            "expected_effect": "提升信号稳定性，降低单一风格失效风险。",
            "impact_score": 4.5,
            "urgency_score": 4.2,
            "feasibility_score": 4.0,
            "report_page": 11,
        },
        {
            "improvement_id": "IMP002",
            "improvement_name": "组合止损与仓位控制",
            "risk_evidence": f"当前策略最大回撤约 {max_dd:.2%}。" if np.isfinite(max_dd) else "当前策略存在回撤控制需求。",
            "related_module": "12_risk_control_simulator",
            "current_problem": "极端行情下净值回撤较深。",
            "proposed_method": "组合回撤触发降仓，并结合波动率目标控制仓位。",
            "expected_effect": "降低最大回撤，改善 Calmar。",
            "impact_score": 4.7,
            "urgency_score": 4.6,
            "feasibility_score": 4.1,
            "report_page": 11,
        },
        {
            "improvement_id": "IMP003",
            "improvement_name": "市场状态识别",
            "risk_evidence": f"策略相对沪深300 Beta 为 {beta:.2f}。" if np.isfinite(beta) else "需要监控市场暴露。",
            "related_module": "09_market_effect_analysis",
            "current_problem": "市场效应和系统性风险需要显性化监控。",
            "proposed_method": "基于滚动 Beta、均线和波动率识别市场状态。",
            "expected_effect": "在高风险市场降低仓位或切换防御配置。",
            "impact_score": 4.0,
            "urgency_score": 3.8,
            "feasibility_score": 3.8,
            "report_page": 4,
        },
        {
            "improvement_id": "IMP004",
            "improvement_name": "行业权重约束",
            "risk_evidence": "行业暴露表用于识别单一行业集中。",
            "related_module": "05_risk_exposure",
            "current_problem": "行业集中可能导致风格切换风险。",
            "proposed_method": "设置单行业权重上限，并监控行业主动暴露。",
            "expected_effect": "降低行业拥挤和结构性行情回撤。",
            "impact_score": 3.9,
            "urgency_score": 3.7,
            "feasibility_score": 4.2,
            "report_page": 10,
        },
        {
            "improvement_id": "IMP005",
            "improvement_name": "换手率与成本控制",
            "risk_evidence": "换手率表用于评估交易成本压力。",
            "related_module": "05_risk_exposure",
            "current_problem": "较高调仓频率可能侵蚀收益。",
            "proposed_method": "加入调仓缓冲区，优先选择低成本参数组合。",
            "expected_effect": "降低交易成本，提升净收益稳定性。",
            "impact_score": 3.8,
            "urgency_score": 4.0,
            "feasibility_score": 4.3,
            "report_page": 10,
        },
    ]
    return pd.DataFrame(rows)


def score_improvement_items(items: pd.DataFrame, config) -> pd.DataFrame:
    if items.empty:
        return pd.DataFrame()
    w = config.IMPROVEMENT_SCORE_WEIGHTS
    df = items.copy()
    df["priority_score"] = (
        df["impact_score"] * w["impact"]
        + df["urgency_score"] * w["urgency"]
        + df["feasibility_score"] * w["feasibility"]
    )
    df["priority_level"] = pd.cut(
        df["priority_score"],
        bins=[-np.inf, 2.8, 3.5, 4.2, np.inf],
        labels=["低", "中", "中高", "高"],
    )
    return df.sort_values("priority_score", ascending=False)


def _plot_priority_matrix(scored: pd.DataFrame, chart_dir: Path) -> Path | None:
    if scored.empty:
        return None
    fig, ax = plt.subplots(figsize=(7, 5))
    scatter = ax.scatter(scored["feasibility_score"], scored["impact_score"], s=scored["urgency_score"] * 60)
    for _, row in scored.iterrows():
        ax.annotate(row["improvement_id"], (row["feasibility_score"], row["impact_score"]), xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("Feasibility")
    ax.set_ylabel("Impact")
    ax.set_title("Improvement Priority Matrix")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out = chart_dir / "improvement_priority_matrix.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def run_improvement_scoring(
    risk_metrics: pd.DataFrame,
    market_effect: dict[str, pd.DataFrame],
    extreme_diagnostics: dict[str, pd.DataFrame],
    exposure_results: dict[str, pd.DataFrame],
    factor_results: dict[str, pd.DataFrame],
    risk_control_results: dict[str, pd.DataFrame],
    config,
) -> tuple[dict[str, pd.DataFrame], list[Path]]:
    mapping = map_risk_findings_to_improvements(
        risk_metrics,
        market_effect,
        extreme_diagnostics,
        exposure_results,
        factor_results,
        risk_control_results,
    )
    scored = score_improvement_items(mapping, config)
    chart = _plot_priority_matrix(scored, config.CHART_DIR)
    return (
        {
            "risk_to_improvement_mapping": mapping,
            "strategy_improvement_list_v4_1": scored,
            "improvement_priority_score": scored[[
                "improvement_id",
                "improvement_name",
                "impact_score",
                "urgency_score",
                "feasibility_score",
                "priority_score",
                "priority_level",
                "report_page",
            ]],
        },
        [chart] if chart is not None else [],
    )
