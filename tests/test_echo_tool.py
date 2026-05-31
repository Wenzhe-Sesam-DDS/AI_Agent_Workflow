"""Tests for the EchoTool."""

import pytest
from ai_agent.tools.echo_tool import EchoTool


@pytest.mark.asyncio
async def test_echo_tool_returns_input() -> None:
    tool = EchoTool()
    assert await tool.run(text="hello") == "hello"


@pytest.mark.asyncio
async def test_echo_tool_empty_string() -> None:
    tool = EchoTool()
    assert await tool.run(text="") == ""
