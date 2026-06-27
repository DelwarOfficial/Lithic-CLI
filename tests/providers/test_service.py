from pathlib import Path

import lithic.providers.service as provider_service
from lithic.config import AgentConfig
from lithic.providers.service import LLMService


def test_anthropic_uses_provider_default_when_model_not_overridden(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured = {}

    class FakeProvider:
        def __init__(self, model: str):
            captured["model"] = model

    monkeypatch.setattr(provider_service, "_PROVIDER_MAP", {"anthropic": FakeProvider})
    service = LLMService(
        AgentConfig(
            project_root=tmp_path,
            graph_output_dir=tmp_path / "graphify-out",
            provider="anthropic",
        )
    )

    service.get_provider()

    assert captured["model"].startswith("claude-")


def test_explicit_provider_model_is_preserved(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    class FakeProvider:
        def __init__(self, model: str):
            captured["model"] = model

    monkeypatch.setattr(provider_service, "_PROVIDER_MAP", {"anthropic": FakeProvider})
    service = LLMService(
        AgentConfig(
            project_root=tmp_path,
            graph_output_dir=tmp_path / "graphify-out",
            provider="anthropic",
            model="claude-custom",
        )
    )

    service.get_provider()

    assert captured["model"] == "claude-custom"
