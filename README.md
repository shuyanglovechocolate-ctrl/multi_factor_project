# HS300 Multi-Factor Project

本项目用于完成沪深300多因子选股研究流程，覆盖 Week 1 数据获取与因子探索、Week 2 多因子模型构建、Week 3 策略回测与优化。项目将前复权行情和可用因子整理成标准股票-日期面板，并输出单因子检验、多因子合成、组合回测、风险控制、基准对比和可视化 Dashboard。

## Week 1 完成状态

Week 1 v1.0 已完成中等样本研究版，覆盖 2020-01-02 至 2023-12-29，共 46 只股票、44,536 条日频记录。

当前版本包含：

- 数据质量检查
- 5 个可用因子：动量、波动率、换手率、市值近似、短期反转
- IC / Rank IC / ICIR / 显著性检验
- 自适应分组回测
- 年度稳定性分析
- 分组收益单调性检查
- 34 张可视化图表
- 自动 Markdown 报告

由于 Tushare 权限限制，当前版本采用 AKShare 前复权行情构建学习研究版样本。ROE 因子保留为正式版扩展项，暂不纳入有效性判断。

## 项目当前状态

- Week 1 v1.0：已完成，中等样本研究版
- Week 1 v1.1：动态股票池升级管线已完成，完整动态数据待本地长时间运行
- Week 2 v2.1：已完成，基于静态中等样本完成多因子模型构建、冗余剔除、行业 + 市值中性化、滚动 IC 加权、单调性分析和策略成本衔接
- Week 2 v2.2：待 `factor_panel_dynamic.csv` 生成后切换输入重跑动态股票池正式版
- Week 3 v3.2：已完成，基于静态中等样本完成向量化回测、Backtrader 主策略验证、无未来函数检查、双基准对比、Alpha / Beta 分析、月度年度收益、持仓集中度、行业暴露、交易明细和风险控制参数网格
- Week 3 v3.3：已完成，新增组合约束、权重方法对照、交易可行性过滤、极端行情压力测试、参数成本联动、风控参数联动和回测框架差异拆解，并已生成新增 CSV / 图表结果
- Week 3 v3.4：待动态股票池和动态 Week 2 信号生成后重跑正式策略版
- Week 4 v4.1：已完成风险归因、极端行情诊断与策略改进增强版，包含市场效应显性化、Alpha/Beta、滚动 Beta、上下行捕获率、极端事件诊断、动态因子权重、风控模拟、改进建议评分和 12 页报告材料索引

Week 2 v2.1 当前最优结果为 `composite_ic_weight_industry_size_neutral`：Rank IC mean 为 0.07158，Rank ICIR 为 0.34533，G5-G1 年化收益为 13.16%，Sharpe 为 0.64，胜率为 57.16%，最高组平均换手率为 6.82%。当前结果用于验证多因子建模流程，动态股票池正式结果将在 Week 2 v2.2 中补充。

Week 3 v3.2 默认策略使用 `composite_ic_weight_industry_size_neutral`，采用 20 个交易日调仓、Top 20 等权持仓、0.1% 单边交易成本和 0.05% 滑点假设。向量化默认策略年化收益为 4.08%，样本等权基准年化收益为 1.48%，沪深300年化收益为 -4.84%，最大回撤为 -30.31%，Calmar 为 0.13。Backtrader 主策略验证年化收益为 4.29%，Calmar 为 0.16。相对沪深300回归结果显示策略年化 Alpha 为 6.25%，Beta 为 0.06。参数敏感性测试中，当前推荐组合为 60 日调仓 + Top 30，年化收益为 6.32%，Calmar 为 0.25。

Week 3 v3.3 在 v3.2 基础上进一步补充风险平价 / 波动率倒数加权对照、参数敏感性与换手成本联动解释、涨跌停 / 停牌 / ST 学习版交易约束、单股和行业硬性组合约束、Backtrader 与向量化回测差异拆解、极端行情压力测试，以及风控规则和参数组合的联动测试。当前 v3.3 已完成代码开发、结果生成与 Dashboard 展示接入。

