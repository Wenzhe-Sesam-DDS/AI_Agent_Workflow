"""
MCP Server — exposes registered tools via the Model Context Protocol.

Run directly:
    python -m ai_agent.mcp.server

Or start from the VS Code MCP panel using .vscode/mcp.json.
"""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

from ai_agent.tools import get_all_tools


class MCPServer:
    """Wraps all registered BaseTool instances as an MCP-compatible server."""

    def __init__(self) -> None:
        self._server = Server("ai-agent-mcp")
        self._tools = {t.name: t for t in get_all_tools()}
        self._register_handlers()

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        @self._server.list_tools()
        async def list_tools(_request: ListToolsRequest) -> ListToolsResult:
            return ListToolsResult(
                tools=[
                    Tool(
                        name=tool.name,
                        description=tool.description,
                        inputSchema=tool.input_schema(),
                    )
                    for tool in self._tools.values()
                ]
            )

        @self._server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            tool_name = request.params.name
            arguments: dict[str, Any] = request.params.arguments or {}

            if tool_name not in self._tools:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {tool_name}")],
                    isError=True,
                )

            try:
                result = await self._tools[tool_name].run(**arguments)
                return CallToolResult(
                    content=[TextContent(type="text", text=str(result))]
                )
            except Exception as exc:
                logger.exception("Tool '{}' raised an error", tool_name)
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {exc}")],
                    isError=True,
                )

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    async def serve(self) -> None:
        logger.info("Starting MCP server with {} tool(s): {}", len(self._tools), list(self._tools))
        async with stdio_server() as (read_stream, write_stream):
            await self._server.run(read_stream, write_stream, self._server.create_initialization_options())


def main() -> None:
    asyncio.run(MCPServer().serve())


if __name__ == "__main__":
    main()
