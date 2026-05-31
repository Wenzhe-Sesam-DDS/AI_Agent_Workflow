"""Fetch the text content of a URL."""

from __future__ import annotations

from typing import Any

import httpx

from ai_agent.tools.base_tool import BaseTool


class FetchUrlTool(BaseTool):
    name = "fetch_url"
    description = "Fetch the text content of an HTTP(S) URL."

    async def run(self, url: str, timeout: float = 10.0) -> str:  # type: ignore[override]
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "HTTP(S) URL to fetch"},
                "timeout": {"type": "number", "description": "Timeout in seconds", "default": 10.0},
            },
            "required": ["url"],
        }
