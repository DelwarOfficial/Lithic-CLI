"""LLM service — provider map, factory, completion."""

from __future__ import annotations

from typing import Any, cast

from lithic.config import AgentConfig

_PROVIDER_MAP: dict[str, type[Any]] = {}
_DEFAULT_MODEL = "gpt-4.1-mini"
_PROVIDER_DEFAULT_MODELS = {
    "anthropic": "claude-3-5-sonnet-latest",
    "ollama": "llama3.1",
    "openai": _DEFAULT_MODEL,
    "openrouter": "openai/gpt-4.1-mini",
}


def _init_provider_map() -> None:
    if _PROVIDER_MAP:
        return
    try:
        from lithic.providers.anthropic_provider import AnthropicProvider
        _PROVIDER_MAP["anthropic"] = AnthropicProvider
    except ImportError:
        pass
    try:
        from lithic.providers.openai_provider import OpenAIProvider
        _PROVIDER_MAP["openai"] = OpenAIProvider
    except ImportError:
        pass
    try:
        from lithic.providers.ollama_provider import OllamaProvider
        _PROVIDER_MAP["ollama"] = OllamaProvider
    except ImportError:
        pass
    try:
        from lithic.providers.openrouter_provider import OpenRouterProvider
        _PROVIDER_MAP["openrouter"] = OpenRouterProvider
    except ImportError:
        pass


class LLMService:
    """Lazy provider resolution and completion."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self._provider: Any = None

    def get_provider(self) -> Any:
        if self._provider is not None:
            return self._provider
        _init_provider_map()
        ptype = _PROVIDER_MAP.get(self.config.provider)
        if ptype is None:
            return None
        model = self.config.model
        if model == _DEFAULT_MODEL:
            model = _PROVIDER_DEFAULT_MODELS.get(self.config.provider, model)
        self._provider = ptype(model=model)
        return self._provider

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        p = self.get_provider()
        if p is None:
            raise RuntimeError(
                f"no provider for '{self.config.provider}' "
                f"(valid: {list(_PROVIDER_MAP) or 'none'})"
            )
        return cast(str, p.complete(messages, **kwargs))

    @staticmethod
    def available() -> list[str]:
        _init_provider_map()
        return list(_PROVIDER_MAP)
