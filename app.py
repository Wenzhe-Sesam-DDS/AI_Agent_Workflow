"""
AI Agent GUI — powered by Gradio + local Ollama (qwen3.5:9b).

Run:
    python app.py
    # then open http://localhost:7860
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import gradio as gr
from openai import AsyncOpenAI

from ai_agent.config import settings
from ai_agent.logging_config import setup_logging
from ai_agent.tools import get_all_tools
from ai_agent.tools.base_tool import BaseTool

setup_logging()

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

_tools: dict[str, BaseTool] = {t.name: t for t in get_all_tools()}

# ---------------------------------------------------------------------------
# History persistence
# ---------------------------------------------------------------------------

_HISTORY_FILE = Path("data/chat_history.json")
_CLEARED_FLAG = Path("data/cleared.flag")


def _load_all_sessions() -> list:
    if _HISTORY_FILE.exists():
        try:
            return json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_session(messages: list) -> None:
    """Append / update today’s session with current messages."""
    if not messages:
        return
    _HISTORY_FILE.parent.mkdir(exist_ok=True)
    sessions = _load_all_sessions()
    today = datetime.now().strftime("%Y-%m-%d")
    now_iso = datetime.now().isoformat(timespec="seconds")
    # Update today’s entry if present, else append
    for s in sessions:
        if s["date"] == today:
            s["messages"] = messages
            s["updated"] = now_iso
            break
    else:
        sessions.append({"date": today, "id": now_iso, "messages": messages, "updated": now_iso})
    _HISTORY_FILE.write_text(json.dumps(sessions, ensure_ascii=False, indent=2), encoding="utf-8")


def _restore_last_session() -> list:
    """Return messages from the last saved session, or [] if just cleared."""
    if _CLEARED_FLAG.exists():
        _CLEARED_FLAG.unlink(missing_ok=True)
        return []
    sessions = _load_all_sessions()
    return sessions[-1]["messages"] if sessions else []


def _clear_session() -> tuple:
    """Mark cleared so next page-load starts fresh."""
    _CLEARED_FLAG.parent.mkdir(exist_ok=True)
    _CLEARED_FLAG.write_text("cleared", encoding="utf-8")
    return [], ""


def _history_markdown() -> str:
    sessions = _load_all_sessions()
    if not sessions:
        return "*暂无历史记录。开始对话后会自动保存。*"
    lines = []
    for s in reversed(sessions):
        msgs = s["messages"]
        lines.append(f"### 📅 {s['date']} &nbsp; *({len(msgs)//2} 轮对话)*")
        for m in msgs:
            icon = "👤" if m["role"] == "user" else "🤖"
            raw = m["content"]
            text = raw if isinstance(raw, str) else " ".join(str(c) for c in raw)
            preview = text[:160].replace("\n", " ")
            if len(text) > 160:
                preview += "…"
            lines.append(f"{icon} **{m['role']}**: {preview}")
        lines.append("")
    return "\n".join(lines)


def _openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(base_url=settings.ollama_base_url, api_key="ollama")


def _tool_specs() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.input_schema(),
            },
        }
        for t in _tools.values()
    ]


# ---------------------------------------------------------------------------
# Core chat logic (streaming)
# ---------------------------------------------------------------------------

async def _run_simple(messages: list[dict]) -> str:
    """Plain chat — no tools, streaming response."""
    client = _openai_client()
    result = ""
    stream = await client.chat.completions.create(
        model=settings.ollama_model,
        messages=messages,  # type: ignore[arg-type]
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            result += delta
    return result


async def _run_with_tools(messages: list[dict]) -> str:
    """Agentic loop: model may call tools repeatedly until it gives a final answer."""
    import json

    client = _openai_client()
    history = list(messages)

    for _ in range(10):  # max iterations
        response = await client.chat.completions.create(
            model=settings.ollama_model,
            messages=history,  # type: ignore[arg-type]
            tools=_tool_specs(),  # type: ignore[arg-type]
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content or ""

        # Append assistant message with tool calls
        history.append(msg)  # type: ignore[arg-type]

        # Execute each tool call
        for tc in msg.tool_calls:
            tool = _tools.get(tc.function.name)
            try:
                args = json.loads(tc.function.arguments or "{}")
                result = str(await tool.run(**args)) if tool else f"Unknown tool: {tc.function.name}"
            except Exception as exc:
                result = f"Error: {exc}"

            history.append(
                {"role": "tool", "tool_call_id": tc.id, "content": result}
            )

    return "[Agent] max iterations reached."


# ---------------------------------------------------------------------------
# Gradio event handler
# ---------------------------------------------------------------------------

def _history_to_messages(chat_history: list, system_prompt: str, user_message: str) -> list[dict]:
    """Convert Gradio messages history to OpenAI messages format."""
    messages: list[dict] = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})
    for turn in chat_history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})
    return messages


def _read_uploaded_file(file_obj: Any) -> tuple[str, str] | None:
    """Read an uploaded file and return (filename, content). Returns None if no file."""
    if file_obj is None:
        return None
    # Gradio 6 File component returns a dict with 'name' (temp path) and 'orig_name'
    if isinstance(file_obj, dict):
        path = file_obj.get("name") or file_obj.get("path", "")
        orig_name = file_obj.get("orig_name") or Path(path).name
    else:
        path = getattr(file_obj, "name", str(file_obj))
        orig_name = Path(path).name
    try:
        content = Path(path).read_text(encoding="utf-8", errors="replace")
        return orig_name, content
    except Exception as exc:
        return orig_name, f"[Error reading file: {exc}]"


async def respond(
    user_message: str,
    chat_history: list,
    use_tools: bool,
    system_prompt: str,
) -> tuple[str, list]:
    if not user_message.strip():
        return "", chat_history

    messages = _history_to_messages(chat_history, system_prompt, user_message)

    if use_tools:
        answer = await _run_with_tools(messages)
    else:
        answer = await _run_simple(messages)

    return "", chat_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": answer},
    ]


# ---------------------------------------------------------------------------
# Streaming variant (simple mode only)
# ---------------------------------------------------------------------------

def _read_uploaded_file(file_obj: Any) -> tuple[str, str] | None:
    """Read an uploaded file and return (filename, content). Returns None if no file."""
    if file_obj is None:
        return None
    if isinstance(file_obj, dict):
        path = file_obj.get("name") or file_obj.get("path", "")
        orig_name = file_obj.get("orig_name") or Path(path).name
    else:
        path = getattr(file_obj, "name", str(file_obj))
        orig_name = Path(path).name
    try:
        content = Path(path).read_text(encoding="utf-8", errors="replace")
        return orig_name, content
    except Exception as exc:
        return orig_name, f"[Error reading file: {exc}]"


async def respond_stream(
    user_message: str,
    chat_history: list,
    use_tools: bool,
    system_prompt: str,
    uploaded_file: Any = None,
):
    """Yields partial responses for streaming display in simple mode."""
    effective_message = user_message.strip()
    display_message = effective_message

    file_info = _read_uploaded_file(uploaded_file)
    if file_info:
        fname, fcontent = file_info
        file_block = f"<file: {fname}>\n\n{fcontent}"
        effective_message = (f"{effective_message}\n\n---\n{file_block}"
                             if effective_message else file_block)
        display_message = (f"📎 **{fname}**\n\n{user_message.strip()}"
                           if user_message.strip() else f"📎 **{fname}**")

    if not effective_message:
        yield "", chat_history
        return

    messages = _history_to_messages(chat_history, system_prompt, effective_message)
    user_turn = {"role": "user", "content": display_message}

    if use_tools:
        answer = await _run_with_tools(messages)
        final_history = chat_history + [user_turn, {"role": "assistant", "content": answer}]
        _save_session(final_history)
        yield "", final_history
    else:
        client = _openai_client()
        stream = await client.chat.completions.create(
            model=settings.ollama_model,
            messages=messages,  # type: ignore[arg-type]
            stream=True,
        )
        partial = ""
        cur_history = chat_history
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                partial += delta
                cur_history = chat_history + [user_turn, {"role": "assistant", "content": partial}]
                yield "", cur_history
        if not partial:
            cur_history = chat_history + [user_turn, {"role": "assistant", "content": "(no response)"}]
            yield "", cur_history
        _save_session(cur_history)


# ---------------------------------------------------------------------------
# Ollama status check
# ---------------------------------------------------------------------------

async def _check_ollama() -> str:
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            r = await c.get(settings.ollama_base_url.replace("/v1", "") + "/api/tags")
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                found = any(settings.ollama_model in m for m in models)
                badge = "🟢 已连接" if found else "🟡 已连接（模型未找到）"
                return f"{badge} &nbsp;·&nbsp; 已加载模型: `{', '.join(models) or '无'}`"
    except Exception:
        pass
    return "🔴 无法连接 Ollama — 请确认 `ollama serve` 已启动"


# ---------------------------------------------------------------------------
# Build UI
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
/* ── Global ─────────────────────────────────────────────── */
:root {
    --radius-lg: 14px;
    --radius-sm: 8px;
    --accent:    #7c6aff;
    --accent-2:  #a78bfa;
    --bg-card:   rgba(255,255,255,0.04);
    --border:    rgba(255,255,255,0.08);
}

/* Header gradient */
.header-banner {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
    border-radius: var(--radius-lg);
    padding: 20px 28px 16px;
    margin-bottom: 8px;
    border: 1px solid rgba(124,106,255,0.3);
}
.header-banner h1 { margin: 0 0 4px; font-size: 1.7rem; }
.header-banner p  { margin: 0; opacity: 0.75; font-size: 0.9rem; }

/* Status bar */
.status-bar {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 8px 14px;
    font-size: 0.85rem;
}

/* Tabs */
.tab-nav button {
    font-weight: 600;
    font-size: 0.9rem;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
}

/* Cards */
.settings-card, .tools-card, .tips-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 16px;
    margin-bottom: 10px;
}

/* Send button */
#send-btn {
    background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
    border: none !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px;
    min-height: 46px !important;
}
#send-btn:hover { opacity: 0.9; transform: translateY(-1px); }

/* Input box */
#msg-input textarea {
    border-radius: var(--radius-sm) !important;
    font-size: 0.95rem !important;
    padding: 10px 14px !important;
    min-height: 80px !important;
    resize: vertical !important;
    line-height: 1.5 !important;
}

/* ── Action column (right side of input row) ──────── */
#action-col {
    display: flex !important;
    flex-direction: column !important;
    gap: 6px !important;
    align-self: stretch !important;
    justify-content: flex-end !important;
    min-width: 120px !important;
    max-width: 120px !important;
    flex-shrink: 0 !important;
}
#icon-row {
    display: flex !important;
    gap: 6px !important;
}

/* Shared icon button base */
.icon-action-btn button, .icon-action-btn {
    height: 40px !important;
    min-height: 40px !important;
    width: 100% !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
    background: rgba(255,255,255,0.06) !important;
    color: rgba(255,255,255,0.65) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.2px !important;
    cursor: pointer !important;
    transition: border-color .15s, background .15s, color .15s, box-shadow .15s !important;
    padding: 0 10px !important;
}
.icon-action-btn button:hover, .icon-action-btn:hover {
    border-color: var(--accent) !important;
    background: rgba(124,106,255,0.18) !important;
    color: rgba(255,255,255,0.95) !important;
    box-shadow: 0 0 0 2px rgba(124,106,255,0.15) !important;
}

/* Example chips */
.example-chip { cursor: pointer; }

/* Chatbot bubbles */
.message-bubble-border { border-radius: var(--radius-lg) !important; }

/* upload UploadButton — inherits .icon-action-btn base */
#upload-btn { flex: 1 !important; }
#upload-btn button { width: 100% !important; }

/* Drag-over highlight on the whole input row */
#msg-input.drag-active textarea {
    border-color: var(--c-accent) !important;
    box-shadow: 0 0 0 3px var(--c-accent-glow) !important;
}

/* Hide footer */
footer { display: none !important; }
"""

