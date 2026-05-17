"""Live terminal dashboard — Rich Live display of Galaxy status.

Shows real-time progress of agent pipeline, file generation,
and project status in a terminal dashboard.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text


console = Console()


class DashboardView:
    """Terminal dashboard for Galaxy execution.

    Displays:
    - Agent status (master, domains, workers)
    - Pipeline progress
    - File generation stats
    - Activity log
    """

    def __init__(self) -> None:
        self._agents: list[dict[str, Any]] = []
        self._files_generated: int = 0
        self._files_total: int = 0
        self._chunks_merged: int = 0
        self._status: str = "idle"
        self._project_name: str = ""
        self._activity: list[str] = []

    def update_agents(self, agents: list[dict[str, Any]]) -> None:
        self._agents = agents

    def update_progress(self, generated: int, total: int, chunks: int = 0) -> None:
        self._files_generated = generated
        self._files_total = total
        self._chunks_merged = chunks

    def update_status(self, status: str, project_name: str = "") -> None:
        self._status = status
        if project_name:
            self._project_name = project_name

    def add_activity(self, message: str) -> None:
        self._activity.append(message)
        if len(self._activity) > 20:
            self._activity = self._activity[-20:]

    def render(self) -> Panel:
        """Render the full dashboard as a Rich Panel."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        # Header
        header = Text(f"🌌 Galaxy AI — {self._project_name or 'Ready'}", style="bold cyan")
        layout["header"].update(Panel(header, border_style="cyan"))

        # Body — agents + progress
        layout["body"].split_row(
            Layout(name="agents", ratio=2),
            Layout(name="stats", ratio=1),
        )

        layout["body"]["agents"].update(self._render_agents())
        layout["body"]["stats"].update(self._render_stats())

        # Footer
        status_text = f"Status: {self._status} | Files: {self._files_generated}/{self._files_total} | Chunks: {self._chunks_merged}"
        layout["footer"].update(Panel(Text(status_text, style="dim"), border_style="dim"))

        return Panel(layout, title="[bold cyan]Dashboard[/bold cyan]", border_style="cyan")

    def _render_agents(self) -> Panel:
        """Render agent status table."""
        table = Table(title="Agents", show_lines=True)
        table.add_column("Name", style="cyan")
        table.add_column("Tier", style="dim")
        table.add_column("Status", style="bold")
        table.add_column("Task", style="dim")

        for agent in self._agents:
            status = agent.get("status", "idle")
            style = "green" if status == "idle" else "yellow" if status == "working" else "red"
            table.add_row(
                agent.get("name", "?"),
                agent.get("tier", "?"),
                f"[{style}]{status}[/{style}]",
                agent.get("task", "")[:40],
            )

        if not self._agents:
            table.add_row("—", "—", "[dim]no agents[/dim]", "")

        return Panel(table, border_style="dim")

    def _render_stats(self) -> Panel:
        """Render progress stats."""
        lines = [
            f"[bold]Project:[/bold] {self._project_name or 'N/A'}",
            f"[bold]Status:[/bold] {self._status}",
            "",
            f"[bold]Files:[/bold] {self._files_generated}/{self._files_total}",
            f"[bold]Chunks:[/bold] {self._chunks_merged}",
            "",
            "[bold]Recent Activity:[/bold]",
        ]

        for msg in self._activity[-5:]:
            lines.append(f"  [dim]• {msg}[/dim]")

        return Panel(
            "\n".join(lines),
            title="Stats",
            border_style="dim",
        )

    def print_snapshot(self) -> None:
        """Print a single snapshot of the dashboard."""
        console.print(self.render())
