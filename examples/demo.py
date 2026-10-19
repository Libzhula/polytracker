from __future__ import annotations

import json

from polytracker_showcase.domain import FeatureContext
from polytracker_showcase.features import (
    PriceExtremenessFeature,
    RecentActivityFeature,
    RelativeTradeSizeFeature,
)
from polytracker_showcase.ingestion import parse_trade_payload
from polytracker_showcase.pipeline import FeaturePipeline


def main() -> None:
    provider_payload = {
        "id": "synthetic-trade-1",
        "proxyWallet": "wallet-synthetic-1",
        "conditionId": "synthetic-market-1",
        "price": "0.72",
        "size": "150",
        "timestamp": 1_750_000_000,
        "side": "BUY",
        "slug": "synthetic-market",
    }

    trade = parse_trade_payload(provider_payload)
    analysis = FeaturePipeline(
        [
            RelativeTradeSizeFeature(),
            PriceExtremenessFeature(),
            RecentActivityFeature(),
        ]
    ).analyze(
        trade,
        FeatureContext(
            market_average_trade_size=100,
            trader_recent_trade_count=4,
            market_average_trader_trade_count=3,
        ),
    )

    print(json.dumps(analysis.model_dump(mode="json"), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
