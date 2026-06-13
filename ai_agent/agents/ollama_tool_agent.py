"""
OllamaToolAgent — Ollama-backed agent that can call registered Tools
via the OpenAI-compatible function-calling protocol.

Loops:
    user task → Ollama → (tool_calls? → run Tool → return result) → ... → final text
"""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from loguru import logger

from ai_agent.agents.base_agent import BaseAgent
from ai_agent.config import settings
from ai_agent.tools import get_all_tools
from ai_agent.tools.base_tool import BaseTool


class OllamaToolAgent(BaseAgent):
    name = "ollama_tool_user"
    description = "Ollama agent that autonomously calls registered tools."

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        max_iterations: int = 10,
        client: AsyncOpenAI | None = None,
    ) -> None:
        super().__init__()
        self._model = model or settings.ollama_model
        self._base_url = base_url or settings.ollama_base_url
        self._max_iterations = max_iterations
        self._client = client
        self._tools: dict[str, BaseTool] = {t.name: t for t in get_all_tools()}

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                base_url=self._base_url,
                api_key="ollama",
            )
        return self._client

    def _tool_specs(self) -> list[dict[str, Any]]:
        """Build OpenAI-format function tool specs from registered tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema(),
                },
            }
            for t in self._tools.values()
        ]

    async def run(self, task: str, **kwargs: Any) -> str:
        messages: list[ChatCompletionMessageParam] = [
            {"role": "user", "content": task}
        ]
        logger.info("OllamaToolAgent task: {!r}", task)

        for step in range(self._max_iterations):
            response = await self._get_client().chat.completions.create(
                model=self._model,
                messages=messages,
                tools=self._tool_specs(),  # type: ignore[arg-type]
                tool_choice="auto",
            )

            choice = response.choices[0]
            assistant_msg = choice.message

            # No more tool calls — return the final text.
            if not assistant_msg.tool_calls:
                return assistant_msg.content or ""

            # Append assistant message (with tool_calls) to history.
            messages.append(assistant_msg)  # type: ignore[arg-type]

            # Execute each requested tool call and append results.
            for tc in assistant_msg.tool_calls:
                tool = self._tools.get(tc.function.name)
                try:
                    args = json.loads(tc.function.arguments or "{}")
                    if tool is None:
                        result_text = f"Unknown tool: {tc.function.name}"
                    else:
                        result_text = str(await tool.run(**args))
                except Exception as exc:
                    logger.exception("Tool '{}' failed", tc.function.name)
                    result_text = f"Error: {exc}"

                logger.debug(
                    "[step {}] tool={} → {} chars", step, tc.function.name, len(result_text)
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_text,
                    }
                )

        return "[OllamaToolAgent] max iterations reached without final answer"
