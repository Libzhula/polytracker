from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from pydantic import ValidationError

from polytracker_showcase.domain import IngestionRejection, IngestionTelemetry, Trade


def _timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        timestamp = value
    elif isinstance(value, (int, float)):
        seconds = float(value)
        if seconds > 10_000_000_000:
            seconds /= 1000.0
        timestamp = datetime.fromtimestamp(seconds, tz=timezone.utc)
    elif isinstance(value, str):
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("unsupported timestamp")

    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _required(payload: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        value = payload.get(name)
        if value not in (None, ""):
            return value
    raise ValueError("missing required field")


def _payload_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(dict(payload), sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _rejection(payload: Mapping[str, Any], *, source: str, reason: str) -> IngestionRejection:
    return IngestionRejection(
        source=source,
        entity_type="trade",
        reason_code=reason,
        payload_hash=_payload_hash(payload),
        field_names=tuple(sorted(str(key) for key in payload)),
    )


def parse_trade_payload(payload: Mapping[str, Any]) -> Trade:
    """Map a public-provider-shaped row into the internal trade contract.

    Only an allowlisted set of fields is copied. Unknown provider fields are not
    propagated into the domain model.
    """

    side = payload.get("side")
    normalized_side = str(side).upper() if side is not None else None
    return Trade(
        id=str(_required(payload, "id", "tradeId")),
        user_id=str(_required(payload, "proxyWallet", "user", "user_id")),
        market_id=str(_required(payload, "conditionId", "market", "market_id")),
        price=float(_required(payload, "price")),
        size=float(_required(payload, "size")),
        timestamp=_timestamp(_required(payload, "timestamp", "createdAt")),
        side=normalized_side,
        outcome=str(payload["outcome"]) if payload.get("outcome") is not None else None,
        asset_id=str(payload["asset_id"]) if payload.get("asset_id") is not None else None,
        market_slug=str(payload["slug"]) if payload.get("slug") is not None else None,
    )


def parse_trade_batch(
    rows: Sequence[Mapping[str, Any]],
    *,
    source: str = "public_market_data",
) -> tuple[list[Trade], IngestionTelemetry]:
    """Parse valid rows while quarantining invalid rows without leaking values."""

    telemetry = IngestionTelemetry(received_rows=len(rows))
    parsed: list[Trade] = []
    for row in rows:
        try:
            trade = parse_trade_payload(row)
        except (TypeError, ValueError, ValidationError):
            telemetry.add_rejection(
                _rejection(row, source=source, reason="invalid_or_missing_field")
            )
            continue
        parsed.append(trade)

    telemetry.parsed_rows = len(parsed)
    return parsed, telemetry

