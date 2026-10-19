from __future__ import annotations

from typing import Iterable, Protocol

from polytracker_showcase.domain import FeatureContext, FeatureResult, Trade


class Feature(Protocol):
    name: str
    description: str
    weight: float

    def compute(self, trade: Trade, context: FeatureContext) -> FeatureResult:
        ...


class FeatureRegistry:
    """Small registry that makes feature composition explicit and testable."""

    def __init__(self, features: Iterable[Feature]) -> None:
        self._features = list(features)
        names = [feature.name for feature in self._features]
        if len(names) != len(set(names)):
            raise ValueError("feature names must be unique")

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(feature.name for feature in self._features)

    def compute_all(self, trade: Trade, context: FeatureContext) -> list[FeatureResult]:
        return [feature.compute(trade, context) for feature in self._features]

