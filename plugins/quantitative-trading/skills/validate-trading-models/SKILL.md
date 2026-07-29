---
name: validate-trading-models
description: Validate statistical and machine-learning models used in trading and execution. Use for regression, probability, nonlinear, clustering, classification, neural-network, surrogate, or optimization-warm-start models; leakage audits; sampling and resampling design; feature selection; calibration; holdout evaluation; and model-governance reviews.
---

# Validate Trading Models

Test whether a model is useful for the intended trading decision under future
conditions, not whether it explains the development sample.

Read [references/model-validation.md](references/model-validation.md) for model
selection, temporal evaluation, resampling, and reporting. Read the shared
[method provenance](../../references/method-provenance.md) when citing or
extending the published framework.

## Frame The Claim

1. Define the prediction time, target, horizon, unit of observation, population,
   and downstream action.
2. List every input with its event time, availability time, revision behavior,
   and missing-data rule.
3. State the baseline, loss function, operational constraint, and minimum
   improvement that would change a decision.
4. Identify clusters and overlapping outcomes by parent order, asset, session,
   strategy, and regime.

## Build A Valid Test

Use chronological train, validation, and final test periods. Purge or embargo
overlapping labels where information can cross a boundary. Perform feature
selection, preprocessing, hyperparameter search, and threshold selection inside
training and validation only.

Choose resampling that preserves dependence. IID row bootstraps are usually
invalid for child fills, overlapping returns, and repeated asset-day
observations.

Compare against a naive and an interpretable baseline. Add nonlinear or
machine-learning complexity only when the holdout gain survives costs, regime
breaks, and sensitivity tests.

## Diagnose

- check leakage, duplicate economic events, target contamination, and survivorship;
- assess calibration as well as discrimination for probability outputs;
- examine residuals, tails, heteroskedasticity, autocorrelation, and subgroup bias;
- report parameter or feature stability across windows;
- stress missing, stale, extreme, and out-of-domain inputs;
- distinguish predictive accuracy from economic value and execution feasibility.

## Deliver

Provide the intended decision, data lineage, split design, baseline, candidate
models, metric definitions, uncertainty, final holdout results, subgroup and
stress results, reproducibility artifacts, failure conditions, and a deployment
or rejection recommendation. Never tune on the final holdout.
