# Week 1 输出说明

本目录为 Week 1 数据获取与因子探索输出结果。

当前版本为 Week 1 v1.0 中等样本研究版。由于 Tushare 权限限制，当前版本采用 AKShare 前复权行情构建学习研究版样本，覆盖 2020-01-02 至 2023-12-29，共 46 只股票、44,536 条日频记录。

## 主要输出

- `factor_ic_summary.csv`：IC、Rank IC、ICIR、t 检验和 p 值汇总
- `factor_ic_by_year.csv`：年度 IC 稳定性分析
- `factor_group_summary.csv`：分组收益和最高组减最低组结果
- `factor_group_monotonicity.csv`：分组收益单调性检查
- `factor_descriptive_stats.csv`：因子描述性统计
- `data_quality_report.csv`：数据质量检查明细
- `data_quality_summary.txt`：数据质量摘要
- `week1_report.md`：自动生成的 Week 1 Markdown 小报告
- `ic_series_factor_*.csv`：单因子 IC 时间序列
- `group_return_factor_*.csv`：单因子分组收益序列
- `figures/`：Week 1 可视化图表

## 当前限制

ROE 因子暂未纳入有效性判断。当前 AKShare 学习版财务数据未能稳定按股票代码和公告日对齐，因此 `factor_roe` 保留为正式版扩展项。正式版可在补充 Tushare / Wind / CSMAR 财务数据后扩展。

当前可用的 5 个候选因子为：

- `factor_momentum`
- `factor_volatility`
- `factor_turnover`
- `factor_size`
- `factor_reversal_5d`

## v1.1 动态股票池扩展

Week 1 v1.1 将新增动态沪深300股票池结果，计划输出到：

```text
outputs/week1/dynamic_universe/
```

动态版本会同时保留：

- 标准十分位分组：`decile_group_summary.csv`
- 自适应分组：`adaptive_group_summary.csv`
- 静态 vs 动态对照：`universe_comparison_summary.csv`

其中标准十分位分组作为动态股票池主结果，自适应分组作为鲁棒性补充。
