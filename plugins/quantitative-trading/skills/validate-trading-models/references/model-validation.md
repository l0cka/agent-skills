# Trading-model validation

## Match the model to the target

| Target | Candidate starting point | Required diagnostic |
| --- | --- | --- |
| Continuous cost or return | Linear or transformed regression | Residual shape, stability, robust error |
| Binary fill or event probability | Logistic or probit model | Calibration, class balance, threshold value |
| Bounded rate or proportion | Appropriate link or bounded model | Predictions stay in range |
| Nonlinear cost curve | Constrained nonlinear regression | Starting-value sensitivity and identifiability |
| Regime grouping | Clustering or mixture model | Stability and usefulness outside the fit sample |
| Complex prediction | Tree, neural, or ensemble model | Baseline gain, ablation, drift, reproducibility |
| Optimizer warm start | Surrogate trained on solved cases | Feasibility and final solver optimality |

Use the simplest model that can answer the decision. Statistical significance
does not imply a useful effect, and high fit does not imply temporal validity.

## Leakage audit

For every feature, record:

- source event time;
- time it became available to the strategy;
- whether it is revised later;
- transformation window;
- relationship to the label horizon;
- behavior when missing.

Common leaks include final-day volume in an intraday forecast, close prices in
an earlier decision, revised fundamentals, fill-derived features used to predict
the same fill, random splitting of overlapping windows, and preprocessing fit
on the full sample.

## Splits and resampling

Prefer a chronological development period, a later validation period, and a
locked final test period. Use rolling or expanding walk-forward evaluation when
retraining is part of the real process.

Resample at the economic dependence unit:

- parent order rather than fill;
- asset-day or session rather than tick;
- block bootstrap for serially dependent time series;
- clustered uncertainty for repeated assets or dates.

Keep a complete transformation pipeline inside each fold. If labels overlap in
time, purge or embargo observations around split boundaries.

## Selection and complexity

Use subject-matter plausibility, regularization, and validation performance
together. Correlation screens, PCA, and forward selection can be exploratory,
but they must occur inside the training procedure and cannot justify a final
claim by themselves.

For nonlinear optimizers, test multiple feasible starting points and report
convergence and constraint violations. A learned warm start may reduce solve
time, but the final optimizer must still verify feasibility and objective
quality.

## Metrics

Report both statistical and economic metrics:

- bias, MAE or robust error, RMSE, and tail error for continuous targets;
- log loss or Brier score, calibration, discrimination, and decision-threshold
  outcomes for probabilities;
- net benefit after fees, impact, latency, and rejected or infeasible actions;
- interval coverage and uncertainty calibration;
- stability by time, asset, side, size, liquidity, and regime.

Choose the primary metric before viewing final-test outcomes.

## Acceptance record

Document:

1. data snapshot and feature lineage;
2. code, configuration, random seeds, and environment;
3. split boundaries and all exclusions;
4. baseline and candidate selection process;
5. locked-test result with uncertainty;
6. stress and subgroup results;
7. operational limits and fail-closed behavior;
8. monitoring and retraining trigger;
9. decision owner and rollback criterion.
