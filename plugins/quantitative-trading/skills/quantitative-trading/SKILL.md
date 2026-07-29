---
name: quantitative-trading
description: Route and govern evidence-led quantitative analysis for trading systems. Use for broad or cross-cutting strategy diagnostics, telemetry, backtests, edge and fill analysis, exposure, drawdowns, latency, market selection, parameter changes, and requests spanning execution design, transaction costs, impact, volume, risk, optimization, model validation, or cost-aware portfolios.
---

# Quantitative Trading

Use this skill as the suite router and shared safety contract. Ground conclusions
in the user's current code, data window, order lifecycle, and operational
controls. Treat theory and fitted models as aids, not substitutes for evidence.

## Route The Work

Use the narrowest focused skill that covers the decision:

| Need | Skill |
| --- | --- |
| Choose benchmark, objective, algorithm style, or adaptation | `design-algorithmic-execution` |
| Measure implementation shortfall or compare execution | `analyze-transaction-costs` |
| Estimate or challenge market impact | `model-market-impact` |
| Audit a statistical or machine-learning model | `validate-trading-models` |
| Forecast daily, intraday, or remaining volume | `forecast-market-volume` |
| Estimate volatility, covariance, or residual trade risk | `model-execution-risk` |
| Build or reoptimize a constrained schedule | `optimize-trade-schedules` |
| Include cost, capacity, or liquidation in a portfolio | `integrate-cost-aware-portfolios` |

Combine skills only when the output of one is an input to another. Preserve each
skill's assumptions, units, timestamps, and uncertainty through the chain.

## Establish The Evidence Boundary

1. Define the decision and whether the work is descriptive, predictive,
   counterfactual, or operational.
2. Locate the repository, runtime state, ledgers, market-data archives, model
   versions, and governing `AGENTS.md`. Do not assume paths from an older host.
3. Record the data window, timezone, source freshness, exclusions, and whether
   rows represent signals, parent orders, child orders, fills, positions, or
   resolved outcomes.
4. Identify live-operation boundaries before recommending a change. Analysis
   does not authorize order submission, cancellation, service restart,
   deployment, or a parameter rollout.

Never encode private hostnames, usernames, absolute home paths, account
identifiers, wallet addresses, or credential locations in reusable output.

## Preserve Measurement Integrity

Apply these controls whenever the corresponding data exists:

1. Replay realized net PnL and executable fills, not only average signal value.
2. Reconcile parent orders, child orders, fills, cancels, residuals, positions,
   and resolutions before calculating rates.
3. Verify venue duplication, economic-trade identifiers, maker/taker semantics,
   fees, rebates, multipliers, currency, and side signs.
4. Reproduce the live firing domain and decision-time feature values. Revised
   archives or end-of-period data can introduce look-ahead bias.
5. Use chronological development and locked holdout periods. Preserve clusters
   such as parent order, asset-day, and overlapping label window.
6. Report uncertainty, denominators, tails, correlated events, exclusions, and
   what remains unknown.
7. Treat missing, empty, stale, corrupt, or out-of-domain data as unknown—not
   evidence of zero exposure, zero cost, or safety.
8. Derive halt and re-entry behavior from current policy and live evidence, not
   a stale reason string.

## Inspect Trading Telemetry

Profile raw JSON or JSONL without printing identifiers or secrets:

```bash
python3 <plugin-root>/scripts/profile_jsonl.py <file>.jsonl[.gz]
```

Use `--since`, `--until`, `--group-by`, and repeatable `--metric` options as
needed. Quote its covered UTC window in the conclusion. Inspect the actual
signal, sizing, order, fill, PnL, and guard code paths before interpreting
metrics.

## Use Optional Research References

The focused execution methods include published technical foundations. Read the
shared [method provenance](../../references/method-provenance.md) before citing
them.

The plugin also supports an optional, separately licensed QuantEcon lecture
checkout. Read
[references/quantecon-provenance.md](references/quantecon-provenance.md) before
syncing it, then run:

```bash
<plugin-root>/scripts/sync_quantecon.sh
python3 <plugin-root>/scripts/list_lectures.py
python3 <plugin-root>/scripts/search_lectures.py "search terms"
```

The scripts use `QUANTITATIVE_TRADING_QUANTECON_ROOT` when set, otherwise
`${XDG_CACHE_HOME:-$HOME/.cache}/quantitative-trading/lecture-python.myst`.
Cite the lecture file and explain its relevance; do not turn a trading decision
into a generic economics lesson.

## Output Contract

Provide:

- the decision, conclusion, and focused skill or method used;
- exact source files or datasets and covered time window;
- metric definitions, units, denominators, uncertainty, and exclusions;
- evidence for and against the hypothesis;
- expected benefit, tail risk, and live-risk concern;
- a reversible verification or rollout plan;
- explicit unknowns and the next evidence needed.

Default to read-only work. Never submit, cancel, sell, unpark, recreate, deploy,
or restart live trading systems unless the user explicitly requests that exact
operation.
