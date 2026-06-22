# Week 3 Strategy Backtest Report

## 1. Objective

Week 3 converts the Week 2 composite factor into a long-only stock-selection strategy, then evaluates default parameters and parameter sensitivity.

## 2. Signal Source

Main signal: `composite_ic_weight_industry_size_neutral`.
Control signal: `composite_rolling_ic_weight_industry_size_neutral`.

## 3. Strategy Rules

- Rebalance every 20 trading days for the default strategy.
- Select Top 20 stocks by composite factor score.
- Use equal weight allocation among selected stocks.
- One-way commission plus slippage is 0.15%.
- Turnover is defined as 0.5 * sum(abs(new_weight - old_weight)).

## 4. Benchmark

The v3.0 learning version uses the equal-weight return of all tradable sample stocks as the benchmark when HS300 index data is not supplied.

## 5. Default Strategy Metrics

| signal                                    |   rebalance_days |   top_n |   annual_return |   annual_volatility |   sharpe |   max_drawdown |   calmar |   win_rate |   benchmark_annual_return |   excess_annual_return |   information_ratio |   avg_turnover |   annual_cost |
|:------------------------------------------|-----------------:|--------:|----------------:|--------------------:|---------:|---------------:|---------:|-----------:|--------------------------:|-----------------------:|--------------------:|---------------:|--------------:|
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.0408089 |            0.193151 | 0.211279 |      -0.303097 |  0.13464 |   0.509278 |                 0.0147513 |              0.0260576 |            0.387365 |       0.295918 |    0.00565052 |

## 6. Parameter Sensitivity

| signal                                    |   rebalance_days |   top_n |   annual_return |   annual_volatility |   sharpe |   max_drawdown |    calmar |   win_rate |   benchmark_annual_return |   excess_annual_return |   information_ratio |   avg_turnover |   annual_cost |
|:------------------------------------------|-----------------:|--------:|----------------:|--------------------:|---------:|---------------:|----------:|-----------:|--------------------------:|-----------------------:|--------------------:|---------------:|--------------:|
| composite_ic_weight_industry_size_neutral |                5 |      10 |       0.0372157 |            0.188764 | 0.197155 |      -0.248274 | 0.149898  |   0.506186 |                 0.0147513 |             0.0224644  |           0.233144  |      0.177835  |    0.0134443  |
| composite_ic_weight_industry_size_neutral |                5 |      20 |       0.0292778 |            0.192926 | 0.151757 |      -0.290959 | 0.100625  |   0.503093 |                 0.0147513 |             0.0145265  |           0.214555  |      0.123969  |    0.00937206 |
| composite_ic_weight_industry_size_neutral |                5 |      30 |       0.0405863 |            0.195523 | 0.207578 |      -0.273239 | 0.148538  |   0.502062 |                 0.0147513 |             0.025835   |           0.500668  |      0.0763746 |    0.00577392 |
| composite_ic_weight_industry_size_neutral |               20 |      10 |       0.0634189 |            0.193599 | 0.327578 |      -0.254561 | 0.249131  |   0.492784 |                 0.0147513 |             0.0486676  |           0.487913  |      0.4       |    0.00763794 |
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.0408089 |            0.193151 | 0.211279 |      -0.303097 | 0.13464   |   0.509278 |                 0.0147513 |             0.0260576  |           0.387365  |      0.295918  |    0.00565052 |
| composite_ic_weight_industry_size_neutral |               20 |      30 |       0.0385513 |            0.194439 | 0.19827  |      -0.276084 | 0.139636  |   0.492784 |                 0.0147513 |             0.0238     |           0.471258  |      0.186054  |    0.00355268 |
| composite_ic_weight_industry_size_neutral |               60 |      10 |       0.0473283 |            0.203841 | 0.232183 |      -0.268273 | 0.176418  |   0.517526 |                 0.0147513 |             0.032577   |           0.320298  |      0.485294  |    0.00321495 |
| composite_ic_weight_industry_size_neutral |               60 |      20 |       0.0205835 |            0.196599 | 0.104698 |      -0.267384 | 0.0769811 |   0.5      |                 0.0147513 |             0.00583219 |           0.0879028 |      0.375     |    0.00248428 |
| composite_ic_weight_industry_size_neutral |               60 |      30 |       0.06324   |            0.1977   | 0.319879 |      -0.252337 | 0.250617  |   0.495876 |                 0.0147513 |             0.0484887  |           1.0251    |      0.252941  |    0.00167567 |

