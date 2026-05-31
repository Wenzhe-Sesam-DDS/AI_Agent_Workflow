"""
Entry point — run a quick demo of the AssistantAgent.

Usage:
    python -m ai_agent.main
    # or
    python ai_agent/main.py
"""

from __future__ import annotations

import asyncio

from loguru import logger

from ai_agent.agents.assistant_agent import AssistantAgent
from ai_agent.config import settings
from ai_agent.logging_config import setup_logging


async def main() -> None:
    setup_logging()

    if not settings.anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
        return

    agent = AssistantAgent(model=settings.anthropic_model)
    result = await agent.run("Say hello and introduce yourself in one sentence.")
    logger.info("Agent response: {}", result)


if __name__ == "__main__":
    asyncio.run(main())
