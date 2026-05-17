"""User confirmation — asks permission before destructive actions.

Provides the confirmation flow required before Galaxy starts
generating code, spending compute, or modifying files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

console = Console()


@dataclass
class ConfirmationItem:
    """A single item to confirm with the user."""
    label: str = ""
    detail: str = ""
    category: str = "general"

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.label, "detail": self.detail, "category": self.category}


@dataclass
class ConfirmationRequest:
    """A request for user confirmation before proceeding."""
    title: str = ""
    items: list[ConfirmationItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    estimated_time: str = ""
    estimated_chunks: int = 0

    def add(self, label: str, detail: str = "", category: str = "general") -> None:
        self.items.append(ConfirmationItem(label=label, detail=detail, category=category))

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)


def confirm_action(request: ConfirmationRequest, auto_approve: bool = False) -> bool:
    """Display a confirmation prompt and wait for user approval.

    Args:
        request: The confirmation request to display.
        auto_approve: Skip confirmation (for non-interactive mode).

    Returns:
        True if user approves, False otherwise.
    """
    if auto_approve:
        return True

    # Build the panel
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Item", style="bold")
    table.add_column("Detail", style="dim")

    for item in request.items:
        table.add_row(f"• {item.label}", item.detail)

    console.print(Panel(
        table,
        title=f"[bold cyan]{request.title}[/bold cyan]",
        border_style="cyan",
    ))

    if request.warnings:
        for warning in request.warnings:
            console.print(f"  [yellow]⚠ {warning}[/yellow]")

    if request.estimated_time:
        console.print(f"  [dim]Estimated time: {request.estimated_time}[/dim]")

    if request.estimated_chunks:
        console.print(f"  [dim]Estimated chunks: {request.estimated_chunks}[/dim]")

    return Confirm.ask("\n[bold]Proceed?[/bold]", default=True)


def build_project_confirmation(
    project_name: str,
    features: list[str],
    domains: list[str],
    tech_stack: list[str],
    estimated_chunks: int = 0,
) -> ConfirmationRequest:
    """Build a confirmation request for project creation.

    Args:
        project_name: Name of the project.
        features: List of features to build.
        domains: Active domains.
        tech_stack: Technologies to use.
        estimated_chunks: Estimated code chunks.

    Returns:
        ConfirmationRequest ready for display.
    """
    request = ConfirmationRequest(
        title=f"Create Project: {project_name}",
        estimated_chunks=estimated_chunks,
    )

    request.add("Project", project_name, category="identity")
    request.add("Tech Stack", ", ".join(tech_stack), category="tech")
    request.add("Domains", ", ".join(domains), category="structure")

    for feature in features[:10]:  # Cap display
        request.add(feature, category="feature")

    if len(features) > 10:
        request.add(f"... and {len(features) - 10} more features")

    return request
