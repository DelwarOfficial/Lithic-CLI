---
name: lithic
description: >
  Graph-first codebase intelligence via Lithic CLI. Use when the user says "lithic",
  "/lithic", "use lithic", "graph-first", or wants codebase understanding via architecture
  graph instead of raw file reading. Also use for compressing large output, generating commit
  messages, and reviewing diffs with graph context.
---

## Activation

Persistent. Active every turn after `/lithic`. Off only: "stop lithic" or "normal mode".

## Core Principle

Graph first, file second. Before exploring code by reading files, query the architecture graph.
This saves tokens and gives structural context that raw file reads miss.

## Workflow

All commands use `uv run lithic` prefix.

1. **First activation**: Run `uv run lithic index .` to build/refresh the graph.
2. **Before broad questions**: Use `uv run lithic ask "<question>"` — graph-guided Q&A.
3. **Before explaining concepts**: Use `uv run lithic explain "<symbol|module|file>"`.
4. **Before finding connections**: Use `uv run lithic path <source> <target>`.
5. **Before large edits**: Use `uv run lithic edit "<task description>"` for read-only orientation.
6. **For diff review**: Run `uv run lithic review` — compressed, severity-ranked findings.
7. **For commit messages**: Run `uv run lithic commit` — Conventional Commits from staged/working changes.
8. **For large files**: Run `uv run lithic compress-file <path>` to compress before analysis.

## Command Reference

All commands require `uv run` prefix (project uses uv as package manager).

| Task | Command |
|------|---------|
| Build graph | `uv run lithic index .` or `uv run lithic index <path>` |
| Ask question | `uv run lithic ask "how does auth work?"` |
| Explain concept | `uv run lithic explain "Orchestrator"` |
| Trace path | `uv run lithic path AuthService UserService` |
| Orient for edit | `uv run lithic edit "add rate limiting to API"` |
| Review diff | `uv run lithic review` |
| Generate commit | `uv run lithic commit` |
| Compress file | `uv run lithic compress-file output.log` |
| Check stats | `uv run lithic stats` |
| MCP server | `uv run lithic mcp serve` |

## Rules

- Run `uv run lithic index .` if graph is stale or doesn't exist. Check `uv run lithic stats` first if unsure.
- Prefer `uv run lithic ask` over raw `grep`/`read_file` for architecture-level questions.
- Use `uv run lithic edit` before implementing changes that span multiple files.
- Use `uv run lithic review` before committing — severity-ranked findings catch issues.
- Use `uv run lithic commit` for commit messages — follows Conventional Commits.
- For code-level details (exact line numbers, specific variable names), combine graph context with targeted file reads.
- Lithic supplements, not replaces, direct file access. Use both.

## When NOT to Use Lithic

- Single-file, small changes where you already know the file path.
- Exact string search or regex — use `grep` directly.
- File contents you already have in context.

## Integration with Other Skills

- Combine with `/caveman` for compressed graph-first responses.
- `lithic review` output pairs well with caveman's terse format.
- `lithic commit` generates proper Conventional Commits regardless of communication style.
