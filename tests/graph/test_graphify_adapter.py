from pathlib import Path

import pytest

from lithic.graph.graphify_adapter import GRAPH_OUTPUT_MARKER, GraphifyAdapter


def test_graph_exists_false(tmp_path: Path) -> None:
    adapter = GraphifyAdapter(tmp_path)
    assert adapter.graph_exists() is False


def test_build_graph_creates_graph(monkeypatch, tmp_path: Path) -> None:
    adapter = GraphifyAdapter(tmp_path)

    def fake_run(args: list[str]) -> str:
        adapter.graph_output_dir.mkdir(parents=True, exist_ok=True)
        adapter.graph_path.write_text('{"nodes": [], "edges": []}', encoding="utf-8")
        return "done"

    monkeypatch.setattr(adapter, "_run", fake_run)
    assert adapter.build_graph(".") == adapter.graph_path
    assert adapter.graph_exists()


def test_query_builds_missing_graph(monkeypatch, tmp_path: Path) -> None:
    adapter = GraphifyAdapter(tmp_path)
    calls: list[list[str]] = []

    def fake_run(args: list[str]) -> str:
        calls.append(args)
        if args[1] == "extract":
            adapter.graph_output_dir.mkdir(parents=True, exist_ok=True)
            adapter.graph_path.write_text('{"nodes": [], "edges": []}', encoding="utf-8")
        return "answer"

    monkeypatch.setattr(adapter, "_run", fake_run)
    assert adapter.query("what is this?") == "answer"
    assert calls[0][1] == "extract"
    assert calls[1][1] == "query"


def test_query_sanitizes_control_chars(monkeypatch, tmp_path: Path) -> None:
    adapter = GraphifyAdapter(tmp_path)
    adapter.graph_output_dir.mkdir(parents=True, exist_ok=True)
    adapter.graph_path.write_text('{"nodes": [], "edges": []}', encoding="utf-8")
    seen: list[list[str]] = []

    def fake_run(args: list[str]) -> str:
        seen.append(args)
        return "ok"

    monkeypatch.setattr(adapter, "_run", fake_run)
    adapter.query("hello\x00\nworld")
    assert seen[0][2] == "hello world"


def test_build_graph_refuses_unmanaged_output_dir(monkeypatch, tmp_path: Path) -> None:
    unsafe = tmp_path / "src"
    unsafe.mkdir()
    (unsafe / "important.py").write_text("keep me", encoding="utf-8")
    adapter = GraphifyAdapter(tmp_path, unsafe)
    monkeypatch.setattr(adapter, "_run", lambda args: "unused")

    with pytest.raises(ValueError, match="dedicated graphify-out"):
        adapter.build_graph(".")
    assert (unsafe / "important.py").exists()


def test_build_graph_marks_managed_output_dir(monkeypatch, tmp_path: Path) -> None:
    adapter = GraphifyAdapter(tmp_path)

    def fake_run(args: list[str]) -> str:
        adapter.graph_path.write_text('{"nodes": [], "edges": []}', encoding="utf-8")
        return "done"

    monkeypatch.setattr(adapter, "_run", fake_run)
    adapter.build_graph(".")

    assert (adapter.graph_output_dir / GRAPH_OUTPUT_MARKER).exists()
