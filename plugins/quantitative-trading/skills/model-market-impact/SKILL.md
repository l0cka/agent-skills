---
name: model-market-impact
description: Specify, calibrate, validate, and challenge market-impact models for orders and portfolios. Use when estimating temporary or persistent impact, selecting impact factors or functional shape, calibrating pre-trade cost curves, comparing broker models, reverse-engineering black-box estimates, or stress-testing impact assumptions.
---

# Model Market Impact

Model the incremental price effect associated with executing an order, with an
explicit counterfactual and uncertainty range. Keep observed slippage distinct
from modeled impact.

Read [references/impact-modeling.md](references/impact-modeling.md) for
estimands, features, shape constraints, calibration, and challenge tests. Read
the shared [method provenance](../../references/method-provenance.md) when
citing or extending the published framework.

## Define The Estimand

1. State the decision benchmark, execution horizon, post-trade horizon, side,
   units, and whether the target is total slippage, temporary impact, persistent
   impact, or an implementation-cost component.
2. Describe the no-order counterfactual and how common market movement is
   removed. A benchmark adjustment is not automatically causal identification.
3. Set the observation grain at the parent order or another independent
   economic unit. Do not treat child fills as independent samples.

## Specify And Fit

Start with an interpretable baseline. Use order size relative to expected volume,
participation or trading rate, volatility, spread, duration, liquidity stability,
and market regime. Add factors only when they improve temporal holdout
performance and preserve plausible behavior.

Require the fitted response to be directionally sensible within the supported
domain: larger or faster orders should not become cheaper without an explained
interaction. Test linear, concave, and convex alternatives instead of assuming
one universal shape.

Fit on chronological training data. Keep validation and final test periods
untouched, and evaluate residuals by side, size, liquidity, volatility, asset,
venue, and regime.

## Challenge The Model

- Compare against simple and existing production baselines.
- Reconcile predicted cost with realized implementation shortfall without
  claiming they are identical.
- Test monotonicity, calibration, tail errors, parameter stability, missing-data
  behavior, and extrapolation.
- Separate temporary decay from information-driven persistence only when the
  data design supports it.
- For a black-box broker model, use controlled input perturbations and label the
  result an approximation of behavior, not recovered intellectual property.

## Deliver

Provide the estimand, counterfactual, population, features available at
prediction time, functional form, parameter uncertainty, temporal validation,
residual diagnostics, supported domain, stress range, and limitations. Do not
use a cost estimate to authorize live execution.
