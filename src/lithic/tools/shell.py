"""Shell helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

_DESTRUCTIVE_RULES: set[tuple[str, str]] = {
    ("rm", "-rf"),
    ("rm", "-r"),
    ("rm", "-fr"),
    ("rmdir", "/s"),
    ("del", "/s"),
    ("del", "/f"),
    ("git", "reset"),
    ("git", "clean"),
    ("drop", "table"),
    ("drop", "database"),
    ("format", "volume"),
    ("remove-item", ""),
    ("truncate", ""),
}


def _is_destructive(command: list[str]) -> bool:
    if not command:
        return False
    cmd0 = command[0].lower()
    args_lower = [a.lower() for a in command[1:]]
    for base, flag in _DESTRUCTIVE_RULES:
        if cmd0 == base:
            if not flag:
                return True
            if any(flag in arg for arg in args_lower):
                return True
    return False


def run(command: list[str], cwd: Path, timeout: int = 60) -> str:
    """Run a shell command safely using subprocess list form."""
    if _is_destructive(command):
        raise ValueError(f"refusing destructive command without confirmation: {' '.join(command)}")
    try:
        result = subprocess.run(
            command, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"command timed out after {timeout}s: {' '.join(command)}") from exc
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    if result.returncode != 0:
        raise RuntimeError(output or "command failed")
    return output
