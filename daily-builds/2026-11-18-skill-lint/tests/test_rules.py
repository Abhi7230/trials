"""Tests for linting rules."""

from pathlib import Path

from skill_lint.config import Config
from skill_lint.linter import LintContext
from skill_lint.models import Skill
from skill_lint.rules.description import check_description_length, check_trigger_phrase
from skill_lint.rules.frontmatter import check_frontmatter, check_name_format
from skill_lint.rules.references import check_duplicate_names, check_referenced_files
from skill_lint.rules.security import check_secrets
from skill_lint.rules.structure import (
    check_body_length,
    check_concrete_examples,
    check_filler_phrases,
    check_heading_hierarchy,
)


def test_sl001_missing_frontmatter() -> None:
    """Test SL001: missing frontmatter."""
    skill = Skill(path=Path("test.md"), body="content", frontmatter={})
    ctx = LintContext(config=Config(), all_skills=[skill])
    
    findings = check_frontmatter(skill, ctx)
    
    assert len(findings) == 1
    assert findings[0].rule_id == "SL001"


def test_sl001_valid_frontmatter() -> None:
    """Test SL001: valid frontmatter."""
    skill = Skill(
        path=Path("test.md"),
        body="content",
        frontmatter={"name": "test", "description": "desc"},
        name="test",
        description="desc",
    )
    ctx = LintContext(config=Config(), all_skills=[skill])
    
    findings = check_frontmatter(skill, ctx)
    
    assert len(findings) == 0


def test_sl002_kebab_case() -> None:
    """Test SL002: name format."""
    skill = Skill(
        path=Path("test-skill/SKILL.md"),
        body="content",
        name="Test_Skill",
        frontmatter={"name": "Test_Skill"},
    )
    ctx = LintContext(config=Config(), all_skills=[skill])
    
    findings = check_name_format(skill, ctx)
    
    assert any("kebab-case" in f.message for f in findings)


def test_sl003_description_too_short() -> None:
    """Test SL003: description too short."""
    skill = Skill(
        path=Path("test.md"),
        body="content",
        description="Short",
        frontmatter={},
    )
    ctx = LintContext(config=Config(), all_skills=[skill])
    
    findings = check_description_length(skill, ctx)
    
    assert len(findings) == 1
    assert "too short" in findings[0].message


def test_sl004_trigger_phrase() -> None:
    """Test SL004: trigger phrase detection."""
    skill_with = Skill(
        path=Path("test.md"),
        body="content",
        description="Use when you need to process data",
        frontmatter={},
    )
    skill_without = Skill(
        path=Path("test.md"),
        body="content",
        description="This is a skill that processes data in various ways",
        frontmatter={},
    )
    ctx = LintContext(config=Config(), all_skills=[])
    
    findings_with = check_trigger_phrase(skill_with, ctx)
    findings_without = check_trigger_phrase(skill_without, ctx)
    
    assert len(findings_with) == 0
    assert len(findings_without) == 1


def test_sl005_body_too_long() -> None:
    """Test SL005: body too long."""
    long_body = "\n".join(f"Line {i}" for i in range(600))
    skill = Skill(path=Path("test.md"), body=long_body, frontmatter={})
    ctx = LintContext(config=Config(), all_skills=[skill])
    
    findings = check_body_length(skill, ctx)
    
    assert len(findings) == 1
    assert "too long" in findings[0].message


def test_sl006_missing_reference(tmp_path: Path) -> None:
    """Test SL006: referenced file doesn't exist."""
    skill_path = tmp_path / "SKILL.md"
    skill = Skill(
        path=skill_path,
        body="content",
        referenced_files=["./missing.md"],
        frontmatter={},
    )
    ctx = LintContext(config=Config(), all_skills=[skill])
    
    findings = check_referenced_files(skill, ctx)
    
    assert len(findings) == 1
    assert "does not exist" in findings[0].message


def test_sl007_heading_hierarchy() -> None:
    """Test SL007: broken heading hierarchy."""
    body = "# Heading 1\n\n### Heading 3\n\nSkipped h2!"
    skill = Skill(path=Path("test.md"), body=body, frontmatter={})
    ctx = LintContext(config=Config(), all_skills=[skill])
    
    findings = check_heading_hierarchy(skill, ctx)
    
    assert len(findings) == 1
    assert "jump" in findings[0].message.lower()


def test_sl008_filler_phrases() -> None:
    """Test SL008: filler phrase density."""
    body = "This has etc. and various things and stuff as needed and so on etc."
    skill = Skill(path=Path("test.md"), body=body, frontmatter={})
    ctx = LintContext(config=Config(), all_skills=[skill])
    
    findings = check_filler_phrases(skill, ctx)
    
    assert len(findings) == 1
    assert "filler" in findings[0].message.lower()


def test_sl009_no_examples() -> None:
    """Test SL009: no code examples."""
    skill = Skill(
        path=Path("test.md"),
        body="Just text without any code examples",
        frontmatter={},
    )
    ctx = LintContext(config=Config(), all_skills=[skill])
    
    findings = check_concrete_examples(skill, ctx)
    
    assert len(findings) == 1


def test_sl009_has_examples() -> None:
    """Test SL009: has code examples."""
    skill = Skill(
        path=Path("test.md"),
        body="Here's code:\n\n```python\nprint('hello')\n```",
        frontmatter={},
    )
    ctx = LintContext(config=Config(), all_skills=[skill])
    
    findings = check_concrete_examples(skill, ctx)
    
    assert len(findings) == 0


def test_sl010_secrets() -> None:
    """Test SL010: detect secrets."""
    body = 'api_key="sk-1234567890abcdef1234567890abcdef"'
    skill = Skill(path=Path("test.md"), body=body, frontmatter={})
    ctx = LintContext(config=Config(), all_skills=[skill])
    
    findings = check_secrets(skill, ctx)
    
    assert len(findings) >= 1
    assert any("key" in f.message.lower() for f in findings)


def test_sl011_duplicate_names() -> None:
    """Test SL011: duplicate skill names."""
    skill1 = Skill(
        path=Path("dir1/SKILL.md"),
        body="content",
        name="duplicate",
        frontmatter={},
    )
    skill2 = Skill(
        path=Path("dir2/SKILL.md"),
        body="content",
        name="duplicate",
        frontmatter={},
    )
    ctx = LintContext(config=Config(), all_skills=[skill1, skill2])
    
    findings = check_duplicate_names(skill1, ctx)
    
    assert len(findings) == 1
    assert "Duplicate" in findings[0].message
