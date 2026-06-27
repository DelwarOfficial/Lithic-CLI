# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |
| < 0.1   | No        |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report security issues via GitHub's private vulnerability reporting, or email the maintainer directly at delwarnetwork@gmail.com. Please include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge receipt within 48 hours and aim to release a fix within 7 days for critical issues.

## Security Model

Lithic is a **local development tool** that combines graph indexing, compression, and response policies. It runs as a CLI tool and optionally as a local MCP stdio server.

### Threat Surface

| Vector | Mitigation |
|--------|------------|
| **Path traversal** | `validate_graph_path()` resolves paths and requires them to be inside `graphify-out/` |
| **XSS in graph HTML output** | `sanitize_label()` strips control characters, caps at 256 chars, and HTML-escapes labels |
| **Prompt injection** | User-controlled content is sanitized before being passed to LLM contexts |
| **Command injection** | Input is sanitized for shell metacharacters before subprocess calls |
| **YAML injection** | `_yaml_str()` escapes special characters before embedding in YAML |
| **Symlink traversal** | `os.walk(..., followlinks=False)` is used throughout |
| **Corrupted graph.json** | `_load_graph()` wraps `json.JSONDecodeError` with recovery message |

### What Lithic Does NOT Do

- Does not run a network listener (MCP server communicates over stdio only)
- Does not execute arbitrary code from source files
- Does not use `shell=True` in any subprocess call
- Does not store credentials or API keys

## Best Practices for Users

1. **Keep Lithic updated** - Always use the latest version for security fixes
2. **Review graph output** - Always review generated HTML before sharing
3. **Use virtual environments** - Isolate dependencies to reduce supply chain risks
4. **Validate URLs** - When using `ingest`, ensure URLs are from trusted sources

## Security Contact

For security concerns, email delwarnetwork@gmail.com or use GitHub's private vulnerability reporting.
