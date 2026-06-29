"""Health check endpoints for production deployment."""

from __future__ import annotations

import json
import time
from pathlib import Path

from lithic_cli.config import AgentConfig
from lithic_cli.graph.service import GraphService


class HealthChecker:
    """Production health and readiness checks."""

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig.from_env()
        self.start_time = time.time()

    def health_check(self) -> dict[str, object]:
        """Basic liveness check - always returns OK if process running."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self.start_time,
        }

    def readiness_check(self) -> dict[str, object]:
        """Readiness check - validates core dependencies available."""
        checks = {}
        overall_ready = True

        # Check if project root exists and is readable
        try:
            if self.config.project_root.exists() and self.config.project_root.is_dir():
                checks["project_root"] = "ready"
            else:
                checks["project_root"] = "not_found"
                overall_ready = False
        except Exception as e:
            checks["project_root"] = f"error: {e}"
            overall_ready = False

        # Check if graph output directory is writable
        try:
            self.config.graph_output_dir.mkdir(parents=True, exist_ok=True)
            test_file = self.config.graph_output_dir / ".health_check"
            test_file.write_text("test")
            test_file.unlink()
            checks["graph_output_dir"] = "ready"
        except Exception as e:
            checks["graph_output_dir"] = f"error: {e}"
            overall_ready = False

        # Check graph service initialization
        try:
            graph = GraphService(self.config.project_root, self.config.graph_output_dir)
            checks["graph_service"] = "ready"
        except Exception as e:
            checks["graph_service"] = f"error: {e}"
            overall_ready = False

        return {
            "status": "ready" if overall_ready else "not_ready",
            "timestamp": time.time(),
            "checks": checks,
        }

    def metrics(self) -> dict[str, object]:
        """Basic metrics for monitoring."""
        try:
            graph = GraphService(self.config.project_root, self.config.graph_output_dir)
            graph_stats = graph.stats()
        except Exception:
            graph_stats = {"error": "graph unavailable"}

        return {
            "uptime_seconds": time.time() - self.start_time,
            "graph": graph_stats,
            "config": {
                "provider": self.config.provider,
                "model": self.config.model,
                "response_mode": self.config.response_mode,
            },
        }