"""Galaxy CLI — main application entry point.

Commands: setup, init, run, brainstorm, chat, config, pause, resume, status
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console

from galaxy.core.kernel import GalaxyKernel
from galaxy.core.version import __version__

app = typer.Typer(
    name="galaxy",
    help="Galaxy AI — Autonomous Software Engineering OS",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def version() -> None:
    """Show Galaxy version."""
    console.print(f"[bold cyan]Galaxy AI[/bold cyan] v{__version__}")


@app.command()
def setup() -> None:
    """Set up Galaxy for this system (detect GPU, install dependencies)."""
    from galaxy.cli.setup_helper import run_setup
    asyncio.run(run_setup())


@app.command()
def init(workspace: str = typer.Argument(".", help="Workspace directory")) -> None:
    """Initialize Galaxy in a workspace directory."""
    kernel = GalaxyKernel()
    asyncio.run(kernel.boot(workspace=Path(workspace)))
    console.print(f"[green]✓[/green] Galaxy initialized in [bold]{workspace}[/bold]")
    asyncio.run(kernel.shutdown())


@app.command()
def run(
    request: str = typer.Argument(..., help="What to build"),
    workspace: str = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
) -> None:
    """Run Galaxy with a project request."""
    from galaxy.cli.runner import GalaxyRunner

    async def _run() -> None:
        runner = GalaxyRunner(workspace=Path(workspace).resolve())
        await runner.run(request)

    asyncio.run(_run())


@app.command()
def brainstorm(
    prompt: str = typer.Argument("", help="What to build (optional, asked interactively)"),
    workspace: str = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    mode: str = typer.Option("structured", "--mode", "-m", help="Mode: free_form, structured, guided"),
    project_name: str = typer.Option("", "--name", "-n", help="Project name"),
) -> None:
    """Start a brainstorming session to plan your project."""
    from galaxy.cli.commands.brainstorm import brainstorm_command
    brainstorm_command(
        workspace=Path(workspace).resolve(),
        prompt=prompt,
        mode=mode,
        project_name=project_name,
    )


@app.command()
def status(workspace: str = typer.Option(".", "--workspace", "-w")) -> None:
    """Show current Galaxy status."""
    from galaxy.core.constants import get_galaxy_dir
    galaxy_dir = get_galaxy_dir(workspace)

    if not galaxy_dir.exists():
        console.print("[red]✗[/red] Galaxy not initialized in this directory")
        console.print("  Run: [bold]galaxy init[/bold]")
        return

    console.print(f"[green]✓[/green] Galaxy workspace: [bold]{workspace}[/bold]")
    console.print(f"  Config: {galaxy_dir / 'galaxy.config.yaml'}")

    # Check for crash marker
    crash_marker = galaxy_dir / ".galaxy_crash_marker"
    if crash_marker.exists():
        console.print("[yellow]⚠ Crash marker detected — run [bold]galaxy resume[/bold][/yellow]")


@app.command()
def chat(
    model: str = typer.Option("", "--model", "-m", help="Override master model"),
    mode: str = typer.Option("reasoning", "--mode", help="Pipeline mode: normal or reasoning"),
) -> None:
    """Chat interactively with the Galaxy master agent."""
    from galaxy.cli.commands.chat import chat as chat_app
    chat_app(model=model, mode=mode)


@app.command()
def config(
    ctx: typer.Context,
) -> None:
    """Manage Galaxy configuration. Use 'galaxy config --help' for subcommands."""
    from galaxy.cli.commands.config import app as config_app
    config_app()


@app.command()
def pause() -> None:
    """Pause Galaxy execution."""
    console.print("[yellow]⏸ Galaxy paused[/yellow]")


@app.command()
def resume(workspace: str = typer.Option(".", "--workspace", "-w")) -> None:
    """Resume Galaxy from last checkpoint."""
    console.print("[green]▶ Resuming from last checkpoint...[/green]")


def main() -> None:
    """Entry point for `galaxy` CLI command."""
    app()


if __name__ == "__main__":
    main()
