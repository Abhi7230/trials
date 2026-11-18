"""Description quality rules."""

import re

from ..models import Finding, Severity, Skill
from . import RuleContext, register


@register("SL003")
def check_description_length(skill: Skill, ctx: RuleContext) -> list[Finding]:
    """Check description length is appropriate."""
    findings = []
    
    if not skill.description:
        return findings  # Already caught by SL001
    
    desc_len = len(skill.description)
    min_len = ctx.config.thresholds["description_min_length"]
    max_len = ctx.config.thresholds["description_max_length"]
    
    if desc_len < min_len:
        findings.append(Finding(
            rule_id="SL003",
            severity=Severity.WARNING,
            message=f"Description too short ({desc_len} chars, minimum {min_len})",
            line=1,
        ))
    elif desc_len > max_len:
        findings.append(Finding(
            rule_id="SL003",
            severity=Severity.WARNING,
            message=f"Description too long ({desc_len} chars, maximum {max_len})",
            line=1,
        ))
    
    return findings


@register("SL004")
def check_trigger_phrase(skill: Skill, ctx: RuleContext) -> list[Finding]:
    """Check that description contains a 'when to use' trigger phrase."""
    findings = []
    
    if not skill.description:
        return findings
    
    trigger_patterns = [
        r'\buse\s+(?:when|if|to|for)\b',
        r'\bwhen\s+(?:you|the|to)\b',
        r'\b(?:helps?|allows?|enables?)\s+(?:you|to)\b',
        r'\bfor\s+(?:when|creating|building|working)\b',
    ]
    
    has_trigger = any(re.search(pattern, skill.description.lower()) for pattern in trigger_patterns)
    
    if not has_trigger:
        findings.append(Finding(
            rule_id="SL004",
            severity=Severity.INFO,
            message="Description lacks a clear 'when to use' trigger phrase",
            line=1,
        ))
    
    return findings
