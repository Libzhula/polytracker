from __future__ import annotations

from dataclasses import dataclass


RETRYABLE_STATUS_CODES = frozenset({408, 425, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 4
    base_seconds: float = 0.5
    max_seconds: float = 8.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if self.base_seconds < 0.0:
            raise ValueError("base_seconds must be non-negative")
        if self.max_seconds < self.base_seconds:
            raise ValueError("max_seconds must be at least base_seconds")


def is_retryable_status(status_code: int) -> bool:
    return status_code in RETRYABLE_STATUS_CODES


def retry_delay_seconds(
    attempt: int,
    policy: RetryPolicy = RetryPolicy(),
    *,
    retry_after_seconds: float | None = None,
) -> float:
    """Return a deterministic capped delay; jitter belongs at the caller boundary."""

    if retry_after_seconds is not None:
        return max(0.0, min(float(retry_after_seconds), policy.max_seconds))
    exponential = policy.base_seconds * (2 ** max(attempt, 0))
    return max(0.0, min(exponential, policy.max_seconds))

