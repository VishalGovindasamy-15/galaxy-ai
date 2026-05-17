"""Activity feed view — shows real-time event log.

Renders a scrolling log of pipeline events, agent actions,
and file generation progress.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


class ActivityItem:
    """A single activity event."""

    def __init__(
        self,
        message: str,
        category: str = "system",
        agent: str = "",
        timestamp: datetime | None = None,
    ) -> None:
        self.message = message
        self.category = category
        self.agent = agent
        self.timestamp = timestamp or datetime.now(timezone.utc)

    @property
    def icon(self) -> str:
        icons = {
            "system": "⚙",
            "agent": "🤖",
            "file": "📄",
            "error": "❌",
            "success": "✓",
            "plan": "📋",
        }
        return icons.get(self.category, "•")


class ActivityFeed:
    """Activity feed that tracks and displays pipeline events.

    Usage:
        feed = ActivityFeed()
        feed.add("Master agent started planning", category="agent")
        feed.add("Generated auth/service.py", category="file")
        feed.render()
    """

    def __init__(self, max_items: int = 50) -> None:
        self._items: list[ActivityItem] = []
        self._max_items = max_items

    def add(
        self,
        message: str,
        category: str = "system",
        agent: str = "",
    ) -> None:
        """Add an activity item."""
        self._items.append(ActivityItem(message=message, category=category, agent=agent))
        if len(self._items) > self._max_items:
            self._items = self._items[-self._max_items:]

    @property
    def items(self) -> list[ActivityItem]:
        return list(self._items)

    @property
    def count(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()

    def render(self, limit: int = 15) -> Panel:
        """Render the activity feed as a Rich Panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Time", style="dim", width=8)
        table.add_column("Icon", width=2)
        table.add_column("Message")

        for item in self._items[-limit:]:
            time_str = item.timestamp.strftime("%H:%M:%S")
            table.add_row(time_str, item.icon, item.message)

        if not self._items:
            table.add_row("", "", "[dim]No activity yet[/dim]")

        return Panel(table, title="[bold]Activity[/bold]", border_style="dim")

    def print_feed(self, limit: int = 15) -> None:
        """Print the activity feed."""
        console.print(self.render(limit))
