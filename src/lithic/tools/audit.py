"""Audit logging for security-relevant events."""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_LOG = logging.getLogger("lithic.audit")
_LOG_HANDLER: logging.Handler | None = None


def _setup() -> None:
    global _LOG_HANDLER
    if _LOG_HANDLER is not None:
        return
    _LOG.setLevel(logging.INFO)
    target = os.getenv("LITHIC_AUDIT_LOG", "")
    if target:
        handler: logging.Handler = logging.FileHandler(target, encoding="utf-8")
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    _LOG.addHandler(handler)
    _LOG.propagate = False
    _LOG_HANDLER = handler


def _event(event: str, **fields: object) -> None:
    _setup()
    record = {"event": event, "ts": time.time(), **fields}
    _LOG.info(json.dumps(record, default=str))


def tool_call(
    tool: str, args: dict[str, Any] | None, ok: bool, duration: float, error: str = ""
) -> None:
    _event(
        "mcp.tool_call",
        tool=tool,
        args=_summarize(args),
        ok=ok,
        duration_ms=round(duration * 1000),
        error=error,
    )


def subprocess(command: list[str], returncode: int, duration: float, error: str = "") -> None:
    _event(
        "subprocess.run",
        command=command,
        returncode=returncode,
        duration_ms=round(duration * 1000),
        error=error,
    )


def auth_failure(reason: str, peer: str = "") -> None:
    _event("auth.failure", reason=reason, peer=peer)


def rate_limit(tool: str) -> None:
    _event("rate_limit.hit", tool=tool)


def input_rejected(tool: str, reason: str) -> None:
    _event("input.rejected", tool=tool, reason=reason)


def _summarize(args: dict[str, Any] | None) -> dict[str, Any]:
    if not args:
        return {}
    out: dict[str, Any] = {}
    for k, v in args.items():
        if isinstance(v, str) and len(v) > 200:
            out[k] = v[:200] + "..."
        else:
            out[k] = v
    return out
