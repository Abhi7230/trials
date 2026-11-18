"""Main linting orchestration."""

from pathlib import Path
from typing import Any

from .config import Config
from .critic import Critic, get_critic
from .models import Finding, Report, Skill
from .parser import parse_skill
from .rules import get_all_rules
from .scoring import calculate_score


class LintContext:
    """Context for linting operations."""
    
    def __init__(self, config: Config, all_skills: list[Skill]) -> None:
        """Initialize context."""
        self.config = config
        self.all_skills = all_skills


def lint_skill(skill: Skill, context: LintContext) -> list[Finding]:
    """Lint a single skill.
    
    Args:
        skill: The skill to lint
        context: Linting context
        
    Returns:
        List of findings
    """
    findings: list[Finding] = []
    rules = get_all_rules()
    
    for rule_id, rule_func in rules.items():
        if context.config.is_rule_enabled(rule_id):
            findings.extend(rule_func(skill, context))
    
    return findings


def lint_path(
    path: Path,
    config: Config | None = None,
    use_llm: bool = False,
) -> Report:
    """Lint SKILL.md files in a path.
    
    Args:
        path: Path to file or directory
        config: Optional configuration
        use_llm: Whether to use LLM critic
        
    Returns:
        Complete linting report
    """
    if config is None:
        config = Config()
    
    # Find all SKILL.md files
    if path.is_file():
        skill_files = [path]
    else:
        skill_files = list(path.rglob("SKILL.md")) + list(path.rglob("*.skill.md"))
    
    # Parse all skills
    skills = [parse_skill(f) for f in skill_files]
    
    # Create context
    context = LintContext(config=config, all_skills=skills)
    
    # Lint each skill
    findings_map: dict[str, list[Finding]] = {}
    scores_map: dict[str, Any] = {}
    
    for skill in skills:
        findings = lint_skill(skill, context)
        findings_map[str(skill.path)] = findings
        scores_map[str(skill.path)] = calculate_score(findings)
    
    # Add optional LLM critique
    critic: Critic | None = None
    critiques: dict[str, str] = {}
    if use_llm:
        critic = get_critic(use_llm=True)
        for skill in skills:
            critiques[str(skill.path)] = critic.critique(skill)
    
    # Calculate summary
    total_findings = sum(len(f) for f in findings_map.values())
    avg_score = sum(s.value for s in scores_map.values()) / len(scores_map) if scores_map else 0
    
    summary = {
        "total_skills": len(skills),
        "total_findings": total_findings,
        "average_score": round(avg_score, 1),
        "critiques": critiques if critiques else None,
    }
    
    return Report(
        skills=skills,
        findings=findings_map,
        scores=scores_map,
        summary=summary,
    )


def lint_text(content: str, filename: str = "skill.md", config: Config | None = None) -> Report:
    """Lint a skill from text content.
    
    Args:
        content: SKILL.md content
        filename: Filename for reporting
        config: Optional configuration
        
    Returns:
        Complete linting report
    """
    if config is None:
        config = Config()
    
    # Parse skill
    path = Path(filename)
    skill = parse_skill(path, content)
    
    # Create context with just this skill
    context = LintContext(config=config, all_skills=[skill])
    
    # Lint
    findings = lint_skill(skill, context)
    score = calculate_score(findings)
    
    return Report(
        skills=[skill],
        findings={filename: findings},
        scores={filename: score},
        summary={
            "total_skills": 1,
            "total_findings": len(findings),
            "average_score": score.value,
        },
    )
