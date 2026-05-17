"""Galaxy brainstorm CLI command.

Provides the `galaxy brainstorm` interactive command for pre-execution
idea exploration with temp/permanent stores and decision logging.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from galaxy.brainstorm.engine import BrainstormEngine
from galaxy.brainstorm.interviewer import BrainstormInterviewer
from galaxy.brainstorm.types import (
    BrainstormMode,
    BrainstormPhase,
    IdeaCategory,
    IdeaStatus,
)

console = Console()

# ─── Category shortcuts ─────────────────────────────────────────────────────

CATEGORY_SHORTCUTS: dict[str, IdeaCategory] = {
    "f": IdeaCategory.FEATURE,
    "a": IdeaCategory.ARCHITECTURE,
    "c": IdeaCategory.CONSTRAINT,
    "s": IdeaCategory.SECURITY,
    "d": IdeaCategory.DEPENDENCY,
    "w": IdeaCategory.WORKFLOW,
    "t": IdeaCategory.TESTING,
    "o": IdeaCategory.DEVOPS,
    "p": IdeaCategory.PERFORMANCE,
    "u": IdeaCategory.UI_UX,
}


def _parse_category(cat_str: str) -> IdeaCategory:
    """Parse a category string or shortcut."""
    cat_str = cat_str.strip().lower()
    if cat_str in CATEGORY_SHORTCUTS:
        return CATEGORY_SHORTCUTS[cat_str]
    try:
        return IdeaCategory(cat_str)
    except ValueError:
        return IdeaCategory.FEATURE


def _display_ideas_table(engine: BrainstormEngine) -> None:
    """Display a table of all ideas (temp + permanent)."""
    table = Table(title="💡 Ideas", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", style="bold")
    table.add_column("Category", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Store", style="yellow")

    idx = 1
    for idea in engine.permanent_store.list_all():
        table.add_row(
            str(idx),
            idea.title,
            idea.category.value,
            f"[green]✓ {idea.status.value}[/green]",
            "[green]PERMANENT[/green]",
        )
        idx += 1

    for idea in engine.temp_store.list_all():
        status_style = {
            IdeaStatus.DRAFT: "[dim]draft[/dim]",
            IdeaStatus.EXPLORING: "[yellow]exploring[/yellow]",
            IdeaStatus.REJECTED: "[red]rejected[/red]",
            IdeaStatus.DEFERRED: "[yellow]deferred[/yellow]",
        }.get(idea.status, idea.status.value)
        table.add_row(
            str(idx),
            idea.title,
            idea.category.value,
            status_style,
            "[dim]TEMP[/dim]",
        )
        idx += 1

    console.print(table)


def _display_summary(engine: BrainstormEngine) -> None:
    """Display session summary."""
    summary = engine.end_session()
    table = Table(title="📊 Brainstorm Summary")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="cyan")
    table.add_row("Total Ideas", str(summary.total_ideas))
    table.add_row("Approved", f"[green]{summary.approved_ideas}[/green]")
    table.add_row("Rejected", f"[red]{summary.rejected_ideas}[/red]")
    table.add_row("Deferred", f"[yellow]{summary.deferred_ideas}[/yellow]")
    table.add_row("Pending", str(summary.pending_ideas))
    table.add_row("Decisions Logged", str(summary.total_decisions))
    console.print(table)


def run_brainstorm(
    workspace: Path,
    prompt: str = "",
    mode: str = "structured",
    project_name: str = "",
) -> BrainstormEngine:
    """Run an interactive brainstorming session.

    Args:
        workspace: Project workspace directory.
        prompt: Initial project prompt.
        mode: Brainstorming mode (free_form, structured, guided).
        project_name: Project name.

    Returns:
        The BrainstormEngine with completed session.
    """
    engine = BrainstormEngine(workspace=workspace)
    interviewer = BrainstormInterviewer()

    # Try to load existing session
    counts = engine.load()
    if counts["permanent_ideas"] > 0 or counts["temp_ideas"] > 0:
        console.print(
            f"[cyan]Loaded existing session: "
            f"{counts['permanent_ideas']} permanent, "
            f"{counts['temp_ideas']} temp ideas[/cyan]"
        )

    # Parse mode
    try:
        bs_mode = BrainstormMode(mode)
    except ValueError:
        bs_mode = BrainstormMode.STRUCTURED

    # Get prompt if not provided
    if not prompt:
        prompt = Prompt.ask("\n[bold]What do you want to build?[/bold]")

    # Start session
    session = engine.start_session(
        prompt=prompt,
        project_name=project_name or workspace.name,
        mode=bs_mode,
    )

    console.print(Panel(
        f"[bold cyan]🧠 Brainstorming Session[/bold cyan]\n"
        f"Project: {session.project_name}\n"
        f"Mode: {bs_mode.description}\n"
        f"Prompt: {prompt}",
        border_style="cyan",
    ))

    # Show initial questions
    questions = interviewer.get_questions(
        prompt=prompt,
        existing_ideas=engine.temp_store.list_all(),
        mode=bs_mode,
        count=3,
    )
    if questions:
        console.print("\n[bold yellow]Consider these questions:[/bold yellow]")
        for i, q in enumerate(questions, 1):
            console.print(f"  {i}. {q}")

    # Interactive loop
    console.print(
        "\n[dim]Commands: [bold]add[/bold] idea | [bold]approve[/bold] ID | "
        "[bold]reject[/bold] ID | [bold]defer[/bold] ID | [bold]list[/bold] | "
        "[bold]questions[/bold] | [bold]gaps[/bold] | [bold]spec[/bold] | "
        "[bold]done[/bold][/dim]\n"
    )

    while True:
        try:
            user_input = Prompt.ask("[bold]brainstorm>[/bold]").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("done", "quit", "exit", "q"):
            break

        elif cmd == "add":
            title = arg or Prompt.ask("  Title")
            description = Prompt.ask("  Description", default="")
            cat_str = Prompt.ask(
                "  Category [f]eature/[a]rch/[c]onstraint/[s]ecurity/[d]ep/[t]est",
                default="f",
            )
            category = _parse_category(cat_str)
            idea = engine.add_idea(title, description, category)
            console.print(f"  [green]✓[/green] Added: {idea.title} ({idea.id})")

            # Show follow-up questions
            follow_ups = interviewer.get_follow_up(idea)
            if follow_ups:
                for fq in follow_ups[:2]:
                    console.print(f"  [dim]→ {fq}[/dim]")

        elif cmd == "approve":
            if not arg:
                console.print("  [red]Usage: approve <idea_id>[/red]")
                continue
            reason = Prompt.ask("  Reason", default="")
            result = engine.approve_idea(arg, reason=reason)
            if result:
                console.print(f"  [green]✓[/green] Approved: {result.title} → PERMANENT")
            else:
                console.print(f"  [red]✗[/red] Idea not found: {arg}")

        elif cmd == "reject":
            if not arg:
                console.print("  [red]Usage: reject <idea_id>[/red]")
                continue
            reason = Prompt.ask("  Reason", default="")
            result = engine.reject_idea(arg, reason=reason)
            if result:
                console.print(f"  [red]✗[/red] Rejected: {result.title}")
            else:
                console.print(f"  [red]✗[/red] Idea not found: {arg}")

        elif cmd == "defer":
            if not arg:
                console.print("  [red]Usage: defer <idea_id>[/red]")
                continue
            reason = Prompt.ask("  Reason", default="")
            result = engine.defer_idea(arg, reason=reason)
            if result:
                console.print(f"  [yellow]⏸[/yellow] Deferred: {result.title}")
            else:
                console.print(f"  [red]✗[/red] Idea not found: {arg}")

        elif cmd == "list":
            _display_ideas_table(engine)

        elif cmd == "questions":
            qs = interviewer.get_questions(
                prompt=prompt,
                existing_ideas=engine.temp_store.list_all() + engine.permanent_store.list_all(),
                count=3,
            )
            if qs:
                for i, q in enumerate(qs, 1):
                    console.print(f"  {i}. {q}")
            else:
                console.print("  [dim]No more questions — looking good![/dim]")

        elif cmd == "gaps":
            analysis = interviewer.generate_gap_analysis(
                prompt,
                engine.temp_store.list_all() + engine.permanent_store.list_all(),
            )
            if analysis["missing_categories"]:
                console.print("  [yellow]Missing:[/yellow] " + ", ".join(analysis["missing_categories"]))
            else:
                console.print("  [green]All categories covered![/green]")
            for s in analysis["suggestions"][:3]:
                console.print(f"  [dim]→ {s}[/dim]")

        elif cmd == "spec":
            spec = engine.get_project_spec()
            for key, items in spec.items():
                if items:
                    console.print(f"  [bold]{key}:[/bold]")
                    for item in items:
                        console.print(f"    • {item['title']}")

        else:
            console.print(f"  [dim]Unknown command: {cmd}[/dim]")

    # End session
    _display_summary(engine)
    engine.save()
    console.print("[green]✓ Session saved[/green]")

    return engine
