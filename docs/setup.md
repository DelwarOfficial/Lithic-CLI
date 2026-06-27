# Setup

Single command install (recommended):

```powershell
uv tool install git+https://github.com/DelwarOfficial/Lithic-CLI.git
lithic --help
# or
pip install git+https://github.com/DelwarOfficial/Lithic-CLI.git
```

For dev / from source:

```powershell
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
uv sync
uv run lithic --help
```

Optional Headroom:

```powershell
uv sync --extra headroom
```

If Headroom builds from source on Windows, install Visual Studio Build Tools with the C++ workload first.

Environment variables:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `OPENROUTER_API_KEY`
- `LITHIC_PROVIDER`
- `LITHIC_MODEL`
- `LITHIC_GRAPH_DIR`
- `LITHIC_RESPONSE_MODE`
- `LITHIC_VERBOSE`

Lithic also accepts the older `UDA_*` variables as a compatibility fallback while migrating older setups.
