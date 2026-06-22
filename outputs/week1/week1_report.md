# Week 1 Factor Exploration Report

## 1. Data Sample

- Rows: 44,536
- Stocks: 46
- Period: 2020-01-02 to 2023-12-29
- Data source: AKShare qfq price data; HS300 membership from Tushare index_weight.

## 2. Factor Coverage

| factor             |   count |   missing_rate |
|:-------------------|--------:|---------------:|
| factor_momentum    |   43616 |     0.0206574  |
| factor_volatility  |   43616 |     0.0206574  |
| factor_roe         |       0 |     1          |
| factor_size        |   44536 |     0          |
| factor_turnover    |   43662 |     0.0196246  |
| factor_reversal_5d |   44306 |     0.00516436 |

## 3. IC Summary

| factor             |   sample_periods |      ic_mean |     ic_std |   rank_ic_mean |   rank_ic_std |   ic_win_rate |   rank_ic_win_rate |         icir |    rank_icir |   ic_t_stat |   ic_p_value |   rank_ic_t_stat |   rank_ic_p_value |
|:-------------------|-----------------:|-------------:|-----------:|---------------:|--------------:|--------------:|-------------------:|-------------:|-------------:|------------:|-------------:|-----------------:|------------------:|
| factor_turnover    |              931 |   0.0256368  |   0.263822 |     0.0677675  |      0.218786 |      0.557732 |           0.582474 |   0.0971746  |   0.309744   |    2.96502  |   0.00310392 |         9.45099  |       2.63925e-20 |
| factor_volatility  |              930 |   0.00195949 |   0.243883 |     0.0433972  |      0.21611  |      0.510309 |           0.556701 |   0.00803456 |   0.20081    |    0.245021 |   0.806494   |         6.12389  |       1.34623e-09 |
| factor_size        |              950 |   0.0128525  |   0.20051  |    -0.00149123 |      0.209144 |      0.506186 |           0.462887 |   0.064099   |  -0.00713016 |    1.97566  |   0.0484823  |        -0.219766 |       0.8261      |
| factor_reversal_5d |              945 |  -0.00768126 |   0.225475 |    -0.00536192 |      0.203203 |      0.473196 |           0.45567  |  -0.0340671  |  -0.026387   |   -1.04725  |   0.295252   |        -0.81116  |       0.417478    |
| factor_momentum    |              930 |  -0.0138883  |   0.234594 |    -0.0249409  |      0.222064 |      0.460825 |           0.443299 |  -0.0592014  |  -0.112314   |   -1.8054   |   0.0713357  |        -3.42511  |       0.000641456 |
| factor_roe         |                0 | nan          | nan        |   nan          |    nan        |      0        |           0        | nan          | nan          |  nan        | nan          |       nan        |     nan           |

## 4. Group Return Summary

| factor             |   lowest_group |   highest_group |   lowest_group_return |   highest_group_return |   high_minus_low |   long_short_mean |   available_groups |   sample_periods |
|:-------------------|---------------:|----------------:|----------------------:|-----------------------:|-----------------:|------------------:|-------------------:|-----------------:|
| factor_turnover    |              1 |              10 |           -0.00261619 |            0.00135887  |      0.00397506  |       0.00397506  |                 10 |              931 |
| factor_size        |              1 |              10 |           -0.00299456 |           -3.99219e-05 |      0.00295464  |       0.00295464  |                 10 |              950 |
| factor_volatility  |              1 |              10 |            0.00365545 |            0.00336096  |     -0.000294489 |      -0.000294489 |                 10 |              930 |
| factor_momentum    |              1 |              10 |            0.00323478 |            0.00125282  |     -0.00198196  |      -0.00198196  |                 10 |              930 |
| factor_reversal_5d |              1 |              10 |            0.00432797 |            0.00232992  |     -0.00199805  |      -0.00199805  |                 10 |              945 |
| factor_roe         |            nan |             nan |          nan          |          nan           |    nan           |     nan           |                  0 |                0 |

## 5. Monotonicity

| factor             |   available_groups |   bottom_return |    top_return |   top_bottom_spread |   monotonic_score |
|:-------------------|-------------------:|----------------:|--------------:|--------------------:|------------------:|
| factor_momentum    |                 10 |      0.00323478 |   0.00125282  |        -0.00198196  |          0.555556 |
| factor_volatility  |                 10 |      0.00365545 |   0.00336096  |        -0.000294489 |          0.555556 |
| factor_size        |                 10 |     -0.00299456 |  -3.99219e-05 |         0.00295464  |          0.555556 |
| factor_turnover    |                 10 |     -0.00261619 |   0.00135887  |         0.00397506  |          0.555556 |
| factor_reversal_5d |                 10 |      0.00432797 |   0.00232992  |        -0.00199805  |          0.555556 |
| factor_roe         |                  0 |    nan          | nan           |       nan           |        nan        |

## 6. Figures

- `figures/ic_decay.png`
- `figures/factor_correlation_heatmap.png`
- `figures/factor_coverage_bar.png`
- `figures/rank_ic_by_year.png`
- `figures/rank_ic_factor_*.png`
- `figures/distribution_factor_*.png`
- `figures/group_return_factor_*.png`
- `figures/long_short_cumret_factor_*.png`

## 7. Current Limitations

- ROE remains unavailable in the learning version because financial indicators are not reliably aligned by stock code and announcement date.
- `factor_size` uses HS300 constituent weight as a market-cap proxy because historical market-cap data is unavailable without higher Tushare permissions.
- The current analysis is suitable for Week 1 workflow validation and preliminary factor exploration.

## 8. Week 2 Candidate Factors

factor_momentum, factor_volatility, factor_size, factor_turnover, factor_reversal_5d
