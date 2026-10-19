# Polytracker Portfolio Showcase

This directory is a standalone, sanitized showcase of backend and data-engineering patterns from Polytracker.

It demonstrates how to turn provider-shaped market events into validated domain objects, compute reusable features, and safely process realtime messages. It intentionally does **not** contain the production application, proprietary scoring logic, private Lineups, credentials, database access, deployment configuration, or real user data.

## What this showcase demonstrates

- Typed Pydantic domain models for trades, market events, feature context, and ingestion telemetry.
- Provider-to-domain normalization with an allowlisted field mapping.
- Per-record validation and rejection handling without leaking raw payload values.
- Bounded retry-policy calculations for transient upstream failures.
- A reusable feature protocol and registry.
- Explainable, normalized example features for relative size, price extremeness, and recent activity.
- A pure WebSocket message parser that ignores control/unknown events and validates supported events.
- A bounded recent-event buffer with explicit FIFO eviction and latest-by-market fallback.
- Synthetic fixtures and meaningful `unittest` coverage.

## Architecture

```text
synthetic/provider-shaped rows
            │
            ▼
   ingestion.parsing
            │
            ├── valid rows ──> Pydantic Trade
            │                       │
            │                       ▼
            │                 FeaturePipeline
            │                       │
            │                       ▼
            │                 FeatureResult[]
            │
            └── invalid rows ─> safe rejection metadata

WebSocket text/bytes
            │
            ▼
   realtime.market_events
            │
            ├── validated MarketEvent[]
            └── malformed/control messages ignored
                         │
                         ▼
                 bounded RecentEventBuffer
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the production-to-showcase boundary and engineering decisions.

## Quickstart

The showcase is network-free and does not require PostgreSQL, Redis, Docker, a live API, or a WebSocket server.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -t . -v
python examples/demo.py
```

The package requires Python 3.11+ and Pydantic 2.x. The test suite uses the standard library `unittest` runner so no test framework is required.

## Production implementation versus showcase adaptation

The original Polytracker implementation contains a larger system: asynchronous public-market ingestion, market metadata enrichment, PostgreSQL persistence, Redis caching/realtime state, FastAPI, Next.js, Telegram delivery, migrations, Lineups, receipts, reports, and OCI Compose deployment.

This directory keeps only safe, reusable patterns:

- the domain contracts are reduced to public, generic fields;
- ingestion is represented by pure parsers instead of live API clients;
- the feature pipeline exposes interfaces and small demonstration metrics;
- the proprietary final scorer, model versions, thresholds, and private strategy rules are omitted;
- WebSocket handling is limited to parsing and bounded buffering, with no endpoint or subscription configuration;
- all fixtures are synthetic.

The examples are functional but are not a drop-in replacement for the production application.

## Recruiter signal

This small artifact makes the engineering boundaries inspectable: untrusted inputs are validated at the edge, malformed records are isolated, feature contracts are composable, realtime memory is bounded, and behavior is covered by deterministic tests and CI. The implementation favors reproducibility and explicit limitations over claims about trading performance.

## Capabilities and limitations

Implemented here:

- deterministic normalization and validation;
- safe handling of malformed rows/messages;
- typed, explainable feature outputs;
- bounded in-memory realtime state with documented eviction;
- unit tests for core behavior.

Not implemented here:

- network I/O or provider authentication;
- persistence, migrations, or cache infrastructure;
- alert delivery, frontend, user accounts, or private Lineups;
- production scoring, ML calibration, backtesting, or trade execution;
- full order-book processing or durable event streaming.

The production system's data caveats also apply conceptually: filtered event streams are not complete market tapes, closed-position history can be incomplete, and a feature value is not evidence of profitability without point-in-time and execution-aware evaluation.

## Testing

Run:

```bash
python -m unittest discover -s tests -t . -v
```

Result for this snapshot: 23 tests passed after package installation. Tests use synthetic data only and do not contact external services.

## Attribution and publication boundary

See [NOTICE.md](NOTICE.md). The showcase is derived from the recovered Polytracker source snapshot, but it is intentionally a separate public-facing artifact. Review licensing and attribution before publishing it as an independent GitHub repository.

