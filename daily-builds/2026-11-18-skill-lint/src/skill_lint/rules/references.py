"""File reference rules."""

from ..models import Finding, Severity, Skill
from . import RuleContext, register


@register("SL006")
def check_referenced_files(skill: Skill, ctx: RuleContext) -> list[Finding]:
    """Check that referenced files exist."""
    findings = []
    
    for ref_file in skill.referenced_files:
        # Resolve path relative to the skill file
        file_path = skill.path.parent / ref_file
        
        if not file_path.exists():
            findings.append(Finding(
                rule_id="SL006",
                severity=Severity.ERROR,
                message=f"Referenced file does not exist: {ref_file}",
                line=None,
            ))
    
    return findings


@register("SL011")
def check_duplicate_names(skill: Skill, ctx: RuleContext) -> list[Finding]:
    """Check for duplicate skill names across directory."""
    findings = []
    
    if not skill.name:
        return findings
    
    # Check if any other skill has the same name
    duplicates = [
        s for s in ctx.all_skills 
        if s.name == skill.name and s.path != skill.path
    ]
    
    if duplicates:
        dup_paths = ", ".join(str(s.path) for s in duplicates[:3])
        findings.append(Finding(
            rule_id="SL011",
            severity=Severity.ERROR,
            message=f"Duplicate skill name '{skill.name}' found in: {dup_paths}",
            line=1,
        ))
    
    return findings
