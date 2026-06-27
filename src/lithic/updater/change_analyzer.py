"""Change analyzer for update workflow."""

from __future__ import annotations

from pathlib import Path


class ChangeAnalyzer:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def analyze_diff(self, diff_text: str) -> dict[str, int | list[str]]:
        lines = diff_text.splitlines()
        files_changed: list[str] = []
        additions = 0
        deletions = 0
        for line in lines:
            if line.startswith("+++ b/"):
                files_changed.append(line[6:])
            elif line.startswith("---"):
                continue
            elif line.startswith("+"):
                additions += 1
            elif line.startswith("-"):
                deletions += 1
        return {
            "files_changed": files_changed,
            "additions": additions,
            "deletions": deletions,
            "total_lines": len(lines),
        }
