"""Content structure rules."""

import re

from ..models import Finding, Severity, Skill
from . import RuleContext, register


@register("SL005")
def check_body_length(skill: Skill, ctx: RuleContext) -> list[Finding]:
    """Check that body is not too long."""
    findings = []
    
    max_lines = ctx.config.thresholds["body_max_lines"]
    body_lines = len([line for line in skill.body.split("\n") if line.strip()])
    
    if body_lines > max_lines:
        findings.append(Finding(
            rule_id="SL005",
            severity=Severity.WARNING,
            message=f"Body too long ({body_lines} lines, maximum {max_lines})",
            line=None,
        ))
    
    return findings


@register("SL007")
def check_heading_hierarchy(skill: Skill, ctx: RuleContext) -> list[Finding]:
    """Check for broken heading hierarchy."""
    findings = []
    
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
    previous_level = 0
    
    for i, line in enumerate(skill.body.split("\n"), start=1):
        match = heading_pattern.match(line)
        if match:
            current_level = len(match.group(1))
            
            # Check if we skipped levels (e.g., h1 -> h3)
            if current_level > previous_level + 1 and previous_level > 0:
                findings.append(Finding(
                    rule_id="SL007",
                    severity=Severity.WARNING,
                    message=f"Heading level jump from h{previous_level} to h{current_level}",
                    line=i,
                ))
            
            previous_level = current_level
    
    return findings


@register("SL008")
def check_filler_phrases(skill: Skill, ctx: RuleContext) -> list[Finding]:
    """Check for vague filler phrases."""
    findings = []
    
    filler_phrases = [
        r'\betc\.?\b',
        r'\bas needed\b',
        r'\bvarious\b',
        r'\bmany\b',
        r'\bsome\b',
        r'\bstuff\b',
        r'\bthings?\b',
        r'\band so on\b',
    ]
    
    content = skill.body.lower()
    word_count = len(content.split())
    
    if word_count == 0:
        return findings
    
    filler_count = sum(len(re.findall(pattern, content)) for pattern in filler_phrases)
    density = filler_count / word_count
    
    threshold = ctx.config.thresholds["filler_density_threshold"]
    
    if density > threshold:
        findings.append(Finding(
            rule_id="SL008",
            severity=Severity.INFO,
            message=f"High density of vague filler phrases ({filler_count} in {word_count} words)",
            line=None,
        ))
    
    return findings


@register("SL009")
def check_concrete_examples(skill: Skill, ctx: RuleContext) -> list[Finding]:
    """Check for concrete examples or code blocks."""
    findings = []
    
    # Look for code blocks (fenced or indented)
    has_fenced_code = bool(re.search(r'```[\s\S]*?```', skill.body))
    has_indented_code = bool(re.search(r'(?:^|\n)    \S', skill.body, re.MULTILINE))
    
    if not (has_fenced_code or has_indented_code):
        findings.append(Finding(
            rule_id="SL009",
            severity=Severity.INFO,
            message="No concrete examples or code blocks found",
            line=None,
        ))
    
    return findings
