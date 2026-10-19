from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from typing import Any, Mapping

from pydantic import ValidationError

from polytracker_showcase.domain import MarketEvent


def _event_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        seconds = float(value)
        if seconds > 10_000_000_000:
            seconds /= 1000.0
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    raise ValueError("unsupported event timestamp")


def _messages(raw: str | bytes) -> list[Mapping[str, Any]]:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    if raw in {"PING", "PONG"}:
        return []
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    candidates = payload if isinstance(payload, list) else [payload]
    return [candidate for candidate in candidates if isinstance(candidate, Mapping)]


def parse_market_messages(
    raw: str | bytes,
    *,
    ingested_at: datetime | None = None,
) -> list[MarketEvent]:
    """Parse only supported last-price events and ignore malformed messages.

    This function intentionally has no WebSocket client, URL, credential, or
    subscription code. It is safe to reuse at the boundary of any WebSocket
    consumer.
    """

    resolved_ingested_at = ingested_at or datetime.now(timezone.utc)
    events: list[MarketEvent] = []
    for message in _messages(raw):
        if message.get("event_type") != "last_trade_price":
            continue
        try:
            side = message.get("side")
            event = MarketEvent(
                event_type="last_trade_price",
                asset_id=str(message["asset_id"]),
                market_id=str(message["market_id"]),
                price=float(message["price"]),
                size=float(message.get("size", 0.0)),
                side=str(side).upper() if side is not None else None,
                event_at=_event_timestamp(message.get("timestamp")),
                ingested_at=resolved_ingested_at,
            )
        except (KeyError, TypeError, ValueError, ValidationError):
            continue
        events.append(event)
    return events


class RecentEventBuffer:
    """Bounded FIFO event retention with bounded latest-event lookup.

    When the event limit is reached, the oldest retained event is evicted. If
    that event was the latest retained event for its market, the lookup falls
    back to the newest remaining event for that market. Markets with no
    retained event are removed from the lookup map.
    """

    def __init__(self, max_events: int = 100) -> None:
        if max_events < 1:
            raise ValueError("max_events must be positive")
        self._max_events = max_events
        self._events: deque[MarketEvent] = deque(maxlen=max_events)
        self._latest_by_market: dict[str, MarketEvent] = {}

    def append(self, event: MarketEvent) -> None:
        if len(self._events) == self._max_events:
            evicted = self._events.popleft()
            if self._latest_by_market.get(evicted.market_id) is evicted:
                replacement = next(
                    (
                        candidate
                        for candidate in reversed(self._events)
                        if candidate.market_id == evicted.market_id
                    ),
                    None,
                )
                if replacement is None:
                    self._latest_by_market.pop(evicted.market_id, None)
                else:
                    self._latest_by_market[evicted.market_id] = replacement
        self._events.append(event)
        self._latest_by_market[event.market_id] = event

    def extend(self, events: list[MarketEvent]) -> None:
        for event in events:
            self.append(event)

    def recent(self) -> tuple[MarketEvent, ...]:
        return tuple(self._events)

    def latest_for_market(self, market_id: str) -> MarketEvent | None:
        return self._latest_by_market.get(market_id)

    @property
    def market_count(self) -> int:
        """Return the number of markets represented by retained events."""

        return len(self._latest_by_market)

