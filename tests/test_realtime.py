import json
import unittest
from datetime import datetime, timezone

from polytracker_showcase.realtime import RecentEventBuffer, parse_market_messages


class RealtimeProcessingTests(unittest.TestCase):
    def test_parser_ignores_control_and_unknown_messages(self):
        self.assertEqual(parse_market_messages("PING"), [])
        self.assertEqual(parse_market_messages(json.dumps({"event_type": "book"})), [])
        self.assertEqual(parse_market_messages("not-json"), [])
        self.assertEqual(parse_market_messages(b"\xff\xfe"), [])

    def test_parser_ignores_invalid_timestamp(self):
        raw = json.dumps({
            "event_type": "last_trade_price",
            "asset_id": "asset-1",
            "market_id": "market-1",
            "price": 0.5,
            "size": 1,
            "timestamp": "not-a-timestamp",
        })

        self.assertEqual(parse_market_messages(raw), [])

    def test_parser_validates_last_price_events(self):
        raw = json.dumps([
            {
                "event_type": "last_trade_price",
                "asset_id": "asset-1",
                "market_id": "market-1",
                "price": "0.72",
                "size": "15",
                "side": "buy",
                "timestamp": 1_750_000_000_000,
            },
            {"event_type": "last_trade_price", "asset_id": "missing-market"},
        ])

        events = parse_market_messages(
            raw,
            ingested_at=datetime(2025, 6, 15, tzinfo=timezone.utc),
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].side, "BUY")
        self.assertEqual(events[0].market_id, "market-1")
        self.assertEqual(events[0].event_at.tzinfo, timezone.utc)

    def test_buffer_is_bounded_and_tracks_latest_market_event(self):
        messages = [
            json.dumps({
                "event_type": "last_trade_price",
                "asset_id": f"asset-{index}",
                "market_id": "market-1",
                "price": 0.5 + index / 100,
                "size": 1,
                "timestamp": 1_750_000_000 + index,
            })
            for index in range(3)
        ]
        buffer = RecentEventBuffer(max_events=2)
        for message in messages:
            buffer.extend(parse_market_messages(message))

        self.assertEqual(len(buffer.recent()), 2)
        self.assertEqual(buffer.latest_for_market("market-1").asset_id, "asset-2")

    def test_buffer_evicts_latest_lookup_when_market_leaves_retention(self):
        def event(market_id: str, asset_id: str) -> str:
            return json.dumps({
                "event_type": "last_trade_price",
                "asset_id": asset_id,
                "market_id": market_id,
                "price": 0.5,
                "size": 1,
                "timestamp": 1_750_000_000,
            })

        buffer = RecentEventBuffer(max_events=2)
        buffer.extend(parse_market_messages(event("market-a", "asset-a1")))
        buffer.extend(parse_market_messages(event("market-a", "asset-a2")))
        buffer.extend(parse_market_messages(event("market-b", "asset-b1")))
        buffer.extend(parse_market_messages(event("market-b", "asset-b2")))

        self.assertIsNone(buffer.latest_for_market("market-a"))
        self.assertEqual(buffer.latest_for_market("market-b").asset_id, "asset-b2")
        self.assertEqual(len(buffer.recent()), 2)
        self.assertLessEqual(buffer.market_count, 2)

    def test_buffer_rejects_non_positive_capacity(self):
        with self.assertRaises(ValueError):
            RecentEventBuffer(max_events=0)

