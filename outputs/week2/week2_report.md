# Week 2 Multi-Factor Model Report

## 1. Week 2 Objective

Week 2 builds on the Week 1 single-factor analysis by running factor correlation analysis, redundant factor screening, composite-factor construction, industry + size neutralization, rolling IC weighting, five-layer backtesting, turnover analysis, and transaction-cost preparation for Week 3.

## 2. Candidate Factors

factor_momentum, factor_volatility, factor_turnover, factor_size, factor_reversal_5d

ROE is not included in the v2.0 model because it remains a formal-data-source extension item.

## 3. Selected Factors

factor_momentum, factor_volatility, factor_turnover, factor_size, factor_reversal_5d

## 4. Redundancy Decision

A threshold of 0.7 is used for redundant-factor detection. When the absolute average cross-sectional Spearman correlation exceeds 0.7, the model keeps the factor with stronger Rank IC, ICIR, or clearer economic interpretation.

| factor_a          | factor_b           |   spearman_corr |   abs_corr |   threshold | keep_factor   | drop_factor   | reason                                 |
|:------------------|:-------------------|----------------:|-----------:|------------:|:--------------|:--------------|:---------------------------------------|
| factor_momentum   | factor_volatility  |     -0.230352   | 0.230352   |         0.7 |               |               | abs_corr_not_above_threshold_keep_both |
| factor_momentum   | factor_turnover    |     -0.107372   | 0.107372   |         0.7 |               |               | abs_corr_not_above_threshold_keep_both |
| factor_momentum   | factor_size        |     -0.00205756 | 0.00205756 |         0.7 |               |               | abs_corr_not_above_threshold_keep_both |
| factor_momentum   | factor_reversal_5d |     -0.441      | 0.441      |         0.7 |               |               | abs_corr_not_above_threshold_keep_both |
| factor_volatility | factor_turnover    |      0.58018    | 0.58018    |         0.7 |               |               | abs_corr_not_above_threshold_keep_both |
| factor_volatility | factor_size        |     -0.0322792  | 0.0322792  |         0.7 |               |               | abs_corr_not_above_threshold_keep_both |
| factor_volatility | factor_reversal_5d |      0.0466122  | 0.0466122  |         0.7 |               |               | abs_corr_not_above_threshold_keep_both |
| factor_turnover   | factor_size        |      0.0134532  | 0.0134532  |         0.7 |               |               | abs_corr_not_above_threshold_keep_both |
| factor_turnover   | factor_reversal_5d |     -0.00446644 | 0.00446644 |         0.7 |               |               | abs_corr_not_above_threshold_keep_both |
| factor_size       | factor_reversal_5d |      0.00793486 | 0.00793486 |         0.7 |               |               | abs_corr_not_above_threshold_keep_both |

## 5. Factor Weights

| factor             |   weight_equal |   weight_ic | selected   |
|:-------------------|---------------:|------------:|:-----------|
| factor_momentum    |            0.2 |    0        | True       |
| factor_volatility  |            0.2 |    0.390387 | True       |
| factor_turnover    |            0.2 |    0.609613 | True       |
| factor_size        |            0.2 |    0        | True       |
| factor_reversal_5d |            0.2 |    0        | True       |

## 6. Industry Mapping

The current v2.1 static-sample version uses a reproducible learning-version industry mapping based on stock-code prefixes. It is used to run the industry + size neutralization pipeline and can be replaced by Wind, Shenwan, Tushare, or CSMAR industry classifications in the formal-data version.

| ts_code   | industry   | mapping_source       |
|:----------|:-----------|:---------------------|
| 000001.SZ | Financials | learning_code_prefix |
| 000002.SZ | Financials | learning_code_prefix |
| 000063.SZ | Financials | learning_code_prefix |
| 000069.SZ | Financials | learning_code_prefix |
| 000100.SZ | Financials | learning_code_prefix |
| 000157.SZ | Financials | learning_code_prefix |
| 000166.SZ | Financials | learning_code_prefix |
| 000333.SZ | Financials | learning_code_prefix |
| 000338.SZ | Financials | learning_code_prefix |
| 000415.SZ | Financials | learning_code_prefix |
| 000423.SZ | Financials | learning_code_prefix |
| 000425.SZ | Financials | learning_code_prefix |
| 000538.SZ | Financials | learning_code_prefix |
| 000568.SZ | Financials | learning_code_prefix |
| 000596.SZ | Financials | learning_code_prefix |
| 000625.SZ | Financials | learning_code_prefix |
| 000629.SZ | Financials | learning_code_prefix |
| 000630.SZ | Financials | learning_code_prefix |
| 000651.SZ | Financials | learning_code_prefix |
| 000656.SZ | Financials | learning_code_prefix |

## 7. Rolling IC Weights

Rolling IC weights use only historical Rank IC information. Positive historical IC values participate in weighting; non-positive values receive zero weight; when all are non-positive, the model falls back to equal weights.

