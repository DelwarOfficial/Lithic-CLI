"""Lithic CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import click
from rich.console import Console

from lithic.config import AgentConfig
from lithic.orchestrator import Orchestrator
from lithic.updater import UpstreamChecker

console = Console()


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
@click.option("--provider", default=None,
              help="LLM provider (anthropic, openai, ollama, openrouter)")
@click.option("--model", default=None, help="Model name for the provider")
@click.option("--mode", default=None,
              help="Response mode (concise, normal, caveman_full, review, commit)")
@click.option("--graph-dir", default=None, help="Graph output directory",
              type=click.Path(path_type=Path))
@click.pass_context
def main(ctx: click.Context, verbose: bool, provider: str | None,
         model: str | None, mode: str | None, graph_dir: Path | None) -> None:
    """Lithic - Carve Knowledge. Compress Context. Deliver Stone-Sharp Precision."""
    ctx.ensure_object(dict)
    config = AgentConfig.from_env(Path.cwd())
    overrides: dict[str, object] = {}
    if verbose:
        overrides["verbose"] = True
    if provider is not None:
        overrides["provider"] = provider
    if model is not None:
        overrides["model"] = model
    if mode is not None:
        overrides["response_mode"] = mode
    if graph_dir is not None:
        overrides["graph_output_dir"] = graph_dir.resolve()
    if overrides:
        try:
            config = AgentConfig(
                project_root=config.project_root,
                graph_output_dir=overrides.get("graph_output_dir", config.graph_output_dir),  # type: ignore[arg-type]
                provider=str(overrides.get("provider", config.provider)),
                model=str(overrides.get("model", config.model)),
                response_mode=str(overrides.get("response_mode", config.response_mode)),
                verbose=bool(overrides.get("verbose", config.verbose)),
            )
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
    ctx.obj["orchestrator"] = Orchestrator(config)


@main.command()
@click.argument("path", default=".")
@click.pass_context
def index(ctx: click.Context, path: str) -> None:
    """Build or refresh the project graph."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.index(path))


@main.command()
@click.argument("question")
@click.pass_context
def ask(ctx: click.Context, question: str) -> None:
    """Ask an architecture/codebase question."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.ask(question))


@main.command()
@click.argument("concept")
@click.pass_context
def explain(ctx: click.Context, concept: str) -> None:
    """Explain a symbol, module, file, or concept."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.explain(concept))


@main.command("path")
@click.argument("source")
@click.argument("target")
@click.pass_context
def graph_path(ctx: click.Context, source: str, target: str) -> None:
    """Find a relationship path between two graph concepts."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.path_between(source, target))


@main.command()
@click.argument("task")
@click.pass_context
def edit(ctx: click.Context, task: str) -> None:
    """Orient for an edit task without mutating files."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.orient_edit(task))


@main.command()
@click.pass_context
def review(ctx: click.Context) -> None:
    """Review current working-tree diff."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.review())


@main.command()
@click.pass_context
def commit(ctx: click.Context) -> None:
    """Generate a Conventional Commit message."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.commit())


@main.command("compress-file")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_context
def compress_file(ctx: click.Context, file: Path) -> None:
    """Compress a large text file."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.compress_file(str(file)))


@main.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Show graph and compression stats."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    data = cast(dict[str, Any], orch.stats())
    compression = cast(dict[str, Any], data["compression"])
    console.print(f"Graph exists: {data['graph_exists']}")
    console.print(f"History count: {data['history_count']}")
    console.print(f"Compression calls: {compression['calls']}")


@main.command("upstream-status")
@click.option("--local-only", is_flag=True, help="Skip remote checks.")
def upstream_status(local_only: bool) -> None:
    """Check pinned upstream submodules."""
    statuses = UpstreamChecker(Path.cwd()).check(remote=not local_only)
    for item in statuses:
        line = f"{item.name}: {item.status} {item.local_commit[:12]}"
        if item.remote_commit:
            line += f" remote={item.remote_commit[:12]}"
        if item.error:
            line += f" error={item.error}"
        console.print(line)


@main.group(invoke_without_command=True)
@click.pass_context
def mcp(ctx: click.Context) -> None:
    """Manage the Lithic MCP server."""
    if ctx.invoked_subcommand is None:
        from lithic.mcp.server import serve as _serve
        _serve()


@mcp.command()
@click.pass_context
def serve(ctx: click.Context) -> None:
    """Start the MCP stdio server."""
    from lithic.mcp.server import serve as _serve
    _serve()