## 7. Best Parameter Set

| signal                                    |   rebalance_days |   top_n |   annual_return |   annual_volatility |   sharpe |   max_drawdown |   calmar |   win_rate |   benchmark_annual_return |   excess_annual_return |   information_ratio |   avg_turnover |   annual_cost |
|:------------------------------------------|-----------------:|--------:|----------------:|--------------------:|---------:|---------------:|---------:|-----------:|--------------------------:|-----------------------:|--------------------:|---------------:|--------------:|
| composite_ic_weight_industry_size_neutral |               60 |      30 |         0.06324 |              0.1977 | 0.319879 |      -0.252337 | 0.250617 |   0.495876 |                 0.0147513 |              0.0484887 |              1.0251 |       0.252941 |    0.00167567 |

## 8. Current Limits

The v3.3 result is based on the static medium-sized Week 2 panel. It is intended to validate strategy logic, turnover accounting, no-look-ahead handling, benchmark comparison, risk control, weight-method comparison, tradeability filters, portfolio constraints, stress testing, and parameter search. After the dynamic HS300 panel is generated, the same script should be rerun as the formal dynamic version.

## 9. Strategy vs Benchmark

| benchmark           |   annual_return |   annual_volatility |    sharpe |   max_drawdown |     calmar |   win_rate |   excess_return |   information_ratio |
|:--------------------|----------------:|--------------------:|----------:|---------------:|-----------:|-----------:|----------------:|--------------------:|
| strategy            |       0.0408089 |            0.193151 |  0.211279 |      -0.303097 |  0.13464   |   0.509278 |     nan         |          nan        |
| sample_equal_weight |       0.0147513 |            0.201526 |  0.073198 |      -0.322013 |  0.0458096 |   0.496388 |       0.0261005 |            0.388004 |
| hs300               |      -0.0483514 |            0.191203 | -0.25288  |      -0.432221 | -0.111867  |   0.495876 |       0.0891603 |            0.338198 |

## 10. Alpha Beta Analysis

|   alpha_daily |   alpha_annual |      beta |   r_squared |   tracking_error |   information_ratio |
|--------------:|---------------:|----------:|------------:|-----------------:|--------------------:|
|   0.000240423 |      0.0624518 | 0.0596792 |  0.00349011 |         0.263633 |            0.338198 |

## 11. Yearly Returns

|   year |   strategy_return |   benchmark_return |   hs300_return |   excess_return |   max_drawdown |     sharpe |
|-------:|------------------:|-------------------:|---------------:|----------------:|---------------:|-----------:|
|   2020 |        0.243669   |          0.258026  |      0.255055  |     -0.0143571  |      -0.19362  |  1.0481    |
|   2021 |        0.044796   |          0.0522947 |     -0.0519864 |     -0.00749873 |      -0.17036  |  0.282123  |
|   2022 |       -0.109145   |         -0.187126  |     -0.216328  |      0.0779804  |      -0.284212 | -0.526745  |
|   2023 |        0.00767705 |         -0.0168861 |     -0.113782  |      0.0245632  |      -0.150478 |  0.0608309 |

## 12. Risk Control Comparison