|   window | factor             |   avg_weight |   median_weight |   max_weight |   active_periods |
|---------:|:-------------------|-------------:|----------------:|-------------:|-----------------:|
|      120 | factor_momentum    |    0.131791  |       0         |     1        |              377 |
|      120 | factor_volatility  |    0.240936  |       0.244427  |     0.804563 |              732 |
|      120 | factor_turnover    |    0.359064  |       0.387244  |     0.772935 |              896 |
|      120 | factor_size        |    0.181866  |       0         |     0.812271 |              445 |
|      120 | factor_reversal_5d |    0.0863427 |       0.0323455 |     0.486603 |              534 |
|      252 | factor_momentum    |    0.157911  |       0         |     1        |              411 |
|      252 | factor_volatility  |    0.235073  |       0.252856  |     0.432929 |              873 |
|      252 | factor_turnover    |    0.403779  |       0.434554  |     0.76977  |              896 |
|      252 | factor_size        |    0.164548  |       0         |     0.741633 |              441 |
|      252 | factor_reversal_5d |    0.0386895 |       0         |     0.2      |              406 |

## 8. Composite Model Comparison

| model                                             | neutralized   |   rank_ic_mean |   rank_ic_ir |   g5_g1_ann_return |    sharpe |   max_drawdown |   win_rate |   turnover |
|:--------------------------------------------------|:--------------|---------------:|-------------:|-------------------:|----------:|---------------:|-----------:|-----------:|
| composite_equal                                   | False         |      0.0375757 |    0.177614  |          0.0645492 |  0.290626 |      -0.991491 |   0.538947 |  0.159041  |
| composite_equal_size_neutral                      | True          |      0.0488909 |    0.251544  |          0.0570453 |  0.284443 |      -0.966012 |   0.544211 |  0.207316  |
| composite_equal_industry_size_neutral             | True          |      0.0530186 |    0.273428  |          0.0835501 |  0.418316 |      -0.960287 |   0.545263 |  0.20766   |
| composite_equal_neutral                           | True          |      0.0488909 |    0.251544  |          0.0570453 |  0.284443 |      -0.966012 |   0.544211 |  0.207316  |
| composite_ic_weight                               | False         |      0.0587337 |    0.268272  |          0.0898682 |  0.432083 |      -0.978852 |   0.552632 |  0.0712074 |
| composite_ic_weight_size_neutral                  | True          |      0.07048   |    0.343227  |          0.132156  |  0.641928 |      -0.969892 |   0.576842 |  0.0638688 |
| composite_ic_weight_industry_size_neutral         | True          |      0.0715793 |    0.34533   |          0.131625  |  0.644008 |      -0.943726 |   0.571579 |  0.0682261 |
| composite_ic_weight_neutral                       | True          |      0.07048   |    0.343227  |          0.132156  |  0.641928 |      -0.969892 |   0.576842 |  0.0638688 |
| composite_pca                                     | False         |      0.0159278 |    0.0668567 |         -0.0323181 | -0.141866 |      -0.999492 |   0.507527 |  0.238262  |
| composite_pca_size_neutral                        | True          |      0.0470875 |    0.219231  |          0.0389119 |  0.182754 |      -0.981885 |   0.545161 |  0.23674   |
| composite_pca_industry_size_neutral               | True          |      0.047884  |    0.222933  |          0.0695631 |  0.330198 |      -0.941442 |   0.551613 |  0.23756   |
| composite_pca_neutral                             | True          |      0.0470875 |    0.219231  |          0.0389119 |  0.182754 |      -0.981885 |   0.545161 |  0.23674   |
| composite_rolling_ic_weight                       | False         |      0.066925  |    0.302624  |          0.144652  |  0.616179 |      -0.984111 |   0.576842 |  0.110423  |
| composite_rolling_ic_weight_size_neutral          | True          |      0.0553519 |    0.254944  |          0.0637197 |  0.299005 |      -0.977468 |   0.551579 |  0.12854   |
| composite_rolling_ic_weight_industry_size_neutral | True          |      0.0587943 |    0.272313  |          0.100138  |  0.466532 |      -0.930729 |   0.556842 |  0.13393   |

## 9. Composite IC Summary

| factor                                            |   sample_periods |   rank_ic_mean |   rank_ic_std |   rank_icir |   rank_ic_win_rate |
|:--------------------------------------------------|-----------------:|---------------:|--------------:|------------:|-------------------:|
| composite_equal                                   |              950 |      0.0375757 |      0.211558 |   0.177614  |           0.576842 |
| composite_equal_industry_size_neutral             |              950 |      0.0530186 |      0.193903 |   0.273428  |           0.617895 |
| composite_equal_neutral                           |              950 |      0.0488909 |      0.194363 |   0.251544  |           0.616842 |
| composite_equal_size_neutral                      |              950 |      0.0488909 |      0.194363 |   0.251544  |           0.616842 |
| composite_ic_weight                               |              931 |      0.0587337 |      0.218933 |   0.268272  |           0.612245 |
| composite_ic_weight_industry_size_neutral         |              931 |      0.0715793 |      0.207278 |   0.34533   |           0.647691 |
| composite_ic_weight_neutral                       |              931 |      0.07048   |      0.205345 |   0.343227  |           0.647691 |
| composite_ic_weight_size_neutral                  |              931 |      0.07048   |      0.205345 |   0.343227  |           0.647691 |
| composite_pca                                     |              930 |      0.0159278 |      0.238238 |   0.0668567 |           0.524731 |
| composite_pca_industry_size_neutral               |              930 |      0.047884  |      0.214791 |   0.222933  |           0.594624 |
| composite_pca_neutral                             |              930 |      0.0470875 |      0.214785 |   0.219231  |           0.58172  |
| composite_pca_size_neutral                        |              930 |      0.0470875 |      0.214785 |   0.219231  |           0.58172  |
| composite_rolling_ic_weight                       |              950 |      0.066925  |      0.221149 |   0.302624  |           0.632632 |
| composite_rolling_ic_weight_industry_size_neutral |              950 |      0.0587943 |      0.215907 |   0.272313  |           0.601053 |
| composite_rolling_ic_weight_size_neutral          |              950 |      0.0553519 |      0.217114 |   0.254944  |           0.598947 |

