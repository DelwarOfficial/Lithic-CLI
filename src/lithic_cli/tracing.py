"""Distributed tracing with OpenTelemetry for production observability."""

from __future__ import annotations

import functools
import os
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

# Global tracing enabled flag
_TRACING_ENABLED = os.getenv("LITHIC_TRACING_ENABLED", "false").lower() in ("true", "1", "yes")

# OpenTelemetry components (lazy imported)
_tracer = None
_trace = None


def _init_tracing():
    """Initialize OpenTelemetry tracing if enabled."""
    global _tracer, _trace
    
    if not _TRACING_ENABLED or _tracer is not None:
        return
    
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        
        # Configure resource
        resource = Resource.create({
            "service.name": "lithic-cli",
            "service.version": "0.2.0",
        })
        
        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider(resource=resource))
        tracer_provider = trace.get_tracer_provider()
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
            agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Get tracer
        _tracer = trace.get_tracer("lithic-cli")
        _trace = trace
        
    except ImportError:
        # OpenTelemetry not installed - disable tracing
        _TRACING_ENABLED = False


def trace_operation(operation_name: str, **attributes: Any):
    """Decorator to trace function calls."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not _TRACING_ENABLED:
                return func(*args, **kwargs)
            
            _init_tracing()
            
            if _tracer is None:
                return func(*args, **kwargs)
            
            with _tracer.start_as_current_span(operation_name) as span:
                # Add custom attributes
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
                
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("operation.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("operation.status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise
                finally:
                    duration = time.time() - start_time
                    span.set_attribute("operation.duration", duration)
        
        return wrapper
    return decorator


def add_span_attribute(key: str, value: Any) -> None:
    """Add attribute to current span if tracing is enabled."""
    if not _TRACING_ENABLED:
        return
    
    _init_tracing()
    
    if _trace is None:
        return
    
    current_span = _trace.get_current_span()
    if current_span:
        current_span.set_attribute(key, str(value))


def create_child_span(operation_name: str, **attributes: Any):
    """Create a child span context manager."""
    if not _TRACING_ENABLED:
        return _NoOpSpan()
    
    _init_tracing()
    
    if _tracer is None:
        return _NoOpSpan()
    
    span = _tracer.start_span(operation_name)
    for key, value in attributes.items():
        span.set_attribute(key, str(value))
    
    return span


class _NoOpSpan:
    """No-op span for when tracing is disabled."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def set_attribute(self, key: str, value: Any) -> None:
        pass


def get_trace_id() -> str | None:
    """Get current trace ID if available."""
    if not _TRACING_ENABLED:
        return None
    
    _init_tracing()
    
    if _trace is None:
        return None
    
    current_span = _trace.get_current_span()
    if current_span:
        trace_id = current_span.get_span_context().trace_id
        return f"{trace_id:032x}"
    
    return None


def is_tracing_enabled() -> bool:
    """Check if tracing is enabled."""
    return _TRACING_ENABLED