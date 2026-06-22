"""Strategy improvement checklist for Week 4 reporting."""

import pandas as pd


def build_strategy_improvement_list() -> pd.DataFrame:
    rows = [
        {
            "direction": "dynamic_factor_weight",
            "proposal": "Use rolling IC weights instead of full-sample fixed IC weights.",
            "risk_addressed": "前视偏差和因子阶段性失效",
            "implementation_priority": "high",
            "week3_connection": "Week 2 已生成 rolling IC 信号，Week 3 可直接作为对照信号回测。",
        },
        {
            "direction": "stop_loss_control",
            "proposal": "Add drawdown-based de-risking when portfolio drawdown breaches 10%-20%.",
            "risk_addressed": "极端行情最大回撤",
            "implementation_priority": "high",
            "week3_connection": "Week 3 已有回撤降仓和参数网格，可在 Week 4 复盘其适用区间。",
        },
        {
            "direction": "volatility_target_position",
            "proposal": "Scale exposure according to rolling realized volatility and target annual volatility.",
            "risk_addressed": "组合波动率过高",
            "implementation_priority": "medium",
            "week3_connection": "Week 3 已测试 10%/15%/20% 目标波动率。",
        },
        {
            "direction": "industry_weight_constraint",
            "proposal": "Limit single-industry exposure and monitor active industry bets.",
            "risk_addressed": "行业集中和风格切换",
            "implementation_priority": "high",
            "week3_connection": "Week 3 已生成行业暴露和行业权重约束结果。",
        },
        {
            "direction": "single_stock_weight_constraint",
            "proposal": "Set max single-stock weight and minimum holding count.",
            "risk_addressed": "个股集中风险",
            "implementation_priority": "medium",
            "week3_connection": "Week 3 已加入单股权重上限和最少持股约束。",
        },
        {
            "direction": "turnover_cost_control",
            "proposal": "Prefer lower-frequency rebalance if factor decay and turnover allow it.",
            "risk_addressed": "交易成本侵蚀",
            "implementation_priority": "high",
            "week3_connection": "Week 3 参数敏感性表已联动换手率和年化成本。",
        },
        {
            "direction": "liquidity_and_tradeability_filter",
            "proposal": "Replace learning-version tradeability rules with real suspension, limit-up/down and ST flags.",
            "risk_addressed": "不可交易和成交偏差",
            "implementation_priority": "medium",
            "week3_connection": "Week 3 已预留学习版交易可行性过滤模块。",
        },
    ]
    return pd.DataFrame(rows)