Week 4 v4.1 当前定位为风险归因、极端行情诊断与策略改进增强版。该模块不展开完整 12 页报告，而是先整理研究步骤、代码模块和可复用输出材料。当前已新增 `week4_risk_management/`，可运行 `.venv/bin/python week4_risk_management/main_week4.py` 生成风险指标汇总、Brinson 归因、市场效应拆解、Alpha/Beta、滚动 Beta、极端事件诊断、动态因子权重建议、风控模拟、改进建议评分和 12 页报告材料索引。由于当前静态样本覆盖 2020-2023，2015 股灾、2016 熔断、2018 熊市阶段会保留在压力测试表中并标记为数据不可用，待动态股票池正式数据生成后可直接重跑。

## 目录结构

```text
multi_factor_project/
├── data/
│   ├── raw/
│   │   ├── hs300_members.csv
│   │   ├── price_qfq.csv
│   │   ├── daily_basic.csv
│   │   └── fina_indicator.csv
│   └── processed/
│       ├── factor_panel.csv
│       └── factor_panel.parquet
├── notebooks/
├── app.py
├── outputs/
│   └── week1/
│       ├── factor_ic_summary.csv
│       ├── factor_ic_by_year.csv
│       ├── factor_group_summary.csv
│       ├── factor_group_monotonicity.csv
│       ├── factor_descriptive_stats.csv
│       ├── data_quality_report.csv
│       ├── week1_report.md
│       └── figures/
├── scripts/
│   ├── download_data.py
│   ├── download_data_akshare.py
│   ├── 02_download_akshare_qfq.py
│   ├── build_factor_panel.py
│   ├── week1_factor_analysis.py
│   ├── week1_factor_test.py
│   └── week1_data_quality_report.py
└── requirements.txt
```

## 安装环境

