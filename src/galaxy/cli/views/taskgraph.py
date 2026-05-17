"""Task graph view — ASCII DAG of execution plan.

Renders execution plan nodes and dependencies as an ASCII
directed acyclic graph for terminal display.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from galaxy.cognitive.types import ExecutionPlan, PlanNode

console = Console()


class TaskGraphView:
    """Renders an ExecutionPlan as an ASCII DAG.

    Usage:
        view = TaskGraphView(plan)
        view.render()
    """

    def __init__(self, plan: ExecutionPlan | None = None) -> None:
        self._plan = plan

    def set_plan(self, plan: ExecutionPlan) -> None:
        self._plan = plan

    def render(self) -> Panel:
        """Render the task graph as a Rich Panel."""
        if not self._plan or not self._plan.nodes:
            return Panel("[dim]No execution plan[/dim]", title="Task Graph", border_style="dim")

        tree = Tree("📋 [bold cyan]Execution Plan[/bold cyan]")

        # Group by domain
        by_domain: dict[str, list[PlanNode]] = {}
        for node in self._plan.nodes:
            by_domain.setdefault(node.domain, []).append(node)

        for domain, nodes in sorted(by_domain.items()):
            domain_branch = tree.add(f"[bold]{domain}[/bold]")
            for node in nodes:
                deps = f" → [{', '.join(d[:8] for d in node.dependencies)}]" if node.dependencies else ""
                status_icon = self._priority_icon(node.priority)
                domain_branch.add(
                    f"{status_icon} {node.name} [dim]~{node.estimated_chunks} chunks{deps}[/dim]"
                )

        return Panel(tree, title="[bold]Task Graph[/bold]", border_style="cyan")

    def render_ascii(self) -> str:
        """Render as plain ASCII text."""
        if not self._plan or not self._plan.nodes:
            return "No execution plan"

        lines: list[str] = []
        lines.append("=== Execution Plan ===")
        lines.append("")

        node_map = {n.id: n for n in self._plan.nodes}

        for i, node_id in enumerate(self._plan.execution_order):
            node = node_map.get(node_id)
            if not node:
                continue

            prefix = "├──" if i < len(self._plan.execution_order) - 1 else "└──"
            deps = ""
            if node.dependencies:
                dep_names = [node_map[d].name for d in node.dependencies if d in node_map]
                if dep_names:
                    deps = f" (after: {', '.join(dep_names)})"

            lines.append(f"  {prefix} [{node.domain}] {node.name}{deps}")

        lines.append("")
        lines.append(f"Total: {len(self._plan.nodes)} tasks, ~{self._plan.estimated_total_chunks} chunks")
        return "\n".join(lines)

    def print_graph(self) -> None:
        """Print the graph to console."""
        console.print(self.render())

    @staticmethod
    def _priority_icon(priority: int) -> str:
        if priority <= 1:
            return "🔴"
        elif priority <= 2:
            return "🟡"
        else:
            return "🟢"
