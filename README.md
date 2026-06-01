# AI Agent Framework

A Python framework for building AI agents with skills, tools, and MCP (Model Context Protocol) support. Agents are powered by Claude (Anthropic) and can autonomously call tools, compose skills, and serve as an MCP server for VS Code or Claude Desktop.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Agent](#running-the-agent)
   - [CLI commands](#cli-commands)
   - [Programmatic usage](#programmatic-usage)
   - [Example scripts](#example-scripts)
5. [Project Layout](#project-layout)
6. [Built-in Components](#built-in-components)
   - [Agents](#agents)
   - [Tools](#tools)
   - [Skills](#skills)
7. [Extending the Framework](#extending-the-framework)
   - [Adding a Tool](#adding-a-tool)
   - [Adding a Skill](#adding-a-skill)
   - [Adding an Agent](#adding-an-agent)
8. [MCP Server](#mcp-server)
9. [Testing](#testing)

---

## Prerequisites

- Python 3.11 or newer
- An [Anthropic API key](https://console.anthropic.com/) (required for any agent that calls Claude)

---

## Installation

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install the package and all dev dependencies
pip install -e ".[dev]"
```

The `-e` flag installs in editable mode so code changes take effect immediately without re-installing.

---

## Configuration

All settings are read from environment variables or a `.env` file in the project root.

```powershell
# Copy the example file (if it exists) or create .env manually
Copy-Item .env.example .env
```

Then open `.env` and fill in the values:

```dotenv
ANTHROPIC_API_KEY=sk-ant-...   # Required — your Anthropic API key
ANTHROPIC_MODEL=claude-opus-4-5  # Optional — defaults to claude-opus-4-5
MCP_SERVER_HOST=0.0.0.0          # Optional — MCP server bind host
MCP_SERVER_PORT=8080             # Optional — MCP server port
LOG_LEVEL=INFO                   # Optional — DEBUG | INFO | WARNING | ERROR
```

Settings are loaded once at startup via `ai_agent/config.py` using Pydantic Settings. Import them anywhere:

```python
from ai_agent.config import settings
print(settings.anthropic_model)
```

---

## Running the Agent

### CLI commands

The package installs an `ai-agent` entry point that exposes four sub-commands:

| Command | Description |
|---|---|
| `ai-agent ask "<task>"` | Run the simple `AssistantAgent` (no tools, pure Q&A) |
| `ai-agent tool-ask "<task>"` | Run the `ToolUsingAgent` (Claude chooses and calls tools automatically) |
| `ai-agent list-tools` | Print every registered tool and its description |
| `ai-agent mcp-serve` | Start the MCP server over stdio |

**Examples:**

```powershell
# Ask a plain question
ai-agent ask "What is the capital of France?"

# Let the agent fetch a URL and answer a question about it
ai-agent tool-ask "Fetch https://example.com and tell me the page title"

# Show all tools the agent knows about
ai-agent list-tools

# Start the MCP server (for VS Code / Claude Desktop integration)
ai-agent mcp-serve
```

You can also invoke the CLI via the module directly if the entry point is not on your PATH:

```powershell
python -m ai_agent.cli ask "Explain async/await in Python in two sentences."
```

### Programmatic usage

```python
import asyncio
from ai_agent.agents.assistant_agent import AssistantAgent
from ai_agent.agents.tool_using_agent import ToolUsingAgent
from ai_agent.config import settings

async def main():
    # Simple assistant — no tools
    agent = AssistantAgent(model=settings.anthropic_model)
    answer = await agent.run("Summarize the Zen of Python.")
    print(answer)

    # Tool-using agent — automatically calls fetch_url, read_file, echo, etc.
    tool_agent = ToolUsingAgent(model=settings.anthropic_model)
    result = await tool_agent.run("Read the file README.md and give me a one-sentence summary.")
    print(result)

asyncio.run(main())
```

You can also attach a skill directly to any agent before running it:

```python
from ai_agent.agents.assistant_agent import AssistantAgent
from ai_agent.skills.summarize_skill import SummarizeSkill

agent = AssistantAgent()
agent.register_skill(SummarizeSkill())
# The agent can now call skill.execute() internally
```

### Example scripts

Ready-to-run examples live in `examples/`:

| File | What it demonstrates |
|---|---|
| [examples/01_simple_assistant.py](examples/01_simple_assistant.py) | `AssistantAgent` with a plain text task |
| [examples/02_tool_using_agent.py](examples/02_tool_using_agent.py) | `ToolUsingAgent` fetching a URL autonomously |
| [examples/03_mcp_server_demo.py](examples/03_mcp_server_demo.py) | Starting the MCP server programmatically |

```powershell
python examples/01_simple_assistant.py
python examples/02_tool_using_agent.py
```

---

## Project Layout

```
ai_agent/
├── agents/
│   ├── base_agent.py        # Abstract BaseAgent — register_skill(), register_tool(), run()
│   ├── assistant_agent.py   # Simple Claude chat agent (no tools)
│   └── tool_using_agent.py  # Claude agent with full tool-use loop
├── skills/
│   ├── base_skill.py        # Abstract BaseSkill — execute()
│   └── summarize_skill.py   # Summarize text via Claude
├── tools/
│   ├── base_tool.py         # Abstract BaseTool — run(), input_schema()
│   ├── echo_tool.py         # Echo input back (useful for testing)
│   ├── fetch_url_tool.py    # HTTP GET a URL and return its text
│   └── read_file_tool.py    # Read a local UTF-8 file
├── mcp/
│   └── server.py            # MCP server — auto-exposes all registered tools
├── resources/
│   ├── prompts/             # Prompt template text files
│   ├── knowledge_base/      # Static reference data
│   └── configs/             # Extra config files
├── config.py                # Pydantic Settings — reads from .env
├── logging_config.py        # Loguru setup
├── registry.py              # Auto-discovery of BaseTool / BaseSkill / BaseAgent subclasses
├── cli.py                   # `ai-agent` CLI entry point
└── main.py                  # Quick demo entry point
examples/                    # Standalone runnable scripts
tests/                       # Pytest test suite
```

**Key design point — auto-discovery:** You do not need to edit any `__init__.py` when adding a new tool or skill. `registry.py` scans the package at startup and instantiates every concrete subclass it finds. Simply drop your new file in the right folder and it will be picked up automatically.

---

## Built-in Components

### Agents

| Class | Module | Description |
|---|---|---|
| `AssistantAgent` | `agents/assistant_agent.py` | Sends a single message to Claude and returns the text response. No tools. |
| `ToolUsingAgent` | `agents/tool_using_agent.py` | Runs a multi-step loop: Claude decides which tool to call → tool runs → result fed back → loop repeats until Claude produces a final answer. Max 10 iterations by default. |

### Tools

Tools are auto-discovered and available in both the `ToolUsingAgent` and the MCP server.

| Name | Class | Description |
|---|---|---|
| `echo` | `EchoTool` | Returns its input unchanged. Useful for testing. |
| `fetch_url` | `FetchUrlTool` | HTTP GET a URL and return the response body as text. Optional `timeout` parameter (default 10 s). |
| `read_file` | `ReadFileTool` | Read a local file by path. Optional `max_bytes` cap (default 100 000). |

List all tools at any time:

```powershell
ai-agent list-tools
```

### Skills

Skills are reusable capability modules that agents can call internally.

| Name | Class | Description |
|---|---|---|
| `summarize` | `SummarizeSkill` | Summarize a block of text using Claude. Accepts `text` and optional `max_words` (default 100). |

---

## Extending the Framework

### Adding a Tool

1. Create `ai_agent/tools/my_tool.py`:

```python
from __future__ import annotations
from typing import Any
from ai_agent.tools.base_tool import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "One-line description shown to the LLM."

    async def run(self, param: str) -> str:          # type: ignore[override]
        return f"Result for: {param}"

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "Input parameter"},
            },
            "required": ["param"],
        }
```

2. That's it. The auto-discovery in `registry.py` will find and instantiate `MyTool` automatically. It will be available to `ToolUsingAgent` and the MCP server on the next run.

### Adding a Skill

1. Create `ai_agent/skills/my_skill.py`:

```python
from __future__ import annotations
from typing import Any
from ai_agent.skills.base_skill import BaseSkill

class MySkill(BaseSkill):
    name = "my_skill"
    description = "Short description."

    async def execute(self, input_text: str, **kwargs: Any) -> str:  # type: ignore[override]
        # Your logic here
        return input_text.upper()
```

2. Use it from an agent:

```python
from ai_agent.skills.my_skill import MySkill

agent.register_skill(MySkill())
skill = agent._skills["my_skill"]
result = await skill.execute(input_text="hello")
```

### Adding an Agent

1. Create `ai_agent/agents/my_agent.py`:

```python
from __future__ import annotations
from typing import Any
from ai_agent.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    name = "my_agent"
    description = "What this agent does."

    async def run(self, task: str, **kwargs: Any) -> str:
        # Custom reasoning / orchestration logic
        return f"Handled: {task}"
```

2. Instantiate and call it directly in your code — agents are not auto-discovered (unlike tools/skills), so you import and use them explicitly.

---

## MCP Server

The MCP server exposes every registered tool as an MCP-compatible endpoint over stdio. This lets VS Code Copilot Chat, Claude Desktop, and any other MCP client use your tools without extra code.

**Start the server:**

```powershell
# Via CLI entry point
ai-agent mcp-serve

# Or via the module directly
python -m ai_agent.mcp.server
```

**VS Code integration** — add `.vscode/mcp.json` to your workspace:

```json
{
  "servers": {
    "ai-agent": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "ai_agent.mcp.server"]
    }
  }
}
```

Once connected, VS Code Copilot Chat can call your tools (e.g. `fetch_url`, `read_file`) directly from the chat panel.

---

## Testing

```powershell
# Run the full test suite
pytest tests/ -v

# Run a single test file
pytest tests/test_echo_tool.py -v

# Run with coverage (requires pytest-cov)
pytest tests/ --cov=ai_agent --cov-report=term-missing
```

Tests use `pytest-asyncio` with `asyncio_mode = "auto"`, so `async def test_*` functions work without any extra decorators.

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `anthropic` | Claude API client |
| `mcp` | Model Context Protocol SDK |
| `pydantic` / `pydantic-settings` | Data validation and settings management |
| `httpx` | Async HTTP client (used by `FetchUrlTool`) |
| `python-dotenv` | `.env` file loading |
| `loguru` | Structured logging |

See [claude.md](claude.md) for full coding conventions.
