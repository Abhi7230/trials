"""Tests for configuration."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from skill_lint.config import Config


def test_default_config() -> None:
    """Test default configuration."""
    config = Config()
    
    assert len(config.disabled_rules) == 0
    assert config.thresholds["description_min_length"] == 40
    assert config.min_score == 0


def test_load_config_from_file() -> None:
    """Test loading configuration from TOML file."""
    config_content = """
disabled_rules = ["SL008", "SL009"]
min_score = 70

[thresholds]
description_min_length = 50
description_max_length = 600
"""
    
    with NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(config_content)
        config_path = Path(f.name)
    
    try:
        config = Config(config_path=config_path)
        
        assert "SL008" in config.disabled_rules
        assert "SL009" in config.disabled_rules
        assert config.min_score == 70
        assert config.thresholds["description_min_length"] == 50
        assert config.thresholds["description_max_length"] == 600
    finally:
        config_path.unlink()


def test_rule_enabled() -> None:
    """Test rule enabled check."""
    config = Config()
    config.disabled_rules = {"SL008"}
    
    assert config.is_rule_enabled("SL001")
    assert not config.is_rule_enabled("SL008")