| risk_control     | signal                                    |   rebalance_days |   top_n |   annual_return |   annual_volatility |    sharpe |   max_drawdown |    calmar |   win_rate |   benchmark_annual_return |   excess_annual_return |   information_ratio |   avg_turnover |   annual_cost |   avg_exposure |
|:-----------------|:------------------------------------------|-----------------:|--------:|----------------:|--------------------:|----------:|---------------:|----------:|-----------:|--------------------------:|-----------------------:|--------------------:|---------------:|--------------:|---------------:|
| base             | composite_ic_weight_industry_size_neutral |               20 |      20 |      0.0408089  |            0.193151 | 0.211279  |      -0.303097 | 0.13464   |   0.509278 |                 0.0147513 |            0.0260576   |          0.387365   |       0.295918 |    0.00565052 |       1        |
| vol_target_15pct | vol_target_15pct                          |               20 |      20 |      0.014152   |            0.152837 | 0.0925954 |      -0.265698 | 0.0532633 |   0.509278 |                 0.0147513 |           -0.000599361 |         -0.00655159 |     nan        |    0          |       0.853213 |
| drawdown_control | drawdown_control                          |               20 |      20 |      0.00915498 |            0.134539 | 0.0680468 |      -0.234752 | 0.0389985 |   0.509278 |                 0.0147513 |           -0.00559634  |         -0.0549999  |     nan        |    0          |       0.641237 |

## 13. Parameter Recommendation

|   ranking |   rebalance_days |   top_n |   annual_return |   sharpe |   max_drawdown |   calmar |   avg_turnover | reason                                                                                               |
|----------:|-----------------:|--------:|----------------:|---------:|---------------:|---------:|---------------:|:-----------------------------------------------------------------------------------------------------|
|         1 |               60 |      30 |       0.06324   | 0.319879 |      -0.252337 | 0.250617 |      0.252941  | Calmar 0.25, annual return 6.32%, turnover 25.29%; balances return, drawdown, and trading frequency. |
|         2 |               20 |      10 |       0.0634189 | 0.327578 |      -0.254561 | 0.249131 |      0.4       | Calmar 0.25, annual return 6.34%, turnover 40.00%; balances return, drawdown, and trading frequency. |
|         3 |               60 |      10 |       0.0473283 | 0.232183 |      -0.268273 | 0.176418 |      0.485294  | Calmar 0.18, annual return 4.73%, turnover 48.53%; balances return, drawdown, and trading frequency. |
|         4 |                5 |      30 |       0.0405863 | 0.207578 |      -0.273239 | 0.148538 |      0.0763746 | Calmar 0.15, annual return 4.06%, turnover 7.64%; balances return, drawdown, and trading frequency.  |
|         5 |               20 |      20 |       0.0408089 | 0.211279 |      -0.303097 | 0.13464  |      0.295918  | Calmar 0.13, annual return 4.08%, turnover 29.59%; balances return, drawdown, and trading frequency. |

## 14. Cost Sensitivity

