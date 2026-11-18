"""Tests for CLI."""

import subprocess
import sys
from pathlib import Path


def test_cli_help() -> None:
    """Test CLI help output."""
    result = subprocess.run(
        [sys.executable, "-m", "skill_lint.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    
    assert result.returncode == 0
    assert "skill-lint" in result.stdout.lower()


def test_cli_lint_good_example() -> None:
    """Test CLI with good example."""
    examples_dir = Path(__file__).parent.parent / "examples" / "good"
    
    result = subprocess.run(
        [sys.executable, "-m", "skill_lint.cli", str(examples_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    
    assert result.returncode == 0
    assert "SKILL-LINT REPORT" in result.stdout


def test_cli_lint_bad_example() -> None:
    """Test CLI with bad example."""
    examples_dir = Path(__file__).parent.parent / "examples" / "bad"
    
    result = subprocess.run(
        [sys.executable, "-m", "skill_lint.cli", str(examples_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    
    # Should exit with error code
    assert result.returncode == 1
    assert "ERROR" in result.stdout or "error" in result.stdout.lower()


def test_cli_json_format() -> None:
    """Test CLI with JSON format."""
    examples_dir = Path(__file__).parent.parent / "examples" / "good"
    
    result = subprocess.run(
        [sys.executable, "-m", "skill_lint.cli", "--format", "json", str(examples_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    
    assert result.returncode == 0
    assert '"version"' in result.stdout
    assert '"results"' in result.stdout
