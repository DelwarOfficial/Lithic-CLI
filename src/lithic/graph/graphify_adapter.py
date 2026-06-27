"""Stable subprocess adapter around Graphify."""

from __future__ import annotations

import json
import logging
import os
import shlex
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

from lithic.tools.audit import subprocess as audit_subprocess

_LOG = logging.getLogger(__name__)

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", ".cache", "__pycache__", "vendor", "graphify-out"}
GRAPH_OUTPUT_MARKER = ".lithic-graph-output"
GRAPH_OUTPUT_DIR_NAMES = {"graphify-out", ".graphify-out"}


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
            err = str(exc).lower()
            if "api key" in err or "llm" in err or "auth" in err:
                try:
                    self._run(["graphify", "update", str(target), "--force"])
                except RuntimeError:
                    if self.graph_exists():
                        _log.warning("extract failed (no API key), reusing existing graph")
                        return self.graph_path
                    raise RuntimeError(
                        "Graphify needs LLM API key. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
                    ) from exc
            else:
                raise
        if not self.graph_exists():
            raise RuntimeError(f"Graphify finished but graph was not written: {self.graph_path}")
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
        if self.graph_output_dir == self.project_root:
            raise ValueError(f"graph output dir cannot be project root: {self.graph_output_dir}")
        if self.graph_output_dir.name not in GRAPH_OUTPUT_DIR_NAMES:
            raise ValueError(
                "graph output dir must be a dedicated graphify-out directory: "
                f"{self.graph_output_dir}"
            )
        # Backup existing graph before reset
        graph_backup = None
        if self.graph_path.exists():
            graph_backup = self.graph_path.read_bytes()
        if self.graph_output_dir.exists():
            marker = self.graph_output_dir / GRAPH_OUTPUT_MARKER
            has_contents = next(self.graph_output_dir.iterdir(), None) is not None
            if has_contents and not marker.exists():
                raise ValueError(
                    "refusing to delete unmanaged graph output dir without marker: "
                    f"{self.graph_output_dir}"
                )
            if has_contents:
                self._rmtree_safe(self.graph_output_dir)
        self.graph_output_dir.mkdir(parents=True, exist_ok=True)
        (self.graph_output_dir / GRAPH_OUTPUT_MARKER).write_text(
            "generated by lithic\n",
            encoding="utf-8",
        )
        # Restore graph backup if it existed
        if graph_backup is not None:
            self.graph_path.write_bytes(graph_backup)

    @staticmethod
    def _rmtree_safe(path: Path) -> None:
        """Remove a directory tree bottom-up, checking symlinks at deletion time."""
        for entry in sorted(path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if entry.is_symlink():
                raise RuntimeError(f"refusing to remove symlink: {entry}")
            try:
                entry.chmod(entry.stat().st_mode | stat.S_IWRITE)
            except PermissionError as exc:
                _LOG.warning("cannot chmod %s: %s", entry, exc)
            try:
                if entry.is_dir():
                    entry.rmdir()
                else:
                    entry.unlink()
            except (OSError, PermissionError) as exc:
                raise RuntimeError(f"cannot remove {entry}: {exc}") from exc
        try:
            path.rmdir()
        except OSError as exc:
            raise RuntimeError(f"cannot remove root {path}: {exc}") from exc

    def _graph_arg(self) -> str:
        try:
            return str(self.graph_path.relative_to(self.project_root))
        except ValueError:
            return str(self.graph_path)

    def _run(self, args: list[str], timeout: int = 120) -> str:
        exe = shutil.which(args[0])
        command = args if exe is not None else ["uv", "run", *args]
        env = os.environ.copy()
        env["GRAPHIFY_OUT"] = str(self.graph_output_dir)

        # On Windows, uv trampoline can fail for graphify; use python -m fallback
        if sys.platform == "win32" and command[0] in ("graphify", "graphify.exe"):
            command = [sys.executable, "-m", "graphify"] + command[1:]
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
        return output or error or "(empty response)"
