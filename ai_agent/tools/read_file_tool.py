"""Read a UTF-8 text file from the local filesystem (within the workspace)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_agent.tools.base_tool import BaseTool


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a UTF-8 text file by absolute or relative path."

    async def run(self, path: str, max_bytes: int = 100_000) -> str:  # type: ignore[override]
        p = Path(path).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Not a file: {p}")
        data = p.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="replace")

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "max_bytes": {"type": "integer", "description": "Max bytes to read", "default": 100000},
            },
            "required": ["path"],
        }
