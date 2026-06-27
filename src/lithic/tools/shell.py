"""Shell helpers."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from lithic.tools.audit import subprocess as audit_subprocess

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
    cmd0 = os.path.basename(command[0]).lower()
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
    start = time.monotonic()
    try:
        result = subprocess.run(
            command, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - start
        audit_subprocess(command, -1, elapsed, f"timed out after {timeout}s")
        raise RuntimeError(f"command timed out after {timeout}s: {' '.join(command)}") from exc
    elapsed = time.monotonic() - start
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    if result.returncode != 0:
        audit_subprocess(command, result.returncode, elapsed, output[:500])
        raise RuntimeError(output or "command failed")
    audit_subprocess(command, result.returncode, elapsed)
    return output
