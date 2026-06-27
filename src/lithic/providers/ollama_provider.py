"""Ollama provider."""

from __future__ import annotations

from typing import Any

from lithic.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    """Minimal Ollama chat provider."""

    def __init__(self, model: str | None = None, base_url: str = "http://127.0.0.1:11434"):
        self.model = model or "llama3.1"
        self.base_url = base_url.rstrip("/")

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        import httpx

        payload = {"model": self.model, "messages": messages, "stream": False}
        payload.update(kwargs)
        response = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=60.0)
        response.raise_for_status()
        body = response.json()
        message = body.get("message", {})
        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("Ollama returned no message content")
        return content
