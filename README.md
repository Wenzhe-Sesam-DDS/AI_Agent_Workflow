# AI Agent Framework

一个基于 Python 的 AI Agent 框架，支持本地大模型（Ollama）和云端 Claude API，内置 Web GUI、工具调用、技能模块与 MCP 协议服务端。

---

## 目录

1. [功能特性](#功能特性)
2. [快速开始](#快速开始)
3. [Web GUI](#web-gui)
4. [配置说明](#配置说明)
5. [CLI 命令](#cli-命令)
6. [编程使用](#编程使用)
7. [项目结构](#项目结构)
8. [内置组件](#内置组件)
9. [扩展框架](#扩展框架)
10. [MCP 服务端](#mcp-服务端)
11. [测试](#测试)
12. [依赖包说明](#依赖包说明)

---

## 功能特性

- **本地 LLM 支持** — 通过 Ollama 运行 `qwen3.5:9b` 等任意本地模型，无需 API Key
- **云端 Claude 支持** — 通过 Anthropic API 使用 Claude 系列模型
- **Web GUI** — 基于 Gradio 的现代深色主题聊天界面，支持流式输出、历史记录、工具调用
- **Agent 工具调用** — Agent 可自动决策并调用工具（抓取网页、读取文件等）
- **技能模块（Skills）** — 可复用的能力模块，可挂载到任意 Agent
- **MCP 协议服务端** — 将所有工具暴露为 MCP 端点，兼容 VS Code Copilot Chat 和 Claude Desktop
- **工具自动发现** — 在 `tools/` 中新建文件即自动注册，无需修改任何配置

---

## 快速开始

### 前置要求

- Python 3.11+
- （本地模式）[Ollama](https://ollama.com/) 已安装并运行
- （云端模式）[Anthropic API Key](https://console.anthropic.com/)

### 安装

```powershell
# 1. 创建并激活虚拟环境
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. 安装项目及所有依赖（含开发工具）
pip install -e ".[dev]"
```

`-e` 为可编辑模式，修改代码后无需重新安装即可生效。

### 本地模型（推荐）

```powershell
# 启动 Ollama
ollama serve

# 拉取模型（首次使用）
ollama pull qwen3.5:9b

# 运行示例
python examples/01_simple_assistant.py
```

### 启动 Web GUI

```powershell
python app.py
# 浏览器自动打开 http://127.0.0.1:7860
```

---

## Web GUI

运行 `python app.py` 启动基于 Gradio 的 Web 界面：

| 标签页 | 功能 |
|--------|------|
| 💬 对话 | 流式聊天，支持 Shift+Enter 换行，可开启工具调用模式 |
| 📜 历史记录 | 按日期查看所有历史对话（自动保存到 `data/chat_history.json`） |
| 🛠️ 工具 | 查看所有已注册工具的名称、说明和参数 Schema |
| ℹ️ 关于 | 项目架构图和当前配置信息 |

**界面特性：**
- 启动时自动检测 Ollama 连接状态（🟢/🟡/🔴）
- 刷新页面自动恢复上次会话
- 输入框支持多行、可调整大小
- 对话框高度可拖拽调整

---

## 配置说明

所有配置通过环境变量或项目根目录的 `.env` 文件加载：

```dotenv
# ── 云端 Claude（可选）──────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-...       # Anthropic API Key
ANTHROPIC_MODEL=claude-opus-4-5    # 默认 Claude 模型

# ── 本地 Ollama（默认）─────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434/v1  # Ollama OpenAI 兼容端点
OLLAMA_MODEL=qwen3.5:9b                   # 本地模型名称

# ── MCP 服务端 ──────────────────────────────────────────
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8080

# ── 日志 ────────────────────────────────────────────────
LOG_LEVEL=INFO    # DEBUG | INFO | WARNING | ERROR
```

在代码中读取配置：

```python
from ai_agent.config import settings
print(settings.ollama_model)
print(settings.anthropic_api_key)
```

---

## CLI 命令

安装后可直接使用 `ai-agent` 命令：

| 命令 | 说明 |
|------|------|
| `ai-agent ask "<问题>"` | 使用 AssistantAgent（Claude，无工具）回答问题 |
| `ai-agent tool-ask "<任务>"` | 使用 ToolUsingAgent（Claude + 工具调用） |
| `ai-agent list-tools` | 列出所有已注册工具 |
| `ai-agent mcp-serve` | 启动 MCP stdio 服务端 |

```powershell
# 示例
ai-agent ask "Python 中 GIL 是什么？"
ai-agent tool-ask "抓取 https://example.com 并总结其内容"
ai-agent list-tools
```

也可通过模块直接调用：

```powershell
python -m ai_agent.cli ask "解释 async/await"
```

---

## 编程使用

### 使用本地 Ollama 模型

```python
import asyncio
from ai_agent.agents.ollama_agent import OllamaAgent
from ai_agent.agents.ollama_tool_agent import OllamaToolAgent
from ai_agent.config import settings

async def main():
    # 纯对话，无工具
    agent = OllamaAgent(model=settings.ollama_model)
    answer = await agent.run("用两句话解释量子纠缠。")
    print(answer)

    # 带工具调用
    tool_agent = OllamaToolAgent(model=settings.ollama_model)
    result = await tool_agent.run("抓取 https://example.com 并总结内容")
    print(result)

asyncio.run(main())
```

### 使用云端 Claude

```python
import asyncio
from ai_agent.agents.assistant_agent import AssistantAgent
from ai_agent.agents.tool_using_agent import ToolUsingAgent
from ai_agent.config import settings

async def main():
    agent = AssistantAgent(model=settings.anthropic_model)
    answer = await agent.run("总结 Python 的 Zen。")
    print(answer)

asyncio.run(main())
```

### 挂载技能

```python
from ai_agent.agents.ollama_agent import OllamaAgent
from ai_agent.skills.summarize_skill import SummarizeSkill

agent = OllamaAgent()
agent.register_skill(SummarizeSkill())
```

### 示例脚本

| 文件 | 说明 |
|------|------|
| [examples/01_simple_assistant.py](examples/01_simple_assistant.py) | OllamaAgent 基础对话 |
| [examples/02_tool_using_agent.py](examples/02_tool_using_agent.py) | ToolUsingAgent 自动调用工具 |
| [examples/03_mcp_server_demo.py](examples/03_mcp_server_demo.py) | 以编程方式启动 MCP 服务端 |

```powershell
python examples/01_simple_assistant.py
python examples/02_tool_using_agent.py
```

---

## 项目结构

```
AI_Agent_Workflow/
├── app.py                       # Gradio Web GUI 入口
├── pyproject.toml               # 项目元数据与依赖声明
├── .env                         # 本地配置（不提交到 Git）
│
├── ai_agent/
│   ├── agents/
│   │   ├── base_agent.py        # 抽象基类：register_skill/tool, run()
│   │   ├── assistant_agent.py   # Claude 纯对话 Agent
│   │   ├── tool_using_agent.py  # Claude + 工具调用 Agent
│   │   ├── ollama_agent.py      # 本地 Ollama 纯对话 Agent ★
│   │   └── ollama_tool_agent.py # 本地 Ollama + 工具调用 Agent ★
│   ├── skills/
│   │   ├── base_skill.py        # 抽象基类：execute()
│   │   └── summarize_skill.py   # 文本摘要技能（Claude）
│   ├── tools/
│   │   ├── base_tool.py         # 抽象基类：run(), input_schema()
│   │   ├── echo_tool.py         # 回显输入（测试用）
│   │   ├── fetch_url_tool.py    # HTTP GET 抓取网页
│   │   └── read_file_tool.py    # 读取本地文件
│   ├── mcp/
│   │   └── server.py            # MCP 服务端，自动暴露所有工具
│   ├── config.py                # Pydantic Settings，读取 .env
│   ├── logging_config.py        # Loguru 日志配置
│   ├── registry.py              # 工具/技能自动发现
│   ├── cli.py                   # ai-agent CLI 入口
│   └── main.py                  # 快速演示入口
│
├── examples/                    # 可直接运行的示例脚本
├── tests/                       # Pytest 测试套件
└── data/                        # 运行时数据（不提交到 Git）
    └── chat_history.json        # GUI 对话历史（自动生成）
```

★ 为本次新增文件

**自动发现机制：** `registry.py` 在启动时扫描 `tools/` 和 `skills/` 目录，自动实例化所有 `BaseTool`/`BaseSkill` 子类。新增工具只需在对应目录创建文件，无需修改任何 `__init__.py`。

---

## 内置组件

### Agents

| 类 | 后端 | 工具调用 | 说明 |
|----|------|----------|------|
| `OllamaAgent` | Ollama（本地） | ❌ | 纯对话，无工具，流式输出 |
| `OllamaToolAgent` | Ollama（本地） | ✅ | 多步工具调用循环，最多 10 次迭代 |
| `AssistantAgent` | Claude API | ❌ | 纯对话，需要 ANTHROPIC_API_KEY |
| `ToolUsingAgent` | Claude API | ✅ | 工具调用，需要 ANTHROPIC_API_KEY |

### Tools

| 名称 | 类 | 说明 |
|------|----|------|
| `echo` | `EchoTool` | 原样返回输入，用于测试 |
| `fetch_url` | `FetchUrlTool` | HTTP GET 并返回响应文本，支持 `timeout` 参数 |
| `read_file` | `ReadFileTool` | 读取本地 UTF-8 文件，支持 `max_bytes` 限制 |

### Skills

| 名称 | 类 | 说明 |
|------|----|------|
| `summarize` | `SummarizeSkill` | 使用 Claude 对文本摘要，支持 `max_words` 参数 |

---

## 扩展框架

### 添加工具

新建 `ai_agent/tools/my_tool.py`：

```python
from __future__ import annotations
from typing import Any
from ai_agent.tools.base_tool import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "工具的一行描述（LLM 会看到这个）。"

    async def run(self, param: str) -> str:          # type: ignore[override]
        return f"结果: {param}"

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "输入参数"},
            },
            "required": ["param"],
        }
```

无需其他操作。下次运行时自动注册到所有 Agent 和 MCP 服务端。

### 添加技能

新建 `ai_agent/skills/my_skill.py`：

```python
from __future__ import annotations
from typing import Any
from ai_agent.skills.base_skill import BaseSkill

class MySkill(BaseSkill):
    name = "my_skill"
    description = "技能描述。"

    async def execute(self, input_text: str, **kwargs: Any) -> str:
        return input_text.upper()
```

### 添加 Agent

新建 `ai_agent/agents/my_agent.py`，继承 `BaseAgent` 并实现 `run()` 方法。Agent 不自动发现，需要显式导入使用。

---

## MCP 服务端

MCP 服务端通过 stdio 暴露所有已注册工具，兼容 VS Code Copilot Chat、Claude Desktop 等 MCP 客户端。

```powershell
# 通过 CLI 启动
ai-agent mcp-serve

# 或通过模块启动
python -m ai_agent.mcp.server
```

**VS Code 集成** — 在工作区添加 `.vscode/mcp.json`：

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

连接后，VS Code Copilot Chat 可直接调用 `fetch_url`、`read_file` 等工具。

---

## 测试

```powershell
# 运行完整测试套件
pytest tests/ -v

# 运行单个测试文件
pytest tests/test_echo_tool.py -v

# 带覆盖率报告（需安装 pytest-cov）
pytest tests/ --cov=ai_agent --cov-report=term-missing
```

测试使用 `pytest-asyncio`，`asyncio_mode = "auto"`，`async def test_*` 函数无需额外装饰器。

---

## 依赖包说明

### 运行时依赖

| 包 | 版本要求 | 用途 |
|----|----------|------|
| `anthropic` | ≥0.28 | Claude API 客户端（云端模式） |
| `openai` | ≥1.0 | Ollama OpenAI 兼容 API 客户端（本地模式） |
| `mcp` | ≥1.0 | Model Context Protocol SDK |
| `pydantic` | ≥2.0 | 数据验证与序列化 |
| `pydantic-settings` | ≥2.0 | 从 .env 加载配置 |
| `httpx` | ≥0.27 | 异步 HTTP 客户端（FetchUrlTool / Ollama 状态检测） |
| `python-dotenv` | ≥1.0 | .env 文件加载 |
| `loguru` | ≥0.7 | 结构化日志 |
| `gradio` | ≥6.0 | Web GUI 框架 |

### 开发依赖

| 包 | 用途 |
|----|------|
| `pytest` | 测试框架 |
| `pytest-asyncio` | 异步测试支持 |
| `ruff` | 代码检查（Linter） |
| `black` | 代码格式化 |

---

更多开发规范请参见 [claude.md](claude.md)。


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
