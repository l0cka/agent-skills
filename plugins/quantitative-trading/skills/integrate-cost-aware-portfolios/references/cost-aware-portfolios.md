# Cost-aware portfolio decisions

## Decision bridge

For each candidate trade, connect:

```text
gross expected benefit
- acquisition and implementation cost
- expected financing, tax, or borrow cost when in scope
- expected future liquidation cost
= net expected benefit before uncertainty
```

Match every component to a horizon and avoid counting the same price movement
as both impact and alpha decay.

## Pre-trade of pre-trade

Before final target construction:

1. estimate the trade list implied by each candidate portfolio.
2. generate cost, risk, duration, and completion ranges.
3. feed those ranges back into the portfolio choice.
4. compare with no trade and partial implementation.
5. retain the ex-ante inputs for later attribution.

This prevents the optimizer from selecting an attractive paper portfolio that
is too expensive or slow to implement.

## Cost integration

Linear cost penalties are transparent but may understate large-order impact.
Piecewise-linear, quadratic, or convex approximations can represent increasing
marginal cost while remaining tractable. Validate any approximation over the
actual size and participation domain.

Useful controls include turnover budgets, per-asset liquidity limits, minimum
net-benefit thresholds, and no-trade regions. Constraints should complement,
not conceal, the economic cost model.

## Cost-adjusted frontier

Evaluate candidate portfolios on:

- expected return or alpha after implementation cost.
- portfolio risk and benchmark-relative risk.
- turnover, concentration, and liquidity.
- implementation duration and residual execution risk.
- expected acquisition and stressed liquidation cost.

Show the no-trade portfolio on the same comparison. A frontier is decision
support, not proof that the forecasts are correct.

## Capacity and alpha capture

Scale capital, order sizes, or turnover while holding the stated signal and
liquidity assumptions consistent. For each level, recompute impact, schedule,
completion, and net expected benefit. Treat capacity as reached when marginal
net benefit, risk, or operational limits fail. Do not use an arbitrary ADV
threshold.

Relate alpha decay to execution speed. Fast execution may preserve more alpha
but consume it through impact. Slow execution may reduce impact while exposing
the order to decay and market risk.

## Liquidation stress

Model a separate exit trade list and test:

- ordinary and stressed volumes.
- higher spread and volatility.
- correlation convergence and factor shocks.
- shortened horizon and participation caps.
- unavailable venues or instruments.
- concentration and one-sided market pressure.

Report liquidation cost as a range tied to scenarios, not a precise invariant.

## Backtest controls

Use point-in-time holdings, corporate actions, liquidity, risk estimates, and
cost-model versions. Apply costs at the same rebalance grain used in production.
Keep turnover and unfilled quantity, and test sensitivity to systematic cost
underestimation.
