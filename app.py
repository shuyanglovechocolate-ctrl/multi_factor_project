from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "outputs" / "week1"
FIG_DIR = OUT_DIR / "figures"
WEEK2_DIR = BASE_DIR / "outputs" / "week2"
WEEK2_FIG_DIR = WEEK2_DIR / "figures"
WEEK3_DIR = BASE_DIR / "outputs" / "week3"
WEEK3_FIG_DIR = WEEK3_DIR / "figures"
WEEK4_DIR = BASE_DIR / "week4_risk_management" / "output"
WEEK4_TABLE_DIR = WEEK4_DIR / "tables"
WEEK4_FIG_DIR = WEEK4_DIR / "charts"
WEEK4_REPORT_DIR = WEEK4_DIR / "report_materials"
DATA_DIR = BASE_DIR / "data" / "processed"

VALID_FACTORS = [
    "factor_momentum",
    "factor_volatility",
    "factor_turnover",
    "factor_size",
    "factor_reversal_5d",
]

ALL_FACTORS = [
    *VALID_FACTORS,
    "factor_roe",
]


st.set_page_config(
    page_title="多因子选股策略 Dashboard",
    page_icon="📈",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def read_csv_safe(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def read_text_safe(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def show_dataframe(title: str, df: pd.DataFrame) -> None:
    st.subheader(title)
    if df.empty:
        st.warning(f"未找到数据：{title}")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


def show_image(path: Path, caption: str | None = None) -> None:
    if path.exists():
        st.image(str(path), caption=caption or path.name, use_container_width=True)
    else:
        st.info(f"未找到图表：{path.name}")


def format_percent(value: float) -> str:
    if pd.isna(value):
        return "NA"
    return f"{value:.2%}"


def method_from_model(model: str) -> str:
    mapping = {
        "composite_equal": "equal_weight",
        "composite_equal_size_neutral": "equal_weight_size_neutral",
        "composite_equal_industry_size_neutral": "equal_weight_industry_size_neutral",
        "composite_equal_neutral": "equal_weight_neutral",
        "composite_ic_weight": "ic_weight",
        "composite_ic_weight_size_neutral": "ic_weight_size_neutral",
        "composite_ic_weight_industry_size_neutral": "ic_weight_industry_size_neutral",
        "composite_ic_weight_neutral": "ic_weight_neutral",
        "composite_pca": "pca",
        "composite_pca_size_neutral": "pca_size_neutral",
        "composite_pca_industry_size_neutral": "pca_industry_size_neutral",
        "composite_pca_neutral": "pca_neutral",
        "composite_rolling_ic_weight": "rolling_ic_weight",
        "composite_rolling_ic_weight_size_neutral": "rolling_ic_weight_size_neutral",
        "composite_rolling_ic_weight_industry_size_neutral": "rolling_ic_weight_industry_size_neutral",
    }
    return mapping.get(model, model.replace("composite_", ""))


st.title("多因子选股策略研究 Dashboard")
st.caption("Week 1 - Week 4：数据获取、因子探索、多因子模型、策略回测与风险管理")

page = st.sidebar.radio(
    "选择页面",
    [
        "项目总览",
        "数据质量",
        "单因子分析",
        "分组回测",
        "Week 2 因子相关性",
        "Week 2 综合因子",
        "Week 2 分层回测",
        "Week 3 策略回测",
        "Week 4 风险管理",
        "图表中心",
    ],
)

factor_panel = read_csv_safe(DATA_DIR / "factor_panel.csv")


if page == "项目总览":
    st.header("项目总览")

    col1, col2, col3, col4, col5 = st.columns(5)

    if factor_panel.empty:
        st.warning("未找到 data/processed/factor_panel.csv")
    else:
        stock_count = factor_panel["ts_code"].nunique()
        row_count = len(factor_panel)
        start_date = factor_panel["trade_date"].min()
        end_date = factor_panel["trade_date"].max()
        valid_factor_count = sum(
            col in factor_panel.columns and factor_panel[col].notna().sum() > 0 for col in VALID_FACTORS
        )
        figure_count = (
            len(list(FIG_DIR.glob("*.png")))
            + len(list(WEEK2_FIG_DIR.glob("*.png")))
            + len(list(WEEK3_FIG_DIR.glob("*.png")))
            + len(list(WEEK4_FIG_DIR.glob("*.png")))
        )

        col1.metric("股票数量", stock_count)
        col2.metric("样本行数", f"{row_count:,}")
        col3.metric("有效因子", valid_factor_count)
        col4.metric("图表数量", figure_count)
        col5.metric("版本状态", "Week 4 v4.1")

        st.info(f"数据区间：{start_date} 至 {end_date}")

    st.markdown(
        """
        ### 项目说明

        本项目目标是基于量价和可获得的基础因子，构建 A 股沪深300股票池内的多因子选股研究流程。

        当前 Week 1 已完成 AKShare 前复权行情数据获取、数据清洗、因子面板构建、5 个有效候选因子、
        IC / Rank IC / 显著性检验、分组回测、数据质量检查和可视化输出。

        当前 Week 2 已完成因子相关性分析、显式冗余剔除决策、等权 / IC 加权 / PCA / 滚动 IC 综合因子、
        行业 + 市值中性化、五分组回测、单调性检查和交易成本估算。

        当前 Week 3 已完成基于 Week 2 最优综合因子的 Top N 等权组合策略回测、Backtrader 兼容验证、
        交易成本和滑点扣减、无未来函数检查、样本等权基准与沪深300指数基准对比、Alpha / Beta 分析、
        月度与年度收益分析、风险控制版本、持仓集中度、行业暴露、交易明细、交易成本敏感性分析，
        调仓周期 / 持股数量参数敏感性分析，并已完成 v3.3 的权重方法对照、交易可行性过滤、
        组合硬约束、压力测试、风控参数联动和回测框架差异拆解。

        当前 Week 4 已完成 v4.1 风险归因、极端行情诊断与策略改进增强版，覆盖市场效应显性化、
        Brinson 归因、Alpha / Beta、滚动 Beta、上下行捕获率、极端事件诊断、动态因子权重、
        风控模拟、改进建议评分和 12 页报告材料索引。

        由于 Tushare token 权限限制，ROE 因子暂作为正式版扩展项；当前有效因子为动量、波动率、
        换手率、市值近似和短期反转。
        """
    )

    report_text = read_text_safe(OUT_DIR / "week1_report.md")
    if report_text:
        with st.expander("查看自动生成的 Week 1 报告"):
            st.markdown(report_text)

    week2_report = read_text_safe(WEEK2_DIR / "week2_report.md")
    if week2_report:
        with st.expander("查看自动生成的 Week 2 报告"):
            st.markdown(week2_report)

    week3_report = read_text_safe(WEEK3_DIR / "week3_report.md")
    if week3_report:
        with st.expander("查看自动生成的 Week 3 报告"):
            st.markdown(week3_report)

    week4_summary = read_text_safe(WEEK4_REPORT_DIR / "Week4_Analysis_Summary.md")
    if week4_summary:
        with st.expander("查看 Week 4 风险管理摘要"):
            st.markdown(week4_summary)


elif page == "数据质量":
    st.header("数据质量报告")

    summary_text = read_text_safe(OUT_DIR / "data_quality_summary.txt")
    if summary_text:
        st.code(summary_text, language="text")

    quality_df = read_csv_safe(OUT_DIR / "data_quality_report.csv")
    show_dataframe("数据质量明细", quality_df)

    col1, col2 = st.columns(2)
    with col1:
        show_image(FIG_DIR / "factor_coverage_bar.png", "因子覆盖率")
    with col2:
        show_image(FIG_DIR / "factor_correlation_heatmap.png", "因子相关性")


elif page == "单因子分析":
    st.header("单因子分析")

    ic_summary = read_csv_safe(OUT_DIR / "factor_ic_summary.csv")
    ic_by_year = read_csv_safe(OUT_DIR / "factor_ic_by_year.csv")
    desc_stats = read_csv_safe(OUT_DIR / "factor_descriptive_stats.csv")

    show_dataframe("IC 汇总", ic_summary)
    show_dataframe("年度 IC 分析", ic_by_year)
    show_dataframe("因子描述统计", desc_stats)

    col1, col2 = st.columns(2)
    with col1:
        show_image(FIG_DIR / "ic_decay.png", "IC 衰减曲线")
    with col2:
        show_image(FIG_DIR / "rank_ic_by_year.png", "年度 Rank IC")

    factor = st.selectbox("选择因子查看细节", ALL_FACTORS, key="single_factor")
    col3, col4 = st.columns(2)
    with col3:
        show_image(FIG_DIR / f"rank_ic_{factor}.png", f"{factor} Rank IC")
    with col4:
        show_image(FIG_DIR / f"distribution_{factor}.png", f"{factor} 分布")


elif page == "分组回测":
    st.header("分组回测")

    group_summary = read_csv_safe(OUT_DIR / "factor_group_summary.csv")
    monotonicity = read_csv_safe(OUT_DIR / "factor_group_monotonicity.csv")

    show_dataframe("分组收益汇总", group_summary)
    show_dataframe("分组收益单调性", monotonicity)

    factor = st.selectbox("选择因子", ALL_FACTORS, key="group_factor")
    group_file = read_csv_safe(OUT_DIR / f"group_return_{factor}.csv")

    if not group_file.empty:
        st.subheader(f"{factor} 分组收益序列")
        st.dataframe(group_file, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        show_image(FIG_DIR / f"group_return_{factor}.png", f"{factor} 分组收益")
        show_image(FIG_DIR / f"group_heatmap_{factor}.png", f"{factor} 年度分组收益热力图")
    with col2:
        show_image(FIG_DIR / f"long_short_cumret_{factor}.png", f"{factor} 多空累计收益")
        show_image(FIG_DIR / f"rank_ic_{factor}.png", f"{factor} Rank IC")


elif page == "Week 2 因子相关性":
    st.header("Week 2 因子相关性")

    show_dataframe("平均横截面 Spearman 相关性", read_csv_safe(WEEK2_DIR / "factor_spearman_corr.csv"))
    show_dataframe("冗余因子剔除决策", read_csv_safe(WEEK2_DIR / "factor_redundancy_decision.csv"))
    show_dataframe("因子筛选与权重", read_csv_safe(WEEK2_DIR / "selected_factors.csv"))

    col1, col2 = st.columns(2)
    with col1:
        show_image(WEEK2_FIG_DIR / "factor_spearman_corr_heatmap.png", "因子相关性热力图")
    with col2:
        show_image(WEEK2_FIG_DIR / "ic_weight_bar.png", "IC 加权因子权重")


elif page == "Week 2 综合因子":
    st.header("Week 2 综合因子")

    composite_ic = read_csv_safe(WEEK2_DIR / "composite_ic_summary.csv")
    selected = read_csv_safe(WEEK2_DIR / "selected_factors.csv")
    model_comparison = read_csv_safe(WEEK2_DIR / "composite_model_comparison.csv")
    composite_ic_by_year = read_csv_safe(WEEK2_DIR / "composite_ic_by_year.csv")
    neutralization = read_csv_safe(WEEK2_DIR / "neutralization_comparison.csv")
    rolling_weights = read_csv_safe(WEEK2_DIR / "rolling_ic_weight_summary.csv")
    desc_stats = read_csv_safe(WEEK2_DIR / "composite_factor_descriptive_stats.csv")
    pca_explained = read_csv_safe(WEEK2_DIR / "pca_explained_variance.csv")
    pca_components = read_csv_safe(WEEK2_DIR / "pca_components.csv")

    if not model_comparison.empty:
        best = model_comparison.sort_values(["sharpe", "rank_ic_mean"], ascending=False).iloc[0]
        st.subheader("当前最佳模型")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("模型", str(best["model"]).replace("composite_", ""))
        col2.metric("Rank IC", f"{best['rank_ic_mean']:.4f}")
        col3.metric("G5-G1 年化", format_percent(best["g5_g1_ann_return"]))
        col4.metric("Sharpe", f"{best['sharpe']:.2f}")
        col5.metric("G5 换手率", format_percent(best["turnover"]))

    show_dataframe("综合模型对比", model_comparison)
    show_dataframe("综合因子 IC 汇总", composite_ic)
    show_dataframe("综合因子年度 IC", composite_ic_by_year)
    show_dataframe("因子权重", selected[["factor", "selected", "weight_equal", "weight_ic"]] if not selected.empty else selected)
    show_dataframe("滚动 IC 权重汇总", rolling_weights)
    show_dataframe("综合因子描述统计", desc_stats)
    show_dataframe("中性化前后对比", neutralization)
    show_dataframe("PCA 解释方差", pca_explained)
    show_dataframe("PCA 载荷", pca_components)

    st.markdown(
        """
        当前 v2.1 构建了等权、全样本 IC 加权、PCA 和滚动 IC 加权综合因子。
        同时基于学习版行业映射完成行业 + 市值中性化；正式版可替换为 Wind / 申万 / Tushare 行业分类。
        """
    )

    model_options = [
        "composite_equal",
        "composite_equal_neutral",
        "composite_equal_industry_size_neutral",
        "composite_ic_weight",
        "composite_ic_weight_neutral",
        "composite_ic_weight_industry_size_neutral",
        "composite_pca",
        "composite_pca_neutral",
        "composite_pca_industry_size_neutral",
        "composite_rolling_ic_weight",
        "composite_rolling_ic_weight_industry_size_neutral",
    ]
    model = st.selectbox("选择综合因子查看 IC 时间序列", model_options, index=5)
    method = method_from_model(model)
    col1, col2 = st.columns(2)
    with col1:
        show_image(WEEK2_FIG_DIR / f"composite_rank_ic_series_{method}.png", f"{model} Rank IC 时间序列")
    with col2:
        show_image(WEEK2_FIG_DIR / "composite_factor_distribution_compare.png", "综合因子分布对比")
        show_image(WEEK2_FIG_DIR / "rolling_ic_weights.png", "滚动 IC 权重")

    composite_panel = read_csv_safe(WEEK2_DIR / "composite_factor_panel.csv")
    if not composite_panel.empty:
        cols = [
            "trade_date",
            "ts_code",
            "composite_equal",
            "composite_equal_neutral",
            "composite_equal_industry_size_neutral",
            "composite_ic_weight",
            "composite_ic_weight_neutral",
            "composite_ic_weight_industry_size_neutral",
            "composite_pca",
            "composite_pca_neutral",
            "composite_pca_industry_size_neutral",
            "composite_rolling_ic_weight",
            "composite_rolling_ic_weight_industry_size_neutral",
        ]
        st.subheader("综合因子面板预览")
        st.dataframe(composite_panel[[col for col in cols if col in composite_panel.columns]].head(200), use_container_width=True, hide_index=True)


elif page == "Week 2 分层回测":
    st.header("Week 2 分层回测")

    layer_summary = read_csv_safe(WEEK2_DIR / "layer_backtest_summary.csv")
    layer_by_year = read_csv_safe(WEEK2_DIR / "layer_backtest_by_year.csv")
    turnover_summary = read_csv_safe(WEEK2_DIR / "layer_turnover_summary.csv")
    monotonicity = read_csv_safe(WEEK2_DIR / "layer_monotonicity_summary.csv")
    monotonicity_by_year = read_csv_safe(WEEK2_DIR / "layer_monotonicity_by_year.csv")
    cost_estimation = read_csv_safe(WEEK2_DIR / "turnover_cost_estimation.csv")
    show_dataframe("五分组回测汇总", layer_summary)
    show_dataframe("年度分层回测", layer_by_year)
    show_dataframe("分层单调性", monotonicity)
    show_dataframe("年度分层单调性", monotonicity_by_year)
    show_dataframe("最高组换手率", turnover_summary)
    show_dataframe("交易成本估算", cost_estimation)

    method = st.selectbox(
        "选择综合因子方法",
        [
            "equal_weight",
            "equal_weight_neutral",
            "equal_weight_industry_size_neutral",
            "ic_weight",
            "ic_weight_neutral",
            "ic_weight_industry_size_neutral",
            "pca",
            "pca_neutral",
            "pca_industry_size_neutral",
            "rolling_ic_weight",
            "rolling_ic_weight_industry_size_neutral",
        ],
        index=5,
    )
    layer_return = read_csv_safe(WEEK2_DIR / f"layer_return_{method}.csv")
    show_dataframe(f"{method} 分层收益序列", layer_return)

    col1, col2 = st.columns(2)
    with col1:
        show_image(WEEK2_FIG_DIR / f"layer_return_{method}.png", f"{method} 分层收益")
        show_image(WEEK2_FIG_DIR / f"layer_cumret_{method}.png", f"{method} 分层累计收益")
    with col2:
        show_image(WEEK2_FIG_DIR / f"long_short_cumret_{method}.png", f"{method} 多空累计收益")
        show_image(WEEK2_FIG_DIR / f"top_group_turnover_{method}.png", f"{method} 最高组换手率")
        show_image(WEEK2_FIG_DIR / "turnover_cost_estimation.png", "交易成本估算")

    week2_report = read_text_safe(WEEK2_DIR / "week2_report.md")
    if week2_report:
        with st.expander("查看 Week 2 自动报告"):
            st.markdown(week2_report)


elif page == "Week 3 策略回测":
    st.header("Week 3 策略回测")

    metrics = read_csv_safe(WEEK3_DIR / "strategy_metrics.csv")
    sensitivity = read_csv_safe(WEEK3_DIR / "parameter_sensitivity.csv")
    best = read_csv_safe(WEEK3_DIR / "best_strategy_summary.csv")
    turnover = read_csv_safe(WEEK3_DIR / "trades_turnover.csv")
    risk_control = read_csv_safe(WEEK3_DIR / "risk_control_comparison.csv")
    cost_sensitivity = read_csv_safe(WEEK3_DIR / "cost_sensitivity.csv")
    recommendation = read_csv_safe(WEEK3_DIR / "parameter_recommendation.csv")
    holding_frequency = read_csv_safe(WEEK3_DIR / "top_holdings_frequency.csv")
    holding_stats = read_csv_safe(WEEK3_DIR / "holding_period_stats.csv")
    benchmark_metrics = read_csv_safe(WEEK3_DIR / "strategy_vs_benchmark_metrics.csv")
    alpha_beta = read_csv_safe(WEEK3_DIR / "alpha_beta_analysis.csv")
    backtrader_metrics = read_csv_safe(WEEK3_DIR / "backtrader_metrics.csv")
    monthly_returns = read_csv_safe(WEEK3_DIR / "monthly_returns.csv")
    yearly_returns = read_csv_safe(WEEK3_DIR / "yearly_returns.csv")
    holding_concentration = read_csv_safe(WEEK3_DIR / "holding_concentration.csv")
    industry_exposure = read_csv_safe(WEEK3_DIR / "industry_exposure_by_rebalance.csv")
    trade_records = read_csv_safe(WEEK3_DIR / "trade_records.csv")
    risk_control_sensitivity = read_csv_safe(WEEK3_DIR / "risk_control_sensitivity.csv")
    weight_method_comparison = read_csv_safe(WEEK3_DIR / "weight_method_comparison.csv")
    parameter_cost_linkage = read_csv_safe(WEEK3_DIR / "parameter_sensitivity_cost_linkage.csv")
    framework_comparison = read_csv_safe(WEEK3_DIR / "backtest_framework_comparison.csv")
    framework_attribution = read_csv_safe(WEEK3_DIR / "backtest_difference_attribution.csv")
    tradeability_summary = read_csv_safe(WEEK3_DIR / "tradeability_filter_summary.csv")
    trade_restriction_events = read_csv_safe(WEEK3_DIR / "trade_restriction_events.csv")
    constrained_metrics = read_csv_safe(WEEK3_DIR / "constrained_strategy_metrics.csv")
    constraint_summary = read_csv_safe(WEEK3_DIR / "constraint_violation_summary.csv")
    risk_control_parameter_grid = read_csv_safe(WEEK3_DIR / "risk_control_parameter_grid.csv")
    stress_periods = read_csv_safe(WEEK3_DIR / "stress_periods_auto.csv")
    stress_metrics = read_csv_safe(WEEK3_DIR / "stress_test_metrics.csv")
    no_lookahead = read_text_safe(WEEK3_DIR / "no_lookahead_check.txt")

    if not metrics.empty:
        row = metrics.iloc[0]
        st.subheader("默认策略")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("年化收益", format_percent(row["annual_return"]))
        col2.metric("Sharpe", f"{row['sharpe']:.2f}")
        col3.metric("最大回撤", format_percent(row["max_drawdown"]))
        col4.metric("Calmar", f"{row['calmar']:.2f}")
        col5.metric("平均换手", format_percent(row["avg_turnover"]))

    show_dataframe("默认策略指标", metrics)
    show_dataframe("Backtrader 主策略验证", backtrader_metrics)
    show_dataframe("策略 vs 基准指标对比", benchmark_metrics)
    show_dataframe("Alpha / Beta / 信息比率分析", alpha_beta)
    if no_lookahead:
        with st.expander("查看无未来函数检查"):
            st.code(no_lookahead, language="text")

    show_dataframe("参数敏感性", sensitivity)
    show_dataframe("最佳参数组合", best)
    show_dataframe("参数推荐表", recommendation)
    show_dataframe("风险控制对比", risk_control)
    show_dataframe("风险控制参数网格", risk_control_sensitivity)
    show_dataframe("v3.3 权重方法对照", weight_method_comparison)
    show_dataframe("v3.3 参数-成本联动", parameter_cost_linkage)
    show_dataframe("v3.3 回测框架指标差异", framework_comparison)
    show_dataframe("v3.3 回测框架差异归因", framework_attribution)
    show_dataframe("v3.3 交易可行性过滤汇总", tradeability_summary)
    show_dataframe("v3.3 交易限制事件", trade_restriction_events)
    show_dataframe("v3.3 组合约束指标", constrained_metrics)
    show_dataframe("v3.3 组合约束违约汇总", constraint_summary)
    show_dataframe("v3.3 风控 × 参数网格", risk_control_parameter_grid)
    show_dataframe("v3.3 压力测试区间", stress_periods)
    show_dataframe("v3.3 压力测试指标", stress_metrics)
    show_dataframe("交易成本敏感性", cost_sensitivity)
    show_dataframe("月度收益", monthly_returns)
    show_dataframe("年度收益", yearly_returns)
    show_dataframe("高频入选股票", holding_frequency.head(20) if not holding_frequency.empty else holding_frequency)
    show_dataframe("持有期统计", holding_stats.head(20) if not holding_stats.empty else holding_stats)
    show_dataframe("持仓集中度", holding_concentration)
    show_dataframe("行业暴露", industry_exposure)
    show_dataframe("调仓换手明细", turnover)
    show_dataframe("交易明细", trade_records.head(200) if not trade_records.empty else trade_records)

    col1, col2 = st.columns(2)
    with col1:
        show_image(WEEK3_FIG_DIR / "nav_curve.png", "策略净值 vs 基准")
        show_image(WEEK3_FIG_DIR / "backtrader_nav_curve.png", "Backtrader 净值曲线")
        show_image(WEEK3_FIG_DIR / "nav_vs_hs300.png", "策略净值 vs 沪深300")
        show_image(WEEK3_FIG_DIR / "nav_risk_control_comparison.png", "风险控制净值对比")
        show_image(WEEK3_FIG_DIR / "drawdown_curve.png", "回撤曲线")
        show_image(WEEK3_FIG_DIR / "monthly_return_heatmap.png", "月度收益热力图")
        show_image(WEEK3_FIG_DIR / "yearly_return_bar.png", "年度收益柱状图")
        show_image(WEEK3_FIG_DIR / "sensitivity_return_heatmap.png", "年化收益敏感性")
    with col2:
        show_image(WEEK3_FIG_DIR / "excess_return_curve.png", "超额收益曲线")
        show_image(WEEK3_FIG_DIR / "excess_vs_hs300.png", "相对沪深300超额")
        show_image(WEEK3_FIG_DIR / "turnover_curve.png", "换手率曲线")
        show_image(WEEK3_FIG_DIR / "industry_exposure_stackplot.png", "行业暴露堆叠图")
        show_image(WEEK3_FIG_DIR / "cost_sensitivity_heatmap.png", "交易成本敏感性")
        show_image(WEEK3_FIG_DIR / "risk_control_sensitivity_heatmap.png", "风险控制参数敏感性")
        show_image(WEEK3_FIG_DIR / "nav_weight_method_comparison.png", "权重方法净值对照")
        show_image(WEEK3_FIG_DIR / "weight_method_metrics_bar.png", "权重方法指标对照")
        show_image(WEEK3_FIG_DIR / "turnover_vs_return_scatter.png", "换手率 vs 年化收益")
        show_image(WEEK3_FIG_DIR / "turnover_vs_calmar_scatter.png", "换手率 vs Calmar")
        show_image(WEEK3_FIG_DIR / "annual_cost_by_parameter_heatmap.png", "参数年化成本热力图")
        show_image(WEEK3_FIG_DIR / "net_return_after_cost_heatmap.png", "扣费后收益热力图")
        show_image(WEEK3_FIG_DIR / "vectorized_vs_backtrader_nav_diff.png", "向量化 vs Backtrader 净值差异")
        show_image(WEEK3_FIG_DIR / "nav_trade_constraints_comparison.png", "交易限制前后净值")
        show_image(WEEK3_FIG_DIR / "nav_constrained_vs_unconstrained.png", "组合约束前后净值")
        show_image(WEEK3_FIG_DIR / "industry_weight_before_after.png", "行业约束前后对照")
        show_image(WEEK3_FIG_DIR / "risk_control_parameter_calmar_heatmap.png", "风控参数 Calmar")
        show_image(WEEK3_FIG_DIR / "stress_test_return_bar.png", "压力测试收益")
        show_image(WEEK3_FIG_DIR / "stress_test_drawdown_bar.png", "压力测试回撤")
        show_image(WEEK3_FIG_DIR / "sensitivity_calmar_heatmap.png", "Calmar 敏感性")
        show_image(WEEK3_FIG_DIR / "sensitivity_sharpe_heatmap.png", "Sharpe 敏感性")

    week3_report = read_text_safe(WEEK3_DIR / "week3_report.md")
    if week3_report:
        with st.expander("查看 Week 3 自动报告"):
            st.markdown(week3_report)


elif page == "Week 4 风险管理":
    st.header("Week 4 风险管理与报告材料")
    st.caption("v4.1：风险归因、极端行情诊断与策略改进增强版")

    risk_metrics = read_csv_safe(WEEK4_TABLE_DIR / "risk_metrics_summary.csv")
    market_effect = read_csv_safe(WEEK4_TABLE_DIR / "market_effect_summary.csv")
    alpha_beta = read_csv_safe(WEEK4_TABLE_DIR / "alpha_beta_summary.csv")
    decomposition = read_csv_safe(WEEK4_TABLE_DIR / "total_return_decomposition.csv")
    brinson_total = read_csv_safe(WEEK4_TABLE_DIR / "brinson_total.csv")
    brinson_by_year = read_csv_safe(WEEK4_TABLE_DIR / "brinson_by_year.csv")
    brinson_by_industry = read_csv_safe(WEEK4_TABLE_DIR / "brinson_by_industry.csv")
    extreme_diag = read_csv_safe(WEEK4_TABLE_DIR / "extreme_event_diagnostics.csv")
    extreme_availability = read_csv_safe(WEEK4_TABLE_DIR / "extreme_event_availability.csv")
    dynamic_weights = read_csv_safe(WEEK4_TABLE_DIR / "dynamic_factor_weight_proposal.csv")
    risk_control = read_csv_safe(WEEK4_TABLE_DIR / "risk_control_comparison.csv")
    improvement_score = read_csv_safe(WEEK4_TABLE_DIR / "improvement_priority_score.csv")
    page_index = read_csv_safe(WEEK4_REPORT_DIR / "Week4_Report_Page_Index.csv")
    material_checklist = read_csv_safe(WEEK4_REPORT_DIR / "Week4_Report_Material_Checklist.csv")

    if not risk_metrics.empty:
        strategy = risk_metrics[risk_metrics["series"] == "strategy"].head(1)
        hs300 = risk_metrics[risk_metrics["series"] == "hs300"].head(1)
        col1, col2, col3, col4, col5 = st.columns(5)
        if not strategy.empty:
            row = strategy.iloc[0]
            col1.metric("策略年化收益", format_percent(row["annual_return"]))
            col2.metric("策略最大回撤", format_percent(row["max_drawdown"]))
            col3.metric("策略 Calmar", f"{row['calmar']:.2f}")
        if not hs300.empty:
            row = hs300.iloc[0]
            col4.metric("沪深300年化", format_percent(row["annual_return"]))
            col5.metric("沪深300回撤", format_percent(row["max_drawdown"]))

    if not alpha_beta.empty:
        row = alpha_beta.iloc[0]
        col1, col2, col3 = st.columns(3)
        col1.metric("年化 Alpha", format_percent(row["alpha_annual"]))
        col2.metric("Beta", f"{row['beta']:.2f}")
        col3.metric("R²", f"{row['r_squared']:.4f}")

    show_dataframe("基础风险指标", risk_metrics)
    show_dataframe("市场效应汇总", market_effect)
    show_dataframe("Alpha / Beta 汇总", alpha_beta)
    show_dataframe("总收益归因：市场 + 行业 + 选股 + 交互 + 残差", decomposition)
    show_dataframe("Brinson 总归因", brinson_total)
    show_dataframe("Brinson 年度归因", brinson_by_year)
    show_dataframe("Brinson 行业归因", brinson_by_industry)
    show_dataframe("极端事件数据可用性", extreme_availability)
    show_dataframe("极端事件诊断", extreme_diag)
    show_dataframe("动态因子权重建议", dynamic_weights)
    show_dataframe("风控模拟对比", risk_control)
    show_dataframe("改进建议优先级评分", improvement_score)
    show_dataframe("12 页报告材料索引", page_index)
    show_dataframe("报告材料检查清单", material_checklist)

    col1, col2 = st.columns(2)
    with col1:
        show_image(WEEK4_FIG_DIR / "nav_comparison.png", "Week 4 净值对比")
        show_image(WEEK4_FIG_DIR / "drawdown_curve.png", "Week 4 回撤曲线")
        show_image(WEEK4_FIG_DIR / "market_effect_decomposition.png", "市场效应与总收益拆解")
        show_image(WEEK4_FIG_DIR / "rolling_beta.png", "滚动 Beta")
        show_image(WEEK4_FIG_DIR / "up_down_capture.png", "上下行捕获率")
        show_image(WEEK4_FIG_DIR / "brinson_stack_chart.png", "Brinson 年度归因")
        show_image(WEEK4_FIG_DIR / "extreme_event_score_bar.png", "极端事件压力得分")
        show_image(WEEK4_FIG_DIR / "extreme_event_return_drawdown.png", "极端事件收益与回撤")
    with col2:
        show_image(WEEK4_FIG_DIR / "factor_ic_bar.png", "因子 Rank IC")
        show_image(WEEK4_FIG_DIR / "factor_rolling_ic.png", "滚动因子 Rank IC")
        show_image(WEEK4_FIG_DIR / "dynamic_factor_weight.png", "动态因子权重建议")
        show_image(WEEK4_FIG_DIR / "risk_control_nav_comparison.png", "风控模拟净值对比")
        show_image(WEEK4_FIG_DIR / "risk_control_drawdown_comparison.png", "风控模拟回撤对比")
        show_image(WEEK4_FIG_DIR / "stop_loss_sensitivity.png", "止损敏感性")
        show_image(WEEK4_FIG_DIR / "improvement_priority_matrix.png", "改进建议优先级矩阵")
        show_image(WEEK4_FIG_DIR / "extreme_market_2020_covid_shock.png", "2020 疫情冲击")

    summary = read_text_safe(WEEK4_REPORT_DIR / "Week4_Analysis_Summary.md")
    if summary:
        with st.expander("查看 Week 4 分析摘要"):
            st.markdown(summary)

elif page == "图表中心":
    st.header("图表中心")

    figure_scope = st.radio("图表来源", ["Week 1", "Week 2", "Week 3", "Week 4", "全部"], horizontal=True)
    if figure_scope == "Week 1":
        png_files = sorted(FIG_DIR.glob("*.png"))
    elif figure_scope == "Week 2":
        png_files = sorted(WEEK2_FIG_DIR.glob("*.png"))
    elif figure_scope == "Week 3":
        png_files = sorted(WEEK3_FIG_DIR.glob("*.png"))
    elif figure_scope == "Week 4":
        png_files = sorted(WEEK4_FIG_DIR.glob("*.png"))
    else:
        png_files = (
            sorted(FIG_DIR.glob("*.png"))
            + sorted(WEEK2_FIG_DIR.glob("*.png"))
            + sorted(WEEK3_FIG_DIR.glob("*.png"))
            + sorted(WEEK4_FIG_DIR.glob("*.png"))
        )
    if not png_files:
        st.warning("未找到图表文件")
    else:
        chart_type = st.selectbox(
            "图表筛选",
            [
                "全部",
                "rank_ic",
                "distribution",
                "group_return",
                "group_heatmap",
                "long_short",
                "correlation",
                "coverage",
                "ic_decay",
                "composite",
                "layer",
                "turnover",
                "neutral",
                "rolling",
                "pca",
                "monotonicity",
                "nav",
                "drawdown",
                "sensitivity",
                "excess",
                "cost",
                "risk",
                "hs300",
                "backtrader",
                "monthly",
                "yearly",
                "industry",
                "weight",
                "stress",
                "constraint",
                "framework",
                "market",
                "beta",
                "capture",
                "brinson",
                "extreme_event",
                "factor",
                "improvement",
            ],
        )

        if chart_type != "全部":
            png_files = [path for path in png_files if chart_type in path.name]

        st.caption(f"当前显示 {len(png_files)} 张图")
        for row_start in range(0, len(png_files), 2):
            cols = st.columns(2)
            for col, img_path in zip(cols, png_files[row_start : row_start + 2]):
                with col:
                    st.subheader(img_path.name)
                    st.image(str(img_path), use_container_width=True)
