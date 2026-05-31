"""Tools package — auto-discovers every BaseTool subclass in this folder."""

from __future__ import annotations

from ai_agent.registry import discover_subclasses
from ai_agent.tools.base_tool import BaseTool


def get_all_tools() -> list[BaseTool]:
    """Return one instance of every BaseTool subclass under ai_agent.tools."""
    return discover_subclasses("ai_agent.tools", BaseTool)


__all__ = ["BaseTool", "get_all_tools"]
