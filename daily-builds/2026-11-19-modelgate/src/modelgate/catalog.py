"""Model catalog with lookup and filtering."""

from dataclasses import dataclass

from modelgate.config import ModelConfig


@dataclass(frozen=True)
class Model:
    """Immutable model metadata."""

    id: str
    provider: str
    cost_per_1m_input: float
    cost_per_1m_output: float
    avg_latency_ms: float
    context_window: int
    quality_tier: int
    capabilities: frozenset[str]

    @classmethod
    def from_config(cls, config: ModelConfig) -> "Model":
        """Create from configuration."""
        return cls(
            id=config.id,
            provider=config.provider,
            cost_per_1m_input=config.cost_per_1m_input,
            cost_per_1m_output=config.cost_per_1m_output,
            avg_latency_ms=config.avg_latency_ms,
            context_window=config.context_window,
            quality_tier=config.quality_tier,
            capabilities=frozenset(config.capabilities),
        )

    def blended_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate total cost for given token counts."""
        input_cost = (input_tokens / 1_000_000) * self.cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * self.cost_per_1m_output
        return input_cost + output_cost


class Catalog:
    """Model catalog with lookup and filtering."""

    def __init__(self, models: list[Model]) -> None:
        self.models = models
        self._by_id = {m.id: m for m in models}

    def get(self, model_id: str) -> Model | None:
        """Get model by ID."""
        return self._by_id.get(model_id)

    def filter(
        self,
        min_context: int | None = None,
        required_capabilities: frozenset[str] | None = None,
    ) -> list[Model]:
        """Filter models by requirements."""
        result = self.models

        if min_context is not None:
            result = [m for m in result if m.context_window >= min_context]

        if required_capabilities:
            result = [m for m in result if required_capabilities.issubset(m.capabilities)]

        return result

    def all(self) -> list[Model]:
        """Get all models."""
        return list(self.models)
