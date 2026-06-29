from pathlib import Path

import pytest

from lithic_cli.config import AgentConfig


def test_valid_mode_accepted(tmp_path: Path) -> None:
    c = AgentConfig(project_root=tmp_path, graph_output_dir=tmp_path, response_mode="concise")
    assert c.response_mode == "concise"


def test_valid_caveman_mode_accepted(tmp_path: Path) -> None:
    c = AgentConfig(
        project_root=tmp_path,
        graph_output_dir=tmp_path,
        response_mode="caveman_full",
    )
    assert c.response_mode == "caveman_full"


def test_invalid_mode_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown response mode"):
        AgentConfig(project_root=tmp_path, graph_output_dir=tmp_path, response_mode="bogus")


def test_default_provider_is_local(tmp_path: Path) -> None:
    c = AgentConfig(project_root=tmp_path, graph_output_dir=tmp_path)
    assert c.provider == "local"


def test_default_model_is_gpt(tmp_path: Path) -> None:
    c = AgentConfig(project_root=tmp_path, graph_output_dir=tmp_path)
    assert c.model == "gpt-4.1-mini"


def test_default_response_mode_concise(tmp_path: Path) -> None:
    c = AgentConfig(project_root=tmp_path, graph_output_dir=tmp_path)
    assert c.response_mode == "concise"


def test_verbose_defaults_false(tmp_path: Path) -> None:
    c = AgentConfig(project_root=tmp_path, graph_output_dir=tmp_path)
    assert c.verbose is False


def test_from_env_reads_provider(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LITHIC_PROVIDER", "ollama")
    c = AgentConfig.from_env(tmp_path)
    assert c.provider == "ollama"


def test_from_env_uses_legacy_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UDA_PROVIDER", "anthropic")
    c = AgentConfig.from_env(tmp_path)
    assert c.provider == "anthropic"


def test_from_env_invalid_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LITHIC_RESPONSE_MODE", "invalid")
    with pytest.raises(ValueError, match="unknown response mode"):
        AgentConfig.from_env(tmp_path)


def test_from_env_non_existent_root() -> None:
    with pytest.raises(ValueError, match="not a valid directory"):
        AgentConfig.from_env(Path("/nonexistent/path/12345"))
