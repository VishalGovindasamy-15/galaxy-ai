"""Galaxy Runner — the main execution engine that wires everything together.

Pipeline: CLI → Master (plan domains) → Domain Agents (plan files) → Workers (generate code) → Disk

The 3-tier hierarchy:
  Master   → Creates domain-level plan (backend, database, testing, etc.)
  Domain   → Decomposes each domain into file-level tasks
  Worker   → Generates code for each individual file
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from galaxy.agents.master import MasterAgent
from galaxy.agents.domain import DomainAgent
from galaxy.agents.worker import WorkerAgent
from galaxy.agents.registry import AgentRegistry
from galaxy.core.config import GalaxyConfig
from galaxy.core.types import AgentTier, Task, TaskStatus
from galaxy.cli.colors import GALAXY_CYAN, GALAXY_GREEN, GALAXY_PURPLE, GALAXY_YELLOW, GALAXY_RED
from galaxy.events import Event
from galaxy.events.bus import EventBus
from galaxy.forge.validator import ContinuousValidator
from galaxy.models.providers.ollama import OllamaProvider
from galaxy.models.router import ModelRouter
from galaxy.models.vram import detect_gpus, select_models_for_vram
from galaxy.orchestrator.task_graph import TaskGraph
from galaxy.vault.checkpoint import Checkpoint

logger = logging.getLogger(__name__)

console = Console()


class GalaxyRunner:
    """Main runner that orchestrates the full 3-tier build pipeline.

    Flow:
    1. Detect GPU → select models
    2. Master Agent → creates domain plan (JSON with domains)
    3. Domain Agents → each decomposes domain into file-level tasks
    4. Workers → generate code for each file, writing to disk
    5. Validator → syntax-checks all generated Python files
    """

    def __init__(self, workspace: Path, config: GalaxyConfig | None = None) -> None:
        self.workspace = workspace
        self.config = config or GalaxyConfig()
        self.event_bus = EventBus()
        self.agent_registry = AgentRegistry()
        self.model_router: ModelRouter | None = None
        self.validator = ContinuousValidator(workspace=str(workspace))
        self._files_written: list[str] = []
        self._total_tokens = 0

    async def run(self, request: str) -> None:
        """Execute the full 3-tier pipeline.

        Args:
            request: User's project request (e.g., "Build a REST API with auth").
        """
        console.print()
        console.print(Panel(
            f"[bold {GALAXY_CYAN}]🌌 Galaxy AI[/bold {GALAXY_CYAN}]",
            subtitle=f"[{GALAXY_PURPLE}]Building: {request}[/]",
            border_style=GALAXY_PURPLE,
        ))

        # ── Step 1: Setup ────────────────────────────────────────────────
        console.print(f"\n[{GALAXY_CYAN}]▸[/] Detecting hardware...")
        self.model_router = await self._setup_router()

        # ── Step 2: Master plans domains ─────────────────────────────────
        console.print(f"\n[{GALAXY_PURPLE}]▸ MASTER AGENT[/] — Planning project architecture...")
        domains = await self._master_plan(request)

        if not domains:
            console.print(f"[{GALAXY_RED}]✗[/] Master agent failed to create a plan")
            return

        # Show domain plan
        console.print(f"[{GALAXY_GREEN}]✓[/] Architecture: [bold]{len(domains)}[/bold] domains\n")
        for d in domains:
            deps = ", ".join(d.get("dependencies", [])) or "none"
            console.print(f"  [{GALAXY_PURPLE}]◆[/] [bold]{d['name']}[/bold] — {d.get('description', '')[:60]}")
            console.print(f"    [dim]depends on: {deps}[/dim]")
        console.print()

        # ── Step 3: Domain agents decompose into files ───────────────────
        console.print(f"[{GALAXY_CYAN}]▸ DOMAIN AGENTS[/] — Decomposing into file tasks...")
        all_tasks = await self._domain_plan(domains, request)

        if not all_tasks:
            console.print(f"[{GALAXY_RED}]✗[/] Domain agents failed to produce tasks")
            return

        # Show file plan
        console.print(f"[{GALAXY_GREEN}]✓[/] Plan: [bold]{len(all_tasks)}[/bold] files to generate\n")
        table = Table(title="📋 File Plan", border_style=GALAXY_PURPLE)
        table.add_column("#", style="dim", width=3)
        table.add_column("File", style=f"bold {GALAXY_CYAN}")
        table.add_column("Domain", style=GALAXY_PURPLE)
        table.add_column("Description", style="white")
        for i, task in enumerate(all_tasks, 1):
            table.add_row(str(i), task.file_path, task.domain, task.description[:50])
        console.print(table)
        console.print()

        # ── Step 4: Workers generate code ────────────────────────────────
        console.print(f"[{GALAXY_GREEN}]▸ WORKER AGENTS[/] — Generating code...\n")
        await self._workers_generate(all_tasks)

        # ── Step 5: Validate ─────────────────────────────────────────────
        console.print(f"\n[{GALAXY_CYAN}]▸[/] Validating generated code...")
        await self._validate()

        # ── Step 6: Summary ──────────────────────────────────────────────
        self._print_summary(request, domains)

    # ─── Step 1: Router Setup ────────────────────────────────────────────────

    async def _setup_router(self) -> ModelRouter:
        """Detect GPU and configure the model router."""
        status = detect_gpus()

        if status.has_gpu:
            models = select_models_for_vram(status.free_vram_gb)
            console.print(f"  GPU: {status.gpus[0].name} ({status.free_vram_gb:.0f}GB free)")
            console.print(f"  Models: master={models['master']}, domain={models['domain']}, worker={models['worker']}")
        else:
            models = select_models_for_vram(0)
            console.print("  No GPU detected — using smallest models")

        config = GalaxyConfig(models={
            "master": {"provider": "ollama", "model": models["master"]},
            "domain": {"provider": "ollama", "model": models.get("domain", models["worker"])},
            "worker": {"provider": "ollama", "model": models["worker"]},
            "embedding": {"provider": "ollama", "model": models.get("embedding", "nomic-embed-text")},
        })

        router = ModelRouter(config)
        router.registry.register("ollama", OllamaProvider())

        if await router.registry.detect_available():
            console.print(f"  [{GALAXY_GREEN}]✓[/] Ollama connected")
        else:
            console.print(f"  [{GALAXY_YELLOW}]⚠ Ollama not available — ensure it's running[/]")

        return router

    # ─── Step 2: Master Agent Plans Domains ──────────────────────────────────

    async def _master_plan(self, request: str) -> list[dict[str, Any]]:
        """Master agent creates the domain-level architecture plan.

        Returns:
            List of domain dicts: [{name, description, dependencies}, ...]
        """
        assert self.model_router is not None

        master = MasterAgent(
            name="master",
            model_router=self.model_router,
            event_bus=self.event_bus,
        )
        self.agent_registry.register(master)

        plan = await master.plan_project(request)
        self._total_tokens += master.total_tokens

        self.agent_registry.unregister(master.id)
        return plan.get("domains", [])

    # ─── Step 3: Domain Agents Decompose into Files ──────────────────────────

    async def _domain_plan(self, domains: list[dict[str, Any]], project_request: str) -> list[Task]:
        """Each domain agent decomposes its domain into file-level tasks.

        Args:
            domains: Domain plan from Master.
            project_request: Original user request for context.

        Returns:
            Aggregated list of Tasks across all domains.
        """
        assert self.model_router is not None

        all_tasks: list[Task] = []

        for domain_info in domains:
            domain_name = domain_info.get("name", "general")
            domain_desc = domain_info.get("description", "")

            console.print(f"  [{GALAXY_CYAN}]◆[/] Domain: [bold]{domain_name}[/bold]")

            domain_agent = DomainAgent(
                name=f"domain_{domain_name}",
                model_router=self.model_router,
                event_bus=self.event_bus,
                domain=domain_name,
            )
            self.agent_registry.register(domain_agent)

            context = f"Project: {project_request}\nDomain: {domain_name}\nDescription: {domain_desc}"
            tasks = await domain_agent.plan_domain(domain_desc, context=context)
            self._total_tokens += domain_agent.total_tokens

            for task in tasks:
                if task.file_path:
                    all_tasks.append(task)
                    console.print(f"    [{GALAXY_GREEN}]→[/] {task.file_path}")

            self.agent_registry.unregister(domain_agent.id)

        return all_tasks

    # ─── Step 4: Workers Generate Code ───────────────────────────────────────

    async def _workers_generate(self, tasks: list[Task]) -> None:
        """Workers generate code for each task and write files to disk."""
        assert self.model_router is not None

        generated_context: dict[str, str] = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            overall = progress.add_task("Generating files", total=len(tasks))

            for task in tasks:
                progress.update(
                    overall,
                    description=f"[{GALAXY_CYAN}]Worker → [/]{task.file_path}",
                )

                worker = WorkerAgent(
                    name=f"worker_{task.file_path.replace('/', '_').replace('.', '_')}",
                    model_router=self.model_router,
                    event_bus=self.event_bus,
                    domain=task.domain,
                )
                self.agent_registry.register(worker)

                # Build context from recently generated files
                context_parts = []
                for path, code in list(generated_context.items())[-5:]:
                    context_parts.append(f"--- {path} ---\n{code[:500]}")
                context = "\n\n".join(context_parts)

                try:
                    code = await worker.execute_task(task, context=context)
                    self._total_tokens += worker.total_tokens

                    # Write to disk
                    file_path = self.workspace / task.file_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(code, encoding="utf-8")

                    self._files_written.append(task.file_path)
                    generated_context[task.file_path] = code

                    console.print(f"  [{GALAXY_GREEN}]✓[/] {task.file_path}")

                except Exception as e:
                    console.print(f"  [{GALAXY_RED}]✗[/] {task.file_path}: {e}")

                self.agent_registry.unregister(worker.id)
                progress.advance(overall)

    # ─── Step 5: Validate ────────────────────────────────────────────────────

    async def _validate(self) -> None:
        """Validate all generated Python files for syntax correctness."""
        py_files = [f for f in self._files_written if f.endswith(".py")]
        passed = 0
        failed = 0

        for f in py_files:
            results = await self.validator.validate_file(f)
            syntax = next((r for r in results if r.step.value == "syntax"), None)
            if syntax and syntax.passed:
                passed += 1
            else:
                failed += 1
                console.print(f"  [{GALAXY_YELLOW}]⚠[/] {f}: syntax issue")

        if py_files:
            console.print(f"  [{GALAXY_GREEN}]✓[/] {passed}/{len(py_files)} files pass syntax check")

    # ─── Step 6: Summary ─────────────────────────────────────────────────────

    def _print_summary(self, request: str, domains: list[dict[str, Any]]) -> None:
        """Print final build summary."""
        console.print()
        console.print(Panel(
            f"[bold {GALAXY_GREEN}]✓ Project Generated Successfully[/bold {GALAXY_GREEN}]",
            border_style=GALAXY_GREEN,
        ))

        table = Table(border_style=GALAXY_PURPLE)
        table.add_column("Metric", style=f"bold {GALAXY_CYAN}")
        table.add_column("Value", style="white")
        table.add_row("Files created", str(len(self._files_written)))
        table.add_row("Domains", str(len(domains)))
        table.add_row("Total tokens", f"{self._total_tokens:,}")
        table.add_row("Workspace", str(self.workspace))
        console.print(table)

        console.print(f"\n  [dim]Generated files:[/dim]")
        for f in self._files_written:
            console.print(f"    [{GALAXY_CYAN}]•[/] {f}")
        console.print()
