"""
Centralized loguru configuration.

Import once at application startup:
    from ai_agent.logging_config import setup_logging
    setup_logging()
"""

from __future__ import annotations

import sys

from loguru import logger

from ai_agent.config import settings

_CONFIGURED = False


def setup_logging() -> None:
    """Configure loguru sinks. Safe to call multiple times."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )
    _CONFIGURED = True
