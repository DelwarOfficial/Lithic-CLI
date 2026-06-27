"""MCP server for Lithic."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
from typing import Any

from lithic.compression.headroom_adapter import HeadroomAdapter
from lithic.orchestrator import Orchestrator
from lithic.tools.audit import input_rejected, tool_call

_log = logging.getLogger("lithic.mcp")

def _env_int(key: str, default: int) -> int:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        _log.warning("invalid %s=%r, using default %d", key, val, default)
        return default


def _env_float(key: str, default: float) -> float:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        _log.warning("invalid %s=%r, using default %g", key, val, default)
        return default


_MAX_INPUT_CHARS = _env_int("LITHIC_MCP_MAX_INPUT_CHARS", 100_000)
_MAX_CALLS_PER_WINDOW = _env_int("LITHIC_MCP_MAX_CALLS", 60)
_WINDOW_SEC = _env_float("LITHIC_MCP_WINDOW_SEC", 60.0)

_QUERY_SIZE_LIMIT = _env_int("LITHIC_MCP_QUERY_SIZE_LIMIT", 2000)
_COMPRESS_SIZE_LIMIT = _env_int("LITHIC_MCP_COMPRESS_SIZE_LIMIT", 500_000)


class _RateLimiter:
    """Sliding-window rate limiter per-process — adequate for stdio only."""

    def __init__(self, max_calls: int = _MAX_CALLS_PER_WINDOW, window: float = _WINDOW_SEC):
        self.max_calls = max_calls
        self.window = window
        self._calls: list[float] = []
        self._lock = threading.Lock()

    def check(self) -> None:
        now = time.monotonic()
        cutoff = now - self.window
        with self._lock:
            self._calls = [t for t in self._calls if t > cutoff]
            if len(self._calls) >= self.max_calls:
                raise RuntimeError(
                    f"rate limit exceeded ({self.max_calls} calls per {self.window:.0f}s)"
                )
            self._calls.append(now)


def _tool_result(text: str) -> list[Any]:
    from mcp.types import TextContent

    return [TextContent(type="text", text=text)]


def _check_input_size(value: str, max_chars: int, label: str) -> str:
    if len(value) > max_chars:
        raise ValueError(f"{label} exceeds {max_chars} character limit")
    return value


def build_server() -> Any:
    """Build an MCP stdio server for Lithic tools."""
    try:
        from mcp.server import Server
        from mcp.types import Tool
    except ImportError as exc:
        raise RuntimeError("mcp package is not installed. Install with `uv add mcp`.") from exc

    from pydantic import BaseModel

    class QueryInput(BaseModel):
        question: str

    class ExplainInput(BaseModel):
        concept: str

    class PathInput(BaseModel):
        source: str
        target: str

    class CompressInput(BaseModel):
        text: str

    server = Server("lithic")
    orch = Orchestrator()
    compressor = HeadroomAdapter()
    limiter = _RateLimiter()

    @server.list_tools()
    async def list_tools() -> list[Any]:
        return [
            Tool(
                name="lithic_graph_query",
                description="Query the project graph",
                inputSchema=QueryInput.model_json_schema(),
            ),
            Tool(
                name="lithic_graph_explain",
                description="Explain a graph concept",
                inputSchema=ExplainInput.model_json_schema(),
            ),
            Tool(
                name="lithic_graph_path",
                description="Find a path between graph concepts",
                inputSchema=PathInput.model_json_schema(),
            ),
            Tool(
                name="lithic_compress",
                description="Compress text safely",
                inputSchema=CompressInput.model_json_schema(),
            ),
            Tool(name="lithic_review", description="Review current diff", inputSchema={}),
            Tool(name="lithic_commit", description="Write commit message", inputSchema={}),
            Tool(name="lithic_stats", description="Return stats", inputSchema={}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None = None) -> list[Any]:
        args = arguments or {}
        start = time.monotonic()
        for v in args.values():
            if isinstance(v, str) and len(v) > _MAX_INPUT_CHARS:
                input_rejected(name, f"input exceeds {_MAX_INPUT_CHARS} chars")
                tool_call(name, args, False, time.monotonic() - start, "input too large")
                return _tool_result(f"error: input exceeds {_MAX_INPUT_CHARS} chars")
        try:
            limiter.check()
            if name == "lithic_graph_query":
                q = _check_input_size(QueryInput(**args).question, _QUERY_SIZE_LIMIT, "question")
                result = orch.ask(q)
                tool_call(name, args, True, time.monotonic() - start)
                return _tool_result(result)
            if name == "lithic_graph_explain":
                c = _check_input_size(ExplainInput(**args).concept, _QUERY_SIZE_LIMIT, "concept")
                result = orch.explain(c)
                tool_call(name, args, True, time.monotonic() - start)
                return _tool_result(result)
            if name == "lithic_graph_path":
                data = PathInput(**args)
                _check_input_size(data.source, _QUERY_SIZE_LIMIT, "source")
                _check_input_size(data.target, _QUERY_SIZE_LIMIT, "target")
                result = orch.path_between(data.source, data.target)
                tool_call(name, args, True, time.monotonic() - start)
                return _tool_result(result)
            if name == "lithic_compress":
                t = _check_input_size(CompressInput(**args).text, _COMPRESS_SIZE_LIMIT, "text")
                result = compressor.compress_text(t)
                tool_call(name, args, True, time.monotonic() - start)
                return _tool_result(result)
            if name == "lithic_review":
                result = orch.review()
                tool_call(name, args, True, time.monotonic() - start)
                return _tool_result(result)
            if name == "lithic_commit":
                result = orch.commit()
                tool_call(name, args, True, time.monotonic() - start)
                return _tool_result(result)
            if name == "lithic_stats":
                result = json.dumps(orch.stats(), indent=2)
                tool_call(name, args, True, time.monotonic() - start)
                return _tool_result(result)
            tool_call(name, args, False, time.monotonic() - start, "unknown tool")
            return _tool_result(f"unknown tool: {name}")
        except Exception as exc:
            _log.warning("tool call failed: %s", exc)
            tool_call(name, args, False, time.monotonic() - start, str(exc))
            return _tool_result("error: internal error")

    return server


async def _serve_async() -> None:
    from mcp.server.stdio import stdio_server

    server = build_server()
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())


def serve() -> None:
    """Serve Lithic MCP tools over stdio."""
    asyncio.run(_serve_async())
