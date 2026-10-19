import unittest
from datetime import timezone

from pydantic import ValidationError

from polytracker_showcase.domain import Trade

from .fixtures import trade_payload


class DomainModelTests(unittest.TestCase):
    def test_trade_normalizes_numeric_timestamp_and_exposes_notional(self):
        trade = Trade(**{
            "id": "trade-1",
            "user_id": "wallet-1",
            "market_id": "market-1",
            "price": 0.5,
            "size": 20,
            "timestamp": 1_750_000_000,
        })

        self.assertEqual(trade.timestamp.tzinfo, timezone.utc)
        self.assertEqual(trade.notional_usd, 10.0)

    def test_trade_rejects_out_of_range_price(self):
        with self.assertRaises(ValidationError):
            Trade(**{
                "id": "trade-1",
                "user_id": "wallet-1",
                "market_id": "market-1",
                "price": 1.2,
                "size": 20,
                "timestamp": 1_750_000_000,
            })

    def test_trade_rejects_invalid_timestamp(self):
        with self.assertRaises(ValidationError):
            Trade(**{
                "id": "trade-1",
                "user_id": "wallet-1",
                "market_id": "market-1",
                "price": 0.5,
                "size": 20,
                "timestamp": "not-a-timestamp",
            })

    def test_fixture_is_provider_shaped_not_internal(self):
        self.assertIn("proxyWallet", trade_payload())
        self.assertNotIn("final_score", trade_payload())

