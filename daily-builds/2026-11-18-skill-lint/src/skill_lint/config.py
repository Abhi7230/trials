"""Configuration handling for skill-lint."""

from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found,no-redef]


class Config:
    """Configuration for skill-lint."""
    
    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize configuration.
        
        Args:
            config_path: Optional path to skill-lint.toml
        """
        self.disabled_rules: set[str] = set()
        self.thresholds: dict[str, Any] = {
            "description_min_length": 40,
            "description_max_length": 500,
            "body_max_lines": 500,
            "filler_density_threshold": 0.1,
        }
        self.min_score = 0
        
        if config_path and config_path.exists():
            self._load(config_path)
    
    def _load(self, path: Path) -> None:
        """Load configuration from TOML file."""
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            
            if "disabled_rules" in data:
                self.disabled_rules = set(data["disabled_rules"])
            
            if "thresholds" in data:
                self.thresholds.update(data["thresholds"])
            
            if "min_score" in data:
                self.min_score = data["min_score"]
        except Exception:
            pass  # Silently ignore config errors
    
    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled."""
        return rule_id not in self.disabled_rules
