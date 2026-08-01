# Trade-schedule optimization

## Objective families

A common scalar objective is:

```text
minimize expected_execution_cost(schedule)
       + lambda * residual_execution_risk(schedule)
```

The cost term may include temporary impact, spread, fees, and expected alpha
decay. You can omit a schedule-independent constant during optimization. Restore
it when reporting total expected cost.

Use alternative formulations to improve governance:

- minimize expected cost subject to a maximum risk.
- minimize risk subject to a cost or participation budget.
- minimize expected shortfall or another tail measure.
- optimize cost first, then choose the least risky schedule within a tolerance.

Map every `lambda` to observable cost, risk, and completion outputs. Never copy
it between formulations or providers by numeric value alone.

## Decision variables and parameterizations

The direct decision variable can be interval quantity, residual quantity,
participation, or trading rate. Direct schedules are flexible but can be large.
Low-dimensional parameterizations, such as exponential decay or a small set of
participation knots, can solve faster but restrict the feasible shapes.

Choose the least restrictive form that meets the latency budget. Verify the
parameterized solution against a richer benchmark on representative cases.

## Constraint checklist

- total scheduled quantity equals the parent quantity.
- residual quantity moves toward zero and completes by the deadline.
- child quantity and participation stay within minimum and maximum bounds.
- side does not flip unless explicitly permitted.
- lot, tick, venue, auction, and restricted-period rules are met.
- portfolio cash, gross, net, factor, and hedge constraints are met.
- stale or missing forecasts produce a safe fallback.
- integer rounding preserves feasibility.

## Solver validation

Report solver status, primal and dual residuals where available, constraint
violations, objective components, runtime, and sensitivity to starting values.
For nonlinear problems, compare multiple starts and a simple feasible schedule.

Recalculate the objective independently from the returned schedule. Test tiny,
large, one-sided, two-sided, illiquid, highly correlated, and missing-input
cases.

## Frontier and uncertainty

Solve across a grid of cost-risk preferences or bounds. Present expected cost,
risk, completion time, maximum participation, and stressed outcomes for each
candidate.

Repeat under volume, impact, volatility, covariance, alpha, and spread
scenarios. Prefer a robust schedule when a nominal optimum is highly sensitive
to estimation error.

## Reoptimization

Use actual executed quantity and residual exposure as the new initial state.
Compare the benefit of changing with the cost of churn, queue loss, additional
impact, and operational latency. Require a material improvement and a feasible
fallback before replacing the current schedule.
