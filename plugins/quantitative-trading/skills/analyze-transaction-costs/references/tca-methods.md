# Transaction-cost analysis methods

## Sign and units

Choose one convention and test it with a favorable buy and favorable sell.
One useful convention is:

```text
side = +1 for a buy, -1 for a sell
executed_cost = side * (execution_price - benchmark_price) * executed_quantity
```

Positive values then represent cost and negative values represent improvement.
Add explicit charges separately. Convert currency cost to basis points only
with a declared denominator, usually benchmark notional. Preserve currency for
portfolio aggregation.

For multiple fills, use quantity-weighted executed value rather than averaging
fill-level basis points. Handle contract multipliers and FX conversion before
aggregation.

## Implementation-shortfall bridge

Construct a bridge from the paper portfolio at the decision benchmark to the
actual outcome:

1. executed-price cost relative to the benchmark;
2. explicit commissions, fees, taxes, and rebates;
3. delay cost between the decision and release;
4. opportunity cost on residual quantity at the declared terminal price;
5. unexplained residual from rounding, FX, corporate actions, or missing data.

Expanded labels such as spread, impact, and market movement can be useful, but
they depend on a model or counterfactual. Present them as estimates and state
the identification method.

## Benchmark diagnostics

- Verify the benchmark existed and was observable at the stated time.
- Ensure the price source, adjustment state, timezone, and trading calendar
  match the fills.
- Report performance against the mandate benchmark first. Secondary benchmarks
  are sensitivity analyses, not substitutes.
- Separate market-adjusted performance from raw slippage and document the
  index, beta, factor, or hedge used for adjustment.
- Do not use the evaluated broker's own pre-trade estimate as the only
  normalization baseline.

## Comparison design

Raw averages mix strategy choice with market conditions. Build a comparison
table containing at least side, size or ADV bucket, volatility, spread,
participation, duration, market move, completion, and parent-order identifier.

Choose the design:

- randomized or genuinely matched parent orders: paired differences and a
  paired nonparametric or permutation test;
- separate comparable populations: rank, permutation, or robust
  regression-adjusted tests;
- repeated orders by asset, day, or manager: clustered or hierarchical
  uncertainty;
- skewed tails: median, quantiles, expected shortfall, and tail frequencies in
  addition to the mean.

Check balance before outcome testing. Simpson's paradox is a warning that a
pooled result can reverse within important strata.

## Adaptation attribution

Reconstruct the initial schedule and each allowed deviation. At every change,
capture observable price, spread, volume, forecast, remaining quantity, and
remaining risk. Compare the adapted path with a predeclared counterfactual over
the same horizon. Do not classify a decision as skilled only because prices
later moved in its favor.

## Minimum report

- covered orders, dates, venues, and data completeness;
- benchmark and sign convention;
- total shortfall and additive decomposition;
- completion and opportunity cost;
- distribution and tail behavior;
- fair-comparison design and uncertainty;
- sensitivity to benchmark, exclusions, and categorization;
- actionable control or experiment.
