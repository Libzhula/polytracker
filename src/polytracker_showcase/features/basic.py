from __future__ import annotations

from polytracker_showcase.domain import FeatureContext, FeatureResult, Trade


def _bounded_ratio(value: float, baseline: float) -> float:
    ratio = max(value, 0.0) / max(baseline, 1e-9)
    return ratio / (1.0 + ratio)


class RelativeTradeSizeFeature:
    name = "relative_trade_size"
    description = "Trade size relative to a market baseline."
    weight = 1.0

    def compute(self, trade: Trade, context: FeatureContext) -> FeatureResult:
        value = _bounded_ratio(trade.size, context.market_average_trade_size)
        return FeatureResult(
            name=self.name,
            value=value,
            weight=self.weight,
            reason=f"size={trade.size:.2f}; baseline={context.market_average_trade_size:.2f}",
        )


class PriceExtremenessFeature:
    name = "price_extremeness"
    description = "Distance of the price from the midpoint of the probability range."
    weight = 1.0

    def compute(self, trade: Trade, context: FeatureContext) -> FeatureResult:
        del context
        value = min(abs(trade.price - 0.5) * 2.0, 1.0)
        return FeatureResult(
            name=self.name,
            value=value,
            weight=self.weight,
            reason=f"price={trade.price:.3f}; midpoint_distance={value:.3f}",
        )


class RecentActivityFeature:
    name = "recent_activity"
    description = "Recent trader activity relative to a market activity baseline."
    weight = 1.0

    def compute(self, trade: Trade, context: FeatureContext) -> FeatureResult:
        del trade
        value = _bounded_ratio(
            context.trader_recent_trade_count,
            context.market_average_trader_trade_count,
        )
        return FeatureResult(
            name=self.name,
            value=value,
            weight=self.weight,
            reason=(
                f"recent={context.trader_recent_trade_count}; "
                f"market_baseline={context.market_average_trader_trade_count:.2f}"
            ),
        )

