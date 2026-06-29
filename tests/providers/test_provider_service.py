from pathlib import Path

import pytest

from lithic_cli.config import AgentConfig
from lithic_cli.providers.service import LLMService


def _cfg(tmp_path: Path, **kwargs) -> AgentConfig:
    overrides = dict(project_root=tmp_path, graph_output_dir=tmp_path / "graph")
    overrides.update(kwargs)
    return AgentConfig(**overrides)


def test_get_provider_returns_none_for_unknown(tmp_path: Path) -> None:
    svc = LLMService(_cfg(tmp_path, provider="nonexistent"))
    assert svc.get_provider() is None


def test_available_empty_when_no_extras(tmp_path: Path) -> None:
    svc = LLMService(_cfg(tmp_path))
    available = svc.available()
    assert isinstance(available, list)


def test_complete_raises_for_unknown_provider(tmp_path: Path) -> None:
    svc = LLMService(_cfg(tmp_path, provider="nonexistent"))
    with pytest.raises(RuntimeError, match="no provider"):
        svc.complete([{"role": "user", "content": "hi"}])


def test_available_includes_ollama() -> None:
    available = LLMService.available()
    assert "ollama" in available


def test_get_provider_ollama(tmp_path: Path) -> None:
    svc = LLMService(_cfg(tmp_path, provider="ollama"))
    p = svc.get_provider()
    assert p is not None
    assert p.model == "llama3.1"
