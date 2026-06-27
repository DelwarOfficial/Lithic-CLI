"""Risk scanner for update workflow."""

from __future__ import annotations

import logging
import re
from pathlib import Path

_LOG = logging.getLogger(__name__)

HIGH_RISK_PATTERNS: list[re.Pattern] = [
    re.compile(r"install\.sh"),
    re.compile(r"(git\s+)?hooks?"),
    re.compile(r"mcp\s*(server|config|setup)"),
    re.compile(r"subprocess\.(run|Popen|call|check)"),
    re.compile(r"os\.system"),
    re.compile(r"shutil\.(rmtree|move)"),
]


class RiskScanner:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def scan_file(self, file_path: Path) -> list[dict[str, str]]:
        if not file_path.exists():
            return []
        findings: list[dict[str, str]] = []
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(text.splitlines(), 1):
                for pattern in HIGH_RISK_PATTERNS:
                    if pattern.search(line):
                        findings.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "line": str(i),
                            "pattern": pattern.pattern,
                            "content": line.strip(),
                        })
        except PermissionError:
            _LOG.warning("permission denied reading %s", file_path)
        except UnicodeDecodeError:
            _LOG.warning("encoding error reading %s", file_path)
        except OSError as exc:
            _LOG.warning("error reading %s: %s", file_path, exc)
        return findings

    def scan_directory(self, directory: Path | None = None) -> list[dict[str, str]]:
        root = directory or self.project_root
        all_findings: list[dict[str, str]] = []
        allowed = {".py", ".sh", ".ps1", ".yaml", ".yml", ".json", ".toml", ".cfg", ".conf"}
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in allowed:
                all_findings.extend(self.scan_file(path))
        return all_findings
