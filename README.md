# AI Agent Framework

A Python framework for building AI agents with skills, tools, and MCP (Model Context Protocol) support.

## Features

- **Agents** — autonomous reasoning units powered by Claude
- **Skills** — reusable capability modules
- **Tools** — atomic operations exposed via MCP
- **MCP Server** — interoperable with any MCP-compatible client (e.g. VS Code, Claude Desktop)
- **Resources** — prompt templates, knowledge bases, configs

## Quickstart

### 1. Create & activate the virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -e ".[dev]"
```

### 3. Configure environment

```powershell
Copy-Item .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
```

### 4. Run the demo agent

```powershell
python -m ai_agent.main
```

### 5. Start the MCP server

```powershell
python -m ai_agent.mcp.server
```

Or use the VS Code MCP integration via [.vscode/mcp.json](.vscode/mcp.json).

## Project Layout

```
ai_agent/
├── agents/            # BaseAgent + concrete agents
├── skills/            # BaseSkill + concrete skills
├── tools/             # BaseTool + concrete tools (auto-exposed via MCP)
├── mcp/               # MCP server
├── resources/
│   ├── prompts/       # Prompt templates
│   ├── knowledge_base/
│   └── configs/
├── config.py          # Pydantic settings
├── logging_config.py  # Loguru setup
└── main.py            # Entry point
tests/                 # Pytest tests
```

## Adding Components

| Component | Steps |
|---|---|
| **Tool** | Subclass `BaseTool` in `tools/`, register in `tools/__init__.py` |
| **Skill** | Subclass `BaseSkill` in `skills/`, register in `skills/__init__.py` |
| **Agent** | Subclass `BaseAgent` in `agents/`, register in `agents/__init__.py` |

See [claude.md](claude.md) for full conventions.

## Testing

```powershell
pytest tests/ -v
```