## 10. Composite IC by Year

|   year | composite_factor                                  |   rank_ic_mean |   rank_ic_win_rate |   sample_periods |
|-------:|:--------------------------------------------------|---------------:|-------------------:|-----------------:|
|   2020 | composite_equal                                   |    -0.0288959  |           0.452675 |              243 |
|   2020 | composite_equal_industry_size_neutral             |     0.0727     |           0.662551 |              243 |
|   2020 | composite_equal_neutral                           |     0.0438325  |           0.609053 |              243 |
|   2020 | composite_equal_size_neutral                      |     0.0438325  |           0.609053 |              243 |
|   2020 | composite_ic_weight                               |     0.0223423  |           0.549107 |              224 |
|   2020 | composite_ic_weight_industry_size_neutral         |     0.0526773  |           0.620536 |              224 |
|   2020 | composite_ic_weight_neutral                       |     0.0323527  |           0.584821 |              224 |
|   2020 | composite_ic_weight_size_neutral                  |     0.0323527  |           0.584821 |              224 |
|   2020 | composite_pca                                     |     0.00197822 |           0.542601 |              223 |
|   2020 | composite_pca_industry_size_neutral               |     0.0402127  |           0.600897 |              223 |
|   2020 | composite_pca_neutral                             |     0.0243576  |           0.55157  |              223 |
|   2020 | composite_pca_size_neutral                        |     0.0243576  |           0.55157  |              223 |
|   2020 | composite_rolling_ic_weight                       |    -0.00412548 |           0.485597 |              243 |
|   2020 | composite_rolling_ic_weight_industry_size_neutral |     0.0327332  |           0.547325 |              243 |
|   2020 | composite_rolling_ic_weight_size_neutral          |     0.012217   |           0.518519 |              243 |
|   2021 | composite_equal                                   |     0.0833373  |           0.633745 |              243 |
|   2021 | composite_equal_industry_size_neutral             |     0.0426308  |           0.617284 |              243 |
|   2021 | composite_equal_neutral                           |     0.0433613  |           0.621399 |              243 |
|   2021 | composite_equal_size_neutral                      |     0.0433613  |           0.621399 |              243 |
|   2021 | composite_ic_weight                               |     0.0495981  |           0.592593 |              243 |
|   2021 | composite_ic_weight_industry_size_neutral         |     0.0651159  |           0.658436 |              243 |
|   2021 | composite_ic_weight_neutral                       |     0.0691796  |           0.662551 |              243 |
|   2021 | composite_ic_weight_size_neutral                  |     0.0691796  |           0.662551 |              243 |
|   2021 | composite_pca                                     |     0.0154524  |           0.493827 |              243 |
|   2021 | composite_pca_industry_size_neutral               |     0.0646326  |           0.63786  |              243 |
|   2021 | composite_pca_neutral                             |     0.0685593  |           0.650206 |              243 |
|   2021 | composite_pca_size_neutral                        |     0.0685593  |           0.650206 |              243 |
|   2021 | composite_rolling_ic_weight                       |     0.0914532  |           0.63786  |              243 |
|   2021 | composite_rolling_ic_weight_industry_size_neutral |     0.0297731  |           0.559671 |              243 |
|   2021 | composite_rolling_ic_weight_size_neutral          |     0.0301686  |           0.547325 |              243 |
|   2022 | composite_equal                                   |     0.0477755  |           0.578512 |              242 |
|   2022 | composite_equal_industry_size_neutral             |     0.0618621  |           0.619835 |              242 |
|   2022 | composite_equal_neutral                           |     0.0651776  |           0.628099 |              242 |
|   2022 | composite_equal_size_neutral                      |     0.0651776  |           0.628099 |              242 |
|   2022 | composite_ic_weight                               |     0.0883414  |           0.68595  |              242 |
|   2022 | composite_ic_weight_industry_size_neutral         |     0.10489    |           0.710744 |              242 |
|   2022 | composite_ic_weight_neutral                       |     0.103039   |           0.710744 |              242 |
|   2022 | composite_ic_weight_size_neutral                  |     0.103039   |           0.710744 |              242 |
|   2022 | composite_pca                                     |    -0.0119253  |           0.454545 |              242 |
|   2022 | composite_pca_industry_size_neutral               |     0.0325704  |           0.549587 |              242 |
|   2022 | composite_pca_neutral                             |     0.0262227  |           0.524793 |              242 |
|   2022 | composite_pca_size_neutral                        |     0.0262227  |           0.524793 |              242 |
|   2022 | composite_rolling_ic_weight                       |     0.102281   |           0.747934 |              242 |
|   2022 | composite_rolling_ic_weight_industry_size_neutral |     0.113238   |           0.694215 |              242 |
|   2022 | composite_rolling_ic_weight_size_neutral          |     0.108803   |           0.702479 |              242 |
|   2023 | composite_equal                                   |     0.0491261  |           0.648649 |              222 |
|   2023 | composite_equal_industry_size_neutral             |     0.0332055  |           0.567568 |              222 |
|   2023 | composite_equal_neutral                           |     0.0427265  |           0.608108 |              222 |
|   2023 | composite_equal_size_neutral                      |     0.0427265  |           0.608108 |              222 |
|   2023 | composite_ic_weight                               |     0.0731777  |           0.617117 |              222 |
|   2023 | composite_ic_weight_industry_size_neutral         |     0.061415   |           0.594595 |              222 |
|   2023 | composite_ic_weight_neutral                       |     0.0748822  |           0.626126 |              222 |
|   2023 | composite_ic_weight_size_neutral                  |     0.0748822  |           0.626126 |              222 |
|   2023 | composite_pca                                     |     0.060823   |           0.617117 |              222 |
|   2023 | composite_pca_industry_size_neutral               |     0.0539502  |           0.59009  |              222 |
|   2023 | composite_pca_neutral                             |     0.0691614  |           0.599099 |              222 |
|   2023 | composite_pca_size_neutral                        |     0.0691614  |           0.599099 |              222 |
|   2023 | composite_rolling_ic_weight                       |     0.0793064  |           0.662162 |              222 |
|   2023 | composite_rolling_ic_weight_industry_size_neutral |     0.0597381  |           0.603604 |              222 |
|   2023 | composite_rolling_ic_weight_size_neutral          |     0.0718664  |           0.630631 |              222 |

