"""Performance benchmarks for Lithic-CLI.

Run with: python benchmarks/bench_compression.py
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lithic_cli.compression.headroom_adapter import HeadroomAdapter


def benchmark_compression(adapter: HeadroomAdapter, text: str, iterations: int = 100) -> dict:
    """Benchmark compression performance."""
    times = []
    original_size = len(text)
    compressed_size = 0
    
    for _ in range(iterations):
        start = time.perf_counter()
        result = adapter.compress_text(text)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        compressed_size = len(result)
    
    return {
        "iterations": iterations,
        "original_size": original_size,
        "compressed_size": compressed_size,
        "compression_ratio": compressed_size / original_size if original_size > 0 else 0,
        "mean_ms": statistics.mean(times) * 1000,
        "median_ms": statistics.median(times) * 1000,
        "stdev_ms": statistics.stdev(times) * 1000 if len(times) > 1 else 0,
        "min_ms": min(times) * 1000,
        "max_ms": max(times) * 1000,
    }


def generate_sample_text(size: int = 10000) -> str:
    """Generate sample text for benchmarking."""
    lines = []
    for i in range(size // 50):
        if i % 10 == 0:
            lines.append(f"ERROR: Something failed at line {i}")
        elif i % 5 == 0:
            lines.append(f"/path/to/file_{i}.py:{i}: Some code content here")
        else:
            lines.append(f"Line {i}: This is a regular line of text content for testing.")
    return "\n".join(lines)


def run_benchmarks() -> None:
    """Run all benchmarks."""
    print("Lithic-CLI Performance Benchmarks")
    print("=" * 50)
    
    adapter = HeadroomAdapter()
    
    # Small text
    small_text = generate_sample_text(1000)
    print(f"\n[Small text: {len(small_text)} chars]")
    result = benchmark_compression(adapter, small_text)
    print(f"  Compression ratio: {result['compression_ratio']:.2%}")
    print(f"  Mean time: {result['mean_ms']:.2f}ms")
    
    # Medium text
    medium_text = generate_sample_text(10000)
    print(f"\n[Medium text: {len(medium_text)} chars]")
    result = benchmark_compression(adapter, medium_text)
    print(f"  Compression ratio: {result['compression_ratio']:.2%}")
    print(f"  Mean time: {result['mean_ms']:.2f}ms")
    
    # Large text
    large_text = generate_sample_text(100000)
    print(f"\n[Large text: {len(large_text)} chars]")
    result = benchmark_compression(adapter, large_text)
    print(f"  Compression ratio: {result['compression_ratio']:.2%}")
    print(f"  Mean time: {result['mean_ms']:.2f}ms")


if __name__ == "__main__":
    run_benchmarks()
