"""Graph service wrapping GraphifyAdapter."""

from __future__ import annotations

import time
from pathlib import Path

from lithic.graph.graphify_adapter import GraphifyAdapter


class _TTLCache:
    """TTL cache with LRU eviction for graph query results."""

    def __init__(self, ttl: float = 60.0, maxsize: int = 128):
        self._ttl = ttl
        self._maxsize = maxsize
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts > self._ttl:
            del self._store[key]
            return None
        self._store[key] = (time.monotonic(), value)
        return value

    def set(self, key: str, value: str) -> None:
        if len(self._store) >= self._maxsize:
            oldest = min(self._store, key=lambda k: self._store[k][0])
            del self._store[oldest]
        self._store[key] = (time.monotonic(), value)


class GraphService:
    """Wraps graph operations behind a stable service interface.

    Parameters
    ----------
    project_root:
        Root directory for the project.
    graph_output_dir:
        Directory for graph output. Defaults to project_root/graphify-out.
    cache_ttl:
        Time-to-live for cached query/explain/path results, in seconds.
    """

    def __init__(
        self,
        project_root: Path,
        graph_output_dir: Path | None = None,
        cache_ttl: float = 60.0,
    ) -> None:
        self._adapter = GraphifyAdapter(project_root, graph_output_dir)
        self._cache = _TTLCache(ttl=cache_ttl)

    @property
    def graph_path(self) -> Path:
        return self._adapter.graph_path

    def query(self, question: str) -> str:
        cached = self._cache.get(question)
        if cached is not None:
            return cached
        result = self._adapter.query(question)
        self._cache.set(question, result)
        return result

    def explain(self, concept: str) -> str:
        cached = self._cache.get(concept)
        if cached is not None:
            return cached
        result = self._adapter.explain(concept)
        self._cache.set(concept, result)
        return result

    def path_between(self, source: str, target: str) -> str:
        key = f"path:{source}:{target}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        result = self._adapter.path_between(source, target)
        self._cache.set(key, result)
        return result

    def build_graph(self, target_path: str = ".") -> Path:
        return self._adapter.build_graph(target_path)

    def graph_exists(self) -> bool:
        return self._adapter.graph_exists()

    def stats(self) -> dict[str, int | str]:
        return self._adapter.stats()

    def clear_cache(self) -> None:
        self._cache = _TTLCache()
