import unittest

from polytracker_showcase.domain import FeatureContext, Trade
from polytracker_showcase.features import (
    FeatureRegistry,
    PriceExtremenessFeature,
    RecentActivityFeature,
    RelativeTradeSizeFeature,
)
from polytracker_showcase.pipeline import FeaturePipeline


def make_trade() -> Trade:
    return Trade(
        id="trade-1",
        user_id="wallet-1",
        market_id="market-1",
        price=0.9,
        size=200,
        timestamp="2025-06-15T12:00:00Z",
    )


class FeaturePipelineTests(unittest.TestCase):
    def test_registry_rejects_duplicate_feature_names(self):
        feature = RelativeTradeSizeFeature()
        with self.assertRaises(ValueError):
            FeatureRegistry([feature, feature])

    def test_pipeline_returns_explainable_normalized_features(self):
        pipeline = FeaturePipeline([
            RelativeTradeSizeFeature(),
            PriceExtremenessFeature(),
            RecentActivityFeature(),
        ])
        analysis = pipeline.analyze(
            make_trade(),
            FeatureContext(
                market_average_trade_size=100,
                trader_recent_trade_count=8,
                market_average_trader_trade_count=4,
            ),
        )

        self.assertEqual(
            [feature.name for feature in analysis.features],
            ["relative_trade_size", "price_extremeness", "recent_activity"],
        )
        self.assertTrue(all(0.0 <= feature.value <= 1.0 for feature in analysis.features))
        self.assertTrue(all(feature.reason for feature in analysis.features))

    def test_pipeline_has_no_final_score_field(self):
        pipeline = FeaturePipeline([PriceExtremenessFeature()])
        analysis = pipeline.analyze(make_trade())

        self.assertNotIn("final_score", analysis.model_dump())

    def test_feature_boundaries_are_normalized(self):
        low_price_trade = make_trade().model_copy(update={"price": 0.0})
        midpoint_trade = make_trade().model_copy(update={"price": 0.5})
        context = FeatureContext(
            market_average_trade_size=100,
            trader_recent_trade_count=0,
            market_average_trader_trade_count=3,
        )

        self.assertEqual(PriceExtremenessFeature().compute(low_price_trade, context).value, 1.0)
        self.assertEqual(PriceExtremenessFeature().compute(midpoint_trade, context).value, 0.0)
        self.assertEqual(RecentActivityFeature().compute(midpoint_trade, context).value, 0.0)

    def test_empty_pipeline_and_large_size_remain_safe(self):
        empty_analysis = FeaturePipeline([]).analyze(make_trade())
        large_trade = make_trade().model_copy(update={"size": 1_000_000})

        self.assertEqual(empty_analysis.features, [])
        self.assertLessEqual(
            RelativeTradeSizeFeature().compute(large_trade, FeatureContext()).value,
            1.0,
        )

