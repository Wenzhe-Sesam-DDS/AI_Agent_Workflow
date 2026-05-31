"""Example tool: echo input back to the caller."""

from __future__ import annotations

from typing import Any

from ai_agent.tools.base_tool import BaseTool


class EchoTool(BaseTool):
    name = "echo"
    description = "Echoes the provided text back. Useful for testing."

    async def run(self, text: str = "") -> str:  # type: ignore[override]
        return text

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to echo back"}
            },
            "required": ["text"],
        }
