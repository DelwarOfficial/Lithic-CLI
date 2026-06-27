"""OpenAI provider."""

from __future__ import annotations

import os
from typing import Any, cast

from lithic.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI chat-completions provider."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("LITHIC_MODEL") or os.getenv("UDA_MODEL") or "gpt-4.1-mini"

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=cast(Any, messages),
            **kwargs,
        )
        if not response.choices:
            raise RuntimeError("OpenAI returned no completions")
        return response.choices[0].message.content or ""