EXAMPLE_PROMPTS = [
    "用 Python 写一个冒泡排序，并解释每个步骤",
    "async/await 和 threading 有什么区别？",
    "解释 Transformer 架构的核心原理",
    "用 3 句话总结量子计算是什么",
]


def build_app() -> gr.Blocks:
    with gr.Blocks(title="AI Agent · Local LLM") as demo:

        # ── Header ──────────────────────────────────────────────────────────
        gr.HTML(f"""
        <div class="header-banner">
            <h1>&#129302; AI Agent Chat</h1>
            <p>本地大模型推理 &nbsp;·&nbsp; 模型: <code>{settings.ollama_model}</code>
               &nbsp;·&nbsp; 端点: <code>{settings.ollama_base_url}</code></p>
        </div>
        """)

        status_md = gr.Markdown("⏳ 正在检测 Ollama 连接…", elem_classes=["status-bar"])

        # ── Tabs ─────────────────────────────────────────────────────────────
        with gr.Tabs(elem_classes=["tab-nav"]):

            # ── Tab 1: Chat ───────────────────────────────────────────────
            with gr.TabItem("💬  对话"):
                with gr.Row(equal_height=False):

                    # Left panel
                    with gr.Column(scale=1, min_width=260):
                        with gr.Group(elem_classes=["settings-card"]):
                            gr.Markdown("#### ⚙️ 运行设置")
                            use_tools = gr.Checkbox(
                                label="启用工具调用 (Agent 模式)",
                                value=False,
                                info="开启后可自动调用 fetch_url / read_file",
                            )
                            system_prompt = gr.Textbox(
                                label="System Prompt",
                                value="You are a helpful AI assistant. Respond in the same language as the user.",
                                lines=5,
                                placeholder="自定义系统提示词…",
                            )

                        with gr.Group(elem_classes=["tips-card"]):
                            gr.Markdown(
                                "#### 💡 快速示例\n"
                                "点击下方示例或直接输入："
                            )
                            for ex in EXAMPLE_PROMPTS:
                                gr.Button(ex, size="sm", elem_classes=["example-chip"])

                    # Right panel — chat
                    with gr.Column(scale=3):
                        chatbot = gr.Chatbot(
                            label="",
                            height=720,
                            resizable=True,
                            buttons=["copy_all"],
                            placeholder=(
                                "<div style='text-align:center;opacity:.45;padding:60px 0'>"
                                "<div style='font-size:2.5rem'>🤖</div>"
                                "<div style='margin-top:8px;font-size:1rem'>发送消息开始对话</div>"
                                "</div>"
                            ),
                            layout="bubble",
                            show_label=False,
                        )

                        with gr.Row(equal_height=False):
                            msg_box = gr.Textbox(
                                placeholder="输入消息，按 Enter 发送，Shift+Enter 换行…",
                                label="",
                                lines=3,
                                max_lines=10,
                                scale=5,
                                container=False,
                                elem_id="msg-input",
                                autofocus=True,
                            )
                            with gr.Column(
                                scale=0,
                                min_width=120,
                                elem_id="action-col",
                            ):
                                with gr.Row(elem_id="icon-row"):
                                    upload_file = gr.UploadButton(
                                        "📎 附件",
                                        file_types=[".txt", ".py", ".md", ".json",
                                                    ".csv", ".yaml", ".yml", ".toml",
                                                    ".log", ".xml", ".html", ".js",
                                                    ".ts", ".css", ".sh", ".bat"],
                                        file_count="single",
                                        elem_id="upload-btn",
                                        elem_classes=["icon-action-btn"],
                                        scale=1,
                                        min_width=0,
                                    )
                                    clear_btn = gr.Button(
                                        "🗑️ 清空",
                                        elem_id="clear-btn",
                                        elem_classes=["icon-action-btn"],
                                        scale=1,
                                        min_width=0,
                                    )
                                send_btn = gr.Button(
                                    "发送 ↑",
                                    variant="primary",
                                    elem_id="send-btn",
                                )

                # Wire example buttons
                for i, btn in enumerate(
                    [c for c in demo.children  # type: ignore[attr-defined]
                     if False]  # placeholder — wired below via iteration
                ):
                    pass

            # ── Tab 2: History ───────────────────────────────────────────
            with gr.TabItem("📜  历史记录"):
                gr.Markdown(
                    "对话内容按日期自动保存到 `data/chat_history.json`。"
                    "刷新页面可恢复上次会话。"
                )
                history_md = gr.Markdown(_history_markdown())
                with gr.Row():
                    refresh_btn = gr.Button("🔄 刷新", size="sm")

            # ── Tab 3: Tools ──────────────────────────────────────────────
            with gr.TabItem("🛠️  工具"):
                gr.Markdown("### 已注册工具")
                rows = []
                for t in _tools.values():
                    schema_str = json.dumps(t.input_schema().get("properties", {}), ensure_ascii=False, indent=2)
                    rows.append([t.name, t.description, schema_str])
                gr.Dataframe(
                    value=rows,
                    headers=["工具名", "说明", "参数 (JSON Schema)"],
                    column_count=(3, "fixed"),
                    wrap=True,
                    row_count=(len(rows), "fixed"),
                )
                gr.Markdown(
                    "> **提示**：在 `ai_agent/tools/` 中新建文件并继承 `BaseTool`，"
                    "无需修改其他代码即可自动注册。"
                )

            # ── Tab 3: About ──────────────────────────────────────────────
            with gr.TabItem("ℹ️  关于"):
                gr.Markdown(f"""
### 项目架构

```
ai_agent/
├── agents/       OllamaAgent · OllamaToolAgent · AssistantAgent · ToolUsingAgent
├── tools/        EchoTool · FetchUrlTool · ReadFileTool  (自动发现)
├── skills/       SummarizeSkill
├── mcp/          MCP Server (暴露工具给 VS Code / Claude Desktop)
├── config.py     .env → Pydantic Settings
└── registry.py   自动发现 BaseTool/BaseSkill 子类
```

### 当前配置

| 键 | 值 |
|---|---|
| 模型 | `{settings.ollama_model}` |
| Ollama 端点 | `{settings.ollama_base_url}` |
| 日志级别 | `{settings.log_level}` |
| MCP 端口 | `{settings.mcp_server_port}` |

### 添加新工具

```python
# ai_agent/tools/my_tool.py
from ai_agent.tools.base_tool import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "做某件事"

    async def run(self, param: str) -> str:
        return f"结果: {{param}}"

    def input_schema(self):
        return {{"type": "object", "properties": {{"param": {{"type": "string"}}}}, "required": ["param"]}}
```
                """)

        # ── Events ───────────────────────────────────────────────────────────
        submit_inputs = [msg_box, chatbot, use_tools, system_prompt, upload_file]
        submit_outputs = [msg_box, chatbot]

        msg_box.submit(respond_stream, submit_inputs, submit_outputs)
        send_btn.click(respond_stream, submit_inputs, submit_outputs)
        clear_btn.click(_clear_session, outputs=[chatbot, msg_box])  # type: ignore[return-value]
        refresh_btn.click(_history_markdown, outputs=history_md)

        # ── On load: check Ollama + restore last session ─────────────────
        demo.load(_check_ollama, outputs=status_md)
        demo.load(_restore_last_session, outputs=chatbot)

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True,
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.violet,
            secondary_hue=gr.themes.colors.indigo,
            neutral_hue=gr.themes.colors.slate,
            font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
            font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
        ),
        css=CUSTOM_CSS,
    )
