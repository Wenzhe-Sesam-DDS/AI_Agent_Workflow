"""
ToolUsingAgent — Claude-powered agent that can call registered Tools
via Anthropic's native tool-use protocol.

Loops:
    user task → Claude → (tool_use? → run Tool → return result) → ... → final text
"""

from __future__ import annotations

from typing import Any

import anthropic
from loguru import logger

from ai_agent.agents.base_agent import BaseAgent
from ai_agent.tools import get_all_tools
from ai_agent.tools.base_tool import BaseTool


class ToolUsingAgent(BaseAgent):
    name = "tool_user"
    description = "Claude agent that autonomously calls registered tools."

    def __init__(
        self,
        model: str = "claude-opus-4-5",
        max_iterations: int = 10,
        client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        super().__init__()
        self._model = model
        self._max_iterations = max_iterations
        self._client = client
        self._tools: dict[str, BaseTool] = {t.name: t for t in get_all_tools()}

    def _get_client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            self._client = anthropic.AsyncAnthropic()
        return self._client

    # ------------------------------------------------------------------
    # Build Anthropic-format tool specs
    # ------------------------------------------------------------------

    def _tool_specs(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema(),
            }
            for t in self._tools.values()
        ]

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run(self, task: str, **kwargs: Any) -> str:
        messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
        logger.info("ToolUsingAgent task: {!r}", task)

        for step in range(self._max_iterations):
            response = await self._get_client().messages.create(
                model=self._model,
                max_tokens=2048,
                tools=self._tool_specs(),
                messages=messages,  # type: ignore[arg-type]
            )

            # Stop if Claude finished without requesting another tool.
            if response.stop_reason != "tool_use":
                text_blocks = [b.text for b in response.content if b.type == "text"]
                return "\n".join(text_blocks)

            # Append assistant's tool_use request to history.
            messages.append({"role": "assistant", "content": response.content})

            # Execute every tool_use block, append tool_result blocks.
            tool_results: list[dict[str, Any]] = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool = self._tools.get(block.name)
                if tool is None:
                    result_text = f"Unknown tool: {block.name}"
                    is_error = True
                else:
                    try:
                        result_text = str(await tool.run(**(block.input or {})))
                        is_error = False
                    except Exception as exc:
                        logger.exception("Tool '{}' failed", block.name)
                        result_text = f"Error: {exc}"
                        is_error = True

                logger.debug("[step {}] tool={} → {} chars", step, block.name, len(result_text))
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                        "is_error": is_error,
                    }
                )

            messages.append({"role": "user", "content": tool_results})

        return "[ToolUsingAgent] max iterations reached without final answer"
