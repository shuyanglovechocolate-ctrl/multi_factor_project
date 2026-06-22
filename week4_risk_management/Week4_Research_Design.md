# Week 4：风险管理与报告撰写模块设计

本阶段先收敛为“研究步骤 + 代码模块设计”，不展开完整 12 页报告。目标是在 Week 3 策略回测结果基础上，补充风险归因、极端行情检验、风险暴露复盘和策略改进建议，为最终项目报告提供结构化素材。

## 一、Week 4 研究目标

Week 4 的主题是风险管理与报告撰写，核心覆盖四类任务：

1. Brinson 收益归因：拆解组合相对基准的配置效应、选择效应和交互效应。
2. 极端市场表现分析：重点检查 2015 股灾和 2020 疫情冲击，并预留 2016 熔断、2018 熊市、2021-2022 调整、2023 风格轮动。
3. 策略风险暴露复盘：分析行业暴露、持仓集中度、换手率和交易成本压力。
4. 策略改进建议：形成动态因子权重、止损、仓位控制、组合约束和交易可行性过滤等改进清单。

## 二、研究步骤

### 1. 整理风险分析数据

输入文件主要来自 Week 2 和 Week 3：

- `outputs/week2/composite_factor_panel.csv`
- `outputs/week3/strategy_nav.csv`
- `outputs/week3/benchmark_nav.csv`
- `outputs/week3/benchmark_hs300_nav.csv`
- `outputs/week3/holdings_by_rebalance.csv`
- `outputs/week3/industry_exposure_by_rebalance.csv`
- `outputs/week3/trades_turnover.csv`

输出数据质量检查表：

- `output/tables/data_quality_check.csv`

### 2. 基础风险指标复盘

复盘策略、样本等权基准、沪深300基准的收益和风险特征：

- 年化收益
- 年化波动
- Sharpe
- 最大回撤
- Calmar
- 胜率
- 相对沪深300超额表现

输出：

- `output/tables/risk_metrics_summary.csv`
- `output/charts/nav_comparison.png`
- `output/charts/drawdown_curve.png`

### 3. Brinson 收益归因

基于持仓行业权重和股票收益近似执行 Brinson 拆解：

- 配置效应：行业权重偏离带来的收益贡献
- 选择效应：行业内部选股能力带来的收益贡献
- 交互效应：行业配置和选股共同作用

输出：

- `output/tables/brinson_total.csv`
- `output/tables/brinson_by_year.csv`
- `output/tables/brinson_by_industry.csv`
- `output/charts/brinson_stack_chart.png`

说明：当前为学习版 Brinson 近似实现，正式版可替换为真实沪深300行业权重和更细行业分类。

### 4. 极端市场压力测试

固定纳入两个重点阶段：

- 2015 股灾：`2015-06-12` 至 `2015-08-26`
- 2020 疫情冲击：`2020-02-03` 至 `2020-03-23`

预留阶段：

- 2016 熔断
- 2018 熊市
- 2021-2022 调整
- 2023 风格轮动

输出：

- `output/tables/extreme_market_test.csv`
- `output/charts/extreme_market_*.png`

如果当前静态样本不覆盖 2015、2016、2018，该表会保留对应阶段并标记 `data_available=False`。动态股票池正式数据生成后可直接重跑。

### 5. 风险暴露分析

主要分析：

- 行业平均暴露和最大暴露
- 持仓集中度：Top1、Top5、HHI、有效持股数量
- 调仓换手率：平均、最大、中位数

输出：

- `output/tables/risk_exposure_industry.csv`
- `output/tables/risk_exposure_holding_concentration.csv`
- `output/tables/risk_exposure_turnover.csv`

### 6. 策略改进建议

形成可写入报告的改进清单：

- 动态因子权重
- 回撤止损
- 波动率目标仓位
- 行业权重约束
- 单股权重约束
- 换手率和交易成本控制
- 流动性与交易可行性过滤

输出：