| signal                                    |   rebalance_days |   top_n |   annual_return |   annual_volatility |   sharpe |   max_drawdown |   calmar |   win_rate |   benchmark_annual_return |   excess_annual_return |   information_ratio |   avg_turnover |   annual_cost |   commission |   slippage |   single_side_cost |
|:------------------------------------------|-----------------:|--------:|----------------:|--------------------:|---------:|---------------:|---------:|-----------:|--------------------------:|-----------------------:|--------------------:|---------------:|--------------:|-------------:|-----------:|-------------------:|
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.0467203 |            0.19308  | 0.241973 |      -0.298803 | 0.156358 |   0.509278 |                 0.0147513 |              0.031969  |            0.475249 |       0.295918 |    0          |        0     |     0      |             0      |
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.0447464 |            0.193103 | 0.231724 |      -0.300237 | 0.149037 |   0.509278 |                 0.0147513 |              0.0299951 |            0.445932 |       0.295918 |    0.00188351 |        0     |     0.0005 |             0.0005 |
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.042776  |            0.193126 | 0.221492 |      -0.301669 | 0.141798 |   0.509278 |                 0.0147513 |              0.0280247 |            0.416635 |       0.295918 |    0.00376701 |        0     |     0.001  |             0.001  |
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.042776  |            0.193126 | 0.221492 |      -0.301669 | 0.141798 |   0.509278 |                 0.0147513 |              0.0280247 |            0.416635 |       0.295918 |    0.00376701 |        0.001 |     0      |             0.001  |
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.0408089 |            0.193151 | 0.211279 |      -0.303097 | 0.13464  |   0.509278 |                 0.0147513 |              0.0260576 |            0.387365 |       0.295918 |    0.00565052 |        0.001 |     0.0005 |             0.0015 |
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.0388452 |            0.193178 | 0.201085 |      -0.304523 | 0.127561 |   0.509278 |                 0.0147513 |              0.0240939 |            0.358126 |       0.295918 |    0.00753402 |        0.001 |     0.001  |             0.002  |
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.0388452 |            0.193178 | 0.201085 |      -0.304523 | 0.127561 |   0.509278 |                 0.0147513 |              0.0240939 |            0.358126 |       0.295918 |    0.00753402 |        0.002 |     0      |             0.002  |
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.0368849 |            0.193206 | 0.190909 |      -0.305947 | 0.12056  |   0.509278 |                 0.0147513 |              0.0221336 |            0.328924 |       0.295918 |    0.00941753 |        0.002 |     0.0005 |             0.0025 |
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.034928  |            0.193236 | 0.180753 |      -0.307368 | 0.113636 |   0.509278 |                 0.0147513 |              0.0201767 |            0.299764 |       0.295918 |    0.011301   |        0.002 |     0.001  |             0.003  |
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.034928  |            0.193236 | 0.180753 |      -0.307368 | 0.113636 |   0.509278 |                 0.0147513 |              0.0201767 |            0.299764 |       0.295918 |    0.011301   |        0.003 |     0      |             0.003  |
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.0329745 |            0.193267 | 0.170616 |      -0.308786 | 0.106788 |   0.509278 |                 0.0147513 |              0.0182232 |            0.270652 |       0.295918 |    0.0131845  |        0.003 |     0.0005 |             0.0035 |
| composite_ic_weight_industry_size_neutral |               20 |      20 |       0.0310243 |            0.1933   | 0.160498 |      -0.310201 | 0.100014 |   0.509278 |                 0.0147513 |              0.016273  |            0.241594 |       0.295918 |    0.015068   |        0.003 |     0.001  |             0.004  |

## 15. Weight Method Comparison

Week 3 v3.3 adds three portfolio weighting methods: equal weight, inverse-volatility weight, and simplified risk-parity weight. Equal weight is retained as the baseline because it is transparent and easy to explain. Inverse-volatility weighting reduces exposure to high-volatility stocks. The simplified risk-parity implementation uses recent volatility estimates to make risk contribution more balanced across holdings.

Key outputs:

- `outputs/week3/weight_method_comparison.csv`
- `outputs/week3/strategy_nav_inverse_vol.csv`
- `outputs/week3/strategy_nav_risk_parity.csv`
- `outputs/week3/figures/nav_weight_method_comparison.png`
- `outputs/week3/figures/weight_method_metrics_bar.png`

## 16. Parameter Sensitivity and Cost Linkage

The parameter sensitivity analysis is extended beyond return and Calmar. Week 3 v3.3 links rebalance frequency and holding count to turnover and annualized trading cost. This helps explain why lower-frequency rebalancing and more diversified holdings can be more stable: shorter holding periods may capture signals faster, but they also increase turnover and cost drag.

Key outputs:

- `outputs/week3/parameter_sensitivity_cost_linkage.csv`
- `outputs/week3/figures/turnover_vs_return_scatter.png`
- `outputs/week3/figures/turnover_vs_calmar_scatter.png`
- `outputs/week3/figures/annual_cost_by_parameter_heatmap.png`
- `outputs/week3/figures/net_return_after_cost_heatmap.png`

## 17. Tradeability Filter

Week 3 v3.3 adds a learning-version A-share tradeability filter. The module approximates suspension, limit-up, limit-down, and ST constraints using available price, return, volume, and name fields. This is not a substitute for official exchange status data, but it makes the backtest workflow closer to real trading constraints and prepares the project for a formal data source later.

Key outputs:

