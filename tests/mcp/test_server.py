import time

import pytest

from lithic.mcp.server import _check_input_size, _RateLimiter


def test_rate_limiter_allows_under_limit() -> None:
    limiter = _RateLimiter(max_calls=5, window=60.0)
    for _ in range(5):
        limiter.check()


def test_rate_limiter_blocks_over_limit() -> None:
    limiter = _RateLimiter(max_calls=3, window=60.0)
    for _ in range(3):
        limiter.check()
    with pytest.raises(RuntimeError, match="rate limit exceeded"):
        limiter.check()


def test_rate_limiter_resets_after_window() -> None:
    limiter = _RateLimiter(max_calls=2, window=0.2)
    limiter.check()
    limiter.check()
    with pytest.raises(RuntimeError):
        limiter.check()
    time.sleep(0.3)
    limiter.check()


def test_check_input_size_passes() -> None:
    result = _check_input_size("hello", 100, "test")
    assert result == "hello"


def test_check_input_size_raises() -> None:
    with pytest.raises(ValueError, match="too long"):
        _check_input_size("x" * 200, 100, "too long")
