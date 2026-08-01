# Market-impact modeling methods

## Estimand first

Impact is not directly observed. A useful analysis distinguishes:

- total implementation shortfall.
- explicit spread and fees.
- order-associated temporary displacement that may decay.
- persistent displacement associated with information or lasting pressure.
- unrelated market or factor movement.

State the post-trade horizon used to assess decay. Results are horizon-dependent,
and persistent impact is especially difficult to identify when trades contain
information.

## Candidate inputs

Use only values available at estimate time:

- signed parent quantity and size relative to forecast volume.
- participation, trading rate, duration, and schedule concentration.
- volatility or another price-elasticity proxy.
- quoted or effective spread and depth.
- daily and intraday volume forecasts.
- liquidity stability, block activity, and venue mix.
- market capitalization or asset-class descriptors when they add information.
- order side, urgency, portfolio context, and market regime.

Avoid realized volume, realized volatility, or final schedule statistics in a
pre-trade model unless you lag or forecast them.

## Functional form

Begin with a low-dimensional, interpretable baseline. Common choices model cost
as a scale term multiplied by powers or transformations of normalized size,
participation, volatility, and spread. Consider:

- linear response for a narrow, well-supported operating range.
- concave response when marginal impact declines with size.
- convex response when liquidity becomes increasingly scarce.
- piecewise or monotone models when the response changes by regime.

Do not infer global shape from a narrow sample. Enforce nonnegative or monotone
behavior only where domain knowledge supports it, and report exceptions rather
than hiding them.

## Calibration workflow

1. Reconcile orders, fills, benchmark prices, fees, and residual quantities.
2. Choose a parent-order target and define all filters before fitting.
3. Split chronologically. Keep the latest representative period as final test.
4. Fit a simple benchmark before nonlinear or machine-learning alternatives.
5. Use robust loss or explicit tail treatment when outliers are genuine
   execution outcomes.
6. Quantify parameter uncertainty and dependence by asset and date.
7. Evaluate calibration plots and residuals by size, participation, volatility,
   spread, side, duration, and regime.
8. Refit only under a declared cadence or drift rule.

## Model checks

- additive reconciliation to the broader TCA measure.
- prediction bias and absolute error in currency and basis points.
- interval coverage and tail underprediction.
- monotonicity under one-factor perturbations.
- stability across windows and assets.
- sensitivity to volume and volatility forecast error.
- behavior at zero or tiny size.
- behavior near participation and liquidity limits.
- graceful failure for missing, stale, or out-of-domain inputs.

## Comparing provider estimates

Use the same order population and information timestamp for every provider.
Compare realized error, calibration, tails, and ranking quality—not only each
provider's predicted level. A provider's own estimate must not be the sole
normalizer of its performance.

For black-box response mapping, build a bounded synthetic grid. Vary one input at
a time. Repeat requests to measure noise. Fit a surrogate only within the
queried domain. Respect contractual and access restrictions.
