"""Anthropic provider."""

from __future__ import annotations

import os
from typing import Any, cast

from lithic_cli.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    """Anthropic messages API provider."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("LITHIC_MODEL") or os.getenv("UDA_MODEL") or "gpt-4.1-mini"

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key, timeout=30.0)
        response = client.messages.create(
            model=self.model,
            max_tokens=kwargs.pop("max_tokens", 1024),
            messages=cast(Any, messages),
            **kwargs,
        )
        return "".join(getattr(block, "text", "") for block in response.content)
