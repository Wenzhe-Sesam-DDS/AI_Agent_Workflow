"""Ollama-backed assistant agent using the OpenAI-compatible API."""

from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI
from loguru import logger

from ai_agent.agents.base_agent import BaseAgent
from ai_agent.config import settings


class OllamaAgent(BaseAgent):
    name = "ollama_assistant"
    description = "General-purpose assistant backed by a local Ollama model."

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        client: AsyncOpenAI | None = None,
    ) -> None:
        super().__init__()
        self._model = model or settings.ollama_model
        self._base_url = base_url or settings.ollama_base_url
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            # Ollama does not require a real API key; "ollama" is a placeholder.
            self._client = AsyncOpenAI(
                base_url=self._base_url,
                api_key="ollama",
            )
        return self._client

    async def run(self, task: str, **kwargs: Any) -> str:
        logger.info("OllamaAgent running task: {!r}", task)

        response = await self._get_client().chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": task}],
        )
        result: str = response.choices[0].message.content or ""
        logger.debug("OllamaAgent result: {!r}", result[:120])
        return result
