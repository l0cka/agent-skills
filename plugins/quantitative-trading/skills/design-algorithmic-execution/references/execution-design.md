# Execution design method

## 1. Translate the mandate

Start from the reason for the order rather than an algorithm name.

| Mandate signal | Typical execution implication | Key challenge |
| --- | --- | --- |
| Fast-decaying information | Higher urgency and earlier completion | Impact can consume the alpha |
| Long-horizon information | More tolerance for patient execution | Information leakage still matters |
| Liquidity or cash flow | Cost-sensitive schedule with firm completion | Avoid taking unintended market views |
| Risk rebalance | Manage residual portfolio risk, not each line alone | Correlation and hedge drift |
| Benchmark replication | Align participation and finish with benchmark | Benchmark gaming or forecast error |

State conflicts explicitly. A close benchmark with an urgent completion mandate,
for example, needs a documented priority rather than an implicit compromise.

## 2. Choose the benchmark ex ante

| Benchmark | Suitable when | Common misuse |
| --- | --- | --- |
| Decision or arrival price | Measure the cost of implementing a current decision | Comparing orders with different delay before release |
| Previous close | The investment decision genuinely predates the session | Charging execution for overnight information not under its control |
| Closing price | The mandate is to finish near the close | Using it after seeing that it was favorable |
| Interval VWAP | The desired behavior is participation over a fixed interval | Treating low VWAP slippage as proof of low total cost |
| Participation-weighted price | The mandate is tied to observable market volume | Ignoring the order's contribution to reported volume |

Keep benchmark performance separate from absolute profit and loss. A good
execution can lose money after an adverse market move, and a poor execution can
benefit from a favorable one.

## 3. Select the objective

Use one primary objective and explicit secondary constraints:

- minimize expected implementation cost;
- minimize residual timing risk subject to a cost budget;
- minimize cost subject to a risk or completion constraint;
- balance expected cost and risk using a documented risk-aversion parameter;
- seek price improvement within a completion and loss bound.

Never reuse a vendor's risk-aversion number without its scale and units. Map it
to observable quantities such as expected cost, timing risk, completion time,
and participation.

## 4. Specify macro and micro decisions

Macro decisions define the benchmark, objective, horizon, initial schedule, and
completion requirement. Micro decisions define how child orders, venue routing,
limit prices, and urgency may change.

For adaptation, record:

- observed inputs and freshness requirements;
- trigger and release thresholds;
- minimum and maximum participation or trading rate;
- how price opportunity and adverse momentum are distinguished;
- whether the strategy may slow below its original rate;
- cooldown, re-entry, and maximum number of changes;
- behavior when forecasts, quotes, or venue state are unavailable.

Evaluate an adaptation against the information available when it fired, not the
subsequent path.

## 5. Control and review

Pre-trade: freeze inputs, model version, expected cost/risk range, and planned
schedule.

Intraday: reconcile target versus actual cumulative quantity, forecast versus
actual volume, realized versus expected cost, remaining risk, rejected orders,
and data age.

Post-trade: attribute benchmark slippage, impact, market movement, delay,
opportunity cost, fees, and deviations from the plan. Preserve the full event
timeline so the result is reproducible.
