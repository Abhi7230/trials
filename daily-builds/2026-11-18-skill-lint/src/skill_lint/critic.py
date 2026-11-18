"""Critic protocol and implementations for LLM-based critiques."""

import os
from typing import Protocol

from .models import Skill


class Critic(Protocol):
    """Protocol for skill critics."""
    
    def critique(self, skill: Skill) -> str:
        """Provide a critique of the skill.
        
        Args:
            skill: The skill to critique
            
        Returns:
            Critique text
        """
        ...


class HeuristicCritic:
    """Offline heuristic-based critic (default)."""
    
    def critique(self, skill: Skill) -> str:
        """Provide heuristic-based critique."""
        critiques = []
        
        if skill.description and len(skill.description) < 100:
            critiques.append("Description could be more detailed")
        
        if not skill.body.strip():
            critiques.append("Body content is empty")
        
        if "example" not in skill.body.lower() and "```" not in skill.body:
            critiques.append("Consider adding concrete examples")
        
        if not critiques:
            return "Skill structure looks good"
        
        return "; ".join(critiques)


class LLMCritic:
    """LLM-based critic (requires API key)."""
    
    def __init__(self) -> None:
        """Initialize LLM critic."""
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("LLM critic requires OPENAI_API_KEY or ANTHROPIC_API_KEY")
    
    def critique(self, skill: Skill) -> str:
        """Provide LLM-based critique."""
        # For now, fall back to heuristic (actual LLM integration would go here)
        fallback = HeuristicCritic()
        return f"[LLM] {fallback.critique(skill)}"


def get_critic(use_llm: bool = False) -> Critic:
    """Get the appropriate critic implementation.
    
    Args:
        use_llm: Whether to use LLM-based critique
        
    Returns:
        Critic implementation
    """
    if use_llm:
        try:
            return LLMCritic()
        except ValueError:
            # Fall back to heuristic if no API key
            return HeuristicCritic()
    return HeuristicCritic()
