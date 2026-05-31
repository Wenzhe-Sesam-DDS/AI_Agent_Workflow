"""
Example 2: Tool-using agent that autonomously calls fetch_url + read_file.

Run:
    python examples/02_tool_using_agent.py
"""

import asyncio

from ai_agent.agents.tool_using_agent import ToolUsingAgent
from ai_agent.config import settings
from ai_agent.logging_config import setup_logging


async def main() -> None:
    setup_logging()
    if not settings.anthropic_api_key:
        print("Set ANTHROPIC_API_KEY in .env first.")
        return

    agent = ToolUsingAgent(model=settings.anthropic_model)
    result = await agent.run(
        "Fetch https://example.com and tell me the page's H1 heading."
    )
    print("\n=== Final Answer ===")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
