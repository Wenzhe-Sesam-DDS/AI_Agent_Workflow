"""
Centralized settings — loaded once from environment / .env file.

Usage:
    from ai_agent.config import settings
    print(settings.anthropic_api_key)
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Claude / Anthropic ----
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    anthropic_model: str = Field(
        default="claude-opus-4-5", description="Default Claude model"
    )

    # ---- MCP server ----
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8080

    # ---- Logging ----
    log_level: str = "INFO"


settings = Settings()
