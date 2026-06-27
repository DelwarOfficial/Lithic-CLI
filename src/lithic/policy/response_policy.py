"""Response shaping policies adapted from Caveman behavior."""

from __future__ import annotations

import re

RISKY_RE = re.compile(
    r"(?i)\b("
    r"rm -rf|del /s|git reset --hard|git clean -fd|drop table|delete\s+from|migration|truncate"
    r"|remove-item|drop database|format volume"
    r")\b"
)
CODE_OR_COMMAND_RE = re.compile(r"(```.*?```|`[^`]+`)", re.DOTALL)


class ResponsePolicy:
    """Shape final responses for different modes and risk levels."""

    modes = {
        "normal",
        "concise",
        "caveman_lite",
        "caveman_full",
        "caveman_ultra",
        "review",
        "commit",
        "safety_clear",
    }

    def detect_risk(self, content: str) -> str:
        """Classify response risk from text content."""
        if RISKY_RE.search(content):
            return "high"
        if re.search(r"(?i)\b(security|token|secret|permission|credentials|sudo)\b", content):
            return "medium"
        return "normal"

    def shape(self, content: str, mode: str = "concise", risk_level: str = "normal") -> str:
        """Apply the requested response mode with safety overrides."""
        if mode not in self.modes:
            raise ValueError(f"unknown response mode: {mode}")
        if risk_level == "high" or self.detect_risk(content) == "high":
            mode = "safety_clear"
        if mode == "normal":
            return content
        if mode == "commit":
            return self.format_commit(content)
        if mode == "review":
            return self.format_review(content)
        if mode == "safety_clear":
            return self._safety(content)
        return self._concise(content, ultra=mode == "caveman_ultra", full=mode == "caveman_full")

    _COMMIT_TYPE_RE = re.compile(
        r"^(fix|feat|chore|docs|refactor|test|style|perf|ci|build|revert)[\s(:]"
    )

    def format_commit(self, content: str) -> str:
        """Generate a conventional commit subject."""
        first = next(
            (line for line in content.splitlines() if line.strip()),
            "update code",
        )
        first = first.lstrip("- *").strip()
        match = self._COMMIT_TYPE_RE.match(first)
        if match:
            prefix = match.group(1)
            first = first[match.end() :].lstrip(": ").strip()
        else:
            first = re.sub(r"^(changed|updated|fixed|added)\s+", "", first, flags=re.I)
            prefix = "fix"
        subject = f"{prefix}: {first[:40].strip()}".lower().rstrip(".")
        return subject

    def format_review(self, content: str) -> str:
        """Generate actionable review findings."""
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            return "No actionable findings."
        findings = []
        for line in lines[:8]:
            severity = "medium" if re.search(r"bug|error|fail|risk|unsafe", line, re.I) else "low"
            findings.append(f"- {severity}: {line}")
        return "\n".join(findings)

    def _concise(self, content: str, *, ultra: bool = False, full: bool = False) -> str:
        parts = CODE_OR_COMMAND_RE.split(content)
        shaped: list[str] = []
        drop = {"basically", "actually", "really", "simply", "just", "sure", "certainly"}
        for part in parts:
            if not part or part.startswith("`"):
                shaped.append(part)
                continue
            text = " ".join(word for word in part.split() if word.lower().strip(".,") not in drop)
            if full or ultra:
                text = re.sub(r"\b(the|a|an)\b\s*", "", text, flags=re.I)
            if ultra:
                text = re.sub(
                    r"\bbecause\b", "->",
                    re.sub(
                        r"\bconfiguration\b", "config",
                        re.sub(
                            r"\bimplementation\b", "impl",
                            re.sub(
                                r"\brequest\b", "req",
                                re.sub(r"\bresponse\b", "res", text, flags=re.I),
                                flags=re.I,
                            ),
                            flags=re.I,
                        ),
                        flags=re.I,
                    ),
                    flags=re.I,
                )
            shaped.append(text)
        return "".join(shaped).strip()

    def _safety(self, content: str) -> str:
        return (
            "Safety note: this may be destructive or high-risk. "
            "Review the command, confirm backups, and run only after explicit approval.\n\n"
            + content
        )
