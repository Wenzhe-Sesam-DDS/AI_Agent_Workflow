"""
Example 3: Start the MCP server over stdio so VS Code or Claude Desktop can use it.

Run:
    python examples/03_mcp_server_demo.py

Or simply rely on .vscode/mcp.json which launches `python -m ai_agent.mcp.server`.
"""

import asyncio

from ai_agent.logging_config import setup_logging
from ai_agent.mcp.server import MCPServer


async def main() -> None:
    setup_logging()
    await MCPServer().serve()


if __name__ == "__main__":
    asyncio.run(main())
