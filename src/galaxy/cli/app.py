"""Galaxy CLI — main application entry point.

Commands: setup, init, run, pause, resume, status, config
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
    async def _run() -> None:
        kernel = GalaxyKernel()
        await kernel.boot(workspace=Path(workspace))
        console.print(f"[bold cyan]Galaxy AI[/bold cyan] — Building: {request}")
        # Full orchestration happens here in later integration
        console.print("[yellow]⚡ Orchestration engine starting...[/yellow]")
        await kernel.shutdown()

    asyncio.run(_run())


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
