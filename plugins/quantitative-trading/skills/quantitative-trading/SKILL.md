---
name: quantitative-trading
description: Perform evidence-led quantitative analysis for trading and market-making systems. Use for strategy diagnostics, backtests, edge and fill analysis, exposure and inventory review, drawdown and variance-vs-decay decisions, re-entry gates, latency, market selection, parameter tuning, trading telemetry, and mapping QuantEcon models into trading workflows.
---

# Quantitative Trading

Use read-only evidence to distinguish genuine edge, execution effects, data
artifacts, regime changes, and ordinary variance. Treat external theory as a
modeling aid; the decision must remain grounded in the system's code, data
window, and live-risk controls.

## Establish The Evidence Boundary

1. Define the decision: strategy health, edge, fills, exposure, drawdown,
   latency, market selection, inventory, re-entry, or parameter tuning.
2. Locate the repository, runtime state, ledgers, market-data archives, and
   governing `AGENTS.md`. Never assume paths from an older host snapshot.
3. Record the data window, timezone, source freshness, exclusions, and whether
   rows represent signals, orders, fills, positions, or resolutions.
4. Identify live-operation boundaries before recommending a change. Analysis
   does not authorize order submission, cancellation, service restart, or a
   parameter rollout.

Discover project and data locations from the current workspace, deployment
configuration, and user-provided scope. Do not encode private hostnames,
usernames, absolute home paths, account identifiers, or credential locations in
reusable output. Treat wallet, environment, token, signing, and access-control
files as sensitive.

## Preserve Measurement Integrity

Apply these invariants whenever the corresponding data exists:

1. Replay realized net PnL, not average signal EV. Adverse selection can make
   signal averages materially overstate executable edge.
2. Understand venue duplication and maker/taker semantics. Confirm whether an
   API returns one economic trade as multiple role-specific rows before counting
   observations.
3. Replay the full live firing domain and filter on realized entry conditions.
   Narrowing the domain can redefine the fire point and inflate apparent edge.
4. Reconcile new replay or edge tools against an established report on the same
   data and exclude assets that the live strategy no longer trades.
5. Verify forecast features at issuance time. Same-day or revised archives can
   introduce look-ahead bias.
6. Treat quiet ledgers as ambiguous until heartbeat age, process/container
   state, and kill or approval gates have been checked.
7. Start drawdown analysis with per-asset results and multi-day trends.
   Same-window correlated fires are not independent samples.
8. Treat missing, empty, stale, or corrupt fetches as unknown—not proof of zero
   exposure or operational safety.
9. Use Wilson bounds, Bayesian intervals, or pre-registered sequential
   boundaries for small samples. Tune on chronological training data and judge
   on untouched chronological holdout.
10. Derive halt behavior from current policy and live fire evidence. Do not
    infer duration from a stale halt reason.

## Analyze

1. Inspect the exact signal, sizing, order, fill, PnL, and guard code paths.
2. Profile raw JSON/JSONL without printing identifiers or secrets:
   `python3 <plugin-root>/scripts/profile_jsonl.py <file>.jsonl[.gz]`.
   Use `--since`, `--until`, `--group-by`, and repeatable `--metric` options as
   needed. Quote its covered UTC window in the conclusion.
3. Separate open/resting orders, submitted orders, fills, resolved outcomes,
   and current positions. Reconcile counts between stages.
4. Form a falsifiable hypothesis and choose a comparison that can disprove it.
   Prefer chronological replay, walk-forward evaluation, or a pre-registered
   sequential test.
5. Report uncertainty, denominators, correlated clusters, fees/slippage,
   exclusions, failure modes, and what remains unknown.

## Use QuantEcon References

The plugin does not redistribute the upstream lecture corpus. Read
[references/quantecon-provenance.md](references/quantecon-provenance.md) before
syncing it. Then run:

```bash
<plugin-root>/scripts/sync_quantecon.sh
python3 <plugin-root>/scripts/list_lectures.py
python3 <plugin-root>/scripts/search_lectures.py "search terms"
```

The scripts use `QUANTITATIVE_TRADING_QUANTECON_ROOT` when set, otherwise
`${XDG_CACHE_HOME:-$HOME/.cache}/quantitative-trading/lecture-python.myst`.

Map recurring questions to an appropriate frame:

| Question | QuantEcon lecture | Frame |
| --- | --- | --- |
| Variance or edge decay? | `wald_friedman.md`, `wald_friedman_2.md` | Pre-registered sequential testing |
| Re-entry criteria | `mccall_model.md`, `odu.md` | Optimal stopping and uncertain offer distributions |
| Small-sample win rate | `likelihood_bayes.md`, `exchangeable.md` | Bayesian updating and likelihood ratios |
| Regime-dependent gates | `finite_markov.md`, `mix_model.md` | State transitions and mixture models |
| Ruin risk and sizing | `kesten_processes.md`, `wealth_dynamics.md` | Heavy-tail wealth dynamics |
| Quote and inventory policy | `inventory_dynamics.md`, `lq_inventories.md`, `lqcontrol.md` | Inventory control and dynamic programming |
| Information aggregation | `harrison_kreps.md`, `information_market_equilibrium.md` | Heterogeneous beliefs and price formation |

Cite the lecture file and explain the mapping. Do not turn the result into a
generic economics lesson.

## Output Contract

Provide:

- the decision and conclusion;
- exact source files or datasets and covered time window;
- metric definition, denominator, uncertainty, and material exclusions;
- evidence for and against the hypothesis;
- expected benefit and live-risk concern;
- a reversible verification or rollout plan;
- explicit unknowns and the next evidence needed.

Default to read-only work. Never submit, cancel, sell, unpark, recreate, deploy,
or restart live trading systems unless the user explicitly requests that exact
operation.
