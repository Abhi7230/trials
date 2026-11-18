"""Tests for parser module."""

from pathlib import Path

from skill_lint.parser import parse_skill


def test_parse_skill_with_frontmatter() -> None:
    """Test parsing skill with valid frontmatter."""
    content = """---
name: test-skill
description: A test skill for parsing
---

# Test Skill

Body content here.
"""
    
    skill = parse_skill(Path("test.md"), content)
    
    assert skill.name == "test-skill"
    assert skill.description == "A test skill for parsing"
    assert "Body content here" in skill.body


def test_parse_skill_without_frontmatter() -> None:
    """Test parsing skill without frontmatter."""
    content = "# Test Skill\n\nNo frontmatter here."
    
    skill = parse_skill(Path("test.md"), content)
    
    assert skill.name is None
    assert skill.description is None
    assert skill.frontmatter == {}


def test_parse_skill_with_references() -> None:
    """Test parsing skill with file references."""
    content = """---
name: test
description: Test skill with references that help you work with files
---

See [helper](./helper.md) and [guide](../guide.md) but not [external](https://example.com).
"""
    
    skill = parse_skill(Path("test.md"), content)
    
    assert "./helper.md" in skill.referenced_files
    assert "../guide.md" in skill.referenced_files
    assert "https://example.com" not in skill.referenced_files


def test_parse_skill_malformed_yaml() -> None:
    """Test parsing skill with malformed YAML."""
    content = """---
name: test
description: [unclosed
---

Body content.
"""
    
    skill = parse_skill(Path("test.md"), content)
    
    assert skill.frontmatter == {}
    assert skill.name is None
