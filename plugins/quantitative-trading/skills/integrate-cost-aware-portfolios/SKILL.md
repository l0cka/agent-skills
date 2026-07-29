---
name: integrate-cost-aware-portfolios
description: Incorporate transaction costs, market impact, liquidity, capacity, and liquidation risk into portfolio construction and rebalancing. Use for cost-adjusted frontiers, turnover-aware optimization, pre-trade-of-pre-trade analysis, investment-capacity studies, acquisition and liquidation scenarios, alpha capture, or deciding whether a rebalance remains worthwhile after implementation.
---

# Integrate Cost-Aware Portfolios

Evaluate the investment decision and its implementation together. A target
portfolio is not economically optimal when expected trading costs, capacity,
and liquidation risk erase its expected benefit.

Read [references/cost-aware-portfolios.md](references/cost-aware-portfolios.md)
for cost integration, capacity, liquidation, and governance. Read the shared
[method provenance](../../references/method-provenance.md) when citing or
extending the published framework.

## Build The Net Decision

1. Freeze current holdings, candidate target, expected returns or alpha horizon,
   risk model, constraints, benchmark, and decision timestamp.
2. Convert target-minus-current holdings into a signed trade list and estimate
   explicit costs, spread, impact, delay, and any expected alpha decay.
3. Distinguish one-way acquisition cost, implementation cost, expected holding
   benefit, and future liquidation cost. Avoid double-counting impact or risk.
4. Compare the target with a no-trade baseline and simpler partial-rebalance
   alternatives.

## Optimize And Diagnose

Place costs inside the portfolio decision when they vary materially by asset or
trade size. Use scenario or piecewise approximations when the true cost curve is
nonlinear, and verify that any approximation preserves ranking and feasibility.

Trace a net-benefit or cost-adjusted frontier across risk aversion, turnover,
capital, and holding horizon. Report which trades are driven by alpha, risk,
cash, constraints, or cost.

Measure capacity by increasing capital or turnover under consistent alpha,
liquidity, and impact assumptions. Stress crowded liquidation, volume shortfall,
volatility, correlation, and a shortened exit horizon.

## Preserve Evidence

Use chronological, point-in-time data and include implementation costs inside
backtests. Keep alpha-model validation separate from cost-model calibration and
reserve a final period for the combined decision.

## Deliver

Provide gross and net expected benefit, cost and risk decomposition, no-trade
comparison, retained and rejected trades, capacity and liquidation scenarios,
sensitivity to cost-model error, constraints, uncertainty, and a reversible
paper or shadow implementation plan.
