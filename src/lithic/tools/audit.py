"""Audit logging for security-relevant events."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_LOG = logging.getLogger("lithic.audit")
_LOG_HANDLER: logging.Handler | None = None

_SECRET_KEY_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|bearer|auth[_-]?token)"
)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password|auth[_-]?token)\b"
    r"(\s*[:=]\s*['\"]?)([^\s'\",}]+)"
)
_AUTH_HEADER_RE = re.compile(
    r"(?i)\bauthorization(\s*[:=]\s*)(?:bearer\s+)?[^\s'\",}]+"
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+\-/]+=*")
_URL_CREDENTIALS_RE = re.compile(r"(://)([^:]+):([^@]+)@")


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


def _redact(value: str) -> str:
    redacted = _AUTH_HEADER_RE.sub(lambda m: f"Authorization{m.group(1)}***", value)
    redacted = _SECRET_ASSIGNMENT_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}***", redacted)
    redacted = _BEARER_RE.sub("Bearer ***", redacted)
    return _URL_CREDENTIALS_RE.sub(r"\1***:***@", redacted)


def _redact_obj(obj: object) -> object:
    if isinstance(obj, str):
        return _redact(obj)
    if isinstance(obj, list):
        return [_redact_obj(i) for i in obj]
    if isinstance(obj, dict):
        return {
            k: "***" if _SECRET_KEY_RE.search(str(k)) else _redact_obj(v)
            for k, v in obj.items()
        }
    return obj


def _event(event: str, **fields: object) -> None:
    _setup()
    record = {"event": event, "ts": time.time(), **fields}
    _LOG.info(json.dumps(_redact_obj(record), default=str))


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
