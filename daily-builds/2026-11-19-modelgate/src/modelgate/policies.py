"""Routing policies for model selection."""

from typing import Protocol

from modelgate.catalog import Model


class Policy(Protocol):
    """Routing policy interface."""

    def rank(
        self, models: list[Model], input_tokens: int, output_tokens: int
    ) -> list[tuple[Model, float]]:
        """Rank models, returning (model, score) pairs sorted best-first."""
        ...


class CheapestPolicy:
    """Select by lowest blended cost."""

    def rank(
        self, models: list[Model], input_tokens: int, output_tokens: int
    ) -> list[tuple[Model, float]]:
        """Rank by cost (lower is better)."""
        scored = [(m, m.blended_cost(input_tokens, output_tokens)) for m in models]
        return sorted(scored, key=lambda x: (x[1], x[0].id))


class FastestPolicy:
    """Select by lowest latency."""

    def rank(
        self, models: list[Model], input_tokens: int, output_tokens: int
    ) -> list[tuple[Model, float]]:
        """Rank by latency (lower is better)."""
        scored = [(m, m.avg_latency_ms) for m in models]
        return sorted(scored, key=lambda x: (x[1], x[0].id))


class QualityFirstPolicy:
    """Select by highest quality tier, then lowest cost."""

    def rank(
        self, models: list[Model], input_tokens: int, output_tokens: int
    ) -> list[tuple[Model, float]]:
        """Rank by quality (higher is better), then cost (lower is better)."""
        scored = [
            (m, -m.quality_tier * 1000 + m.blended_cost(input_tokens, output_tokens))
            for m in models
        ]
        return sorted(scored, key=lambda x: (x[1], x[0].id))


class BalancedPolicy:
    """Weighted combination of cost, latency and quality."""

    def __init__(
        self, cost_weight: float = 0.4, latency_weight: float = 0.3, quality_weight: float = 0.3
    ) -> None:
        self.cost_weight = cost_weight
        self.latency_weight = latency_weight
        self.quality_weight = quality_weight

    def rank(
        self, models: list[Model], input_tokens: int, output_tokens: int
    ) -> list[tuple[Model, float]]:
        """Rank by weighted score (lower is better)."""
        if not models:
            return []

        # Normalize factors to 0-1 range
        costs = [m.blended_cost(input_tokens, output_tokens) for m in models]
        latencies = [m.avg_latency_ms for m in models]
        qualities = [m.quality_tier for m in models]

        max_cost = max(costs) if max(costs) > 0 else 1.0
        max_latency = max(latencies) if max(latencies) > 0 else 1.0
        max_quality = 5.0  # Fixed max quality tier

        scored = []
        for m, cost, latency, quality in zip(models, costs, latencies, qualities, strict=True):
            norm_cost = cost / max_cost
            norm_latency = latency / max_latency
            norm_quality = 1.0 - (quality / max_quality)  # Invert: higher quality = lower score

            score = (
                self.cost_weight * norm_cost
                + self.latency_weight * norm_latency
                + self.quality_weight * norm_quality
            )
            scored.append((m, score))

        return sorted(scored, key=lambda x: (x[1], x[0].id))


POLICIES: dict[str, Policy] = {
    "cheapest": CheapestPolicy(),
    "fastest": FastestPolicy(),
    "quality-first": QualityFirstPolicy(),
    "balanced": BalancedPolicy(),
}


def get_policy(name: str) -> Policy:
    """Get policy by name."""
    if name not in POLICIES:
        raise ValueError(f"Unknown policy: {name}")
    return POLICIES[name]
