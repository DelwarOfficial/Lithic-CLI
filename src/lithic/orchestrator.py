"""Graph-first orchestration for Lithic."""

from __future__ import annotations

import re
from pathlib import Path

from lithic.compression.headroom_adapter import HeadroomAdapter
from lithic.config import AgentConfig
from lithic.graph.graphify_adapter import GraphifyAdapter
from lithic.policy.response_policy import ResponsePolicy
from lithic.tools import git
from lithic.tools.fs import resolve_path_within_root


class Orchestrator:
    """Coordinate graph, compression, and policy layers."""

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig.from_env()
        self.graph = GraphifyAdapter(self.config.project_root, self.config.graph_output_dir)
        self.compression = HeadroomAdapter()
        self.policy = ResponsePolicy()
        self.events: list[str] = []

    def classify(self, task: str) -> str:
        """Classify a user task into a workflow type."""
        t = task.lower().strip()
        if t.startswith("review"):
            return "review"
        if t.startswith("commit"):
            return "commit"
        if t.startswith("index"):
            return "index"
        if t.startswith("test"):
            return "test"
        if "explain" in t:
            return "explain"
        if "path" in t:
            return "path"
        if any(word in t for word in ("fix", "edit", "change", "implement")):
            return "edit"
        return "ask"

    def ask(self, question: str) -> str:
        """Answer a codebase question through the graph."""
        self.events.append("graph.query")
        return self.policy.shape(self.graph.query(question), self.config.response_mode)

    def explain(self, concept: str) -> str:
        """Explain a graph concept."""
        self.events.append("graph.explain")
        return self.policy.shape(self.graph.explain(concept), self.config.response_mode)

    def path_between(self, source: str, target: str) -> str:
        """Return a path between two concepts."""
        self.events.append("graph.path")
        return self.policy.shape(
            self.graph.path_between(source, target),
            self.config.response_mode,
        )

    def review(self) -> str:
        """Review current working-tree changes."""
        try:
            diff = git.diff(self.config.project_root)
        except RuntimeError:
            return "No changes to review."
        if not diff.strip():
            return "No changes to review."
        compressed = self.compression.compress_tool_output(diff)
        return self.policy.shape(compressed, mode="review")

    def commit(self) -> str:
        """Generate a Conventional Commit message."""
        try:
            diff = git.diff(self.config.project_root, staged=True)
            diff = diff or git.diff(self.config.project_root)
        except RuntimeError:
            return "chore: no changes"
        if not diff.strip():
            return "chore: no changes"
        compressed = self.compression.compress_tool_output(diff, max_chars=12000)
        return self.policy.shape(compressed, mode="commit")

    def orient_edit(self, task: str) -> str:
        """Use the graph to orient an edit task without making changes."""
        context = self.ask(f"Locate files and architecture context for edit task: {task}")
        self.events.append("edit.orient")
        return context

    def index(self, path: str = ".") -> str:
        """Build or refresh the project graph."""
        graph_path = self.graph.build_graph(path)
        self.events.append("graph.build")
        return f"Graph built at {graph_path}"

    def run_tests(self) -> str:
        """Record a requested test step."""
        self.events.append("test.requested")
        return "Tests should be run after edits."

    _MAX_COMPRESS_BYTES = 100_000_000

    def compress_file(self, file_path: str) -> str:
        """Compress a file safely within the project root."""
        path = resolve_path_within_root(self.config.project_root, Path(file_path))
        size = path.stat().st_size
        if size > self._MAX_COMPRESS_BYTES:
            return f"file too large ({size} bytes > {self._MAX_COMPRESS_BYTES} limit)"
        content = path.read_text(encoding="utf-8", errors="replace")
        return self.compression.compress_tool_output(content)

    def handle(self, task: str) -> str:
        """Handle a generic user task."""
        kind = self.classify(task)
        if kind == "index":
            return self.index(".")
        if kind == "explain":
            concept = re.sub(r"(?i)^explain\s+", "", task).strip() or task
            return self.explain(concept)
        if kind == "review":
            return self.review()
        if kind == "commit":
            return self.commit()
        if kind == "edit":
            return self.orient_edit(task)
        return self.ask(task)

    def stats(self) -> dict[str, object]:
        """Return runtime stats."""
        return {
            "graph_exists": self.graph.graph_exists(),
            "graph": self.graph.stats(),
            "compression": self.compression.stats(),
            "history_count": len(self.events),
            "events": self.events,
        }
