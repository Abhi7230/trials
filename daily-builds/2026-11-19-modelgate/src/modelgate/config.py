"""Configuration loading and validation."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class ModelConfig(BaseModel):
    """Model configuration."""

    id: str
    provider: str
    cost_per_1m_input: float = Field(gt=0)
    cost_per_1m_output: float = Field(gt=0)
    avg_latency_ms: float = Field(gt=0)
    context_window: int = Field(gt=0)
    quality_tier: int = Field(ge=1, le=5)
    capabilities: list[str] = Field(default_factory=list)

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, v: list[str]) -> list[str]:
        """Validate capability names."""
        valid = {"tools", "vision", "json"}
        if invalid := set(v) - valid:
            raise ValueError(f"Invalid capabilities: {invalid}")
        return v


class CacheConfig(BaseModel):
    """Cache configuration."""

    enabled: bool = True
    max_size: int = Field(default=1000, gt=0)
    ttl_seconds: int = Field(default=3600, gt=0)


class LimitsConfig(BaseModel):
    """Rate and budget limits configuration."""

    default_daily_usd: float = Field(default=100.0, gt=0)
    default_rpm: int = Field(default=60, gt=0)
    default_tpm: int = Field(default=100000, gt=0)


class FallbackConfig(BaseModel):
    """Fallback configuration."""

    max_attempts: int = Field(default=3, ge=1)
    timeout_seconds: float = Field(default=30.0, gt=0)


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""

    failure_threshold: int = Field(default=5, ge=1)
    cooldown_seconds: float = Field(default=60.0, gt=0)


class Config(BaseModel):
    """Root configuration."""

    keys: list[str] = Field(default_factory=list)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    fallback: FallbackConfig = Field(default_factory=FallbackConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    models: list[ModelConfig]

    @field_validator("models")
    @classmethod
    def validate_unique_ids(cls, v: list[ModelConfig]) -> list[ModelConfig]:
        """Ensure model IDs are unique."""
        ids = [m.id for m in v]
        if len(ids) != len(set(ids)):
            duplicates = {mid for mid in ids if ids.count(mid) > 1}
            raise ValueError(f"Duplicate model IDs: {duplicates}")
        return v


def load_config(path: Path) -> Config:
    """Load configuration from YAML file."""
    with path.open() as f:
        data: dict[str, Any] = yaml.safe_load(f)
    return Config.model_validate(data)
