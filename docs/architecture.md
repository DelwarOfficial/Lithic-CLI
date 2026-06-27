# Architecture

Lithic has three independent layers:

- **Graph layer**: `GraphService` wraps `GraphifyAdapter`, which shells out to the Graphify CLI and stores output under `graphify-out/graph.json`. Provides `query()`, `explain()`, `path_between()`, `build_graph()`.
- **Compression layer**: `HeadroomAdapter` uses Headroom when installed and otherwise uses deterministic fallback compression that preserves errors, paths, commands, stack traces, and code blocks. Result cached via LRU.
- **Response policy layer**: `ResponsePolicy` shapes output into normal, concise, caveman-lite/full/ultra, review, commit, and safety-clear modes.

`Orchestrator` wires the three layers plus `LLMService`. Graph-first: questions call Graphify before raw file access. When `LITHIC_PROVIDER` (or `--provider`) is set, `ask()`/`explain()` enhance graph output with an LLM call.

## Module map

| Path | Role |
|------|------|
| `lithic/cli.py` | Click CLI — command definitions, global flags |
| `lithic/orchestrator.py` | Orchestrator — wires graph + LLM + compression + policy |
| `lithic/graph/service.py` | GraphService — delegates to GraphifyAdapter |
| `lithic/graph/graphify_adapter.py` | Subprocess wrapper around `graphify` CLI |
| `lithic/compression/headroom_adapter.py` | Compression adapter with Headroom or fallback |
| `lithic/policy/response_policy.py` | Output shaping — risk detection, commit, review, conciseness |
| `lithic/providers/service.py` | LLMService — provider map, factory, completion |
| `lithic/providers/*.py` | Provider wrappers (OpenAI, Anthropic, Ollama, OpenRouter) |
| `lithic/tools/shell.py` | Safe subprocess runner with destructive-command detection |
| `lithic/tools/audit.py` | JSON audit logging with secret redaction |
| `lithic/tools/fs.py` | Path safety — `resolve_path_within_root()` |
| `lithic/mcp/server.py` | MCP stdio server — exposes graph, compress, review, commit tools |
| `lithic/config.py` | `AgentConfig` — env-driven configuration |
| `lithic/updater/` | Upstream pin validation |

## Data flow

```
User (CLI or MCP)
  │
  ▼
  Orchestrator ──► GraphService ──► GraphifyAdapter ──► graphify CLI
      │                                                      │
      │              ┌── Provider available? ──► LLMService ◄─┘
      │              │
      ▼              ▼
  HeadroomAdapter ──► ResponsePolicy ──► shaped output
```

## Safety model

- Subprocess commands use list form (no `shell=True`).
- `resolve_path_within_root()` constrains file access to project root.
- `_reset_output_dir()` only cleans dedicated, marked graph output directories.
- `_rmtree_safe()` checks symlinks immediately before each deletion.
- Destructive shell commands blocked via structured command rules.
- MCP rate-limited (60 req/60s, configurable via `LITHIC_MCP_*` env vars).
- Audit logs redact API keys, tokens, and secrets before writing.
- MCP errors return sanitized messages; details logged separately.

## Security boundaries

| Boundary | Mechanism |
|----------|-----------|
| Filesystem | `resolve_path_within_root()`, `_safe_target()` |
| Graph output | `_reset_output_dir()` guard, symlink check |
| Subprocess | List-form calls, destructive-command filter |
| LLM providers | Environment-variable API keys, optional libs |
| MCP | Input size caps, rate limiter, sanitized errors |
| Audit | Secret redaction before log write |

## Not yet implemented

- Reversible decompress API
- IDE plugin packaging
- Autonomous edit execution
- Network-mode MCP transport (stdio only)
