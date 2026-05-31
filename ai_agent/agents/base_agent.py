"""
Base agent interface — all agents must subclass this.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    #: Unique agent identifier.
    name: str
    #: Short description of the agent's purpose.
    description: str

    def __init__(self) -> None:
        self._skills: dict[str, Any] = {}
        self._tools: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Registration helpers
    # ------------------------------------------------------------------

    def register_skill(self, skill: Any) -> None:
        self._skills[skill.name] = skill
        logger.debug("Agent '{}' registered skill '{}'", self.name, skill.name)

    def register_tool(self, tool: Any) -> None:
        self._tools[tool.name] = tool
        logger.debug("Agent '{}' registered tool '{}'", self.name, tool.name)

    # ------------------------------------------------------------------
    # Core lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    async def run(self, task: str, **kwargs: Any) -> Any:
        """Run the agent on a given task and return the result."""
