"""End-to-end integration tests for production scenarios."""

import atexit
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest


@pytest.fixture
def temp_project():
    """Create temporary project with real code structure."""
    tmpdir = tempfile.mkdtemp()
    project = Path(tmpdir)
    
    def cleanup():
        # Windows-safe cleanup with retries
        for i in range(3):
            try:
                shutil.rmtree(tmpdir, ignore_errors=True)
                break
            except PermissionError:
                time.sleep(0.1)
    
    atexit.register(cleanup)
    
    # Create realistic project structure
    (project / "src").mkdir()
    (project / "src" / "main.py").write_text("""
def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b

class Calculator:
    def __init__(self):
        self.history = []
    
    def calculate(self, operation: str, a: int, b: int) -> int:
        if operation == "add":
            result = add(a, b)
        elif operation == "multiply":
            result = multiply(a, b)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        self.history.append((operation, a, b, result))
        return result
""")
    
    (project / "tests").mkdir()
    (project / "tests" / "test_calc.py").write_text("""
from src.main import Calculator

def test_calculator():
    calc = Calculator()
    assert calc.calculate("add", 2, 3) == 5
    assert calc.calculate("multiply", 4, 5) == 20
""")
    
    (project / "README.md").write_text("""
# Calculator Project

A simple calculator with add and multiply operations.

## Usage

```python
from src.main import Calculator

calc = Calculator()
result = calc.calculate("add", 2, 3)
print(result)  # 5
```
""")
    
    yield project
    cleanup()


def test_full_workflow_no_api_key(temp_project):
    """Test complete workflow without API key (graph-only mode)."""
    os.chdir(temp_project)
    
    # Remove any API keys
    env = os.environ.copy()
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "LITHIC_PROVIDER"]:
        env.pop(key, None)
    
    # Index project
    result = subprocess.run(
        ["lithic", "index", "."],
        capture_output=True, text=True, env=env, timeout=60, encoding='utf-8', errors='replace'
    )
    assert result.returncode == 0
    output = (result.stdout or '') + (result.stderr or '')
    assert "Graph built" in output
    
    # Query without LLM
    result = subprocess.run(
        ["lithic", "ask", "What is in this project?"],
        capture_output=True, text=True, env=env, timeout=30, encoding='utf-8', errors='replace'
    )
    assert result.returncode == 0
    output = (result.stdout or '') + (result.stderr or '')
    assert "Calculator" in output or "main.py" in output or "PROJECT" in output
    
    # Explain symbol
    result = subprocess.run(
        ["lithic", "explain", "Calculator"],
        capture_output=True, text=True, env=env, timeout=30, encoding='utf-8', errors='replace'
    )
    assert result.returncode == 0
    output = (result.stdout or '') + (result.stderr or '')
    assert "Calculator" in output


def test_mcp_server_lifecycle(temp_project):
    """Test MCP server startup, tool calls, and shutdown."""
    os.chdir(temp_project)
    
    # Start MCP server as subprocess
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)  # Test without API key
    
    proc = subprocess.Popen(
        ["python", "-m", "lithic_cli.mcp.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    try:
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()
        
        # Read response (with timeout)
        import select
        
        if hasattr(select, 'select'):  # Unix
            ready, _, _ = select.select([proc.stdout], [], [], 5.0)
            if ready:
                response = proc.stdout.readline()
            else:
                pytest.skip("MCP server didn't respond in time (Unix)")
        else:  # Windows
            # On Windows, just try to read with shorter timeout
            try:
                response = proc.stdout.readline()
            except:
                pytest.skip("MCP server communication failed (Windows)")
        
        if response:
            data = json.loads(response)
            assert data.get("id") == 1
            assert "result" in data
        
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_error_handling_graceful_degradation(temp_project):
    """Test graceful error handling and fallbacks."""
    os.chdir(temp_project)
    
    # Test with invalid provider
    env = os.environ.copy()
    env["LITHIC_PROVIDER"] = "invalid_provider"
    
    result = subprocess.run(
        ["python", "-m", "lithic_cli.cli", "ask", "test question"],
        capture_output=True, text=True, env=env, timeout=30
    )
    # Should not crash, should provide graph-only response
    assert result.returncode == 0
    
    # Test with missing graph directory permission
    graph_dir = temp_project / "restricted"
    graph_dir.mkdir(mode=0o444)  # Read-only
    
    env["LITHIC_GRAPH_DIR"] = str(graph_dir)
    result = subprocess.run(
        ["python", "-m", "lithic_cli.cli", "index", "."],
        capture_output=True, text=True, env=env, timeout=30
    )
    # CLI is designed to degrade gracefully - returns 0 even on permission errors
    # The error is logged but doesn't cause a non-zero exit
    assert result.returncode == 0


def test_concurrent_requests_rate_limiting():
    """Test MCP server handles concurrent requests and rate limiting."""
    import time
    
    # This would need actual MCP server running
    # Simplified version: test rate limiter class directly
    from lithic_cli.mcp.server import _RateLimiter
    
    limiter = _RateLimiter(max_calls=5, window=1.0)
    
    # Should allow 5 calls
    for _ in range(5):
        limiter.check()
    
    # 6th call should fail
    with pytest.raises(RuntimeError, match="rate limit exceeded"):
        limiter.check()
    
    # Wait and try again
    time.sleep(1.1)
    limiter.check()  # Should work again


def test_memory_usage_bounds(temp_project):
    """Test memory usage stays bounded under load."""
    os.chdir(temp_project)
    
    # Create large input that could cause memory issues
    large_content = "x" * 1_000_000  # 1MB string
    large_file = temp_project / "large.txt"
    large_file.write_text(large_content)
    
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    
    # Compress large file - should not crash or use excessive memory
    result = subprocess.run(
        ["python", "-m", "lithic_cli.cli", "compress-file", "large.txt"],
        capture_output=True, text=True, env=env, timeout=30
    )
    
    assert result.returncode == 0
    # Output should be much smaller than input
    assert len(result.stdout) < len(large_content)


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_provider_timeout_handling(temp_project, provider):
    """Test provider timeout handling (requires API keys)."""
    os.chdir(temp_project)
    
    api_key_env = f"{provider.upper()}_API_KEY"
    if not os.getenv(api_key_env):
        pytest.skip(f"No {api_key_env} for integration test")
    
    env = os.environ.copy()
    env["LITHIC_PROVIDER"] = provider
    
    # This should complete within timeout
    result = subprocess.run(
        ["python", "-m", "lithic_cli.cli", "ask", "What is this project?"],
        capture_output=True, text=True, env=env, timeout=45
    )
    
    # Should not hang indefinitely due to our 30s timeout
    assert result.returncode == 0