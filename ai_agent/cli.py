"""
Unified CLI.

Examples:
    python -m ai_agent.main ask "What is the capital of France?"
    python -m ai_agent.main tool-ask "Fetch https://example.com and summarize it"
    python -m ai_agent.main list-tools
    python -m ai_agent.main mcp-serve
"""

from __future__ import annotations

import argparse
import asyncio

from loguru import logger

from ai_agent.agents.assistant_agent import AssistantAgent
from ai_agent.agents.tool_using_agent import ToolUsingAgent
from ai_agent.config import settings
from ai_agent.logging_config import setup_logging
from ai_agent.tools import get_all_tools


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-agent", description="AI Agent CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ask = sub.add_parser("ask", help="Run AssistantAgent (no tools)")
    p_ask.add_argument("task", help="Task or question for the agent")

    p_tool = sub.add_parser("tool-ask", help="Run ToolUsingAgent (with tools)")
    p_tool.add_argument("task", help="Task for the agent")

    sub.add_parser("list-tools", help="List all registered tools")
    sub.add_parser("mcp-serve", help="Start the MCP server over stdio")

    return parser


async def _run(args: argparse.Namespace) -> None:
    setup_logging()

    if args.cmd == "list-tools":
        for tool in get_all_tools():
            print(f"- {tool.name}: {tool.description}")
        return

    if args.cmd == "mcp-serve":
        from ai_agent.mcp.server import MCPServer

        await MCPServer().serve()
        return

    if not settings.anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
        return

    if args.cmd == "ask":
        agent = AssistantAgent(model=settings.anthropic_model)
        result = await agent.run(args.task)
        print(result)
    elif args.cmd == "tool-ask":
        agent = ToolUsingAgent(model=settings.anthropic_model)
        result = await agent.run(args.task)
        print(result)


def main() -> None:
    args = _build_parser().parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
