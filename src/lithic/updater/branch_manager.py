"""Branch manager for update workflow."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_BRANCH_RE = re.compile(r"^[a-zA-Z0-9_/.-]+$")
_MAX_BRANCH = 255


class BranchManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    @staticmethod
    def _validate_branch_name(name: str) -> None:
        if not name or len(name) > _MAX_BRANCH:
            raise ValueError(f"branch name length must be 1-{_MAX_BRANCH}")
        if not _BRANCH_RE.match(name):
            raise ValueError(
                f"branch name contains invalid chars: {name!r} "
                f"(allowed: a-z, A-Z, 0-9, _, /, ., -)"
            )
        if name.startswith("-") or name.endswith(".") or ".." in name or ".lock" in name:
            raise ValueError(f"branch name has invalid pattern: {name!r}")

    def create_branch(self, branch_name: str, timeout: int = 30) -> str:
        self._validate_branch_name(branch_name)
        try:
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.project_root,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"git checkout timed out after {timeout}s") from exc
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()

    def current_branch(self, timeout: int = 10) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"git rev-parse timed out after {timeout}s") from exc
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()
