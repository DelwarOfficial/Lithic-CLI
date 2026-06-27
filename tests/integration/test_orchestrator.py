from pathlib import Path

from lithic.config import AgentConfig
from lithic.orchestrator import Orchestrator


def _orch(tmp_path: Path) -> Orchestrator:
    return Orchestrator(
        AgentConfig(project_root=tmp_path, graph_output_dir=tmp_path / "graphify-out")
    )


def test_graph_first_behavior(monkeypatch, tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    monkeypatch.setattr(orch.graph, "query", lambda question: "graph answer")
    assert orch.ask("how auth works") == "graph answer"
    assert orch.events == ["graph.query"]


def test_explain_uses_graph(monkeypatch, tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    monkeypatch.setattr(orch.graph, "explain", lambda concept: f"about {concept}")
    assert orch.explain("UserService") == "about UserService"
    assert orch.events == ["graph.explain"]


def test_stats_shape(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    stats = orch.stats()
    assert "graph" in stats
    assert "compression" in stats


def test_commit_uses_diff(monkeypatch, tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    monkeypatch.setattr(
        "lithic.orchestrator.git.diff",
        lambda root, staged=False: "bug in auth redirect",
    )
    out = orch.commit()
    assert out.startswith("fix:")


def test_classify_returns_expected_types(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    assert orch.classify("review my changes") == "review"
    assert orch.classify("commit staged changes") == "commit"
    assert orch.classify("index this repo") == "index"
    assert orch.classify("test everything") == "test"
    assert orch.classify("explain how GraphService works") == "explain"
    assert orch.classify("path A B") == "path"
    assert orch.classify("fix the bug in parser") == "edit"
    assert orch.classify("what is the architecture?") == "ask"


def test_compress_file_too_large(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    big = tmp_path / "big.log"
    big.write_text("x" * 200_000_000, encoding="utf-8")
    result = orch.compress_file(str(big))
    assert "file too large" in result


def test_compress_file_small(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    f = tmp_path / "small.txt"
    f.write_text("hello world", encoding="utf-8")
    result = orch.compress_file(str(f))
    assert "hello world" in result


def test_review_with_no_changes(monkeypatch, tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    monkeypatch.setattr("lithic.orchestrator.git.diff", lambda root, staged=False: "")
    assert orch.review() == "No changes to review."