```bash
cd /Users/gaoshuyang/Desktop/高舒扬PTA/multi_factor_project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 下载数据

先在 Tushare Pro 个人中心复制 token，然后设置环境变量：

```bash
export TUSHARE_TOKEN="你的Tushare Token"
```

最小可行版本默认下载 2020-2023 年、前 50 只历史沪深300成分股：

```bash
python scripts/download_data.py
```

完整样本可改为：

```bash
python scripts/download_data.py --start 20150101 --end 20231231 --max-stocks 0
```

注意：`index_weight`、`pro_bar`、`daily_basic`、`fina_indicator` 都可能受 Tushare 积分权限限制。如果接口报权限错误，先用默认小样本验证流程，再考虑补权限或改用 AKShare 学习版。

## AKShare 学习版下载

如果 Tushare token 没有日线行情或每日指标权限，可以先用 AKShare 生成学习版数据。这个版本复用 Tushare 已下载的 `hs300_members.csv`，用 AKShare 下载前复权行情和财务指标：

```bash
python scripts/download_data_akshare.py --start 20200101 --end 20231231 --max-stocks 50
```

学习版限制：

- 财务数据没有真实公告日，脚本使用“报告期后 90 天”近似 `ann_date`。
- 历史 PE/PB 和市值不可用，脚本用沪深300成分权重近似 `total_mv`，仅用于跑通市值因子流程。
- 正式报告建议在 Tushare / Wind / CSMAR 权限补齐后重新生成完整数据。

## 构建因子面板

```bash
python scripts/build_factor_panel.py
```

输出：

```text
data/processed/factor_panel.csv
data/processed/factor_panel.parquet
```

面板核心字段包括：

```text
trade_date, ts_code, close, ret_1d, ret_5d_fwd, ret_20d_fwd,
momentum_20d, volatility_20d, roe, pb, total_mv, turnover_rate,
factor_momentum, factor_volatility, factor_roe, factor_size, factor_turnover, factor_reversal_5d
```

其中财务指标使用 `ann_date` 向后合并到交易日，只使用当日之前已经公告的最新财务数据，避免未来函数。

## Week 1 单因子测试

```bash
python scripts/week1_factor_analysis.py
python scripts/week1_data_quality_report.py
```

输出：

```text
outputs/week1/ic_series.csv
outputs/week1/factor_ic_summary.csv
outputs/week1/factor_ic_by_year.csv
outputs/week1/ic_decay.csv
outputs/week1/group_returns.csv
outputs/week1/factor_group_summary.csv
outputs/week1/factor_group_monotonicity.csv
outputs/week1/factor_descriptive_stats.csv
outputs/week1/data_quality_report.csv
outputs/week1/week1_report.md
outputs/week1/figures/*.png
```

主要分析内容：

- 5 个可用因子：动量、低波动、低换手率、市值近似、短期反转
- ROE 因子保留为正式版扩展项
- IC、Rank IC、ICIR、t 检验和 p 值
- 1/5/10/20/60 日 IC 衰减
- 自适应分组收益和多空收益
- 年度 IC 稳定性、因子描述统计、数据质量检查
- 因子分布、Rank IC 时间序列、分组收益、相关性、覆盖率、多空累计收益等图表

## Week 1 v1.0 交付物

当前建议提交以下内容：

- `data/processed/factor_panel.csv`
- `outputs/week1/factor_ic_summary.csv`
- `outputs/week1/factor_ic_by_year.csv`
- `outputs/week1/factor_group_summary.csv`
- `outputs/week1/factor_group_monotonicity.csv`
- `outputs/week1/factor_descriptive_stats.csv`
- `outputs/week1/data_quality_report.csv`
- `outputs/week1/data_quality_summary.txt`
- `outputs/week1/week1_report.md`
- `outputs/week1/figures/`

## Dashboard 展示

项目包含一个轻量级 Streamlit Dashboard，用于展示 Week 1 的数据质量、单因子分析、分组回测和图表中心。

```bash
streamlit run app.py
```

如果使用项目虚拟环境：

```bash
.venv/bin/streamlit run app.py
```

## Week 1 v1.1 动态股票池升级

Week 1 v1.1 的目标是从静态 46 只股票升级为动态沪深300历史成分股池，并扩展样本到 2015-2023。由于 Tushare `index_weight` 当前频率限制较低，动态成分股下载脚本采用逐月保存和断点续跑。

### 1. 下载动态沪深300成分股

```bash
export TUSHARE_TOKEN="你的Tushare Token"
.venv/bin/python scripts/01_get_hs300_members_dynamic.py --start 20150101 --end 20231231 --sleep 65
```

输出：

```text
data/raw/hs300_members_dynamic_by_month/*.csv
data/raw/hs300_members_dynamic.csv
```

### 2. 提取动态股票列表

```bash
.venv/bin/python scripts/02_prepare_dynamic_stock_list.py
```

输出：

```text
data/processed/hs300_dynamic_stock_list.csv
```

### 3. 下载动态股票池行情

```bash
.venv/bin/python scripts/02_download_akshare_qfq.py \
  --start 20150101 \
  --end 20231231 \
  --stock-list data/processed/hs300_dynamic_stock_list.csv \
  --members-file data/raw/hs300_members_dynamic.csv \
  --max_stocks 0 \
  --sleep 2.5 \
  --retry 2
```

脚本会逐股票保存到：

```text
data/raw/price_qfq_by_stock/
```

并合并输出：

```text
data/raw/price_qfq.csv
data/raw/daily_basic.csv
```

如果中途断开，可以直接重跑同一命令，已存在的单股票文件会自动复用。

### 4. 构建动态因子面板

```bash
.venv/bin/python scripts/build_factor_panel_dynamic.py
```

输出：

```text
data/processed/factor_panel_dynamic.csv
data/processed/factor_panel_dynamic.parquet
data/processed/dynamic_universe.csv
```

### 5. 运行动态股票池 Week 1 分析

```bash
.venv/bin/python scripts/week1_factor_analysis_v11.py
.venv/bin/python scripts/week1_data_quality_report.py \
  --panel-file data/processed/factor_panel_dynamic.csv \
  --output-dir outputs/week1/dynamic_universe
```

动态版本输出目录：

```text
outputs/week1/dynamic_universe/
```

其中会同时包含：

```text
decile_group_summary.csv
adaptive_group_summary.csv
decile_group_return_factor_*.csv
adaptive_group_return_factor_*.csv
```

标准十分位分组作为主结果，自适应分组作为横截面样本不足时的鲁棒性参考。

### 6. 静态 vs 动态对照

```bash
.venv/bin/python scripts/compare_universes.py
```

输出：

```text
outputs/week1/universe_comparison_summary.csv
```

该表用于比较 v1.0 静态股票池与 v1.1 动态股票池在样本规模、Rank IC、ICIR 和多空收益上的差异。

## Week 2 多因子模型

Week 2 v2.1 基于现有静态中等样本 `factor_panel.csv` 跑通多因子流程，包括因子相关性分析、显式冗余因子剔除决策、等权合成、全样本 IC 加权合成、滚动 IC 加权合成、PCA 合成、行业 + 市值中性化、五分组回测、年度稳定性分析、分层单调性检查、最高组换手率分析、PCA 复盘和交易成本估算。

运行：

```bash
.venv/bin/python scripts/week2_multi_factor_model.py \
  --panel-file data/processed/factor_panel.csv \
  --ic-file outputs/week1/factor_ic_summary.csv \
  --output-dir outputs/week2
```

动态股票池数据生成后，可切换为：

```bash
.venv/bin/python scripts/week2_multi_factor_model.py \
  --panel-file data/processed/factor_panel_dynamic.csv \
  --ic-file outputs/week1/dynamic_universe/factor_ic_summary.csv \
  --output-dir outputs/week2/dynamic_universe
```

核心输出：

```text
outputs/week2/factor_spearman_corr.csv
outputs/week2/factor_redundancy_decision.csv
outputs/week2/selected_factors.csv
outputs/week2/selected_factors_final.csv
outputs/week2/industry_mapping.csv
data/processed/factor_panel_with_industry.csv
outputs/week2/composite_factor_panel.csv
outputs/week2/rolling_ic_weights.csv
outputs/week2/rolling_ic_weight_summary.csv
outputs/week2/composite_ic_summary.csv
outputs/week2/composite_ic_by_year.csv
outputs/week2/composite_model_comparison.csv
outputs/week2/composite_factor_descriptive_stats.csv
outputs/week2/composite_factor_correlation.csv
outputs/week2/layer_backtest_summary.csv
outputs/week2/layer_backtest_by_year.csv
outputs/week2/layer_monotonicity_summary.csv
outputs/week2/layer_monotonicity_by_year.csv
outputs/week2/layer_turnover_summary.csv
outputs/week2/neutralization_comparison.csv
outputs/week2/pca_explained_variance.csv
outputs/week2/pca_components.csv
outputs/week2/turnover_cost_estimation.csv
outputs/week2/layer_return_equal_weight.csv
outputs/week2/layer_return_ic_weight.csv
outputs/week2/layer_return_rolling_ic_weight.csv
outputs/week2/layer_return_pca.csv
outputs/week2/week2_report.md
outputs/week2/figures/
```

当前 v2.1 静态样本版本使用股票代码前缀生成学习版行业映射，用于跑通行业 + 市值中性化流程。正式版可将 `industry_mapping.csv` 替换为 Wind、申万、Tushare 或 CSMAR 行业分类。

需要说明的是，全样本 IC 加权方法仍作为基准保留；v2.1 已新增滚动 IC 加权综合因子，每期权重仅使用历史窗口内的 Rank IC 信息，以降低前视偏差。后续 Week 2 v2.2 将在动态股票池面板生成后重新运行同一套流程。

## Week 3 策略回测与参数优化

Week 3 v3.3 基于 Week 2 v2.1 的最优综合因子构建多头选股策略。每个调仓日按照综合因子值从高到低排序，选择 Top N 股票构成组合，并持有至下一调仓日。主结果采用向量化 Pandas 回测，适合多股票因子组合、交易成本扣除和参数网格测试；同时补充 Backtrader 主策略验证，以满足事件驱动回测框架要求。

v3.3 在 v3.2 基础上进一步加入：

- 等权、波动率倒数加权、简化风险平价加权对照
- 参数敏感性与换手率、交易成本联动分析
- 涨跌停、停牌和 ST 股票学习版交易可行性过滤
- 单股最大权重、行业最大权重、最低持股数量等组合硬约束
- Backtrader 与向量化回测差异拆解
- 沪深300极端回撤区间和典型市场阶段压力测试
- 风险控制规则 × 调仓周期 × 持股数量联动测试

默认运行：

```bash
.venv/bin/python scripts/week3_strategy_backtest.py \
  --panel-file outputs/week2/composite_factor_panel.csv \
  --output-dir outputs/week3 \
  --signal composite_ic_weight_industry_size_neutral \
  --alt-signal composite_rolling_ic_weight_industry_size_neutral \
  --rebalance-days 20 \
  --top-n 20 \
  --commission 0.001 \
  --slippage 0.0005 \
  --download-index
```

如果当前环境导入 pandas / numpy / matplotlib 较慢，可以先运行 v3.3 轻量模式：

```bash
.venv/bin/python scripts/week3_strategy_backtest.py \
  --panel-file outputs/week2/composite_factor_panel.csv \
  --output-dir outputs/week3 \
  --signal composite_ic_weight_industry_size_neutral \
  --alt-signal composite_rolling_ic_weight_industry_size_neutral \
  --rebalance-days 20 \
  --top-n 20 \
  --commission 0.001 \
  --slippage 0.0005 \
  --fast
```

`--fast` 仅运行主策略、权重方式对照、参数成本联动和 Backtrader 差异拆解，跳过压力测试、风控大网格、交易约束和组合硬约束完整回测。待轻量模式跑通后，再去掉 `--fast` 运行完整版。

核心输出：

```text
outputs/week3/strategy_nav.csv
outputs/week3/strategy_metrics.csv
outputs/week3/benchmark_nav.csv
outputs/week3/benchmark_hs300_nav.csv
outputs/week3/trades_turnover.csv
outputs/week3/parameter_sensitivity.csv
outputs/week3/parameter_sensitivity_pivot_return.csv
outputs/week3/parameter_sensitivity_pivot_sharpe.csv
outputs/week3/parameter_sensitivity_pivot_calmar.csv
outputs/week3/best_strategy_summary.csv
outputs/week3/parameter_recommendation.csv
outputs/week3/risk_control_comparison.csv
outputs/week3/risk_control_sensitivity.csv
outputs/week3/weight_method_comparison.csv
outputs/week3/strategy_nav_inverse_vol.csv
outputs/week3/strategy_nav_risk_parity.csv
outputs/week3/parameter_sensitivity_cost_linkage.csv
outputs/week3/backtest_framework_comparison.csv
outputs/week3/backtest_difference_attribution.csv
outputs/week3/tradeability_filter_summary.csv
outputs/week3/trade_restriction_events.csv
outputs/week3/strategy_nav_with_trade_constraints.csv
outputs/week3/constrained_strategy_metrics.csv
outputs/week3/constraint_violation_summary.csv
outputs/week3/industry_weight_constraint_check.csv
outputs/week3/stock_weight_constraint_check.csv
outputs/week3/risk_control_parameter_grid.csv
outputs/week3/stress_periods_auto.csv
outputs/week3/stress_test_metrics.csv
outputs/week3/cost_sensitivity.csv
outputs/week3/holdings_by_rebalance.csv
outputs/week3/top_holdings_frequency.csv
outputs/week3/holding_period_stats.csv
outputs/week3/backtrader_nav.csv
outputs/week3/backtrader_metrics.csv
outputs/week3/no_lookahead_check.txt
outputs/week3/strategy_vs_benchmark_metrics.csv
outputs/week3/alpha_beta_analysis.csv
outputs/week3/monthly_returns.csv
outputs/week3/yearly_returns.csv
outputs/week3/holding_concentration.csv
outputs/week3/industry_exposure_by_rebalance.csv
outputs/week3/trade_records.csv
outputs/week3/week3_report.md
outputs/week3/figures/nav_curve.png
outputs/week3/figures/nav_vs_hs300.png
outputs/week3/figures/backtrader_nav_curve.png
outputs/week3/figures/excess_return_curve.png
outputs/week3/figures/excess_vs_hs300.png
outputs/week3/figures/drawdown_curve.png
outputs/week3/figures/turnover_curve.png
outputs/week3/figures/nav_risk_control_comparison.png
outputs/week3/figures/cost_sensitivity_heatmap.png
outputs/week3/figures/risk_control_sensitivity_heatmap.png
outputs/week3/figures/nav_weight_method_comparison.png
outputs/week3/figures/weight_method_metrics_bar.png
outputs/week3/figures/turnover_vs_return_scatter.png
outputs/week3/figures/turnover_vs_calmar_scatter.png
outputs/week3/figures/annual_cost_by_parameter_heatmap.png
outputs/week3/figures/net_return_after_cost_heatmap.png
outputs/week3/figures/vectorized_vs_backtrader_nav_diff.png
outputs/week3/figures/nav_trade_constraints_comparison.png
outputs/week3/figures/nav_constrained_vs_unconstrained.png
outputs/week3/figures/industry_weight_before_after.png
outputs/week3/figures/risk_control_parameter_calmar_heatmap.png
outputs/week3/figures/risk_control_parameter_return_heatmap.png
outputs/week3/figures/stress_test_return_bar.png
outputs/week3/figures/stress_test_drawdown_bar.png
outputs/week3/figures/monthly_return_heatmap.png
outputs/week3/figures/yearly_return_bar.png
outputs/week3/figures/industry_exposure_stackplot.png
outputs/week3/figures/sensitivity_return_heatmap.png
outputs/week3/figures/sensitivity_sharpe_heatmap.png
outputs/week3/figures/sensitivity_calmar_heatmap.png
```

Backtrader 主策略验证：

```bash
.venv/bin/python scripts/week3_backtrader_strategy.py \
  --panel-file outputs/week2/composite_factor_panel.csv \
  --output-dir outputs/week3 \
  --signal composite_ic_weight_industry_size_neutral \
  --rebalance-days 20 \
  --top-n 20 \
  --commission 0.001 \
  --slippage 0.0005
```

当前 v3.3 已通过 AKShare 生成 `data/raw/hs300_index.csv`，并输出沪深300指数基准净值。报告中同时保留样本等权基准和沪深300指数基准：前者用于衡量同股票池内的选股能力，后者用于满足市场基准对比要求。

为避免前视偏差，项目输出 `no_lookahead_check.txt` 记录策略信号和收益对齐规则：调仓日仅使用当期已生成的综合因子排序选股，未来收益字段不参与选股，组合收益从下一交易日开始计算，交易成本在调仓时点扣除。

运行提示：如果本机长时间卡在 pandas / matplotlib 导入阶段，建议先关闭旧的 Streamlit 和 Python 进程，重新打开 VSCode 终端后再运行 Week 3 脚本。脚本顶部已加入 `[BOOT]` 导入进度打印，可用于判断具体卡在 pandas、numpy、matplotlib 还是 seaborn。当前 v3.3 已完成代码开发、结果生成与 Dashboard 展示接入。

环境备注：旧虚拟环境已备份为 `.venv_broken_20260614`；当前项目使用新的 `.venv` 运行。确认新环境稳定后，可按需删除旧备份以释放空间。
