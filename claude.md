# Claude AI Project Instructions

This file provides context and guidelines for Claude AI (and other LLMs) when working in this codebase.

## Project Overview

This is a Python-based AI Agent framework that implements:
- **Agents** — autonomous reasoning units that plan and act
- **Skills** — reusable capability modules attached to agents
- **Tools** — callable functions exposed to agents (compatible with MCP)
- **MCP** — Model Context Protocol server for interoperability with MCP-compatible clients
- **Resources** — static or dynamic data sources accessible by agents

## Architecture

```
ai_agent/
├── agents/       # Agent definitions and orchestration logic
├── skills/       # Reusable skill modules (search, summarize, code, etc.)
├── tools/        # Tool implementations (file I/O, web, shell, APIs)
├── mcp/          # MCP server exposing tools as protocol endpoints
├── resources/    # Data files, prompts, knowledge bases, configs
└── main.py       # Entry point
```

## Coding Conventions

- Python 3.11+
- Use `async/await` for all I/O-bound operations
- Type hints required on all public functions and classes
- Pydantic v2 models for data validation and serialization
- Tools must inherit from `BaseTool` and implement `run()`
- Skills must inherit from `BaseSkill`
- Agents must inherit from `BaseAgent`

## Key Dependencies

| Package | Purpose |
|---|---|
| `anthropic` | Claude API client |
| `mcp` | Model Context Protocol SDK |
| `pydantic` | Data validation |
| `httpx` | Async HTTP client |
| `python-dotenv` | Environment variable management |
| `loguru` | Structured logging |

## Environment Variables

```
ANTHROPIC_API_KEY=       # Claude API key
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8080
LOG_LEVEL=INFO
```

## Adding a New Tool

1. Create a file in `tools/` (e.g., `tools/my_tool.py`)
2. Subclass `BaseTool`, define `name`, `description`, and implement `run()`
3. Register it in `tools/__init__.py`
4. The MCP server auto-discovers registered tools

## Adding a New Skill

1. Create a file in `skills/` (e.g., `skills/my_skill.py`)
2. Subclass `BaseSkill` and implement `execute()`
3. Register it in `skills/__init__.py`

## MCP Server

Start the MCP server with:
```bash
python -m ai_agent.mcp.server
```
or via the VS Code MCP config in `.vscode/mcp.json`.

## Testing

```bash
pytest tests/ -v
```
