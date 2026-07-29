# Market-volume forecasting

## Target definitions

Keep these targets distinct:

- average or median full-session volume for size normalization;
- next-session total volume;
- interval volume by clock or event time;
- cumulative fraction of session volume;
- volume remaining after the forecast issue time.

For fragmented markets, declare whether volume is consolidated, venue-specific,
lit-only, or includes auctions and off-market reports. Use a consistent trading
calendar and adjustment policy.

## Baselines

Start with rolling mean and median estimates over several historical windows.
The median is often more robust to event spikes; the mean may better represent
expected capacity when large days are genuine and recurrent. Select by temporal
validation rather than convention.

Candidate improvements include:

- weekday and holiday effects;
- lagged or autoregressive volume;
- trend or level shifts;
- volatility, event, and market-wide volume indicators available at issue time;
- separate opening, continuous-session, and closing-auction components.

Do not assume a relationship is stable because it was strong over a long
historical sample. Compare recent and longer windows.

## Intraday curves

Build each historical curve from interval volume divided by that session's
eligible full-session volume. Aggregate curves robustly and preserve a
distribution for every interval.

Use a clock that respects session breaks, daylight-saving changes, and early
closes. Treat auction prints separately when they dominate the final interval.
Sparse instruments may need wider bins or a pooled hierarchical curve.

For a desired participation rate `p_t`, a simple schedule input is:

```text
planned_order_volume_t = p_t * forecast_external_market_volume_t
```

Check whether published volume includes the user's own executions; otherwise a
participation calculation can be mechanically overstated.

## Remaining-volume updates

At time `t`, combine:

- actual eligible volume observed through `t`;
- the historical fraction normally completed by `t`;
- current-day deviation from the baseline;
- event and regime information known by `t`.

Avoid the unstable shortcut `observed / historical_fraction` near the open.
Use shrinkage, minimum-history rules, and broad uncertainty bands early in the
session.

## Validation

Use rolling-origin evaluation with the same issue times as production. Report:

- signed and absolute error in volume and percentage terms;
- quantile or interval coverage;
- underforecast frequency and severity;
- induced error in participation, impact, and completion;
- results by weekday, event, liquidity bucket, and session segment.

Define a safe fallback for stale feeds, incomplete sessions, and
out-of-distribution events.
