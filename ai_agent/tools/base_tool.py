"""
Base tool interface — all tools must subclass this.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    #: Unique identifier used by MCP and agent routing.
    name: str
    #: Human-readable description exposed to the LLM.
    description: str

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Execute the tool with the provided arguments."""

    def input_schema(self) -> dict[str, Any]:
        """Return a JSON Schema dict describing the tool's inputs.

        Override this method to provide a richer schema.  The default
        implementation returns an empty object schema.
        """
        return {"type": "object", "properties": {}, "required": []}