## 11. Five-Layer Long-Short Results

| factor                                            | group   |   mean_period_return |   annual_return |   annual_vol |    sharpe |   max_drawdown |   win_rate |
|:--------------------------------------------------|:--------|---------------------:|----------------:|-------------:|----------:|---------------:|-----------:|
| composite_equal                                   | G5-G1   |           0.00497674 |       0.0645492 |     0.222104 |  0.290626 |      -0.991491 |   0.538947 |
| composite_equal_size_neutral                      | G5-G1   |           0.00441269 |       0.0570453 |     0.200551 |  0.284443 |      -0.966012 |   0.544211 |
| composite_equal_industry_size_neutral             | G5-G1   |           0.0063888  |       0.0835501 |     0.199729 |  0.418316 |      -0.960287 |   0.545263 |
| composite_equal_neutral                           | G5-G1   |           0.00441269 |       0.0570453 |     0.200551 |  0.284443 |      -0.966012 |   0.544211 |
| composite_ic_weight                               | G5-G1   |           0.00685328 |       0.0898682 |     0.207988 |  0.432083 |      -0.978852 |   0.552632 |
| composite_ic_weight_size_neutral                  | G5-G1   |           0.00989977 |       0.132156  |     0.205873 |  0.641928 |      -0.969892 |   0.576842 |
| composite_ic_weight_industry_size_neutral         | G5-G1   |           0.00986217 |       0.131625  |     0.204384 |  0.644008 |      -0.943726 |   0.571579 |
| composite_ic_weight_neutral                       | G5-G1   |           0.00989977 |       0.132156  |     0.205873 |  0.641928 |      -0.969892 |   0.576842 |
| composite_pca                                     | G5-G1   |          -0.0026039  |      -0.0323181 |     0.227808 | -0.141866 |      -0.999492 |   0.507527 |
| composite_pca_size_neutral                        | G5-G1   |           0.00303427 |       0.0389119 |     0.212919 |  0.182754 |      -0.981885 |   0.545161 |
| composite_pca_industry_size_neutral               | G5-G1   |           0.00535159 |       0.0695631 |     0.210671 |  0.330198 |      -0.941442 |   0.551613 |
| composite_pca_neutral                             | G5-G1   |           0.00303427 |       0.0389119 |     0.212919 |  0.182754 |      -0.981885 |   0.545161 |
| composite_rolling_ic_weight                       | G5-G1   |           0.01078    |       0.144652  |     0.234756 |  0.616179 |      -0.984111 |   0.576842 |
| composite_rolling_ic_weight_size_neutral          | G5-G1   |           0.00491457 |       0.0637197 |     0.213106 |  0.299005 |      -0.977468 |   0.551579 |
| composite_rolling_ic_weight_industry_size_neutral | G5-G1   |           0.00760303 |       0.100138  |     0.214644 |  0.466532 |      -0.930729 |   0.556842 |

## 12. Five-Layer Results by Year

