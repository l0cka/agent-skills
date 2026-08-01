---
name: design-algorithmic-execution
description: Design benchmark-aligned algorithmic execution plans and decision rules. Use when choosing an execution benchmark, translating an investment mandate into an execution objective, selecting an algorithm style, defining urgency or participation, specifying intraday adaptation, or documenting pre-trade, in-trade, and post-trade controls.
---

# Design Algorithmic Execution

Turn an investment decision into an executable, testable plan. Do not select an
algorithm by label alone: define what success means, what information was
available at decision time, and when the strategy may adapt.

Read [references/execution-design.md](references/execution-design.md) for the
benchmark, objective, and adaptation decision tables. Read the shared
[method provenance](../../references/method-provenance.md) when citing or
extending the published framework.

## Build The Decision Record

1. Record instrument, side, quantity, decision time, horizon, completion
   requirement, venue and order restrictions, and the investment reason.
2. State whether the order is information-driven, liquidity-driven, risk-driven,
   or mixed. Estimate how quickly any alpha or urgency decays.
3. Choose the benchmark before observing fills. Explain why arrival, close,
   interval VWAP, participation-weighted price, or another benchmark matches the
   mandate.
4. Express the objective as cost minimization, risk minimization, a cost-risk
   trade-off, a hard cost or risk constraint, or price improvement.
5. Select an execution style and initial schedule consistent with that objective.
   Treat vendor labels as metadata. Inspect actual behavior and parameters.
6. Define adaptation inputs, thresholds, bounds, cooldowns, and a fallback.
   Separate favorable-opportunity logic from adverse-risk protection.
7. Specify pre-trade estimates, intraday monitoring, post-trade attribution, and
   the owner of each decision.

## Preserve Ex-Ante Integrity

- Freeze the benchmark, objective, model version, and allowable adaptations at
  decision time.
- Keep forecasts and observations timestamped. Do not use revised or end-of-day
  data as if it were available earlier.
- Compare the realized path with both the original plan and the rules that
  authorized any deviation.
- Do not call a favorable outcome "best execution" when the process violated
  the mandate. Distinguish decision quality from luck.

## Bound Live Risk

Include maximum participation, price collars, quantity and notional caps,
completion rules, stale-data handling, cancel behavior, and a human escalation
path. Missing or stale market data must fail closed or fall back to an explicitly
approved safe mode.

Analysis does not authorize sending, changing, or cancelling live orders.

## Deliver

Provide the mandate, ex-ante benchmark, objective, and initial schedule or
parameter range. Provide adaptation rules, hard controls, required data, and
assumptions. Define a post-trade test that could show the plan was wrong.
