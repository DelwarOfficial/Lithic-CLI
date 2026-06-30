FROM python:3.12-slim as builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

RUN uv sync --no-dev --frozen --extra mcp

FROM python:3.12-slim as runtime

# Create non-root user
RUN groupadd --gid 1000 lithic \
    && useradd --uid 1000 --gid lithic --shell /bin/bash --create-home lithic

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=lithic:lithic /app/.venv /app/.venv
COPY --from=builder --chown=lithic:lithic /app/src /app/src

# Create required directories
RUN mkdir -p /app/graphify-out /app/logs \
    && chown -R lithic:lithic /app

# Health check
COPY --chown=lithic:lithic <<EOF /app/healthcheck.py
#!/usr/bin/env python3
import sys
import json
from pathlib import Path
sys.path.insert(0, '/app/src')
from lithic_cli.health import HealthChecker
try:
    health = HealthChecker()
    result = health.health_check()
    if result['status'] == 'healthy':
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)
EOF

RUN chmod +x /app/healthcheck.py

USER lithic

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 /app/healthcheck.py

EXPOSE 8000

ENTRYPOINT ["lithic"]
CMD ["mcp", "serve"]
