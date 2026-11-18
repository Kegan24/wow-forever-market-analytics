"""Offline unit tests for market comparisons and data-quality gates."""
import unittest
from market_analytics import median_deviation_percent, price_signal, eligible_for_estimate


class MarketAnalyticsTests(unittest.TestCase):
    def test_above_median(self):
        self.assertAlmostEqual(median_deviation_percent(120, 100), 20)
        self.assertEqual(price_signal(120, 100), "Above 7d median")

    def test_below_median(self):
        self.assertAlmostEqual(median_deviation_percent(80, 100), -20)
        self.assertEqual(price_signal(80, 100), "Below 7d median")

    def test_near_median(self):
        self.assertEqual(price_signal(105, 100), "Near 7d median")

    def test_missing_or_zero_median(self):
        for median in (None, 0):
            self.assertIsNone(median_deviation_percent(100, median))
            self.assertEqual(price_signal(100, median), "Insufficient history")

    def test_stale_and_missing_prices(self):
        self.assertTrue(eligible_for_estimate(100, 1))
        self.assertFalse(eligible_for_estimate(100, 25))
        self.assertFalse(eligible_for_estimate(None, 1))
        self.assertFalse(eligible_for_estimate(100, None))
        self.assertFalse(eligible_for_estimate(-1, 1))


if __name__ == "__main__":
    unittest.main()
