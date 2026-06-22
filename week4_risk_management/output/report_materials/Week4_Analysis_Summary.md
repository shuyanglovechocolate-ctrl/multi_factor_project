# Week 4 Analysis Summary

本文件用于汇总 Week 4 风险管理与报告撰写模块的可交付材料。

## 研究覆盖范围

- 基础风险指标复盘：收益、波动、Sharpe、最大回撤、Calmar、胜率。
- Brinson 收益归因：配置效应、选择效应、交互效应。
- 市场效应分析：市场收益贡献、Alpha/Beta、滚动 Beta、上下行捕获率。
- 极端行情压力测试：2015 股灾、2020 疫情冲击，并预留 2016、2018、2021-2022、2023 阶段。
- 极端事件诊断：事件可用性、压力得分、自动文字解读和数据限制说明。
- 动态因子权重：基于 Rank IC / ICIR 生成权重建议。
- 风控模拟：组合止损、波动率目标、均线择时、固定仓位对照。
- 风险暴露分析：行业暴露、持仓集中度、换手率。
- 策略改进建议：风险发现映射、优先级评分、12 页报告材料索引。

## 输出表格

- `data_quality_check.csv`
- `risk_metrics_summary.csv`
- `extreme_market_test.csv`
- `strategy_improvement_list.csv`
- `brinson_total.csv`
- `brinson_by_year.csv`
- `brinson_by_industry.csv`
- `risk_exposure_industry.csv`
- `risk_exposure_holding_concentration.csv`
- `risk_exposure_turnover.csv`
- `market_effect_summary.csv`
- `alpha_beta_summary.csv`
- `rolling_beta.csv`
- `up_down_capture.csv`
- `total_return_decomposition.csv`
- `extreme_event_calendar.csv`
- `extreme_event_availability.csv`
- `extreme_event_diagnostics.csv`
- `extreme_event_stress_score.csv`
- `factor_ic_summary.csv`
- `factor_rank_ic_summary.csv`
- `factor_rolling_ic.csv`
- `dynamic_factor_weight_proposal.csv`
- `risk_control_simulation_summary.csv`
- `risk_control_comparison.csv`
- `stop_loss_sensitivity.csv`
- `position_control_sensitivity.csv`
- `risk_to_improvement_mapping.csv`
- `strategy_improvement_list_v4_1.csv`
- `improvement_priority_score.csv`

## 输出图表

- `market_effect_decomposition.png`
- `rolling_beta.png`
- `up_down_capture.png`
- `extreme_event_score_bar.png`
- `extreme_event_return_drawdown.png`
- `factor_ic_bar.png`
- `factor_rolling_ic.png`
- `dynamic_factor_weight.png`
- `risk_control_nav_comparison.png`
- `risk_control_drawdown_comparison.png`
- `stop_loss_sensitivity.png`
- `improvement_priority_matrix.png`
- `nav_comparison.png`
- `drawdown_curve.png`
- `brinson_stack_chart.png`
- `extreme_market_2020_covid_shock.png`
- `extreme_market_2021_2022_growth_adjustment.png`
- `extreme_market_2023_style_rotation.png`

## 报告写作提示

当前 Week 4 模块先作为研究步骤与代码框架，不展开完整 12 页报告。
后续正式报告可以直接引用本目录生成的表格、图表和策略改进清单。
