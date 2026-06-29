# Benchmarks

Performance benchmarks for Lithic-CLI components.

## Running Benchmarks

```bash
# Run compression benchmarks
python benchmarks/bench_compression.py

# Or via Makefile
make bench
```

## Current Benchmarks

- **bench_compression.py** - Measures compression performance across different text sizes

## Adding Benchmarks

Create a new file `bench_<component>.py` in this directory following the existing pattern.
