import unittest
import pandas as pd
from scripts.jensen_alpha import (
    build_cash_flow_adjusted_period_returns,
    _benchmark_return_usd,
    _remove_fx_from_twd_return,
    _twd_opportunity_cost_return,
)


class PerformanceSemanticsTests(unittest.TestCase):
    def test_modified_dietz_external_flows(self):
        history = [{"date": "2026-01-01", "assets": 1000},
                   {"date": "2026-01-05", "assets": 1185}]
        ledger = [{"date": "2026-01-03", "type": "Deposit", "totalCashFlow": 100},
                  {"date": "2026-01-05", "type": "Withdraw", "totalCashFlow": -20},
                  {"date": "2026-01-01", "type": "Deposit", "totalCashFlow": 500},
                  {"date": "2026-01-03", "type": "Buy", "totalCashFlow": -50},
                  {"date": "2026-01-06", "type": "Deposit", "totalCashFlow": 500}]
        row = build_cash_flow_adjusted_period_returns(history, ledger).iloc[0]
        self.assertEqual(row["return_method"], "modified_dietz")
        self.assertEqual(row["external_flow"], 80)
        self.assertEqual(row["weighted_external_flow"], 50)
        self.assertEqual(row["dietz_denominator"], 1050)
        self.assertEqual(row["external_flow_count"], 2)
        self.assertAlmostEqual(row["portfolio_return_twd"], 0.1)

    def test_fx_common_numeraire_and_opportunity_cost(self):
        start, end = pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-05")
        index = pd.DatetimeIndex([start, end])
        prices = pd.Series([100.0, 110.0], index=index)
        fx = pd.Series([30.0, 33.0], index=index)
        rf = pd.Series([0.0, 0.0], index=index)
        self.assertAlmostEqual(_remove_fx_from_twd_return(0.1, 0.1), 0.0)
        self.assertAlmostEqual(_benchmark_return_usd(prices, fx, start, end, "TWD"), 0.0)
        self.assertAlmostEqual(_benchmark_return_usd(prices, fx, start, end, "USD"), 0.1)
        self.assertAlmostEqual(_twd_opportunity_cost_return(rf, fx, start, end), 0.1)


if __name__ == "__main__":
    unittest.main()
