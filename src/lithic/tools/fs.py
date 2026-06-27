"""Filesystem helpers."""

from __future__ import annotations

from pathlib import Path


def resolve_path_within_root(root: Path, candidate: Path | str) -> Path:
    """Resolve a path and ensure it stays inside the given root."""
    candidate_path = Path(candidate)
    if candidate_path.is_absolute():
        base = candidate_path
    else:
        base = root / candidate_path
    resolved = base.resolve()
    if base.is_symlink():
        target = base.readlink()
        if not target.is_absolute():
            target = (base.parent / target).resolve()
        else:
            target = target.resolve()
        resolved = target
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path must stay inside project root: {resolved}") from exc
    return resolved


def read_text(path: Path, max_chars: int = 12000) -> str:
    """Read text with truncation for large files."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text if len(text) <= max_chars else text[:max_chars] + "\n... [truncated] ..."
