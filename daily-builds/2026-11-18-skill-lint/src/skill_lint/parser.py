"""Parse SKILL.md files with YAML frontmatter."""

import re
from pathlib import Path
from typing import Any

import yaml

from .models import Skill


def parse_skill(path: Path, content: str | None = None) -> Skill:
    """Parse a SKILL.md file into a Skill object.
    
    Args:
        path: Path to the skill file
        content: Optional content (if None, reads from path)
        
    Returns:
        Parsed Skill object
    """
    if content is None:
        content = path.read_text(encoding="utf-8")
    
    lines = content.splitlines()
    frontmatter: dict[str, Any] = {}
    body_start = 0
    
    # Check for YAML frontmatter
    if lines and lines[0].strip() == "---":
        # Find closing ---
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                frontmatter_text = "\n".join(lines[1:i])
                try:
                    frontmatter = yaml.safe_load(frontmatter_text) or {}
                except yaml.YAMLError:
                    frontmatter = {}
                body_start = i + 1
                break
    
    body = "\n".join(lines[body_start:])
    
    # Extract referenced files (relative paths in markdown links or includes)
    referenced_files = []
    # Match markdown links: [text](path)
    for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', body):
        link = match.group(2)
        # Only include relative file paths (not URLs)
        if not link.startswith(('http://', 'https://', '#', '/')):
            referenced_files.append(link)
    
    return Skill(
        path=path,
        name=frontmatter.get("name"),
        description=frontmatter.get("description"),
        body=body,
        frontmatter=frontmatter,
        lines=lines,
        referenced_files=referenced_files,
    )
