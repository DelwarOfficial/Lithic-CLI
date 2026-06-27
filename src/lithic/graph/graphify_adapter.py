"""Stable subprocess adapter around Graphify."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import stat
import subprocess
import time
from pathlib import Path

from lithic.tools.audit import subprocess as audit_subprocess

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", ".cache", "__pycache__"}


class GraphifyAdapter:
    def __init__(self, project_root: Path, graph_output_dir: Path | None = None):
        self.project_root = project_root.resolve()
        self.graph_output_dir = (graph_output_dir or self.project_root / "graphify-out").resolve()
        self.graph_path = self.graph_output_dir / "graph.json"

    def graph_exists(self) -> bool:
        return self.graph_path.exists()

    def build_graph(self, target_path: str = ".") -> Path:
        target = self._safe_target(target_path)
        self._reset_output_dir()
        try:
            self._run(["graphify", "extract", str(target), "--no-viz", "--no-cluster"])
        except RuntimeError as exc:
            if "no LLM API key found" not in str(exc):
                raise
            self._run(["graphify", "update", str(target), "--force"])
        if not self.graph_exists():
            raise RuntimeError(f"Graphify finished but graph was not written: {self.graph_path}")
        return self.graph_path

    def update_graph(self, target_path: str = ".") -> Path:
        target = self._safe_target(target_path)
        if not self.graph_exists():
            return self.build_graph(target_path)
        self._run(["graphify", "update", str(target), "--force"])
        return self.graph_path

    def query(self, question: str) -> str:
        self._ensure_graph()
        return self._run(
            ["graphify", "query", self._sanitize_input(question), "--graph", self._graph_arg()]
        )

    def explain(self, concept: str) -> str:
        self._ensure_graph()
        return self._run(
            ["graphify", "explain", self._sanitize_input(concept), "--graph", self._graph_arg()]
        )

    def path_between(self, source: str, target: str) -> str:
        self._ensure_graph()
        return self._run(
            [
                "graphify",
                "path",
                self._sanitize_input(source),
                self._sanitize_input(target),
                "--graph",
                self._graph_arg(),
            ]
        )

    def stats(self) -> dict[str, int | str]:
        if not self.graph_exists():
            return {"graph": str(self.graph_path), "nodes": 0, "edges": 0}
        data = json.loads(self.graph_path.read_text(encoding="utf-8"))
        return {
            "graph": str(self.graph_path),
            "nodes": len(data.get("nodes", [])),
            "edges": len(data.get("edges", data.get("links", []))),
        }

    def _ensure_graph(self) -> None:
        if not self.graph_exists():
            self.build_graph(".")

    def _safe_target(self, target_path: str) -> Path:
        target = (self.project_root / target_path).resolve()
        try:
            target.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError(f"target must stay inside project root: {target}") from exc
        if any(part in SKIP_DIRS for part in target.parts):
            raise ValueError(f"refusing to scan skipped directory: {target}")
        if not target.exists():
            raise FileNotFoundError(f"target path not found: {target}")
        return target

    SHELL_META = frozenset("`$()|&;<>\\\"'")

    def _sanitize_input(self, value: str) -> str:
        cleaned = "".join(ch for ch in value.strip() if ch.isprintable() or ch in "\n\t")
        if any(ch in cleaned for ch in self.SHELL_META):
            raise ValueError(f"input contains shell metacharacters: {self.SHELL_META}")
        cleaned = " ".join(cleaned.split())
        if not cleaned:
            raise ValueError("graph query input cannot be empty")
        if cleaned.startswith("--"):
            raise ValueError("input cannot start with '--' (flag injection)")
        if len(cleaned) > 2000:
            cleaned = cleaned[:2000]
        return cleaned

    def _reset_output_dir(self) -> None:
        try:
            self.graph_output_dir.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError(
                f"graph output dir must stay inside project root: {self.graph_output_dir}"
            ) from exc
        if self.graph_output_dir.exists():
            self._rmtree_safe(self.graph_output_dir)
        self.graph_output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _rmtree_safe(path: Path) -> None:
        """Remove a directory tree, refusing to follow symlinks."""
        for entry in path.rglob("*"):
            if entry.is_symlink():
                raise RuntimeError(f"refusing to follow symlink during rmtree: {entry}")
        for entry in path.rglob("*"):
            try:
                if entry.is_dir():
                    entry.chmod(entry.stat().st_mode | stat.S_IWRITE)
                else:
                    entry.chmod(entry.stat().st_mode | stat.S_IWRITE)
            except Exception:
                pass
        shutil.rmtree(path, onexc=lambda *a: None)

    def _graph_arg(self) -> str:
        try:
            return str(self.graph_path.relative_to(self.project_root))
        except ValueError:
            return str(self.graph_path)

    def _run(self, args: list[str], timeout: int = 120) -> str:
        exe = shutil.which(args[0])
        command = args if exe is not None else ["uv", "run", *args]
        env = {"PATH": os.environ.get("PATH", ""), "GRAPHIFY_OUT": str(self.graph_output_dir)}
        start = time.monotonic()
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = time.monotonic() - start
            audit_subprocess(command, -1, elapsed, f"timed out after {timeout}s")
            rendered = shlex.join(command)
            raise RuntimeError(
                f"Graphify command timed out after {timeout}s ({rendered})"
            ) from exc
        elapsed = time.monotonic() - start
        output = (result.stdout or "").strip()
        error = (result.stderr or "").strip()
        if result.returncode != 0:
            detail = error or output or "no output"
            rendered = shlex.join(command)
            audit_subprocess(command, result.returncode, elapsed, detail)
            raise RuntimeError(f"Graphify command failed ({rendered}): {detail}")
        audit_subprocess(command, result.returncode, elapsed)
        return output or error
