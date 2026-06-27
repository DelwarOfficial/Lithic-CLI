<div align="center">

```
██████╗ ██╗     ██╗████████╗██╗  ██╗██╗ ██████╗    ██████╗██╗     ██╗
██╔════╝██║     ██║╚══██╔══╝██║  ██║██║██╔════╝   ██╔════╝██║     ██║
██║     ██║     ██║   ██║   ███████║██║██║        ██║     ██║     ██║
██║     ██║     ██║   ██║   ██╔══██║██║██║        ██║     ██║     ██║
╚██████╗███████╗██║   ██║   ██║  ██║██║╚██████╗   ╚██████╗███████╗██║
 ╚═════╝╚══════╝╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝    ╚═════╝╚══════╝╚═╝
```

# 🪨 Lithic-CLI

**Graph-first codebase intelligence for AI coding agents**

<p>
  <strong>Cut context cost 80% · Index any repo · Ask architecture questions</strong>
</p>

<p>
  <a href="https://github.com/DelwarOfficial/Lithic-CLI"><img src="https://img.shields.io/github/stars/DelwarOfficial/Lithic-CLI?style=flat&color=yellow" alt="Stars"></a>
  <a href="https://github.com/DelwarOfficial/Lithic-CLI/commits/main"><img src="https://img.shields.io/github/last-commit/DelwarOfficial/Lithic-CLI?style=flat" alt="Last Commit"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/DelwarOfficial/Lithic-CLI?style=flat" alt="License"></a>
  <a href="https://pypi.org/project/lithic-cli/"><img src="https://img.shields.io/badge/pypi-Coming%20Soon-blue" alt="PyPI"></a>
</p>

<p>
  <a href="#-quick-start"><strong>🚀 Quick Start</strong></a> ·
  <a href="#-installation"><strong>📦 Install</strong></a> ·
  <a href="#-cli-commands"><strong>⚡ Commands</strong></a> ·
  <a href="#-mcp-integration"><strong>🔌 MCP</strong></a> ·
  <a href="#-architecture"><strong>🧠 Architecture</strong></a>
</p>

</div>

---

AI agents waste tokens reading your entire codebase. Lithic builds a live architecture graph first, so agents understand structure, find relevant code, and answer questions without dumping everything into context.

```
┌─────────────────────────────────────────────────────────────────┐
│  📂 Your Codebase  →  🕸️ Graph Index  →  🧠 AI Agent        │
│                     (80% fewer tokens)                         │
└─────────────────────────────────────────────────────────────────┘
```

<strong>🔑 Key Benefits</strong>

- ⚡ **80% token reduction** — compress large tool outputs and code context
- 🕸️ **Graph-first understanding** — know architecture, not just files
- 🔌 **MCP server included** — plug directly into Claude Desktop, Cursor, and more
- 🧩 **Multi-provider ready** — OpenAI, Anthropic, OpenRouter, Ollama

---

## 🚀 What It Does

| Command | Purpose |
|---------|---------|
| `lithic index .` | Scan a repository into a queryable architecture graph |
| `lithic ask "..."` | Question the graph about structure, dependencies, design |
| `lithic explain "..."` | Explain any symbol, module, or file with graph context |
| `lithic compress-file <file>` | Strip noise from tool output, logs, and diffs (up to 80% fewer tokens) |
| `lithic review` | Concise diff review without the full context dump |
| `lithic commit` | Generate Conventional Commit messages from staged changes |
| `lithic upstream-status` | Check pinned Graphify, Headroom, and Caveman submodules |

---

## 🖥️ Platform Guidelines

### 🍏 Mac Users

#### Installation

```bash
# Install via git clone (see setup below)
# pip install lithic-cli (planned)
# brew install lithic-cli (planned)
```

#### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open terminal | `Cmd + Space` → type "Terminal" |
| Clear screen | `Cmd + K` |
| Cancel running command | `Ctrl + C` |
| Path autocomplete | `Tab` key |
| Command history | `↑` / `↓` arrow keys |

