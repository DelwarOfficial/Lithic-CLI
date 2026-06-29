"""Graph-first orchestration for Lithic."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any

from lithic_cli.advanced_monitoring import get_apm_collector
from lithic_cli.caching import get_cache
from lithic_cli.compression.headroom_adapter import HeadroomAdapter
from lithic_cli.config import AgentConfig
from lithic_cli.graph.backends import get_default_backend
from lithic_cli.graph.service import GraphService
from lithic_cli.plugins.manager import get_plugin_manager
from lithic_cli.policy.response_policy import ResponsePolicy
from lithic_cli.providers.service import LLMService
from lithic_cli.tools import git
from lithic_cli.tools.fs import resolve_path_within_root
from lithic_cli.tracing import trace_operation

_log = logging.getLogger("lithic_cli.orchestrator")


class Orchestrator:
    """Coordinate graph, LLM, compression, and policy layers."""

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig.from_env()
        
        # Initialize core services
        self.graph = GraphService(self.config.project_root, self.config.graph_output_dir)
        self._llm = LLMService(self.config)
        
        # Plugin-based providers with fallback to legacy adapters
        self.plugin_manager = get_plugin_manager()
        
        # Try plugin-based compression first
        compression_provider = self.plugin_manager.get_compression_provider()
        if compression_provider:
            self.compression = compression_provider
        else:
            # Fallback to legacy adapter
            self.compression = HeadroomAdapter()
        
        # Response provider
        response_provider = self.plugin_manager.get_response_provider()
        if response_provider:
            self.policy = response_provider
        else:
            # Fallback to legacy policy
            self.policy = ResponsePolicy()
        
        # Advanced features
        self.cache = get_cache()
        self.graph_backend = get_default_backend(self.config.graph_output_dir)
        self.apm = get_apm_collector()
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

    @trace_operation("orchestrator.ask", operation_type="llm_query")
    def ask(self, question: str) -> str:
        if not question.strip():
            return "Please provide a question."
        
        # Start APM trace
        trace_id = f"ask-{int(time.time() * 1000)}"
        self.apm.start_trace(trace_id, "orchestrator.ask")
        
        try:
            # Check cache first
            cache_key = self.cache.content_hash(question, "query")
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self.events.append("cache.hit")
                return (self.policy.shape(cached_result, self.config.response_mode) 
                       if hasattr(self.policy, 'shape') else cached_result)
            
            self.events.append("graph.query")
            raw = self.graph.query(question)
            
            if self.provider() is not None:
                raw = self._llm_answer(raw, question)
            
            # Cache result
            self.cache.set(cache_key, raw, ttl=3600)
            
            # Shape response based on provider type
            if hasattr(self.policy, 'shape_response'):
                # Plugin-based response provider
                result = self.policy.shape_response(raw, self.config.response_mode)
                return result.data if result.success else raw
            else:
                # Legacy policy
                return self.policy.shape(raw, self.config.response_mode)
                
        except Exception as e:
            _log.error(f"Ask operation failed: {e}")
            return f"Error processing query: {str(e)}"

    def explain(self, concept: str) -> str:
        if not concept.strip():
            return "Please provide a concept to explain."
        self.events.append("graph.explain")
        raw = self.graph.explain(concept)
        if self.provider() is not None:
            raw = self._llm_answer(raw, f"Explain: {concept}")
        return self.policy.shape(raw, self.config.response_mode)

    def path_between(self, source: str, target: str) -> str:
        if not source.strip() or not target.strip():
            return "Please provide both source and target."
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
        
        # Use plugin-based compression if available
        # Use plugin-based compression if available
        if hasattr(self.compression, 'compress_tool_output'):
            # HeadroomAdapter returns string directly
            compressed = self.compression.compress_tool_output(diff, max_chars=8000)
        else:
            # Legacy compression
            compressed = self.compression.compress_tool_output(diff, max_chars=8000)
        
        # Shape response
        if hasattr(self.policy, 'shape_response'):
            result = self.policy.shape_response(compressed, "review")
            return result.data if result.success else compressed
        else:
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
        
        # Use plugin-based compression if available  
        if hasattr(self.compression, 'compress_tool_output'):
            # HeadroomAdapter returns string directly
            compressed = self.compression.compress_tool_output(diff, max_chars=12000)
        else:
            compressed = self.compression.compress_tool_output(diff, max_chars=12000)
        
        # Shape response
        if hasattr(self.policy, 'shape_response'):
            result = self.policy.shape_response(compressed, "commit")
            return result.data if result.success else compressed
        else:
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
                content = head + f"\n... [file truncated: {size} bytes, showing first {len(head)} chars] ..."
        else:
            content = path.read_text(encoding="utf-8", errors="replace")
        
        # Use plugin-based compression if available
        if hasattr(self.compression, 'compress_text'):
            # HeadroomAdapter returns string directly  
            return self.compression.compress_text(content, "code")
        else:
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
            "compression": (self.compression.get_compression_stats() 
                          if hasattr(self.compression, 'get_compression_stats') 
                          else self.compression.stats()),
            "cache": self.cache.stats(),
            "plugins": self.plugin_manager.get_plugin_stats(),
            "apm": self.apm.get_performance_metrics(),
            "history_count": len(self.events),
            "events": self.events,
        }
