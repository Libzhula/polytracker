from __future__ import annotations


def trade_payload(
    *,
    trade_id: str = "trade-1",
    market_id: str = "market-1",
    price: float = 0.62,
    size: float = 120.0,
    timestamp: object = 1_750_000_000,
) -> dict[str, object]:
    return {
        "id": trade_id,
        "proxyWallet": "wallet-synthetic-1",
        "conditionId": market_id,
        "price": price,
        "size": size,
        "timestamp": timestamp,
        "side": "BUY",
        "slug": "synthetic-market",
    }

