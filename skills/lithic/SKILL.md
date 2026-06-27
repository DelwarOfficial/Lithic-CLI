---
name: lithic
description: >
  Graph-first + caveman full terse. Use /lithic, "lithic", "use lithic" to instantly activate
  graph-first codebase intelligence with full caveman-style output. Use for architecture graph,
  compress, review, commit. Triggers on /lithic for instant caveman + lithic mode.
---

## Activation

Persistent. /lithic instantly activates lithic graph-first + caveman full terse. Active every response. 
Follow full caveman rules: drop articles/fillers/pleasantries. Fragments OK. Short synonyms. 
Preserve code, paths, errors exact. Off only: "stop lithic" or "normal mode".

## Core Principle

Graph first, file second. Caveman full terse output. Before broad reads: query graph. Use `uv run lithic` tools for questions. Terse. Exact technical.

## Response Rules (caveman full)

Drop: articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries, hedging.
Fragments OK. Short synonyms. Code blocks, paths, errors unchanged.
Pattern: [thing] [action] [reason]. [next].
Use `uv run lithic` for all graph, ask, review actions.

## Workflow

1. Index first if needed: `uv run lithic index .`
2. Ask: `uv run lithic ask "<q>"`
3. Explain: `uv run lithic explain "<thing>"`
4. Path: `uv run lithic path <a> <b>`
5. Edit orient: `uv run lithic edit "<task>"`
6. Review: `uv run lithic review`
7. Commit: `uv run lithic commit`
8. Compress: `uv run lithic compress-file <path>`

## Command Reference

All via `uv run lithic <cmd>`. Use when agent needs graph or project cmds.

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

- Always follow Response Rules (caveman full) for final output.
- Run `uv run lithic index .` if graph stale. Check stats first.
- Prefer `uv run lithic ask` for architecture questions.
- Use `uv run lithic edit` before multi-file edits.
- Use `uv run lithic review` / `commit` before commit.
- Lithic + direct reads together. Graph first for broad.

## When NOT to Use Lithic

- Single-file, small changes where you already know the file path.
- Exact string search or regex — use `grep` directly.
- File contents you already have in context.

## Integration with Other Skills

- /lithic alone = graph-first + full caveman terse. No need separate /caveman.
- `lithic review` + `lithic commit` use built-in terse + conventional formats.
- Combine further only if extra modes wanted.
