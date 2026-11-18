"""Provider contract tests run offline with mocked HTTP responses."""
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from market_api import (
    MarketAPIError, cache_seconds, fetch_markets, fetch_price, validate_price,
)


def example():
    return {
        "market": "forever.normal.horde.us",
        "item": {"id": 2770, "name": "Copper Ore"},
        "latest": {
            "observedAt": "2026-11-18T14:02:11.000Z",
            "minBuyout": 200,
            "median7d": 250,
            "quantity": 50,
        },
        "series": [{"t": "2026-11-18T14:00:00.000Z", "min": 200}],
    }


def session(payload=None, status=200, headers=None):
    response = Mock()
    response.status_code = status
    response.headers = headers or {"Cache-Control": "public, max-age=180"}
    response.json.return_value = payload
    client = Mock()
    client.get.return_value = response
    return client


class ApiTests(unittest.TestCase):
    def test_documented_schema(self):
        age = validate_price(example(), "forever.normal.horde.us", 2770)
        self.assertGreater(age, 0)

    def test_market_mismatch(self):
        with self.assertRaisesRegex(MarketAPIError, "Market mismatch"):
            validate_price(example(), "forever.pvp.horde.us", 2770)

    def test_item_mismatch(self):
        with self.assertRaisesRegex(MarketAPIError, "Item mismatch"):
            validate_price(example(), "forever.normal.horde.us", 2772)

    def test_null_latest_explicit(self):
        payload = example()
        payload["latest"] = None
        with self.assertRaisesRegex(MarketAPIError, "no scan"):
            validate_price(payload, "forever.normal.horde.us", 2770)

    def test_invalid_price(self):
        payload = example()
        payload["latest"]["minBuyout"] = -1
        with self.assertRaisesRegex(MarketAPIError, "minBuyout"):
            validate_price(payload, "forever.normal.horde.us", 2770)

    def test_cache_policy(self):
        self.assertEqual(cache_seconds("public, max-age=180"), 180)
        self.assertEqual(cache_seconds("no-store, max-age=180"), 0)
        self.assertEqual(cache_seconds(None), 0)

    def test_market_list(self):
        markets, ttl = fetch_markets(session({"markets": [{"id": "forever.normal.horde.us"}]}))
        self.assertEqual(markets[0]["id"], "forever.normal.horde.us")
        self.assertEqual(ttl, 180)

    def test_price_request(self):
        client = session(example())
        payload, ttl, _ = fetch_price(2770, session=client)
        self.assertEqual(payload["latest"]["minBuyout"], 200)
        self.assertEqual(ttl, 180)
        self.assertEqual(client.get.call_args.kwargs["params"], {"range": "7d"})

    def test_rate_limit(self):
        with self.assertRaisesRegex(MarketAPIError, "429"):
            fetch_price(2770, session=session(status=429, headers={"Retry-After": "30"}))

    def test_bad_json(self):
        client = session()
        client.get.return_value.json.side_effect = ValueError("not JSON")
        with self.assertRaisesRegex(MarketAPIError, "invalid JSON"):
            fetch_price(2770, session=client)


if __name__ == "__main__":
    unittest.main()