|   year | composite_factor                                  |   rank_ic_mean |   rank_ic_win_rate |   long_short_return |     sharpe |   win_rate |
|-------:|:--------------------------------------------------|---------------:|-------------------:|--------------------:|-----------:|-----------:|
|   2020 | composite_equal                                   |    -0.0288959  |           0.452675 |         -0.163018   | -0.70702   |   0.444444 |
|   2021 | composite_equal                                   |     0.0833373  |           0.633745 |          0.293084   |  1.1311    |   0.567901 |
|   2022 | composite_equal                                   |     0.0477755  |           0.578512 |          0.154217   |  0.832427  |   0.570248 |
|   2023 | composite_equal                                   |     0.0491261  |           0.648649 |          0.0204799  |  0.111796  |   0.576577 |
|   2020 | composite_equal_size_neutral                      |     0.0438325  |           0.609053 |         -0.00377922 | -0.0177723 |   0.522634 |
|   2021 | composite_equal_size_neutral                      |     0.0433613  |           0.621399 |          0.0645666  |  0.281151  |   0.534979 |
|   2022 | composite_equal_size_neutral                      |     0.0651776  |           0.628099 |          0.188478   |  1.08055   |   0.61157  |
|   2023 | composite_equal_size_neutral                      |     0.0427265  |           0.608108 |         -0.0159921  | -0.0918279 |   0.504505 |
|   2020 | composite_equal_industry_size_neutral             |     0.0727     |           0.662551 |          0.0749667  |  0.353471  |   0.555556 |
|   2021 | composite_equal_industry_size_neutral             |     0.0426308  |           0.617284 |          0.113497   |  0.518031  |   0.547325 |
|   2022 | composite_equal_industry_size_neutral             |     0.0618621  |           0.619835 |          0.187656   |  1.04112   |   0.607438 |
|   2023 | composite_equal_industry_size_neutral             |     0.0332055  |           0.567568 |         -0.0410216  | -0.22916   |   0.463964 |
|   2020 | composite_equal_neutral                           |     0.0438325  |           0.609053 |         -0.00377922 | -0.0177723 |   0.522634 |
|   2021 | composite_equal_neutral                           |     0.0433613  |           0.621399 |          0.0645666  |  0.281151  |   0.534979 |
|   2022 | composite_equal_neutral                           |     0.0651776  |           0.628099 |          0.188478   |  1.08055   |   0.61157  |
|   2023 | composite_equal_neutral                           |     0.0427265  |           0.608108 |         -0.0159921  | -0.0918279 |   0.504505 |
|   2020 | composite_ic_weight                               |     0.0223423  |           0.549107 |         -0.0181523  | -0.0921579 |   0.493827 |
|   2021 | composite_ic_weight                               |     0.0495981  |           0.592593 |          0.106077   |  0.494061  |   0.526749 |
|   2022 | composite_ic_weight                               |     0.0883414  |           0.68595  |          0.213122   |  1.00356   |   0.615702 |
|   2023 | composite_ic_weight                               |     0.0731777  |           0.617117 |          0.0686102  |  0.336429  |   0.576577 |
|   2020 | composite_ic_weight_size_neutral                  |     0.0323527  |           0.584821 |         -0.0189096  | -0.0956663 |   0.510288 |
|   2021 | composite_ic_weight_size_neutral                  |     0.0691796  |           0.662551 |          0.230395   |  1.13384   |   0.604938 |
|   2022 | composite_ic_weight_size_neutral                  |     0.103039   |           0.710744 |          0.272136   |  1.28536   |   0.623967 |
|   2023 | composite_ic_weight_size_neutral                  |     0.0748822  |           0.626126 |          0.0626747  |  0.308931  |   0.567568 |
|   2020 | composite_ic_weight_industry_size_neutral         |     0.0526773  |           0.620536 |          0.0379539  |  0.200577  |   0.497942 |
|   2021 | composite_ic_weight_industry_size_neutral         |     0.0651159  |           0.658436 |          0.172327   |  0.812494  |   0.563786 |
|   2022 | composite_ic_weight_industry_size_neutral         |     0.10489    |           0.710744 |          0.319081   |  1.5532    |   0.68595  |
|   2023 | composite_ic_weight_industry_size_neutral         |     0.061415   |           0.594595 |          0.0106137  |  0.0524321 |   0.536036 |
|   2020 | composite_ic_weight_neutral                       |     0.0323527  |           0.584821 |         -0.0189096  | -0.0956663 |   0.510288 |
|   2021 | composite_ic_weight_neutral                       |     0.0691796  |           0.662551 |          0.230395   |  1.13384   |   0.604938 |
|   2022 | composite_ic_weight_neutral                       |     0.103039   |           0.710744 |          0.272136   |  1.28536   |   0.623967 |
|   2023 | composite_ic_weight_neutral                       |     0.0748822  |           0.626126 |          0.0626747  |  0.308931  |   0.567568 |
|   2020 | composite_pca                                     |     0.00197822 |           0.542601 |          0.0115138  |  0.0549924 |   0.538117 |
|   2021 | composite_pca                                     |     0.0154524  |           0.493827 |         -0.0928406  | -0.336954  |   0.436214 |
|   2022 | composite_pca                                     |    -0.0119253  |           0.454545 |         -0.065569   | -0.284787  |   0.46281  |
|   2023 | composite_pca                                     |     0.060823   |           0.617117 |          0.0314699  |  0.175283  |   0.603604 |
|   2020 | composite_pca_size_neutral                        |     0.0243576  |           0.55157  |          0.0362544  |  0.186452  |   0.542601 |
|   2021 | composite_pca_size_neutral                        |     0.0685593  |           0.650206 |          0.0586421  |  0.251297  |   0.526749 |
|   2022 | composite_pca_size_neutral                        |     0.0262227  |           0.524793 |         -0.00790948 | -0.0348805 |   0.528926 |
|   2023 | composite_pca_size_neutral                        |     0.0691614  |           0.599099 |          0.0728031  |  0.380616  |   0.585586 |
|   2020 | composite_pca_industry_size_neutral               |     0.0402127  |           0.600897 |          0.105248   |  0.560481  |   0.565022 |
|   2021 | composite_pca_industry_size_neutral               |     0.0646326  |           0.63786  |          0.100762   |  0.435581  |   0.530864 |
|   2022 | composite_pca_industry_size_neutral               |     0.0325704  |           0.549587 |          0.0531652  |  0.239093  |   0.549587 |
|   2023 | composite_pca_industry_size_neutral               |     0.0539502  |           0.59009  |          0.0196633  |  0.100524  |   0.563063 |
|   2020 | composite_pca_neutral                             |     0.0243576  |           0.55157  |          0.0362544  |  0.186452  |   0.542601 |
|   2021 | composite_pca_neutral                             |     0.0685593  |           0.650206 |          0.0586421  |  0.251297  |   0.526749 |
|   2022 | composite_pca_neutral                             |     0.0262227  |           0.524793 |         -0.00790948 | -0.0348805 |   0.528926 |
|   2023 | composite_pca_neutral                             |     0.0691614  |           0.599099 |          0.0728031  |  0.380616  |   0.585586 |
|   2020 | composite_rolling_ic_weight                       |    -0.00412548 |           0.485597 |         -0.142031   | -0.651954  |   0.440329 |
|   2021 | composite_rolling_ic_weight                       |     0.0914532  |           0.63786  |          0.455915   |  1.62478   |   0.62963  |
|   2022 | composite_rolling_ic_weight                       |     0.102281   |           0.747934 |          0.290964   |  1.43566   |   0.681818 |
|   2023 | composite_rolling_ic_weight                       |     0.0793064  |           0.662162 |          0.0504454  |  0.254542  |   0.554054 |
|   2020 | composite_rolling_ic_weight_size_neutral          |     0.012217   |           0.518519 |         -0.132952   | -0.592087  |   0.444444 |
|   2021 | composite_rolling_ic_weight_size_neutral          |     0.0301686  |           0.547325 |          0.0671917  |  0.305033  |   0.526749 |
|   2022 | composite_rolling_ic_weight_size_neutral          |     0.108803   |           0.702479 |          0.320339   |  1.65757   |   0.669421 |
|   2023 | composite_rolling_ic_weight_size_neutral          |     0.0718664  |           0.630631 |          0.0434547  |  0.222584  |   0.567568 |
|   2020 | composite_rolling_ic_weight_industry_size_neutral |     0.0327332  |           0.547325 |         -0.0468121  | -0.201245  |   0.477366 |
|   2021 | composite_rolling_ic_weight_industry_size_neutral |     0.0297731  |           0.559671 |          0.0831547  |  0.387397  |   0.502058 |
|   2022 | composite_rolling_ic_weight_industry_size_neutral |     0.113238   |           0.694215 |          0.39016    |  1.98592   |   0.681818 |
|   2023 | composite_rolling_ic_weight_industry_size_neutral |     0.0597381  |           0.603604 |          0.0108365  |  0.0550668 |   0.567568 |

