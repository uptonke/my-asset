# v0.7 Risk Attribution Diagnostics

This layer belongs to the Risk tab. It does not generate target weights, trade drafts, or execution permissions.

## Added metrics

- Benchmark relative performance
  - active_return_annualized_pct
  - tracking_error_pct
  - information_ratio
  - benchmark_beta
  - benchmark_r_squared
  - correlation_to_benchmark
- Win rate and payoff
  - win_rate_pct
  - loss_rate_pct
  - average_win_pct
  - average_loss_pct
  - payoff_ratio
  - expectancy_pct
- Drawdown recovery
  - drawdown_recovery_days
  - is_unrecovered_drawdown
  - current_drawdown_days
- Factor exposure snapshot
  - Uses existing macro_meta.fama_french when available.
  - Does not rebuild factor data.

## Data source

The benchmark attribution uses the synthetic portfolio daily return series already produced by the risk engine and compares it against a benchmark price series. The benchmark defaults to VOO unless a settings benchmark is configured.

## Safety boundary

This is a risk diagnostics layer only. It does not approve trades, does not write orders, and does not enable execution.
