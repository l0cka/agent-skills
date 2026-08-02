<p align="center">
  <img src="assets/logo.png" alt="Quantitative Trading logo" width="160">
</p>

# Quantitative Trading plugin

Use this plugin for evidence-led research and analysis of trading systems. The
plugin manifest declares read-only capabilities.

## Workflows

- `quantitative-trading`: Route broad or cross-cutting trading analysis.
- `design-algorithmic-execution` and `optimize-trade-schedules`: Design and
  assess execution plans and constrained schedules.
- `analyze-transaction-costs` and `model-market-impact`: Measure cost and
  estimate market impact.
- `forecast-market-volume` and `model-execution-risk`: Estimate volume and
  execution risk.
- `validate-trading-models` and `integrate-cost-aware-portfolios`: Validate
  models and include cost or capacity in portfolio decisions.

The workflows preserve evidence boundaries, timestamps, units, uncertainty,
and live-operation limits. They do not authorize order submission, cancellation,
deployment, or service restart.

## Research provenance

The methods are original operational workflows informed by the sources listed
in [method provenance](references/method-provenance.md). Optional QuantEcon
references use a separate checkout and have separate licensing controls.

## Verify the plugin

Run these commands from the repository root:

```bash
python3 scripts/validate_skills.py
python3 plugins/quantitative-trading/tests/test_quantitative_trading.py -v
```
