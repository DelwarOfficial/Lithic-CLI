"""Shell helpers."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from lithic.tools.audit import subprocess as audit_subprocess


class CommandError(RuntimeError):
    """Raised when a shell command fails, times out, or is destructive."""

_DANGEROUS_PYTHON_KEYWORDS = {"shutil", "rmtree", "os.remove", "os.unlink", "send2trash"}


def _is_destructive(command: list[str]) -> bool:
    if not command:
        return False
    cmd0 = os.path.splitext(os.path.basename(command[0]).lower())[0]
    args_lower = [a.lower() for a in command[1:]]
    joined = " ".join(args_lower)
    if cmd0 == "rm":
        return any(
            arg in {"-r", "-rf", "-fr", "--recursive"}
            or (arg.startswith("-") and "r" in arg.replace("-", ""))
            for arg in args_lower
        )
    if cmd0 in {"rmdir", "rd"}:
        return any(arg == "/s" for arg in args_lower)
    if cmd0 == "del":
        return any(arg in {"/s", "/f", "/q"} for arg in args_lower)
    if cmd0 in {"deltree", "remove-item", "truncate"}:
        return True
    if cmd0 == "git":
        subcommand = args_lower[0] if args_lower else ""
        if subcommand in {"reset", "clean"}:
            return True
        if subcommand == "checkout" and "--" in args_lower:
            return True
        if subcommand == "branch" and any(arg == "-d" for arg in args_lower):
            return True
        if subcommand == "push" and any(
            arg in {"--force", "--force-with-lease", "-f"} for arg in args_lower
        ):
            return True
    if cmd0 == "drop" and any(arg in {"table", "database"} for arg in args_lower):
        return True
    if cmd0 == "format" and "volume" in args_lower:
        return True
    if cmd0 == "fsutil" and "file setzerodata" in joined:
        return True
    if cmd0 == "copy" and "nul" in args_lower:
        return True
    if cmd0 in {"cmd", "powershell", "pwsh"}:
        if any(term in joined for term in (" del ", " rd ", " rmdir ", "remove-item")):
            return True
    if cmd0 in {"python", "python3", "uv"}:
        if any(kw in joined for kw in _DANGEROUS_PYTHON_KEYWORDS):
            return True
    return False


def run(command: list[str], cwd: Path, timeout: int = 60) -> str:
    """Run a shell command safely using subprocess list form."""
    if _is_destructive(command):
        rendered = " ".join(command)
        raise CommandError(f"refusing destructive command: {rendered}")
    start = time.monotonic()
    try:
        result = subprocess.run(
            command, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - start
        audit_subprocess(command, -1, elapsed, f"timed out after {timeout}s")
        raise CommandError(f"command timed out after {timeout}s: {' '.join(command)}") from exc
    elapsed = time.monotonic() - start
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    if result.returncode != 0:
        audit_subprocess(command, result.returncode, elapsed, output[:500])
        msg = (output[:2000] + "...") if len(output) > 2000 else (output or "command failed")
        raise CommandError(msg)
    audit_subprocess(command, result.returncode, elapsed)
    return output
