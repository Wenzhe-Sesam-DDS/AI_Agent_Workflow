"""Tests for centralized settings."""

from ai_agent.config import Settings


def test_settings_defaults() -> None:
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.mcp_server_host == "0.0.0.0"
    assert s.mcp_server_port == 8080
    assert s.log_level == "INFO"
    assert s.anthropic_model.startswith("claude")
