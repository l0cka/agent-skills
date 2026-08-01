# Execution-risk methods

## Returns and volatility

Use adjusted prices and a declared return convention. Log returns are convenient
for aggregation, while PnL risk must ultimately map back to position, price,
multiplier, and currency.

Compare:

- rolling historical volatility as a transparent baseline.
- exponentially weighted estimates for faster adaptation.
- ARCH or GARCH-family models when conditional variance is material and there
  is enough data to estimate them reliably.
- implied or market-wide volatility as a scenario input, not an automatic
  substitute for instrument-specific risk.

Evaluate forecast error over the actual execution horizon. Do not select a
model only by in-sample likelihood.

## Covariance and factors

Sample covariance becomes unstable when the asset count is large relative to
history. Check eigenvalues, condition number, effective rank, and
positive-semidefinite status.

Consider shrinkage or factor structure:

```text
asset_returns = factor_loadings * factor_returns + idiosyncratic_returns
covariance = systematic_covariance + residual_covariance
```

Keep the factor definition, exposure timestamp, and residual assumptions
explicit. Statistical factors can compress risk but may be harder to interpret
and less stable across regimes.

## Residual execution risk

Let `r_t` be the signed residual dollar or unit exposure after interval `t`, and
let `C_t` be a covariance matrix scaled to the relevant interval. A generic
variance contribution is:

```text
residual_variance_t = transpose(r_t) * C_t * r_t
```

Aggregate interval contributions according to the assumed return dependence.
If intervals are not independent, include cross-time covariance or present a
simulation-based range.

Report both total residual risk and contributions by asset, factor, side,
sector, venue, or other decision-relevant grouping.

## Timing and benchmark risk

Timing risk is uncertainty from leaving quantity exposed while execution
continues. Benchmark-relative risk may instead use tracking error against an
index, factor hedge, or target portfolio. Do not mix these denominators without
explaining the decision they answer.

The risk model should reflect schedule shape: front-loaded schedules usually
reduce residual exposure sooner, while slower schedules preserve more price
uncertainty.

## Stress set

At minimum test:

- volatility multipliers and volatility-of-volatility.
- correlation moving toward one within stressed groups.
- factor shocks and basis breakdown.
- stale or missing instruments.
- volume shortfall and extended horizon.
- opening, closing, and overnight gap scenarios.
- covariance estimated from alternative windows.

Define system behavior when covariance repair fails or a required risk input is
stale.
