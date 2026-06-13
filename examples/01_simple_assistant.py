"""
Example 1: Local Ollama assistant (qwen3.5:9b, no tools).

Run:
    python examples/01_simple_assistant.py

Prerequisites:
    - Ollama running locally:  ollama serve
    - Model pulled:            ollama pull qwen3.5:9b
"""

import asyncio

from ai_agent.agents.ollama_agent import OllamaAgent
from ai_agent.config import settings
from ai_agent.logging_config import setup_logging


async def main() -> None:
    setup_logging()

    agent = OllamaAgent(model=settings.ollama_model, base_url=settings.ollama_base_url)
    answer = await agent.run("Explain async/await in Python in 2 sentences.")
    print("\n=== Agent Response ===")
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())
