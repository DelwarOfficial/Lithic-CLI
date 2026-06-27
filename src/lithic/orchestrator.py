"""Graph-first orchestration for Lithic."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from lithic.compression.headroom_adapter import HeadroomAdapter
from lithic.config import AgentConfig
from lithic.graph.service import GraphService
from lithic.policy.response_policy import ResponsePolicy
from lithic.providers.service import LLMService
from lithic.tools import git
from lithic.tools.fs import resolve_path_within_root


_log = logging.getLogger("lithic.orchestrator")


class Orchestrator:
    """Coordinate graph, LLM, compression, and policy layers."""

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig.from_env()
        self.graph = GraphService(self.config.project_root, self.config.graph_output_dir)
        self._llm = LLMService(self.config)
        self.compression = HeadroomAdapter()
        self.policy = ResponsePolicy()
        self.events: list[str] = []

    def provider(self) -> Any:
        return self._llm.get_provider()

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        self.events.append(f"provider.{self.config.provider}")
        return self._llm.complete(messages, **kwargs)

    _CLASSIFY_RE = re.compile(
        r"(?i)\b(review|commit|index|test|explain|path|fix|edit|change|implement)\b"
    )

    def classify(self, task: str) -> str:
        m = self._CLASSIFY_RE.search(task)
        if m:
            word = m.group(1).lower()
            if word in {"fix", "edit", "change", "implement"}:
                return "edit"
            return word
        return "ask"

    def _llm_answer(self, context: str, task: str) -> str:
        p = self.provider()
        if p is None:
            return context
        messages = [
            {
                "role": "system",
                "content": "You are a codebase expert. Answer concisely from context.",
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {task}"},
        ]
        try:
            return self._llm.complete(messages)
        except RuntimeError:
            _log.warning("LLM completion failed, returning raw context", exc_info=True)
            return context

    def ask(self, question: str) -> str:
        self.events.append("graph.query")
        raw = self.graph.query(question)
        if self.provider() is not None:
            raw = self._llm_answer(raw, question)
        return self.policy.shape(raw, self.config.response_mode)

    def explain(self, concept: str) -> str:
        self.events.append("graph.explain")
        raw = self.graph.explain(concept)
        if self.provider() is not None:
            raw = self._llm_answer(raw, f"Explain: {concept}")
        return self.policy.shape(raw, self.config.response_mode)

    def path_between(self, source: str, target: str) -> str:
        self.events.append("graph.path")
        return self.policy.shape(
            self.graph.path_between(source, target),
            self.config.response_mode,
        )

    def review(self) -> str:
        try:
            diff = git.diff(self.config.project_root)
        except RuntimeError as exc:
            return f"git error: {exc}"
        if not diff.strip():
            return "No changes to review."
        compressed = self.compression.compress_tool_output(diff)
        return self.policy.shape(compressed, mode="review")

    def commit(self) -> str:
        diff = ""
        try:
            diff = git.diff(self.config.project_root, staged=True)
        except RuntimeError:
            _log.info("staged diff failed, falling back to working-tree diff", exc_info=True)
            pass
        if not diff:
            try:
                diff = git.diff(self.config.project_root)
            except RuntimeError as exc:
                return f"chore: git error - {exc}"
        if not diff.strip():
            return "chore: no changes"
        compressed = self.compression.compress_tool_output(diff, max_chars=12000)
        return self.policy.shape(compressed, mode="commit")

    def orient_edit(self, task: str) -> str:
        context = self.ask(f"Locate files and architecture context for edit task: {task}")
        self.events.append("edit.orient")
        return context

    def index(self, path: str = ".") -> str:
        graph_path = self.graph.build_graph(path)
        self.events.append("graph.build")
        return f"Graph built at {graph_path}"

    _MAX_COMPRESS_BYTES = 100_000_000

    def compress_file(self, file_path: str) -> str:
        path = resolve_path_within_root(self.config.project_root, Path(file_path))
        size = path.stat().st_size
        if size > self._MAX_COMPRESS_BYTES:
            return f"file too large ({size} bytes > {self._MAX_COMPRESS_BYTES} limit)"
        if size > 10_000_000:
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                head = fh.read(1_000_000)
                return self.compression.compress_tool_output(
                    head + f"\n... [file truncated: {size} bytes, showing first 1MB] ..."
                )
        content = path.read_text(encoding="utf-8", errors="replace")
        return self.compression.compress_tool_output(content)

    def handle(self, task: str) -> str:
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
        return {
            "graph_exists": self.graph.graph_exists(),
            "graph": self.graph.stats(),
            "compression": self.compression.stats(),
            "history_count": len(self.events),
            "events": self.events,
        }