## 13. Layer Monotonicity

If G5 is materially stronger than G1 while the middle layers are not perfectly monotonic, the composite signal is still useful for top-group stock selection, but less reliable for ranking middle-quantile stocks.

| model                                             | year   |    g1_return |    g2_return |   g3_return |   g4_return |    g5_return |       g5_g1 |   monotonic_score |
|:--------------------------------------------------|:-------|-------------:|-------------:|------------:|------------:|-------------:|------------:|------------------:|
| composite_equal                                   | all    | -0.00162111  |  0.00249835  | 0.0036632   |  0.00818479 |  0.00335563  |  0.00497674 |              0.75 |
| composite_equal_size_neutral                      | all    |  0.0002102   |  0.000121368 | 0.00608792  |  0.00482319 |  0.00462289  |  0.00441269 |              0.25 |
| composite_equal_industry_size_neutral             | all    | -0.000319772 |  0.00132758  | 0.00409975  |  0.00475948 |  0.00606902  |  0.0063888  |              1    |
| composite_equal_neutral                           | all    |  0.0002102   |  0.000121368 | 0.00608792  |  0.00482319 |  0.00462289  |  0.00441269 |              0.25 |
| composite_ic_weight                               | all    | -0.00331766  |  0.00354655  | 0.00680025  |  0.00574161 |  0.00353562  |  0.00685328 |              0.5  |
| composite_ic_weight_size_neutral                  | all    | -0.00389261  |  0.0028765   | 0.00285894  |  0.00849661 |  0.00600715  |  0.00989977 |              0.5  |
| composite_ic_weight_industry_size_neutral         | all    | -0.0033889   |  0.00130219  | 0.00458486  |  0.00732518 |  0.00647327  |  0.00986217 |              0.75 |
| composite_ic_weight_neutral                       | all    | -0.00389261  |  0.0028765   | 0.00285894  |  0.00849661 |  0.00600715  |  0.00989977 |              0.5  |
| composite_pca                                     | all    |  0.00246579  |  0.00666699  | 0.00348519  |  0.0032963  | -0.000138108 | -0.0026039  |              0.25 |
| composite_pca_size_neutral                        | all    |  0.00220808  |  0.00136821  | 0.000986858 |  0.00598062 |  0.00524236  |  0.00303427 |              0.25 |
| composite_pca_industry_size_neutral               | all    |  0.00098781  |  0.00298086  | 0.000230452 |  0.00532236 |  0.0063394   |  0.00535159 |              0.75 |
| composite_pca_neutral                             | all    |  0.00220808  |  0.00136821  | 0.000986858 |  0.00598062 |  0.00524236  |  0.00303427 |              0.25 |
| composite_rolling_ic_weight                       | all    | -0.00241882  | -0.00454366  | 0.00541915  |  0.00930045 |  0.00836113  |  0.01078    |              0.5  |
| composite_rolling_ic_weight_size_neutral          | all    |  0.000558303 | -0.00146081  | 0.00295709  |  0.0083128  |  0.00547287  |  0.00491457 |              0.5  |
| composite_rolling_ic_weight_industry_size_neutral | all    | -0.000119081 | -0.00157429  | 0.00254411  |  0.00755923 |  0.00748395  |  0.00760303 |              0.5  |

