"""Galaxy chat command — interactive chat with master agent."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()
app = typer.Typer(help="Chat with Galaxy master agent")


@app.callback(invoke_without_command=True)
def chat(
    ctx: typer.Context,
    model: str = typer.Option("", "--model", "-m", help="Override master model"),
    mode: str = typer.Option("reasoning", "--mode", help="Pipeline mode: normal or reasoning"),
) -> None:
    """Start interactive chat with the Galaxy master agent."""
    console.print(Panel(
        "[bold cyan]🌌 Galaxy Chat[/bold cyan]\n"
        "[dim]Chat with the master agent. Type 'exit' or 'quit' to leave.[/dim]\n"
        "[dim]Commands: /plan, /status, /brainstorm, /help[/dim]",
        border_style="cyan",
    ))

    history: list[dict[str, str]] = []

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input.strip():
            continue

        lower = user_input.strip().lower()
        if lower in ("exit", "quit", "/exit", "/quit"):
            console.print("[dim]Goodbye![/dim]")
            break

        if lower == "/help":
            _show_help()
            continue

        if lower == "/plan":
            _show_plan_summary()
            continue

        if lower == "/status":
            _show_status()
            continue

        if lower == "/brainstorm":
            console.print("[dim]Use 'galaxy brainstorm' for interactive brainstorming.[/dim]")
            continue

        # Add to history
        history.append({"role": "user", "content": user_input})

        # In this phase we show a structured response
        # (Real LLM integration will come with agent upgrades)
        _show_thinking_response(user_input, mode)


def _show_help() -> None:
    """Show chat help."""
    console.print(Panel(
        "[bold]Chat Commands:[/bold]\n"
        "  /plan        — Show current execution plan\n"
        "  /status      — Show project status\n"
        "  /brainstorm  — Switch to brainstorm mode\n"
        "  /help        — Show this help\n"
        "  exit         — Exit chat",
        title="Help",
        border_style="dim",
    ))


def _show_plan_summary() -> None:
    """Show current plan (stub for now)."""
    console.print("[dim]No active plan. Use 'galaxy run <prompt>' to create one.[/dim]")


def _show_status() -> None:
    """Show project status (stub for now)."""
    console.print("[dim]No active project. Use 'galaxy init' to initialize.[/dim]")


def _show_thinking_response(prompt: str, mode: str) -> None:
    """Show a structured thinking response."""
    from galaxy.cognitive.pipeline import CognitivePipeline
    from galaxy.cognitive.types import CognitiveMode

    cog_mode = CognitiveMode.REASONING if mode == "reasoning" else CognitiveMode.NORMAL

    with console.status("[bold cyan]Thinking...[/bold cyan]"):
        pipeline = CognitivePipeline()
        state = pipeline.run(prompt, mode=cog_mode)

    if state.final_plan:
        console.print()
        console.print(Panel(
            Markdown(state.final_plan),
            title="[bold green]Galaxy Master[/bold green]",
            border_style="green",
        ))
    else:
        console.print("[yellow]Could not generate a plan. Try a more specific prompt.[/yellow]")

    # Show pipeline stats
    console.print(
        f"  [dim]Pipeline: {len(state.stage_results)} stages, "
        f"{state.total_duration_ms:.0f}ms[/dim]"
    )
