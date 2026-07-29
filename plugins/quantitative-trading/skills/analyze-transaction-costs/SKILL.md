---
name: analyze-transaction-costs
description: Measure, decompose, and compare transaction costs and execution quality. Use for implementation shortfall, benchmark slippage, explicit and implicit costs, opportunity cost, TCA reports, broker or algorithm comparisons, adaptation attribution, cost-normalized scores, and post-trade statistical analysis.
---

# Analyze Transaction Costs

Measure the economic implementation outcome at a declared grain and benchmark.
Do not infer execution quality from raw average slippage alone.

Read [references/tca-methods.md](references/tca-methods.md) for sign
conventions, decomposition, comparison design, and diagnostics. Read the shared
[method provenance](../../references/method-provenance.md) when citing the
published framework.

## Prepare The Population

1. Define whether one row is a parent order, child order, fill, interval,
   security-day, or portfolio.
2. Reconcile parent quantity to child orders, fills, cancellations, residuals,
   and any unexecuted quantity.
3. Normalize side, currency, multiplier, fees, rebates, corporate actions, and
   timestamps. Preserve both monetary and basis-point results.
4. Select the benchmark from the mandate and freeze it before examining
   outcomes. State its timestamp and source.
5. Record exclusions and missingness. Never silently discard rejects, partial
   fills, or orders with unavailable benchmarks.

## Attribute The Cost

Report, when observable:

- commissions, fees, taxes, and rebates;
- spread or liquidity-taking cost;
- delay between decision and order release;
- market impact and market movement;
- timing risk and benchmark uncertainty;
- opportunity cost from unfilled or cancelled quantity.

Make the decomposition add back to total implementation shortfall or explain the
residual. Do not label a component causal unless the design identifies it.

## Compare Fairly

Match or stratify by side, order size, liquidity, volatility, horizon, market
movement, algorithm family, and mandate. Use paired tests only when orders were
assigned in a way that makes the pairs independent and the algorithms do not
interfere. Otherwise use independent-sample, regression-adjusted, or
hierarchical comparisons.

Report effect size, confidence interval, sample size, cluster count, tail loss,
and completion rate. Correct for repeated slicing of the same economic order and
multiple testing.

## Deliver

Provide the question, population, benchmark and sign convention, covered period,
reconciliation, cost bridge, uncertainty, stratified comparisons, outliers,
missing data, and the next test or execution change. Keep live mutations outside
scope unless explicitly authorized.
