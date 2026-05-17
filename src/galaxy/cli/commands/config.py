"""Galaxy config command — manage Galaxy configuration."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from galaxy.config import GalaxyConfig

console = Console()
app = typer.Typer(help="Manage Galaxy configuration")


@app.command("show")
def config_show() -> None:
    """Show current Galaxy configuration."""
    config = GalaxyConfig.load()

    table = Table(title="Galaxy Configuration", show_lines=True)
    table.add_column("Setting", style="cyan bold")
    table.add_column("Value", style="green")

    table.add_row("Master Model", config.master_model)
    table.add_row("Domain Model", config.domain_model)
    table.add_row("Worker Model", config.worker_model)
    table.add_row("GPU Detected", "✓" if config.gpu_available else "✗")
    table.add_row("VRAM", f"{config.gpu_vram_gb:.1f} GB" if config.gpu_vram_gb else "N/A")

    console.print(table)


@app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key (e.g. master_model)"),
    value: str = typer.Argument(..., help="Config value"),
) -> None:
    """Set a configuration value."""
    config = GalaxyConfig.load()

    valid_keys = {
        "master_model", "domain_model", "worker_model",
    }
    if key not in valid_keys:
        console.print(f"[red]Unknown config key: {key}[/red]")
        console.print(f"[dim]Valid keys: {', '.join(sorted(valid_keys))}[/dim]")
        raise typer.Exit(1)

    setattr(config, key, value)
    config.save()
    console.print(f"[green]✓[/green] Set [cyan]{key}[/cyan] = [bold]{value}[/bold]")


@app.command("reset")
def config_reset() -> None:
    """Reset configuration to defaults."""
    config = GalaxyConfig()
    config.save()
    console.print("[green]✓[/green] Configuration reset to defaults")
