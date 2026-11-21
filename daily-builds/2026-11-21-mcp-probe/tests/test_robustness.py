"""Tests for robustness rules."""

import pytest
from mcp_probe.rules.robustness import check_robustness
from mcp_probe.models import Severity


def test_server_alive():
    """Test no findings when server is healthy."""
    findings = check_robustness(
        is_alive=True,
        stdout_noise=[],
        latency_p50=0.1,
        latency_p95=0.2,
        timeout_count=0,
        crash_count=0,
    )
    
    errors = [f for f in findings if f.severity == Severity.ERROR]
    assert len(errors) == 0


def test_server_died():
    """Test detection when server dies."""
    findings = check_robustness(
        is_alive=False,
        stdout_noise=[],
        latency_p50=0.1,
        latency_p95=0.2,
        timeout_count=0,
        crash_count=0,
    )
    
    assert any(f.rule_id == "RB001" for f in findings)


def test_stdout_noise_detected():
    """Test stdout noise is detected."""
    findings = check_robustness(
        is_alive=True,
        stdout_noise=["line 1", "line 2", "line 3"],
        latency_p50=0.1,
        latency_p95=0.2,
        timeout_count=0,
        crash_count=0,
    )
    
    assert any(f.rule_id == "RB002" for f in findings)


def test_timeout_detected():
    """Test timeouts are detected."""
    findings = check_robustness(
        is_alive=True,
        stdout_noise=[],
        latency_p50=0.1,
        latency_p95=0.2,
        timeout_count=3,
        crash_count=0,
    )
    
    assert any(f.rule_id == "RB003" for f in findings)


def test_crash_detected():
    """Test crashes are detected."""
    findings = check_robustness(
        is_alive=True,
        stdout_noise=[],
        latency_p50=0.1,
        latency_p95=0.2,
        timeout_count=0,
        crash_count=2,
    )
    
    assert any(f.rule_id == "RB004" for f in findings)


def test_high_latency_warning():
    """Test high latency generates warning."""
    findings = check_robustness(
        is_alive=True,
        stdout_noise=[],
        latency_p50=1.0,
        latency_p95=4.5,
        timeout_count=0,
        crash_count=0,
    )
    
    assert any(f.rule_id == "RB005" and f.severity == Severity.WARNING for f in findings)
