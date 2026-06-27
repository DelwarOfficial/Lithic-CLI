"""Headroom adapter with deterministic fallback compression."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

_LOG = logging.getLogger(__name__)

CODE_BLOCK_RE = re.compile(r"(```.*?```)", re.DOTALL)
ERROR_RE = re.compile(r"(?i)(error|exception|traceback|failed|fatal|warning)")
PATH_RE = re.compile(r"([A-Za-z]:\\[^\s:]+|(?:\.{1,2}/|/)?[\w.-]+(?:/[\w.-]+)+)")


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
    def __init__(self) -> None:
        self._stats = CompressionStats()
        try:
            from headroom import compress as headroom_compress

            self._headroom_compress = headroom_compress
            self._stats.headroom_available = True
        except ImportError:
            self._headroom_compress = None
        except Exception as exc:
            _LOG.warning("headroom import failed: %s", exc)
            self._headroom_compress = None

    def compress_text(self, text: str, label: str | None = None) -> str:
        compressed = self._compress_with_headroom(text, label) or self._fallback_compress(text)
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
        compressed = self._fallback_compress(output, max_chars=max_chars)
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
        if protected:
            body += "\n\n[preserved code blocks]\n" + "\n".join(protected)
        if len(body) > max_chars:
            body = body[: max_chars // 2] + "\n... [compressed] ...\n" + body[-max_chars // 2 :]
        return body

    def _record(self, original: str, compressed: str) -> str:
        self._stats.calls += 1
        self._stats.original_chars += len(original)
        self._stats.compressed_chars += len(compressed)
        return compressed
