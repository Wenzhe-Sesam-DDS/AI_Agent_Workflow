"""Tests for the tool registry."""

from ai_agent.tools import get_all_tools
from ai_agent.tools.base_tool import BaseTool


def test_registry_returns_tools() -> None:
    tools = get_all_tools()
    assert len(tools) > 0
    assert all(isinstance(t, BaseTool) for t in tools)


def test_registry_tools_have_metadata() -> None:
    for tool in get_all_tools():
        assert tool.name, "Tool is missing name"
        assert tool.description, f"Tool '{tool.name}' is missing description"
        schema = tool.input_schema()
        assert schema["type"] == "object"
