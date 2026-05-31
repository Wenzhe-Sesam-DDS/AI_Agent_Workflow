"""
Example 1: Direct Claude assistant (no tools).

Run:
    python examples/01_simple_assistant.py
"""

import asyncio

from ai_agent.agents.assistant_agent import AssistantAgent
from ai_agent.config import settings
from ai_agent.logging_config import setup_logging


async def main() -> None:
    setup_logging()
    if not settings.anthropic_api_key:
        print("Set ANTHROPIC_API_KEY in .env first.")
        return

    agent = AssistantAgent(model=settings.anthropic_model)
    answer = await agent.run("Explain async/await in Python in 2 sentences.")
    print("\n=== Agent Response ===")
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())
