"""Setup helper — auto-detect hardware and install dependencies."""

from __future__ import annotations

import logging
import shutil

from rich.console import Console

from galaxy.models.vram import detect_gpus, select_models_for_vram

console = Console()
logger = logging.getLogger(__name__)


async def run_setup() -> None:
    """Run the Galaxy setup wizard."""
    console.print("\n[bold cyan]🌌 Galaxy AI Setup[/bold cyan]\n")

    # 1. Detect GPU
    console.print("[bold]Step 1:[/bold] Detecting GPU...")
    status = detect_gpus()

    if status.has_gpu:
        for gpu in status.gpus:
            console.print(f"  [green]✓[/green] {gpu.name} — {gpu.total_gb:.0f}GB total, {gpu.free_gb:.0f}GB free")
        models = select_models_for_vram(status.free_vram_gb)
        console.print(f"  Recommended models:")
        console.print(f"    master = [bold]{models['master']}[/bold]")
        console.print(f"    domain = [bold]{models['domain']}[/bold]")
        console.print(f"    worker = [bold]{models['worker']}[/bold]")
    else:
        console.print("  [yellow]⚠ No NVIDIA GPU detected — will use CPU or cloud models[/yellow]")

    # 2. Check tmux
    console.print("\n[bold]Step 2:[/bold] Checking tmux...")
    if shutil.which("tmux"):
        console.print("  [green]✓[/green] tmux is installed")
    else:
        console.print("  [red]✗[/red] tmux not found — install: sudo apt install tmux")

    # 3. Check Ollama
    console.print("\n[bold]Step 3:[/bold] Checking Ollama...")
    if shutil.which("ollama"):
        console.print("  [green]✓[/green] Ollama is installed")
    else:
        console.print("  [yellow]⚠[/yellow] Ollama not found — install: curl -fsSL https://ollama.ai/install.sh | sh")

    console.print("\n[bold green]Setup complete![/bold green]")
    console.print("Next: [bold]galaxy init[/bold] to initialize a workspace\n")