#### Common Issues & Fixes

- **Python version**: Ensure Python 3.12+ is installed (`python3 --version`)
- **Permission denied**: Use `sudo` with caution, or install with `--user` flag
- **Virtual environment**: Recommended to avoid dependency conflicts

```bash
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
uv sync
```

### 🪟 Windows Users

#### Installation

```powershell
# Install via git clone (see setup below)
# pip install lithic-cli (planned)
```

#### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open terminal | `Win + R` → type "cmd" or "powershell" |
| Clear screen | `cls` (CMD) or `Clear-Host` (PowerShell) |
| Cancel running command | `Ctrl + C` |
| Path autocomplete | `Tab` key |
| Command history | `↑` / `↓` arrow keys |

#### Common Issues & Fixes

- **Python path**: Ensure Python is in your PATH environment variable
- **Long paths**: Enable long path support in Windows (registry or group policy)
- **Virtual environment**: Use PowerShell for best experience

```powershell
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
uv sync
```

### 🔧 Universal Guidelines

#### Prerequisites

- [ ] Python 3.12+ installed
- [ ] [uv](https://docs.astral.sh/uv/) installed (`pip install uv` or `winget install astral.uv`)
- [ ] Internet connection for first-time install

#### Troubleshooting

1. **Command not found**: Check if Python scripts directory is in PATH
2. **Permission errors**: Install with `--user` flag or use virtual environment
3. **Graph generation fails**: Ensure working directory has read/write access

---

## ✨ Features

- 🕸️ **Graph-powered indexing** — Build and refresh a project knowledge graph
- 💬 **Natural language queries** — Ask architecture and codebase questions
- 🔍 **Symbol explanation** — Explain symbols, files, modules, and relationships
- 🧩 **Path finding** — Find graph paths between concepts
- 📦 **Smart compression** — Compress large file, shell, log, and diff output safely
- 📝 **Review generation** — Generate concise review output
- 💾 **Commit messages** — Generate Conventional Commit-style commit messages
- 🔌 **MCP server** — Expose core capabilities over Model Context Protocol
- 🧠 **Multi-provider** — Support for OpenAI, Anthropic, OpenRouter, and Ollama

---

## 🧠 Architecture

Lithic is organized into three primary runtime layers coordinated by an orchestrator:

```mermaid
graph TB
    subgraph User["👤 User"]
        CLI["CLI / MCP"]
    end

    subgraph Orchestrator["🧠 Orchestrator (graph-first)"]
        direction TB
        Router["Route: graph context first"]
        Fallback["Fallback: narrower reads"]
    end

    subgraph Layers["📦 Runtime Layers"]
        Graph["Graph Layer<br/><code>graphify_adapter</code>"]
        Compression["Compression Layer<br/><code>headroom_adapter</code>"]
        Policy["Policy Layer<br/><code>response_policy</code>"]
    end

    subgraph Output["📤 Output"]
        Response["Concise Engineering Output"]
    end

    User --> Orchestrator
    Orchestrator --> Graph
    Orchestrator --> Compression
    Orchestrator --> Policy
    Graph --> Output
    Compression --> Output
    Policy --> Output

    Graph -.->|"Graphify-inspired"| Graphify["Graphify"]
    Compression -.->|"Headroom-inspired"| Headroom["Headroom"]
    Policy -.->|"Caveman-inspired"| Caveman["Caveman"]

    style Graph fill:#dbeafe,stroke:#1e40af,color:#1e3a8a
    style Compression fill:#fef3c7,stroke:#b45309,color:#92400e
    style Policy fill:#f3e8ff,stroke:#7e22ce,color:#6b21a8
    style Orchestrator fill:#dcfce7,stroke:#166534,color:#14532d
    style User fill:#f8fafc,stroke:#475569,color:#1e293b
    style Output fill:#f8fafc,stroke:#475569,color:#1e293b
    style Graphify fill:#f1f5f9,stroke:#64748b,color:#475569
    style Headroom fill:#f1f5f9,stroke:#64748b,color:#475569
    style Caveman fill:#f1f5f9,stroke:#64748b,color:#475569
```

### Layer Responsibilities

| Layer | Module | Purpose |
|-------|--------|---------|
| **Graph** | `lithic.graph.graphify_adapter` | Codebase indexing, architecture mapping, graph-guided exploration |
| **Compression** | `lithic.compression.headroom_adapter` | Deterministic compression for large tool output, logs, JSON, and file reads |
| **Policy** | `lithic.policy.response_policy` | Mode-aware response shaping for review, commit, and concise workflows |

### Data Flow

1. **User input** enters via CLI or MCP
2. **Orchestrator** routes requests **graph-first**
3. **Graph layer** provides architectural context
4. **Compression layer** reduces token usage
5. **Policy layer** shapes the final response
6. **Concise output** is returned to the user

These layers are coordinated by `lithic.orchestrator`, which is intentionally **graph-first**. Broad codebase questions are routed through graph context before narrower reads or downstream actions.

---

## 🔗 Resources

- 📂 [GitHub Repository](https://github.com/DelwarOfficial/Lithic-CLI)
- 🐛 [Issues](https://github.com/DelwarOfficial/Lithic-CLI/issues)
- 📖 [Docs](docs/architecture.md)

---

## 📄 License

MIT

---

> **Need help?** Provide your OS version and the exact error message for faster support.

More architecture details are available in [`docs/architecture.md`](docs/architecture.md).

---

## 📦 Installation

### 📋 Requirements

- 🐍 Python 3.12+
- ⚡ [uv](https://github.com/astral-sh/uv) — Fast Python package installer
- 🖥️ A shell environment (PowerShell, Terminal, or Bash)

### 🚀 Install

**Recommended (uv):**

```powershell
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
uv sync
```

**Alternative (pip):**

```powershell
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
pip install -e .
```

### Optional Headroom extra

```powershell
uv sync --extra headroom
```

On Windows, `headroom-ai` may require [Rust/MSVC build tools](https://rustup.rs/) when a pre-built wheel is unavailable. Lithic works without this extra by falling back to its built-in deterministic compressor.

On some Windows environments, `headroom-ai` may require Rust/MSVC build tooling when a compatible wheel is unavailable. Lithic still works without that extra by falling back to its built-in deterministic compressor.

---

## 🏃 Quick Start

```bash
# 1. Index your codebase
uv run lithic index .

# 2. Ask an architecture question
uv run lithic ask "explain this project architecture"

# 3. Explain any symbol
uv run lithic explain "GraphifyAdapter"

# 4. Find relationships between concepts
uv run lithic path "GraphifyAdapter" "HeadroomAdapter"

# 5. Compress large files (80% fewer tokens)
uv run lithic compress-file README.md

# 6. Review your changes concisely
uv run lithic review

# 7. Generate a commit message
uv run lithic commit

# 8. Start the MCP server for AI agents
uv run lithic mcp serve
```

## CLI Commands

All commands are optimized for minimal token usage (~0.1-3K per call, compression reduces 60-90%).

| Command | Purpose |
| --- | --- |
| `lithic index .` | Build or refresh the project graph |
| `lithic ask "..."` | Ask a graph-guided codebase question |
| `lithic explain "..."` | Explain a symbol, file, module, or concept |
| `lithic path "A" "B"` | Find a graph relationship path |
| `lithic edit "..."` | Orient an edit task without mutating files |
| `lithic review` | Produce concise review findings from the current diff |
| `lithic commit` | Generate a Conventional Commit-style subject |
| `lithic compress-file <file>` | Compress large text output safely |
| `lithic stats` | Show graph and compression runtime stats |
| `lithic upstream-status` | Check pinned upstream submodules against their remotes |
| `lithic mcp serve` | Serve Lithic MCP tools over stdio |

## MCP Integration

Lithic exposes its core capabilities as an MCP (Model Context Protocol) server, allowing Claude Desktop, Cursor, and other MCP clients to access graph-indexing and compression tools directly.

### Claude Desktop Setup

Add the following to your Claude Desktop MCP configuration file (`mcp_config.json` or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "lithic": {
      "command": "uv",
      "args": ["run", "lithic", "mcp", "serve"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

Or use the direct pip installation path:

```json
{
  "mcpServers": {
    "lithic": {
      "command": "lithic",
      "args": ["mcp", "serve"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### Available MCP Tools

Once connected, Claude can use Lithic tools directly:

- **`index_graph`** — Build or refresh a project graph
- **`ask_graph`** — Query the graph for architecture insights
- **`explain_symbol`** — Get context-rich explanations
- **`compress_content`** — Reduce token usage for tool output

This makes Lithic a powerful backend for AI agents working with large codebases.

## Configuration

Lithic reads configuration from environment variables and supports a local `.env` file.

Primary variables:

- `LITHIC_PROVIDER`
- `LITHIC_MODEL`
- `LITHIC_GRAPH_DIR`
- `LITHIC_RESPONSE_MODE`
- `LITHIC_VERBOSE`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `OPENROUTER_API_KEY`

### Migration from Legacy UDA_* Variables

Legacy `UDA_*` environment variables are deprecated and will be removed in a future release.

| Old Variable | New Variable |
|---|---|
| `UDA_PROVIDER` | `LITHIC_PROVIDER` |
| `UDA_MODEL` | `LITHIC_MODEL` |
| `UDA_GRAPH_DIR` | `LITHIC_GRAPH_DIR` |
| `UDA_RESPONSE_MODE` | `LITHIC_RESPONSE_MODE` |

Rename these in your `.env` file or shell profile to ensure compatibility.

See [docs/model-comparison.md](docs/model-comparison.md) for links to official provider pricing pages.

More setup details are available in [`docs/setup.md`](docs/setup.md).

---

## 🛡️ Safety

Lithic is designed to stay concise without becoming careless.

- 🚫 Destructive shell patterns are refused unless explicitly approved
- 🎯 Risky actions are shifted into clearer language instead of aggressive compression
- ✅ Code blocks, commands, file paths, and error strings are preserved exactly during response shaping and compression
- 🔒 Original upstream repositories are not modified by Lithic itself

---

## 📊 Current Scope And Roadmap

Lithic is a focused CLI/MCP tool for **codebase understanding, compression, review, and commit assistance**. The current product boundary is deliberate: graph-first orientation and context compression are stable first, write-capable automation comes after stronger safety rails.

**Implemented today:**

- 🕸️ Graph-backed indexing and querying
- 📦 Deterministic or Headroom-backed compression
- 📝 Concise policy modes
- 🔌 CLI and MCP surfaces
- 🧩 Optional provider wrappers

**Planned next:**

- ✏️ Guarded file-edit execution with previews, diffs, and explicit approval
- 🔄 Reversible decompression APIs for traceable context round-trips
- 🧰 IDE/plugin packaging for Cursor, Claude Desktop, and other MCP clients

**Maturity:** Lithic is suitable for local development workflows today. Treat autonomous edits and IDE packaging as roadmap items, not advertised shipped features.

---

## 📚 Documentation

- [`docs/architecture.md`](docs/architecture.md) — System architecture and design
- [`docs/setup.md`](docs/setup.md) — Detailed setup instructions
- [`docs/model-comparison.md`](docs/model-comparison.md) — Provider pricing links and comparison
- [`docs/merge-notes.md`](docs/merge-notes.md) — Merge notes
- [`docs/license-attribution.md`](docs/license-attribution.md) — License attributions

---

## 📄 License and Attribution

Lithic includes adapter work and behavioral inspiration from:

- 🕸️ [Graphify](https://github.com/safishamsi/graphify) — MIT
- 📦 [Headroom](https://github.com/chopratejas/headroom) — Apache-2.0
- 🧠 [Caveman](https://github.com/JuliusBrussee/caveman) — MIT

See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and the [`LICENSES/`](LICENSES) directory for full details.
