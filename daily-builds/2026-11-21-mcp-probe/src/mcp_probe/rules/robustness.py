"""Robustness check rules (RB001...)."""

from ..models import Finding, Severity


def check_robustness(
    is_alive: bool,
    stdout_noise: list[str],
    latency_p50: float,
    latency_p95: float,
    timeout_count: int,
    crash_count: int,
) -> list[Finding]:
    """Check server robustness."""
    findings = []
    
    if not is_alive:
        findings.append(Finding(
            rule_id="RB001",
            severity=Severity.ERROR,
            message="server process died during testing"
        ))
    
    if stdout_noise:
        findings.append(Finding(
            rule_id="RB002",
            severity=Severity.WARNING,
            message=f"server produced {len(stdout_noise)} non-JSON lines on stdout",
            details={"sample": stdout_noise[:3]}
        ))
    
    if timeout_count > 0:
        findings.append(Finding(
            rule_id="RB003",
            severity=Severity.ERROR,
            message=f"server timed out on {timeout_count} request(s)"
        ))
    
    if crash_count > 0:
        findings.append(Finding(
            rule_id="RB004",
            severity=Severity.ERROR,
            message=f"server crashed on {crash_count} request(s)"
        ))
    
    if latency_p95 > 3.0:
        findings.append(Finding(
            rule_id="RB005",
            severity=Severity.WARNING,
            message=f"high p95 latency: {latency_p95:.2f}s",
            details={"p50": latency_p50, "p95": latency_p95}
        ))
    
    return findings
