# GitHub Copilot Instructions

See [claude.md](../claude.md) for full project conventions and architecture.

## Quick Reference

- All tools inherit `BaseTool` from `ai_agent/tools/base_tool.py`
- All skills inherit `BaseSkill` from `ai_agent/skills/base_skill.py`
- All agents inherit `BaseAgent` from `ai_agent/agents/base_agent.py`
- Use `async/await` throughout; no blocking I/O in async contexts
- Pydantic v2 models for all structured data
- Prefer `loguru` logger over `print` or stdlib `logging`
