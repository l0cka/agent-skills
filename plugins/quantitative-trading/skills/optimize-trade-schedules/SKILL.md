---
name: optimize-trade-schedules
description: Formulate, solve, and validate constrained single-order and portfolio trade schedules that balance impact, alpha, completion, and residual risk. Use for cost-risk frontiers, participation schedules, multiperiod execution optimization, risk-aversion selection, basket scheduling, real-time reoptimization, or machine-learning warm starts.
---

# Optimize Trade Schedules

Translate execution objectives into a constrained schedule and prove that the
solution is feasible, stable, and better than simple alternatives.

Read [references/schedule-optimization.md](references/schedule-optimization.md)
for objective forms, constraints, parameterizations, solver checks, and
reoptimization. Read the shared
[method provenance](../../references/method-provenance.md) when citing or
extending the published framework.

## Formulate

1. Define signed quantities, intervals, forecast external volume, impact model,
   expected price drift or alpha, residual-risk model, benchmark, and deadline.
2. Choose one objective: weighted expected cost and risk, minimum cost under a
   risk limit, minimum risk under a cost limit, or a lexicographic objective.
3. Express every business rule as a constraint or post-solution acceptance
   test. Include completion, participation, rate, lot, venue, side, cash,
   exposure, and monotone-residual rules as applicable.
4. Fix units and scaling. A risk-aversion parameter has no portable meaning
   without the exact cost and risk definitions.

## Solve And Compare

Build a constant-rate or volume-shaped schedule first. Then solve the selected
linear, quadratic, convex, or nonlinear formulation with multiple feasible
starting points where needed.

Trace a cost-risk frontier rather than reporting one unexplained optimum.
Compare objective value, feasibility, solve time, sensitivity, turnover, and
tail outcomes with the baseline.

A machine-learning model may provide a warm start for a costly optimizer, but
it must not replace the final feasibility and objective checks.

## Reoptimize Deliberately

Recompute from actual fills and current residual positions. Trigger only on
material, fresh changes in price opportunity, forecast volume, liquidity,
impact, risk, or constraints. Use hysteresis and cooldowns so noise does not
cause schedule churn.

Preserve the original plan, each input snapshot, reason for change, and fallback
if the new solution is infeasible or late.

## Deliver

Provide the mathematical objective in plain language, inputs and timestamps,
constraints, baseline, solver and convergence evidence, frontier or sensitivity
results, proposed schedule, reoptimization policy, stress results, and a
simulation or shadow-run gate before any live use.
