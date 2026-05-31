"""Skills package — auto-discovers every BaseSkill subclass in this folder."""

from __future__ import annotations

from ai_agent.registry import discover_subclasses
from ai_agent.skills.base_skill import BaseSkill


def get_all_skills() -> list[BaseSkill]:
    return discover_subclasses("ai_agent.skills", BaseSkill)


__all__ = ["BaseSkill", "get_all_skills"]
