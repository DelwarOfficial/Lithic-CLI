"""Check pinned upstream submodules against their remotes."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class UpstreamStatus:
    name: str
    status: str
    local_path: str
    repo: str
    branch: str
    version: str
    pinned_commit: str
    local_commit: str
    remote_commit: str
    error: str = ""


class UpstreamChecker:
    def __init__(self, project_root: Path, lock_file: Path | None = None):
        self.project_root = project_root.resolve()
        self.lock_file = lock_file or self.project_root / "upstream.lock.yml"

    def check(self, *, remote: bool = True) -> list[UpstreamStatus]:
        if not self.lock_file.exists():
            return []
        try:
            raw = self.lock_file.read_text(encoding="utf-8")
        except OSError:
            return []
        try:
            data = yaml.safe_load(raw) or {}
        except yaml.YAMLError:
            return []
        projects = data.get("projects", {})
        if not isinstance(projects, dict):
            return []
        return [self._check_project(name, entry, remote=remote) for name, entry in projects.items()]

    def _check_project(
        self, name: str, entry: dict[str, Any], *, remote: bool
    ) -> UpstreamStatus:
        local_path = str(entry.get("local_path", ""))
        repo = str(entry.get("repo", ""))
        branch = str(entry.get("branch", "HEAD"))
        version = str(entry.get("version", ""))
        pinned = str(entry.get("commit", ""))
        path = self._resolve_local_path(local_path)
        try:
            local_commit = self._git(["-C", str(path), "rev-parse", "HEAD"])
            remote_commit = self._remote_commit(repo, branch) if remote and repo else ""
            status = self._status(pinned, local_commit, remote_commit)
            return UpstreamStatus(
                name=name,
                status=status,
                local_path=local_path,
                repo=repo,
                branch=branch,
                version=version,
                pinned_commit=pinned,
                local_commit=local_commit,
                remote_commit=remote_commit,
            )
        except RuntimeError as exc:
            return UpstreamStatus(
                name=name,
                status="error",
                local_path=local_path,
                repo=repo,
                branch=branch,
                version=version,
                pinned_commit=pinned,
                local_commit="",
                remote_commit="",
                error=str(exc),
            )

    def _resolve_local_path(self, local_path: str) -> Path:
        path = Path(local_path)
        if not path.is_absolute():
            path = self.project_root / path
        resolved = path.resolve()
        try:
            resolved.relative_to(self.project_root)
        except ValueError as exc:
            raise RuntimeError(f"local_path must stay inside project root: {local_path}") from exc
        return resolved

    def _remote_commit(self, repo: str, branch: str) -> str:
        ref = "HEAD" if branch == "HEAD" else f"refs/heads/{branch}"
        output = self._git(["ls-remote", repo, ref])
        first = output.splitlines()[0] if output else ""
        return first.split()[0] if first else ""

    @staticmethod
    def _status(pinned: str, local_commit: str, remote_commit: str) -> str:
        if pinned and local_commit != pinned:
            return "local-drift"
        if remote_commit and local_commit != remote_commit:
            return "update-available"
        return "up-to-date"

    @staticmethod
    def _git(args: list[str]) -> str:
        result = subprocess.run(
            ["git", *args],
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "git command failed").strip()
            raise RuntimeError(detail)
        return result.stdout.strip()
