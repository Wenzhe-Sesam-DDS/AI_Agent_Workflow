"""Example agent: a simple Claude-powered assistant."""

from __future__ import annotations

from typing import Any

import anthropic
from loguru import logger

from ai_agent.agents.base_agent import BaseAgent


class AssistantAgent(BaseAgent):
    name = "assistant"
    description = "General-purpose Claude assistant agent."

    def __init__(
        self,
        model: str = "claude-opus-4-5",
        client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        super().__init__()
        self._model = model
        self._client = client

    def _get_client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            self._client = anthropic.AsyncAnthropic()
        return self._client

    async def run(self, task: str, **kwargs: Any) -> str:
        logger.info("AssistantAgent running task: {!r}", task)

        messages: list[dict[str, str]] = [{"role": "user", "content": task}]

        response = await self._get_client().messages.create(
            model=self._model,
            max_tokens=1024,
            messages=messages,  # type: ignore[arg-type]
        )
        result: str = response.content[0].text  # type: ignore[union-attr]
        logger.debug("AssistantAgent result: {!r}", result[:120])
        return result
