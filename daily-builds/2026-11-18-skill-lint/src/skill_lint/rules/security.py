"""Security rules."""

import re

from ..models import Finding, Severity, Skill
from . import RuleContext, register


@register("SL010")
def check_secrets(skill: Skill, ctx: RuleContext) -> list[Finding]:
    """Check for possible secrets or API keys."""
    findings = []
    
    # Patterns for common API key formats
    secret_patterns = [
        (r'\bapi[_-]?key\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})', "API key"),
        (r'\btoken\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})', "token"),
        (r'\bsecret\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})', "secret"),
        (r'\bpassword\s*[:=]\s*["\']?([^\s"\']{8,})', "password"),
        (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API key"),
        (r'ghp_[a-zA-Z0-9]{36,}', "GitHub token"),
        (r'AKIA[0-9A-Z]{16}', "AWS access key"),
    ]
    
    content = skill.body
    
    for i, line in enumerate(content.split("\n"), start=1):
        for pattern, secret_type in secret_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append(Finding(
                    rule_id="SL010",
                    severity=Severity.ERROR,
                    message=f"Possible {secret_type} detected",
                    line=i,
                ))
                break  # Only report once per line
    
    return findings
