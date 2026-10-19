# Showcase Architecture

## Purpose

The portfolio showcase isolates transferable engineering work from the original Polytracker application. It is designed to be readable and runnable by a recruiter or engineer without access to production services.

The showcase has four boundaries:

1. provider-shaped input parsing;
2. typed domain validation;
3. reusable feature computation;
4. safe realtime event processing.

No boundary performs network I/O, persistence, authentication, notification delivery, or trading.

## Component map

### `domain/models.py`

Defines the stable contracts shared by the showcase:

- `Trade` is the normalized event used by features;
- `MarketEvent` is the validated output of realtime parsing;
- `FeatureContext` contains only the context required by the demo features;
- `FeatureResult` carries a normalized value, weight, and human-readable reason;
- `TradeAnalysis` deliberately contains features but no final score;
- `IngestionRejection` and `IngestionTelemetry` provide safe operational metadata.

Pydantic rejects unknown fields on domain objects. This prevents provider payload drift from silently becoming application state.

### `ingestion/parsing.py`

The parser maps a provider-shaped mapping to the internal `Trade` contract. It accepts a small compatibility set of common provider field names, converts timestamps to UTC, normalizes the side, and copies only allowlisted values.

Batch parsing is intentionally failure-isolated. One malformed row produces rejection metadata and does not prevent other rows from being processed. Rejections contain a payload hash and field names, not raw payload values. This is suitable for diagnostics without turning an error table into a secrets or privacy sink.

### `ingestion/retry.py`

The retry module contains only deterministic policy logic:

- retryable status classification;
- maximum attempts and delay caps;
- optional provider `Retry-After` support.

Random jitter and HTTP client behavior belong to the caller, which keeps this module deterministic and easy to test.

### `features/base.py` and `features/basic.py`

`Feature` is a structural protocol. Any feature with the required attributes and `compute` method can be registered without inheriting from a framework class.

`FeatureRegistry` enforces unique names and computes features in a stable order. The example features are intentionally generic:

- `RelativeTradeSizeFeature` compares a trade with a baseline;
- `PriceExtremenessFeature` measures distance from the midpoint;
- `RecentActivityFeature` compares recent activity with a market baseline.

They are examples of feature engineering, not Polytracker's proprietary signal formula.

### `pipeline.py`

`FeaturePipeline` owns orchestration only. It resolves default context, invokes the registry, and returns a typed `TradeAnalysis`. It does not apply thresholds, emit alerts, persist data, or produce a business-sensitive score.

This separation makes the pipeline reusable for offline analysis, API services, or batch jobs while keeping policy decisions outside the showcase.

### `realtime/market_events.py`

The realtime module is deliberately a processing boundary rather than a WebSocket client.

`parse_market_messages`:

- accepts text or bytes;
- ignores `PING`, `PONG`, invalid JSON, unknown event types, and malformed records;
- supports a validated `last_trade_price` event shape;
- normalizes timestamps and sides;
- emits only `MarketEvent` objects.

`RecentEventBuffer` provides bounded in-memory retention and latest-by-market lookup. It retains at most `max_events` in FIFO order. Before appending at capacity, it evicts the oldest event; if that event was the latest retained event for its market, the lookup falls back to the newest remaining event for that market. Markets with no retained events are removed from the lookup map, so both structures remain bounded by `max_events`.

No public endpoint, subscription payload, credentials, or internal cache key is included.

## Production-to-showcase mapping

| Production concern | Showcase representation | Why it is safe |
|---|---|---|
| Public market API clients | Pure provider-shaped parser | No network calls, URLs, or credentials |
| Pydantic domain contracts | Reduced `Trade`, `MarketEvent`, and context models | No user records or private fields |
| Feature registry | Protocol, registry, and generic demo features | Proprietary feature weights and final scorer omitted |
| Market WebSocket worker | Message parser and bounded buffer | No endpoint, subscriptions, persistence, or deployment config |
| PostgreSQL/Redis | No implementation dependency | Showcase runs locally with synthetic data |
| Telegram delivery | Excluded | Avoids bot credentials and user destinations |
| Lineups and receipts | Excluded | Private/business-sensitive product logic |
| OCI Compose | Excluded | Avoids production topology, host details, and secrets |

## Engineering decisions

### Validate at the boundary

External payloads are untrusted and unstable. Parsing and validation happen before domain objects enter the rest of the application. Pydantic constraints enforce ranges and required fields.

### Preserve useful diagnostics without raw data

Per-record rejection counts and hashes support debugging and deduplication. Raw rejected payloads are not stored in this public example because they can contain identifiers or accidental secrets.

### Keep feature computation independent

The feature protocol permits new metrics without changing the pipeline. Feature results carry explanations so a downstream product can show why an observation was produced.

### Bound realtime state

The buffer is intentionally finite and evicts oldest events first. The latest-by-market index is derived only from retained events, including fallback after eviction; it cannot retain an unbounded set of market entries. Production systems should use explicit retention, backpressure, and durable storage policies rather than treating an in-memory list as an event log.

### Do not imply profitability

This showcase has no final score, alert threshold, or performance claim. A normalized feature is an analytical observation, not a validated trading edge.

## What remains outside the showcase

The original production-oriented release contains additional concerns that should be discussed separately in a private engineering review: database schema and migrations, API/session/authentication behavior, Telegram delivery, Lineup versioning and ownership, cache policy, worker deployment, backup handling, and performance evaluation.

Those components are intentionally not required here. This keeps the public artifact reproducible, auditable, and safe to publish.

