"""Shared Loguru logging configuration for repository scripts."""

from __future__ import annotations

import sys
from typing import TextIO

from loguru import logger

LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}"


def configure_logging(level: str = "INFO", sink: TextIO = sys.stderr) -> None:
    """Install a consistent Loguru sink for command-line scripts."""
    logger.remove()
    logger.add(
        sink,
        level=level,
        format=LOG_FORMAT,
        colorize=False,
        backtrace=False,
        diagnose=False,
    )
