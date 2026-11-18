"""Frontmatter and naming rules."""

from ..models import Finding, Severity, Skill
from . import RuleContext, register


@register("SL001")
def check_frontmatter(skill: Skill, ctx: RuleContext) -> list[Finding]:
    """Check for missing or invalid frontmatter."""
    findings = []
    
    if not skill.frontmatter:
        findings.append(Finding(
            rule_id="SL001",
            severity=Severity.ERROR,
            message="Missing YAML frontmatter (should start with --- and end with ---)",
            line=1,
        ))
    elif not skill.name or not skill.description:
        findings.append(Finding(
            rule_id="SL001",
            severity=Severity.ERROR,
            message="Frontmatter missing required fields: 'name' and 'description'",
            line=1,
        ))
    
    return findings


@register("SL002")
def check_name_format(skill: Skill, ctx: RuleContext) -> list[Finding]:
    """Check that name is kebab-case and matches directory name."""
    findings = []
    
    if not skill.name:
        return findings  # Already caught by SL001
    
    # Check kebab-case format
    if not skill.name.replace("-", "").replace("_", "").isalnum():
        findings.append(Finding(
            rule_id="SL002",
            severity=Severity.WARNING,
            message=f"Skill name '{skill.name}' should be kebab-case (lowercase-with-hyphens)",
            line=1,
        ))
    elif "_" in skill.name or skill.name != skill.name.lower():
        findings.append(Finding(
            rule_id="SL002",
            severity=Severity.WARNING,
            message=(
                f"Skill name '{skill.name}' should be kebab-case "
                "(use hyphens, not underscores)"
            ),
            line=1,
        ))
    
    # Check if name matches parent directory (if in a directory)
    parent_dir = skill.path.parent.name
    if parent_dir and parent_dir not in (".", skill.name):
        findings.append(Finding(
            rule_id="SL002",
            severity=Severity.WARNING,
            message=f"Skill name '{skill.name}' does not match directory name '{parent_dir}'",
            line=1,
        ))
    
    return findings
