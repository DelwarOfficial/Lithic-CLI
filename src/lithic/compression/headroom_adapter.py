"""Headroom adapter with deterministic fallback compression."""

from __future__ import annotations

import logging
import re
import threading
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

_LOG = logging.getLogger(__name__)

CODE_BLOCK_RE = re.compile(r"(```.*?```)", re.DOTALL)
ERROR_RE = re.compile(r"(?i)(error|exception|traceback|failed|fatal|warning)")
PATH_RE = re.compile(r"([A-Za-z]:[\\/][^\s:]+|(?:\.{1,2}/|/)?[\w.-]+(?:/[\w.-]+)+)")


@dataclass
class CompressionStats:
    calls: int = 0
    original_chars: int = 0
    compressed_chars: int = 0
    headroom_available: bool = False

    def as_dict(self) -> dict[str, int | float | bool]:
        saved = max(0, self.original_chars - self.compressed_chars)
        ratio = 0.0 if self.original_chars == 0 else saved / self.original_chars
        return {
            "calls": self.calls,
            "original_chars": self.original_chars,
            "compressed_chars": self.compressed_chars,
            "saved_chars": saved,
            "savings_ratio": round(ratio, 4),
            "headroom_available": self.headroom_available,
        }


class HeadroomAdapter:
    def __init__(self, cache_size: int = 64) -> None:
        self._stats = CompressionStats()
        self._cache: OrderedDict[int, str] = OrderedDict()
        self._cache_size = cache_size
        self._lock = threading.Lock()
        try:
            from headroom import compress as headroom_compress

            self._headroom_compress = headroom_compress
            self._stats.headroom_available = True
        except ImportError:
            self._headroom_compress = None
        except Exception as exc:
            _LOG.warning("headroom import failed: %s", exc)
            self._headroom_compress = None

    def _cache_key(self, text: str, max_chars: int = 8000) -> int:
        return hash((text, max_chars))

    def _cache_get(self, key: int) -> str | None:
        with self._lock:
            value = self._cache.get(key)
            if value is not None:
                self._cache.move_to_end(key)
            return value

    def _cache_put(self, key: int, value: str) -> None:
        with self._lock:
            self._cache[key] = value
            self._cache.move_to_end(key)
            while len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)

    def compress_text(self, text: str, label: str | None = None) -> str:
        key = self._cache_key(text)
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        compressed = self._compress_with_headroom(text, label) or self._fallback_compress(text)
        self._cache_put(key, compressed)
        return self._record(text, compressed)

    def compress_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if self._headroom_compress is not None:
            try:
                result = self._headroom_compress(
                    messages,
                    compress_user_messages=True,
                    protect_recent=1,
                    kompress_model="disabled",
                )
                compressed = list(result.messages)
                self._record(str(messages), str(compressed))
                return compressed
            except Exception as exc:
                _LOG.warning("headroom compress_messages failed, using fallback: %s", exc)
        out: list[dict[str, Any]] = []
        for message in messages:
            copy = dict(message)
            content = copy.get("content")
            if isinstance(content, str):
                copy["content"] = self.compress_text(content, str(copy.get("role", "message")))
            out.append(copy)
        return out

    def compress_tool_output(self, output: str, max_chars: int = 8000) -> str:
        if len(output) <= max_chars:
            return self._record(output, output)
        key = self._cache_key(output, max_chars)
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        headroom_result = self._compress_with_headroom(output, "tool_output")
        if headroom_result is not None and len(headroom_result) <= max_chars:
            self._cache_put(key, headroom_result)
            return self._record(output, headroom_result)
        compressed = self._fallback_compress(output, max_chars=max_chars)
        self._cache_put(key, compressed)
        return self._record(output, compressed)

    def retrieve(self, ref: str) -> str:
        """Retrieve previously compressed text by reference.
        The fallback adapter does not cache, so this returns a stub.
        """
        return f"[retrieve('{ref}') not available in fallback mode]"

    def stats(self) -> dict[str, int | float | bool]:
        return self._stats.as_dict()

    def _compress_with_headroom(self, text: str, label: str | None) -> str | None:
        if self._headroom_compress is None or len(text) < 4000:
            return None
        try:
            result = self._headroom_compress(
                [{"role": "user", "content": text}],
                compress_user_messages=True,
                protect_recent=0,
                kompress_model="disabled",
            )
            content = result.messages[0].get("content")
            if isinstance(content, str) and content:
                prefix = f"[compressed:{label}]\n" if label else ""
                return prefix + content
        except Exception as exc:
            _LOG.warning("headroom compression failed, using fallback: %s", exc)
            return None
        return None

    def _fallback_compress(self, text: str, max_chars: int = 8000) -> str:
        if len(text) <= max_chars:
            return text
        blocks = CODE_BLOCK_RE.split(text)
        protected: list[str] = []
        compressible: list[str] = []
        for block in blocks:
            if block.startswith("```"):
                protected.append(block)
            else:
                compressible.append(block)
        lines = "\n".join(compressible).splitlines()
        important = [line for line in lines if ERROR_RE.search(line) or PATH_RE.search(line)]
        deduped: list[str] = []
        seen: set[str] = set()
        for line in important:
            key = line.strip()
            if key and key not in seen:
                seen.add(key)
                deduped.append(line)
        head = lines[:80]
        has_middle = len(lines) > 160
        tail = lines[-80:] if has_middle else []
        middle: list[str] = []
        if has_middle:
            middle = [*deduped[:120], "... [compressed middle] ..."]
        elif deduped:
            middle = deduped[:120]
        body = "\n".join([*head, *middle, *tail])
        block_text = "\n\n[preserved code blocks]\n" + "\n".join(protected) if protected else ""
        budget = max_chars - len(block_text)
        if budget < 1:
            block_text = block_text[: max_chars - 100] + "\n... [code blocks truncated]"
            budget = max_chars - len(block_text)
        if len(body) > budget:
            body = body[: max(1, budget)]
        return body + block_text

    def _record(self, original: str, compressed: str) -> str:
        with self._lock:
            self._stats.calls += 1
            self._stats.original_chars += len(original)
            self._stats.compressed_chars += len(compressed)
        return compressed
