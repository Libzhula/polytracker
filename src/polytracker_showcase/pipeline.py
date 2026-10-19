from __future__ import annotations

from collections.abc import Iterable

from polytracker_showcase.domain import FeatureContext, Trade, TradeAnalysis
from polytracker_showcase.features import Feature, FeatureRegistry


class FeaturePipeline:
    """Reusable feature orchestration without a proprietary scoring layer."""

    def __init__(self, features: Iterable[Feature]) -> None:
        self.registry = FeatureRegistry(features)

    def analyze(self, trade: Trade, context: FeatureContext | None = None) -> TradeAnalysis:
        resolved_context = context or FeatureContext()
        return TradeAnalysis(
            trade=trade,
            features=self.registry.compute_all(trade, resolved_context),
        )

