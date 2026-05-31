"""
Base skill interface — all skills must subclass this.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseSkill(ABC):
    """Abstract base class for all agent skills."""

    #: Unique name used for skill registration.
    name: str
    #: Human-readable description.
    description: str

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the skill logic."""