## 14. Top Group Turnover

| model                                             |   avg_turnover |   median_turnover |   sample_periods |
|:--------------------------------------------------|---------------:|------------------:|-----------------:|
| composite_equal                                   |      0.159041  |          0.111111 |              969 |
| composite_equal_size_neutral                      |      0.207316  |          0.222222 |              969 |
| composite_equal_industry_size_neutral             |      0.20766   |          0.222222 |              969 |
| composite_equal_neutral                           |      0.207316  |          0.222222 |              969 |
| composite_ic_weight                               |      0.0712074 |          0.111111 |              969 |
| composite_ic_weight_size_neutral                  |      0.0638688 |          0        |              969 |
| composite_ic_weight_industry_size_neutral         |      0.0682261 |          0.111111 |              969 |
| composite_ic_weight_neutral                       |      0.0638688 |          0        |              969 |
| composite_pca                                     |      0.238262  |          0.222222 |              949 |
| composite_pca_size_neutral                        |      0.23674   |          0.222222 |              949 |
| composite_pca_industry_size_neutral               |      0.23756   |          0.222222 |              949 |
| composite_pca_neutral                             |      0.23674   |          0.222222 |              949 |
| composite_rolling_ic_weight                       |      0.110423  |          0.111111 |              969 |
| composite_rolling_ic_weight_size_neutral          |      0.12854   |          0.111111 |              969 |
| composite_rolling_ic_weight_industry_size_neutral |      0.13393   |          0.111111 |              969 |

## 15. Transaction Cost Estimate

Annual transaction cost is approximated as average turnover * one-way cost * annual rebalance count * 2. The multiplier 2 approximates round-trip buy and sell costs.

| model                                 |   rebalance_days |   avg_turnover |   cost_rate |   annual_cost_estimate |
|:--------------------------------------|-----------------:|---------------:|------------:|-----------------------:|
| composite_equal                       |                5 |       0.159041 |       0.001 |             0.0160314  |
| composite_equal                       |                5 |       0.159041 |       0.002 |             0.0320627  |
| composite_equal                       |                5 |       0.159041 |       0.003 |             0.0480941  |
| composite_equal                       |               10 |       0.159041 |       0.001 |             0.00801569 |
| composite_equal                       |               10 |       0.159041 |       0.002 |             0.0160314  |
| composite_equal                       |               10 |       0.159041 |       0.003 |             0.0240471  |
| composite_equal                       |               20 |       0.159041 |       0.001 |             0.00400784 |
| composite_equal                       |               20 |       0.159041 |       0.002 |             0.00801569 |
| composite_equal                       |               20 |       0.159041 |       0.003 |             0.0120235  |
| composite_equal                       |               60 |       0.159041 |       0.001 |             0.00133595 |
| composite_equal                       |               60 |       0.159041 |       0.002 |             0.0026719  |
| composite_equal                       |               60 |       0.159041 |       0.003 |             0.00400784 |
| composite_equal_size_neutral          |                5 |       0.207316 |       0.001 |             0.0208974  |
| composite_equal_size_neutral          |                5 |       0.207316 |       0.002 |             0.0417948  |
| composite_equal_size_neutral          |                5 |       0.207316 |       0.003 |             0.0626923  |
| composite_equal_size_neutral          |               10 |       0.207316 |       0.001 |             0.0104487  |
| composite_equal_size_neutral          |               10 |       0.207316 |       0.002 |             0.0208974  |
| composite_equal_size_neutral          |               10 |       0.207316 |       0.003 |             0.0313461  |
| composite_equal_size_neutral          |               20 |       0.207316 |       0.001 |             0.00522436 |
| composite_equal_size_neutral          |               20 |       0.207316 |       0.002 |             0.0104487  |
| composite_equal_size_neutral          |               20 |       0.207316 |       0.003 |             0.0156731  |
| composite_equal_size_neutral          |               60 |       0.207316 |       0.001 |             0.00174145 |
| composite_equal_size_neutral          |               60 |       0.207316 |       0.002 |             0.0034829  |
| composite_equal_size_neutral          |               60 |       0.207316 |       0.003 |             0.00522436 |
| composite_equal_industry_size_neutral |                5 |       0.20766  |       0.001 |             0.0209321  |
| composite_equal_industry_size_neutral |                5 |       0.20766  |       0.002 |             0.0418642  |
| composite_equal_industry_size_neutral |                5 |       0.20766  |       0.003 |             0.0627963  |
| composite_equal_industry_size_neutral |               10 |       0.20766  |       0.001 |             0.010466   |
| composite_equal_industry_size_neutral |               10 |       0.20766  |       0.002 |             0.0209321  |
| composite_equal_industry_size_neutral |               10 |       0.20766  |       0.003 |             0.0313981  |

## 16. Neutralization

