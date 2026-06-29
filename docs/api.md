# API Documentation

## Generating API Docs

API documentation is auto-generated from docstrings using pdoc.

### Generate docs

```bash
make docs
```

This creates HTML documentation in `docs/api/`.

### Viewing docs

Open `docs/api/index.html` in a browser after generation.

### Docstring format

Lithic uses Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """Short description of function.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When something is invalid.
    """
```

## Key Modules

- `lithic_cli.config` - Configuration management
- `lithic_cli.orchestrator` - Main orchestration logic
- `lithic_cli.graph` - Graph operations
- `lithic_cli.mcp` - MCP server implementation
- `lithic_cli.compression` - Text compression
- `lithic_cli.secrets` - Secrets management
- `lithic_cli.resilience` - Circuit breaker and retry patterns
- `lithic_cli.monitoring` - Metrics and monitoring
- `lithic_cli.health` - Health check endpoints