- `output/tables/strategy_improvement_list.csv`

## 三、代码模块结构

```text
week4_risk_management/
├── 00_config.py
├── 01_data_loader.py
├── 02_risk_metrics.py
├── 03_brinson_attribution.py
├── 04_extreme_market_test.py
├── 05_risk_exposure.py
├── 06_strategy_improvement.py
├── 07_visualization.py
├── 08_report_data_export.py
├── main_week4.py
├── data/
├── output/
│   ├── tables/
│   ├── charts/
│   └── report_materials/
└── Week4_Research_Design.md
```

运行方式：

```bash
cd /Users/gaoshuyang/Desktop/高舒扬PTA/multi_factor_project
.venv/bin/python week4_risk_management/main_week4.py
```

## 四、题目要求与模块映射

| 题目要求 | 对应模块 | 输出 |
| --- | --- | --- |
| Brinson 归因 | `03_brinson_attribution.py` | `brinson_total.csv`, `brinson_by_year.csv`, `brinson_by_industry.csv` |
| 极端市场表现 | `04_extreme_market_test.py` | `extreme_market_test.csv`, `extreme_market_*.png` |
| 动态因子权重建议 | `06_strategy_improvement.py` | `strategy_improvement_list.csv` |
| 止损建议 | `06_strategy_improvement.py` | `strategy_improvement_list.csv` |
| 仓位控制建议 | `06_strategy_improvement.py` | `strategy_improvement_list.csv` |
| 风险管理复盘 | `02_risk_metrics.py`, `05_risk_exposure.py` | `risk_metrics_summary.csv`, `risk_exposure_*.csv` |
| 报告材料整理 | `08_report_data_export.py` | `Week4_Analysis_Summary.md` |

## 五、当前定位

## 六、v4.1 增强说明

在 v4.0 的基础上，v4.1 进一步补齐 6 个增强模块：

```text
09_market_effect_analysis.py
10_extreme_event_diagnostics.py
11_factor_dynamic_weight_analysis.py
12_risk_control_simulator.py
13_improvement_scoring.py
14_report_page_builder.py
```

增强重点包括：

- 市场效应显性化：将策略总收益拆分为市场效应、行业配置效应、个股选择效应、交互效应和残差项。
- Alpha/Beta 分析：计算策略相对沪深300的 Beta、年化 Alpha、滚动 Beta 和上下行捕获率。
- 极端事件诊断卡片：对 2015 股灾、2016 熔断、2018 熊市、2020 疫情冲击等事件输出可用性、收益、回撤、波动、压力得分和文字解读。
- 动态因子权重依据：基于因子 Rank IC / ICIR 生成动态权重建议，使“动态因子权重”不再只是文字建议。
- 风控模拟：基于现有策略收益序列模拟组合止损、波动率目标、均线择时和固定仓位控制。
- 改进建议评分：将风险发现映射到改进建议，并按影响、紧迫性、可行性给出优先级。
- 12 页材料索引：生成后续完整报告或 PPT 可直接使用的页面大纲、材料索引和检查清单。

v4.1 新增输出包括：

- `market_effect_summary.csv`
- `alpha_beta_summary.csv`
- `rolling_beta.csv`
- `up_down_capture.csv`
- `total_return_decomposition.csv`
- `extreme_event_diagnostics.csv`
- `dynamic_factor_weight_proposal.csv`
- `risk_control_comparison.csv`
- `improvement_priority_score.csv`
- `Week4_12Page_Report_Outline.md`
- `Week4_Report_Page_Index.csv`
- `Week4_Report_Material_Checklist.csv`

Week 4 当前定位为：

```text
Week 4 v4.1：风险归因、极端行情诊断与策略改进增强版
```

它的作用不是替代最终 12 页报告，而是把报告需要的分析步骤、数据表、图表、事件诊断和改进建议整理成可运行的模块。等动态股票池版本完成后，可以复用同一框架重跑正式版风险分析。
