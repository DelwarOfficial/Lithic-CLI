.PHONY: test lint typecheck clean install

install:
	uv sync --group dev

test:
	uv run pytest tests/ -q

lint:
	uv run ruff check src/lithic/ tests/

format:
	uv run ruff format src/lithic/ tests/

typecheck:
	uv run mypy src/lithic/

clean:
	-rm -rf .pytest_cache .ruff_cache .mypy_cache graphify-out

all: lint test typecheck