The v2.1 model applies industry + size neutralization through cross-sectional regression on `factor_size` and industry dummy variables. The residual is used as the neutralized stock-selection signal.

| model             |   raw_rank_ic |   size_neutral_rank_ic |   industry_size_neutral_rank_ic |   raw_g5_g1_return |   size_neutral_g5_g1_return |   industry_size_neutral_g5_g1_return |   raw_size_corr |   size_neutral_size_corr |   industry_size_neutral_size_corr |
|:------------------|--------------:|-----------------------:|--------------------------------:|-------------------:|----------------------------:|-------------------------------------:|----------------:|-------------------------:|----------------------------------:|
| equal_weight      |     0.0375757 |              0.0488909 |                       0.0530186 |          0.0645492 |                   0.0570453 |                            0.0835501 |      0.491494   |                0.0630807 |                         0.0577266 |
| ic_weight         |     0.0587337 |              0.07048   |                       0.0715793 |          0.0898682 |                   0.132156  |                            0.131625  |     -0.00916701 |                0.0889185 |                         0.0944046 |
| pca               |     0.0159278 |              0.0470875 |                       0.047884  |         -0.0323181 |                   0.0389119 |                            0.0695631 |     -0.100266   |                0.0653939 |                         0.0728277 |
| rolling_ic_weight |     0.066925  |              0.0553519 |                       0.0587943 |          0.144652  |                   0.0637197 |                            0.100138  |      0.272898   |                0.0816105 |                         0.0762201 |

## 17. PCA Review

PCA is reviewed separately because it extracts common factor variation rather than directly optimizing future-return predictability. Weak PCA performance can occur when the first principal component captures shared style exposure or noise instead of predictive information.

| component   |   explained_variance_ratio |   cumulative_explained_variance_ratio |
|:------------|---------------------------:|--------------------------------------:|
| PC1         |                  0.377269  |                              0.377269 |
| PC2         |                  0.256525  |                              0.633793 |
| PC3         |                  0.197568  |                              0.831362 |
| PC4         |                  0.098561  |                              0.929923 |
| PC5         |                  0.0700772 |                              1        |

| component   | factor             |    loading |
|:------------|:-------------------|-----------:|
| PC1         | factor_momentum    | -0.489091  |
| PC1         | factor_volatility  |  0.587857  |
| PC1         | factor_turnover    |  0.540405  |
| PC1         | factor_size        | -0.0837114 |
| PC1         | factor_reversal_5d |  0.340837  |
| PC2         | factor_momentum    |  0.475497  |
| PC2         | factor_volatility  |  0.347918  |
| PC2         | factor_turnover    |  0.445281  |
| PC2         | factor_size        | -0.143032  |
| PC2         | factor_reversal_5d | -0.658879  |
| PC3         | factor_momentum    |  0.0139892 |
| PC3         | factor_volatility  |  0.09649   |
| PC3         | factor_turnover    |  0.110032  |
| PC3         | factor_size        |  0.986004  |
| PC3         | factor_reversal_5d | -0.0786374 |
| PC4         | factor_momentum    | -0.707538  |
| PC4         | factor_volatility  |  0.0176562 |
| PC4         | factor_turnover    | -0.244303  |
| PC4         | factor_size        | -0.0172749 |
| PC4         | factor_reversal_5d | -0.662643  |
| PC5         | factor_momentum    | -0.184085  |
| PC5         | factor_volatility  | -0.723709  |
| PC5         | factor_turnover    |  0.661738  |
| PC5         | factor_size        | -0.0057196 |
| PC5         | factor_reversal_5d | -0.0665468 |

## 18. Robustness Note

The original full-sample IC-weighted method is kept as a benchmark, but it can contain look-ahead bias. The rolling IC-weighted factor is therefore added as a more realistic candidate because each date only uses historical IC information.

## 19. Figures

- `figures/factor_spearman_corr_heatmap.png`
- `figures/ic_weight_bar.png`
- `figures/rolling_ic_weights.png`
- `figures/composite_factor_distribution.png`
- `figures/composite_factor_distribution_compare.png`
- `figures/composite_factor_timeseries_compare.png`
- `figures/composite_rank_ic_series_ic_weight.png`
- `figures/layer_cumret_equal_weight.png`
- `figures/layer_cumret_ic_weight.png`
- `figures/long_short_cumret_ic_weight.png`
- `figures/top_group_turnover_ic_weight.png`
- `figures/pca_explained_variance.png`
- `figures/pca_components_heatmap.png`
- `figures/layer_monotonicity_by_year.png`
- `figures/turnover_cost_estimation.png`

## 20. Average Cross-Sectional Correlation

|                    |   factor_momentum |   factor_volatility |   factor_turnover |   factor_size |   factor_reversal_5d |
|:-------------------|------------------:|--------------------:|------------------:|--------------:|---------------------:|
| factor_momentum    |        1          |          -0.230352  |       -0.107372   |   -0.00205756 |          -0.441      |
| factor_volatility  |       -0.230352   |           1         |        0.58018    |   -0.0322792  |           0.0466122  |
| factor_turnover    |       -0.107372   |           0.58018   |        1          |    0.0134532  |          -0.00446644 |
| factor_size        |       -0.00205756 |          -0.0322792 |        0.0134532  |    1          |           0.00793486 |
| factor_reversal_5d |       -0.441      |           0.0466122 |       -0.00446644 |    0.00793486 |           1          |
