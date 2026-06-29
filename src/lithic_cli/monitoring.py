"""Production monitoring and metrics collection."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Any


class PrometheusMetrics:
    """Basic Prometheus-compatible metrics collector."""
    
    def __init__(self):
        self._counters: dict[str, int] = defaultdict(int)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = {}
        self._lock = Lock()
        self.start_time = time.time()
    
    def increment_counter(self, name: str, labels: dict[str, str] | None = None) -> None:
        """Increment a counter metric."""
        key = self._metric_key(name, labels or {})
        with self._lock:
            self._counters[key] += 1
    
    def observe_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record a histogram observation."""
        key = self._metric_key(name, labels or {})
        with self._lock:
            self._histograms[key].append(value)
            # Keep only last 1000 observations to prevent memory growth
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
    
    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Set a gauge metric value."""
        key = self._metric_key(name, labels or {})
        with self._lock:
            self._gauges[key] = value
    
    def _metric_key(self, name: str, labels: dict[str, str]) -> str:
        """Create a metric key from name and labels."""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        
        # Counters
        for key, value in self._counters.items():
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {value}")
        
        # Gauges
        for key, value in self._gauges.items():
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {value}")
        
        # Histograms (simplified - just count and sum)
        for key, values in self._histograms.items():
            base_name = key.split('{')[0]
            lines.append(f"# TYPE {base_name} histogram")
            lines.append(f"{key.replace(base_name, f'{base_name}_count')} {len(values)}")
            lines.append(f"{key.replace(base_name, f'{base_name}_sum')} {sum(values):.6f}")
        
        # Built-in uptime gauge
        uptime = time.time() - self.start_time
        lines.append("# TYPE lithic_uptime_seconds gauge")
        lines.append(f"lithic_uptime_seconds {uptime:.0f}")
        
        return "\n".join(lines) + "\n"
    
    def get_stats(self) -> dict[str, Any]:
        """Get current metrics as a dictionary."""
        with self._lock:
            histogram_stats = {}
            for key, values in self._histograms.items():
                if values:
                    histogram_stats[key] = {
                        "count": len(values),
                        "sum": sum(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                    }
            
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": histogram_stats,
                "uptime_seconds": time.time() - self.start_time,
            }


# Global metrics instance
_metrics = PrometheusMetrics()


def get_metrics() -> PrometheusMetrics:
    """Get the global metrics collector."""
    return _metrics


def track_request_duration(operation: str, provider: str | None = None):
    """Decorator to track operation duration."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            labels = {"operation": operation}
            if provider:
                labels["provider"] = provider
            
            try:
                result = func(*args, **kwargs)
                _metrics.increment_counter("lithic_requests_total", {**labels, "status": "success"})
                return result
            except Exception as e:
                _metrics.increment_counter("lithic_requests_total", {**labels, "status": "error", "error_type": type(e).__name__})
                raise
            finally:
                duration = time.time() - start_time
                _metrics.observe_histogram("lithic_request_duration_seconds", duration, labels)
        
        return wrapper
    return decorator