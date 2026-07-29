---
name: model-execution-risk
description: Estimate volatility, covariance, factor exposure, timing risk, and residual portfolio risk during execution. Use when selecting risk inputs for an execution optimizer, comparing volatility forecasts, modeling unexecuted inventory, measuring tracking error, stress-testing a basket, or diagnosing covariance and factor-model instability.
---

# Model Execution Risk

Model the uncertainty carried by the unexecuted position over the execution
horizon. Match the risk measure, horizon, and covariance treatment to the
actual order and schedule.

Read [references/execution-risk.md](references/execution-risk.md) for volatility,
covariance, factor, residual-risk, and stress methods. Read the shared
[method provenance](../../references/method-provenance.md) when citing or
extending the published framework.

## Establish The Exposure

1. Reconcile signed parent quantity, executed quantity, residual quantity,
   prices, contract multipliers, FX, and the schedule clock.
2. Define the risk target: price variance, standard deviation, tracking error,
   factor exposure, value at risk, or another mandate-specific loss measure.
3. State the return interval, annualization convention, execution horizon, and
   whether overnight or auction risk is included.
4. For baskets, model signed covariance across residual positions. Opposite-side
   trades can hedge or amplify risk depending on the covariance structure.

## Estimate Inputs

Compare a simple historical estimator with at least one adaptive or structured
alternative, such as exponentially weighted volatility, a conditional
volatility model, shrinkage covariance, or a factor model.

Use only information available at the estimate time. Check missing prices,
stale instruments, asynchronous closes, corporate actions, degrees of freedom,
positive-semidefinite covariance, and concentration in dominant factors.

## Convert To Schedule Risk

Apply risk to the residual path, not only the initial portfolio. Report how risk
changes after each planned interval and how much depends on uncertain
correlation, volume, and completion.

Do not scale volatility by the square root of time across horizons where
autocorrelation, jumps, session boundaries, or changing liquidity make that
assumption unreliable.

## Stress And Deliver

Stress volatility level, correlation, factor shocks, gap risk, volume shortfall,
and delayed completion. Provide central and stressed residual-risk paths,
estimator choices, uncertainty, dominant contributors, data-quality failures,
and safe fallback behavior.