- `outputs/week3/tradeability_filter_summary.csv`
- `outputs/week3/trade_restriction_events.csv`
- `outputs/week3/strategy_nav_with_trade_constraints.csv`
- `outputs/week3/figures/nav_trade_constraints_comparison.png`

## 18. Portfolio Hard Constraints

The project extends holding analysis into enforceable portfolio constraints. The constrained strategy supports a single-stock weight cap, an industry weight cap, and a minimum holding count. These constraints are designed to reduce over-concentration in individual stocks or industries and make the strategy more consistent with real portfolio-management requirements.

Key outputs:

- `outputs/week3/constrained_strategy_metrics.csv`
- `outputs/week3/constraint_violation_summary.csv`
- `outputs/week3/industry_weight_constraint_check.csv`
- `outputs/week3/stock_weight_constraint_check.csv`
- `outputs/week3/figures/nav_constrained_vs_unconstrained.png`
- `outputs/week3/figures/industry_weight_before_after.png`

## 19. Backtrader vs Vectorized Backtest

Week 3 v3.3 explicitly decomposes the differences between the vectorized Pandas backtest and the Backtrader event-driven implementation. The two frameworks produce directionally consistent results, but small metric differences are expected because of rebalance timing, price matching, order-value-based costs, residual cash handling, missing-price treatment, and NAV timestamp conventions. The vectorized engine is better suited for broad parameter search, while Backtrader is useful for event-driven validation.

Key outputs:

- `outputs/week3/backtest_framework_comparison.csv`
- `outputs/week3/backtest_difference_attribution.csv`
- `outputs/week3/figures/vectorized_vs_backtrader_nav_diff.png`

## 20. Stress Testing and Risk-Control Linkage

Week 3 v3.3 adds stress testing based on automatically detected HS300 drawdown windows and representative market phases. Compared with monthly or yearly return tables, stress testing focuses on adverse market conditions and helps evaluate drawdown control, excess return, and robustness under rapid declines or style rotation. The project also links risk-control rules with rebalance frequency and holding count through a parameter grid.

Key outputs:

- `outputs/week3/stress_periods_auto.csv`
- `outputs/week3/stress_test_metrics.csv`
- `outputs/week3/risk_control_parameter_grid.csv`
- `outputs/week3/figures/stress_test_return_bar.png`
- `outputs/week3/figures/stress_test_drawdown_bar.png`
- `outputs/week3/figures/risk_control_parameter_calmar_heatmap.png`
- `outputs/week3/figures/risk_control_parameter_return_heatmap.png`

## 21. Figures

- `figures/nav_curve.png`
- `figures/nav_vs_hs300.png`
- `figures/excess_return_curve.png`
- `figures/excess_vs_hs300.png`
- `figures/drawdown_curve.png`
- `figures/turnover_curve.png`
- `figures/nav_risk_control_comparison.png`
- `figures/sensitivity_return_heatmap.png`
- `figures/sensitivity_sharpe_heatmap.png`
- `figures/sensitivity_calmar_heatmap.png`
- `figures/cost_sensitivity_heatmap.png`
- `figures/monthly_return_heatmap.png`
- `figures/yearly_return_bar.png`
- `figures/industry_exposure_stackplot.png`
- `figures/risk_control_sensitivity_heatmap.png`
- `figures/nav_weight_method_comparison.png`
- `figures/weight_method_metrics_bar.png`
- `figures/turnover_vs_return_scatter.png`
- `figures/turnover_vs_calmar_scatter.png`
- `figures/annual_cost_by_parameter_heatmap.png`
- `figures/net_return_after_cost_heatmap.png`
- `figures/vectorized_vs_backtrader_nav_diff.png`
- `figures/nav_trade_constraints_comparison.png`
- `figures/nav_constrained_vs_unconstrained.png`
- `figures/industry_weight_before_after.png`
- `figures/stress_test_return_bar.png`
- `figures/stress_test_drawdown_bar.png`
- `figures/risk_control_parameter_calmar_heatmap.png`
- `figures/risk_control_parameter_return_heatmap.png`
