"""Provider layer exports.

Always-available exports:
  BaseProvider  — ABC for provider implementations
  LLMService    — provider registry and factory

Provider implementations (require optional extras):
  AnthropicProvider  — needs ``uv sync --extra llm``
  OpenAIProvider     — needs ``uv sync --extra llm``
  OllamaProvider     — always available (uses httpx)
  OpenRouterProvider — always available (uses httpx)
"""

from lithic.providers.base import BaseProvider
from lithic.providers.service import LLMService

__all__ = [
    "BaseProvider",
    "LLMService",
]
