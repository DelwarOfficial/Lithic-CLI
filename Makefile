.PHONY: test lint typecheck clean install docs

install:
	uv sync --group dev

test:
	uv run pytest tests/ -q

lint:
	uv run ruff check src/lithic_cli/ tests/

format:
	uv run ruff format src/lithic/ tests/

typecheck:
	uv run mypy src/lithic/

clean:
	-rm -rf .pytest_cache .ruff_cache .mypy_cache graphify-out

docs:
	uv run pdoc src/lithic_cli -o docs/api --docformat google

bench:
	python benchmarks/bench_compression.py

all: lint test typecheck
