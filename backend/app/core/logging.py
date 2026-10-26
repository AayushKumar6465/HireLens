"""
Structured, PII-safe logging configuration.

RULES:
- Never log resume contents, candidate names, emails, IP addresses, tokens, headers, or request bodies.
- Log event names and internal entity IDs only (e.g. user_id, job_id, status_code).
- Standardized event structure: event=<event_name> [entity_id=<id>] status=<status>
"""

from __future__ import annotations

import logging
import sys
from typing import Any

# Disallowed field names to prevent accidental PII logging
_FORBIDDEN_FIELDS = {
    "email",
    "password",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "secret",
    "ip",
    "client_ip",
    "remote_addr",
    "body",
    "headers",
    "name",
    "full_name",
    "raw_text",
    "text",
}


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


def log_event(
    logger: logging.Logger, event: str, level: int = logging.INFO, **fields: Any
) -> None:
    """
    Log an event name and sanitized internal identifiers only.

    Silently strips any PII or sensitive keys (email, token, IP, body, etc.).
    """
    safe_parts = [f"event={event}"]
    for k, v in fields.items():
        if (
            k.lower() in _FORBIDDEN_FIELDS
            or "token" in k.lower()
            or "secret" in k.lower()
            or "password" in k.lower()
        ):
            continue
        safe_parts.append(f"{k}={v}")

    logger.log(level, " ".join(safe_parts))
