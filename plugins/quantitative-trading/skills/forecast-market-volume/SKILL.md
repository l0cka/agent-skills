---
name: forecast-market-volume
description: Build and validate daily, intraday, and remaining-session market-volume forecasts for execution. Use when estimating ADV or median volume, day-of-week effects, intraday volume curves, participation schedules, remaining liquidity, or forecast uncertainty for impact and trade-schedule models.
---

# Forecast Market Volume

Forecast the market volume available to an execution decision at the time that
decision is made. Keep the user's own order flow separate from external market
volume wherever the venue data permits.

Read [references/volume-forecasting.md](references/volume-forecasting.md) for
targets, baselines, intraday curves, conditional updates, and validation. Read
the shared [method provenance](../../references/method-provenance.md) when
citing or extending the published framework.

## Define The Forecast

1. Specify instrument, venue scope, session calendar, target volume definition,
   forecast issue time, horizon, and units.
2. Decide whether the target is full-session volume, interval volume, cumulative
   fraction, or remaining volume.
3. Preserve timestamps for trades, corrections, auctions, and late reports.
   Define the treatment of own-order prints, off-market trades, and venue
   duplication.
4. Identify half-days, holidays, rolls, index events, earnings, outages, and
   structural venue changes before selecting history.

## Build From Baselines

Compare rolling mean and median baselines across several lookback windows. Add
day-of-week, recent-volume persistence, event, and regime terms only when they
improve chronological holdout performance.

Estimate the intraday curve from normalized complete sessions. For a live
update, combine volume observed so far with a conditional forecast of the
remaining curve. Never use final-session volume to normalize an intraday input.

## Validate For Execution

Measure bias, robust absolute error, tail underforecast, interval coverage, and
participation error by issue time. Break results out by liquidity, event class,
weekday, session segment, and regime.

Propagate forecast ranges into impact, participation, and completion scenarios.
A point forecast without uncertainty is insufficient when underforecasting can
breach a participation cap.

## Deliver

Provide the target, information timestamp, data construction, baseline, candidate
model, and temporal split. Report accuracy by horizon and regime, prediction
range, exception calendar, own-order treatment, and downstream stress cases.
