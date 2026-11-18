"""Linting rules for SKILL.md files."""

from collections.abc import Callable
from typing import Protocol

from ..config import Config
from ..models import Finding, Skill


class RuleContext(Protocol):
    """Context passed to rules."""
    
    config: Config
    all_skills: list[Skill]


RuleFunc = Callable[[Skill, RuleContext], list[Finding]]

_REGISTRY: dict[str, RuleFunc] = {}


def register(rule_id: str) -> Callable[[RuleFunc], RuleFunc]:
    """Register a linting rule."""
    def decorator(func: RuleFunc) -> RuleFunc:
        _REGISTRY[rule_id] = func
        return func
    return decorator


def get_all_rules() -> dict[str, RuleFunc]:
    """Get all registered rules."""
    return _REGISTRY.copy()


# Import all rule modules to trigger registration
from . import description, frontmatter, references, security, structure  # noqa: E402, F401
