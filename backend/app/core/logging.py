"""
Structured, PII-safe logging configuration.

RULE: Never log resume content, candidate names, emails, or any PII.
      Log IDs and status codes only.
"""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger for structured output to stdout."""
    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Use module __name__ as the name."""
    return logging.getLogger(name)
