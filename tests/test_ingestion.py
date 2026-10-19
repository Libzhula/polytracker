import unittest

from polytracker_showcase.ingestion import parse_trade_batch, parse_trade_payload

from .fixtures import trade_payload


class IngestionTests(unittest.TestCase):
    def test_parser_maps_provider_fields_to_domain_contract(self):
        trade = parse_trade_payload(trade_payload())

        self.assertEqual(trade.id, "trade-1")
        self.assertEqual(trade.user_id, "wallet-synthetic-1")
        self.assertEqual(trade.market_id, "market-1")
        self.assertEqual(trade.side, "BUY")

    def test_batch_parser_keeps_valid_rows_and_quarantines_invalid_rows(self):
        invalid = trade_payload(trade_id="bad")
        invalid.pop("conditionId")
        rows = [trade_payload(), invalid, {"id": "malformed", "price": "not-a-number"}]

        parsed, telemetry = parse_trade_batch(rows)

        self.assertEqual(len(parsed), 1)
        self.assertEqual(telemetry.received_rows, 3)
        self.assertEqual(telemetry.parsed_rows, 1)
        self.assertEqual(telemetry.rejected_rows, 2)
        self.assertTrue(all(not rejection.field_names == ("token",) for rejection in telemetry.rejections))

    def test_parser_does_not_copy_unknown_fields(self):
        payload = trade_payload()
        payload["private_note"] = "must not enter the domain model"

        trade = parse_trade_payload(payload)

        self.assertNotIn("private_note", trade.model_dump())

    def test_parser_rejects_invalid_timestamp(self):
        payload = trade_payload(timestamp="not-a-timestamp")

        with self.assertRaises(ValueError):
            parse_trade_payload(payload)

