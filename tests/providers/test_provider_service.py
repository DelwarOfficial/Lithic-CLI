from pathlib import Path

import pytest

from lithic.config import AgentConfig
from lithic.providers.service import LLMService


def _cfg(**kwargs) -> AgentConfig:
    overrides = dict(project_root=Path.cwd(), graph_output_dir=Path.cwd())
    overrides.update(kwargs)
    return AgentConfig(**overrides)


def test_get_provider_returns_none_for_unknown() -> None:
    svc = LLMService(_cfg(provider="nonexistent"))
    assert svc.get_provider() is None


def test_available_empty_when_no_extras() -> None:
    svc = LLMService(_cfg())
    available = svc.available()
    assert isinstance(available, list)


def test_complete_raises_for_unknown_provider() -> None:
    svc = LLMService(_cfg(provider="nonexistent"))
    with pytest.raises(RuntimeError, match="no provider"):
        svc.complete([{"role": "user", "content": "hi"}])


def test_available_includes_ollama() -> None:
    available = LLMService.available()
    assert "ollama" in available


def test_get_provider_ollama() -> None:
    svc = LLMService(_cfg(provider="ollama"))
    p = svc.get_provider()
    assert p is not None
    assert p.model == "llama3.1"
