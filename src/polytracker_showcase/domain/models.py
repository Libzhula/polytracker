from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Trade(BaseModel):
    """Normalized trade contract used by ingestion and feature code."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    price: float = Field(ge=0.0, le=1.0)
    size: float = Field(gt=0.0)
    timestamp: datetime
    side: Literal["BUY", "SELL"] | None = None
    outcome: str | None = None
    asset_id: str | None = None
    market_slug: str | None = None

    @property
    def notional_usd(self) -> float:
        return self.price * self.size


class MarketEvent(BaseModel):
    """Validated market event produced by the safe WebSocket parser."""

    model_config = ConfigDict(extra="forbid")

    event_type: Literal["last_trade_price"]
    asset_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    price: float = Field(ge=0.0, le=1.0)
    size: float = Field(ge=0.0)
    side: Literal["BUY", "SELL"] | None = None
    event_at: datetime | None = None
    ingested_at: datetime = Field(default_factory=utc_now)
    latency_ms: float | None = Field(default=None, ge=0.0)


class FeatureContext(BaseModel):
    """Small, explicit context contract for independent feature calculators."""

    model_config = ConfigDict(extra="forbid")

    market_average_trade_size: float = Field(default=100.0, gt=0.0)
    trader_recent_trade_count: int = Field(default=0, ge=0)
    market_average_trader_trade_count: float = Field(default=3.0, gt=0.0)


class FeatureResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    value: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    weight: float = Field(default=1.0, ge=0.0)


class TradeAnalysis(BaseModel):
    """Feature output deliberately without a proprietary final score."""

    model_config = ConfigDict(extra="forbid")

    trade: Trade
    features: list[FeatureResult]


class IngestionRejection(BaseModel):
    """Safe rejection metadata; raw payload values are intentionally omitted."""

    model_config = ConfigDict(extra="forbid")

    source: str
    entity_type: str
    reason_code: str
    payload_hash: str
    field_names: tuple[str, ...] = ()


class IngestionTelemetry(BaseModel):
    received_rows: int = 0
    parsed_rows: int = 0
    rejected_rows: int = 0
    rejections: list[IngestionRejection] = Field(default_factory=list)

    def add_rejection(self, rejection: IngestionRejection) -> None:
        self.rejections.append(rejection)
        self.rejected_rows += 1


JsonObject = dict[str, Any]

