"""Example skill: summarize text using the Claude API."""

from __future__ import annotations

from typing import Any

import anthropic
from loguru import logger

from ai_agent.skills.base_skill import BaseSkill


class SummarizeSkill(BaseSkill):
    name = "summarize"
    description = "Summarizes a block of text using Claude."

    def __init__(self, client: anthropic.AsyncAnthropic | None = None) -> None:
        self._client = client or anthropic.AsyncAnthropic()

    async def execute(self, text: str, max_words: int = 100, **kwargs: Any) -> str:  # type: ignore[override]
        logger.debug("SummarizeSkill: summarizing {} chars", len(text))
        message = await self._client.messages.create(
            model="claude-opus-4-5",
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize the following text in at most {max_words} words:\n\n{text}",
                }
            ],
        )
        return message.content[0].text  # type: ignore[union-attr]
