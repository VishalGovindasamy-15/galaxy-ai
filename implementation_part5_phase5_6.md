# Galaxy Implementation Guide — Part 5: Phase 5, 6 & Installation

---

## PHASE 5: Extensibility & Enterprise

### 1. Plugin SDK — `plugins/`

```python
# plugins/sdk.py
@dataclass
class PluginManifest:
    name: str
    version: str
    type: str                  # tool | agent | provider | analyzer | ui
    author: str
    description: str
    license: str
    compatibility: dict        # galaxy_min, galaxy_max
    permissions: PluginPermissions
    runtime: PluginRuntime
    dependencies: dict
    exports: dict

@dataclass
class PluginPermissions:
    filesystem: dict           # read: [...], write: [...], forbidden: [...]
    network: dict              # outbound: [...]
    tools: dict                # requires: [...]
    resources: dict            # max_memory_mb, max_cpu_percent

@dataclass
class PluginRuntime:
    language: str              # python | node | binary
    entry: str                 # plugin/main.py
    isolation: str             # subprocess | docker | wasm

# plugins/loader.py
class PluginLoader:
    async def discover(self, directories: list[str]) -> list[PluginManifest]:
        """Scan directories for galaxy-plugin.yaml files."""

    async def validate(self, manifest: PluginManifest) -> list[str]:
        """Check compatibility, permissions, dependencies. Return errors."""

    async def install(self, source: str) -> PluginManifest:
        """Install from local path, git URL, or registry."""

    async def load(self, manifest: PluginManifest) -> LoadedPlugin:
        """Start sandbox, initialize plugin, register exports."""

    async def unload(self, plugin_name: str) -> None:
        """Stop sandbox, deregister exports."""

# plugins/sandbox.py
class PluginSandbox:
    """Isolates plugin execution from Galaxy main process."""

    async def start_subprocess(self, manifest: PluginManifest) -> Process:
        """
        1. Create subprocess with resource limits (ulimit)
        2. Set up JSON-RPC communication over stdin/stdout
        3. Pass allowed permissions as environment config
        4. Health check ping
        """

    async def start_docker(self, manifest: PluginManifest) -> Container:
        """
        1. Build/pull Docker image from plugin's Dockerfile
        2. Run with restricted network, read-only root, resource limits
        3. Expose HTTP API for communication
        """

    async def call(self, method: str, params: dict) -> dict:
        """Send JSON-RPC call to sandbox, wait for response."""

    async def stop(self) -> None

# plugins/health.py
class PluginHealthMonitor:
    async def check_all(self) -> dict[str, str]:
        """Ping all loaded plugins. Return name → status."""

    async def handle_unhealthy(self, plugin_name: str) -> None:
        """3 consecutive failures → auto-disable plugin."""

# plugins/permissions.py
class PluginPermissionChecker:
    async def check(self, plugin: str, action: str, target: str) -> bool:
        """Check if plugin is allowed to perform action on target."""

    async def request_escalation(self, plugin: str, permission: str) -> bool:
        """Ask user for runtime permission grant."""
```

### 2. Blueprints — `blueprints/`

```python
# blueprints/loader.py
class BlueprintLoader:
    async def load(self, name: str) -> Blueprint:
        """Load blueprint from built-in templates or installed templates."""

    async def load_from_file(self, path: str) -> Blueprint:
        """Load custom blueprint YAML."""

    async def list_available(self) -> list[BlueprintInfo]:
        """List all available blueprints (built-in + installed)."""

@dataclass
class Blueprint:
    name: str
    version: str
    description: str
    stack: dict                # frontend, backend, database, infrastructure
    architecture: dict         # pattern, layers with rules
    domains: list[dict]        # Domain decomposition
    sentinel: dict             # Style + architecture rules
    structure: list[dict]      # Directory structure
    validation: dict           # Quality criteria

# blueprints/generator.py
class ProjectGenerator:
    async def scaffold(self, blueprint: Blueprint, path: str,
                       overrides: dict = None) -> GenerateResult:
        """
        1. Create directory structure from blueprint
        2. Generate config files (package.json, pyproject.toml, etc.)
        3. Create galaxy.config.yaml with blueprint's model/scheduler config
        4. Write .galaxy/sentinel/style_profile.yaml from blueprint
        5. Write .galaxy/sentinel/arch_rules.yaml from blueprint
        6. Initialize git repo
        7. Return report of created files
        """

# blueprints/detector.py
class ProjectDetector:
    async def detect(self, project_path: str) -> Blueprint | None:
        """
        Scan existing project:
        1. Check for framework indicators (package.json, requirements.txt)
        2. Analyze directory structure
        3. Match against known blueprints
        4. Generate inferred blueprint
        """
```

### 3. Cluster — `cluster/`

```python
# cluster/topology.py
class ClusterManager:
    nodes: dict[str, NodeInfo]

    async def discover_nodes(self) -> list[NodeInfo]:
        """Discover cluster nodes via config or network scan."""

    async def register_node(self, node: NodeInfo) -> None:
    async def remove_node(self, node_id: str) -> None
    async def get_available_resources(self) -> ClusterResources:
        """Aggregate GPU/CPU/RAM across all nodes."""

@dataclass
class NodeInfo:
    node_id: str
    hostname: str
    role: str                  # control | compute | inference | hybrid
    gpus: list[GPUInfo]
    cpu_cores: int
    ram_gb: int
    status: str                # online | offline | draining

# cluster/communication.py
class ClusterEventBus:
    """Extends EventBus for cross-node communication over network."""

    async def connect_to_node(self, node: NodeInfo) -> None:
        """Establish Redis pub/sub connection to remote node."""

    async def publish_cluster(self, topic: str, event: Event) -> None:
        """Publish to all nodes in cluster."""

# cluster/gpu_manager.py
class GPUClusterManager:
    async def allocate_gpu(self, model: str, vram_needed: int) -> GPUAllocation:
        """Find best GPU across cluster for model loading."""

    async def balance_load(self) -> list[Migration]:
        """Rebalance model assignments across GPUs."""
```

### 4. Studio — `studio/`

```python
# studio/server.py
from fastapi import FastAPI, WebSocket

app = FastAPI(title="Galaxy Studio", version="0.1.0")

# ─── READ-ONLY (Monitoring) ───
# GET  /api/status                 — Project status overview
# GET  /api/tasks                  — All tasks with statuses
# GET  /api/tasks/{id}             — Task detail
# GET  /api/agents                 — Active agents
# GET  /api/agents/{id}            — Agent detail + reputation
# GET  /api/memory                 — Memory statistics
# GET  /api/memory/search?q=       — Search memories
# GET  /api/memory/{id}            — Single memory entry
# GET  /api/trust                  — Trust dashboard data
# GET  /api/trust/{id}             — Trust profile for specific output
# GET  /api/costs                  — Cost dashboard data
# GET  /api/costs/breakdown        — Cost by model/agent/domain
# GET  /api/policies               — Policy compliance status
# GET  /api/policies/violations    — Violation history
# GET  /api/events                 — Event stream (paginated)
# GET  /api/cortex/stats           — Code intelligence stats
# GET  /api/cortex/graph/{file}    — Dependency graph for file

# ─── EXECUTION CONTROL ───
# POST /api/run                    — Start new project build
# POST /api/pause                  — Pause execution
# POST /api/resume                 — Resume execution
# POST /api/stop                   — Stop execution

# ─── MODEL MANAGEMENT ───
# GET  /api/models                 — All available models (Ollama + cloud)
# GET  /api/models/loaded          — Currently loaded models + VRAM usage
# POST /api/models/pull            — Pull new Ollama model
# POST /api/models/assign          — Assign model to tier (master/domain/worker)
# POST /api/models/swap            — Hot-swap model mid-execution
# POST /api/models/unload          — Unload model from VRAM
# GET  /api/models/vram            — VRAM allocation chart data
# GET  /api/models/efficiency      — Model efficiency comparison
# PUT  /api/models/cloud-keys      — Set cloud API keys (encrypted)

# ─── CHECKPOINT MANAGEMENT ───
# GET  /api/checkpoints            — Checkpoint history (timeline)
# GET  /api/checkpoints/{id}       — Checkpoint detail (snapshot preview)
# POST /api/checkpoints            — Create manual checkpoint
# POST /api/checkpoints/{id}/restore — Restore to specific checkpoint
# GET  /api/checkpoints/compare?a=&b= — Compare two checkpoints
# GET  /api/checkpoints/{id}/export — Download .vault file
# POST /api/checkpoints/import     — Upload and restore .vault file
# POST /api/hibernate              — Hibernate project
# POST /api/wake                   — Wake from hibernation
# DELETE /api/checkpoints/{id}     — Delete old checkpoint

# ─── CONFIGURATION MANAGEMENT ───
# GET  /api/config                 — Current full config
# PUT  /api/config                 — Update config (live apply)
# GET  /api/config/defaults        — Default config values
# GET  /api/config/diff            — Diff current vs defaults
# POST /api/config/preset          — Apply preset (fast/quality/low-vram)
# GET  /api/config/export          — Export config YAML
# POST /api/config/import          — Import config YAML

# ─── PLUGIN MANAGEMENT ───
# GET  /api/plugins                — Installed plugins + status
# POST /api/plugins/install        — Install plugin (local path/URL/registry)
# DELETE /api/plugins/{name}       — Uninstall plugin
# PUT  /api/plugins/{name}/toggle  — Enable/disable plugin
# GET  /api/plugins/{name}/health  — Plugin health status
# GET  /api/plugins/{name}/logs    — Plugin logs
# PUT  /api/plugins/{name}/permissions — Update plugin permissions
# GET  /api/plugins/registry/search?q= — Search community registry

# ─── BLUEPRINT MANAGEMENT ───
# GET  /api/blueprints             — Available blueprints
# POST /api/blueprints/scaffold    — Generate project from blueprint
# GET  /api/blueprints/preview     — Preview directory structure
# POST /api/blueprints/detect      — Auto-detect project type
# GET  /api/blueprints/registry/search?q= — Search community registry

# ─── POLICY MANAGEMENT ───
# GET  /api/policies               — All policies
# POST /api/policies               — Create new policy
# PUT  /api/policies/{id}          — Update policy
# DELETE /api/policies/{id}        — Delete policy
# PUT  /api/policies/{id}/toggle   — Enable/disable policy
# GET  /api/policies/templates     — Pre-built policy templates

# ─── BUDGET MANAGEMENT ───
# GET  /api/budget                 — Current budget config + usage
# PUT  /api/budget                 — Update budget limits
# GET  /api/budget/alerts          — Alert configuration
# PUT  /api/budget/alerts          — Update alert thresholds
# GET  /api/costs/export           — Export cost report (CSV)

# ─── MEMORY MANAGEMENT ───
# GET  /api/memory                 — Memory stats per level
# GET  /api/memory/search?q=       — Semantic search memories
# GET  /api/memory/{id}            — View single memory
# PUT  /api/memory/{id}            — Edit memory content
# DELETE /api/memory/{id}          — Delete memory
# POST /api/memory/compress        — Trigger manual compression
# GET  /api/memory/tiers           — Tier distribution (hot/warm/cold/frozen)

# ─── REAL-TIME ───
# WS   /ws/events                  — Live event stream (WebSocket)
# WS   /ws/terminal/{agent_id}     — Live terminal output (WebSocket)

# studio/websocket.py
class StudioWebSocket:
    """Broadcasts Galaxy events to connected dashboard clients."""

    connections: list[WebSocket]

    async def broadcast(self, event: Event) -> None:
        """Send event to all connected dashboard clients."""

    async def handle_connection(self, ws: WebSocket) -> None:
        """Accept WebSocket, add to connections, stream events."""
```

### Phase 5 Build Order (8 weeks)

```
Week 1-2: Plugin SDK
  ├── plugins/sdk.py, loader.py, sandbox.py
  ├── plugins/permissions.py, health.py, registry.py
  └── tests (sandbox isolation, permission enforcement)

Week 3-4: Blueprints
  ├── blueprints/loader.py, generator.py, detector.py
  ├── blueprints/templates/*.yaml (6 built-in templates)
  ├── CLI: galaxy init --blueprint, galaxy blueprint search
  └── tests

Week 5-6: Cluster + Vault Extensions + Compass (Strategic Intent)
  ├── cluster/topology.py, communication.py, gpu_manager.py
  ├── vault/hibernate.py (project hibernation)
  ├── vault/export.py (cross-hardware .vault export/import)
  ├── compass/engine.py        — CompassEngine (intent processing)
  ├── compass/intent.py        — Intent data models + .galaxy/intent.yaml
  ├── compass/advisor.py       — StrategyAdvisor (per-subsystem guidance)
  ├── compass/alignment.py     — AlignmentChecker (output scoring vs intent)
  ├── compass/evolution.py     — IntentEvolution (adapt over time)
  ├── Wire Compass → Orchestrator (architecture shaped by priorities)
  ├── Wire Compass → Model Router (model selection by budget intent)
  ├── Wire Compass → Workers (intent preamble in every prompt)
  ├── Wire Compass → Trust (5th dimension: intent alignment)
  ├── Wire Compass → Governance (auto-activate policies from intent)
  ├── Wire Compass → Scribe (doc depth from intent preferences)
  └── tests (intent loading, alignment scoring, conflict detection)

Week 7-8: Studio Dashboard
  ├── studio/server.py (FastAPI)
  ├── studio/websocket.py (real-time events)
  ├── studio/api/*.py (all REST endpoints)
  ├── Studio Intent Dashboard view
  ├── Studio Documentation browser (Scribe output)
  ├── Studio frontend (React/Vite — separate build)
  └── Integration tests
```

---

## PHASE 6: Autonomous Operations

```python
# Phase 6 extends existing subsystems:

# 1. Refiner gains proactive mode:
class ProactiveRefiner:
    async def scheduled_scan(self) -> None:
        """Run during idle time. Auto-apply safe optimizations."""

# 2. Distiller gains hierarchical embeddings:
class HierarchicalIndex:
    levels: list[VectorStore]  # Level 0-3 (detail → summary)
    async def cascading_search(self, query: str) -> list[MemoryEntry]:
        """Search L2 → L1 → L0 for precision with speed."""

# 3. Plugin SDK gains WASM isolation:
class WASMSandbox:
    async def load_wasm(self, wasm_path: str) -> WASMInstance
    async def call(self, method: str, params: dict) -> dict

# 4. Community registries:
class PluginRegistry:
    async def search(self, query: str) -> list[PluginInfo]
    async def install_from_registry(self, name: str) -> PluginManifest

class BlueprintRegistry:
    async def search(self, query: str) -> list[BlueprintInfo]
    async def install_from_registry(self, name: str) -> Blueprint

# 5. Cross-workspace learning:
class KnowledgeTransfer:
    async def export_patterns(self, project: str) -> list[Pattern]
    async def import_patterns(self, patterns: list[Pattern]) -> None

# 6. Skill system:
class SkillManager:
    async def record_skill(self, task: Task, result: TaskResult) -> Skill:
        """Record successful task as reusable skill."""
    async def find_skill(self, task_description: str) -> Skill | None:
        """Find matching skill for new task."""
    async def apply_skill(self, skill: Skill, task: Task) -> TaskResult:
        """Apply saved skill pattern to new task."""

# 7. Compass gains full autonomy:
class AutonomousCompass:
    async def auto_evolve_intent(self, project_state: ProjectState) -> IntentUpdate:
        """Automatically adapt intent as project evolves."""
    async def cross_project_intent_learning(self, projects: list[str]) -> IntentPatterns:
        """Learn intent patterns across multiple projects."""
    async def predict_intent_conflicts(self, intent: ProjectIntent) -> list[Conflict]:
        """Proactively detect intent contradictions before they cause issues."""

# 8. Scribe gains autonomous doc maintenance:
class AutonomousScribe:
    async def scheduled_drift_repair(self) -> list[DocUpdate]:
        """Periodically scan for doc drift, auto-repair."""
    async def cross_reference_audit(self) -> DocHealthReport:
        """Verify all cross-references, links, imports in docs are valid."""
```

---

## END-USER INSTALLATION & USAGE GUIDE

### Prerequisites (ONLY these two — Galaxy handles the rest)
```
- Python 3.11+
- Git
That's it. Galaxy auto-installs everything else.
```

### Install (3 commands total)
```bash
# Step 1: Install Galaxy (pip handles all Python dependencies)
pip install galaxy-ai

# Step 2: Auto-setup (ONE command — installs tmux, Ollama, pulls models)
galaxy setup
#  → Checks Python version                    ✅
#  → Installs tmux (apt/brew/pacman)           ✅
#  → Installs Ollama                           ✅
#  → Detects GPU + VRAM                        ✅
#  → Pulls best models for your hardware       ✅
#  → Generates default config                  ✅
#  → Ready!                                    🚀

# Step 3: Build something (starts CLI + web dashboard TOGETHER)
mkdir my-app && cd my-app
galaxy run "Build a REST API with user auth"
#  → Terminal shows live progress (Rich CLI)
#  → Browser auto-opens http://localhost:8420 (Galaxy Studio)
#  → Both work simultaneously. No separate commands.
```

### That's It. No Separate Steps For:
```
❌ No manual tmux install          → galaxy setup handles it
❌ No manual Ollama install        → galaxy setup handles it
❌ No manual model pulling         → galaxy setup handles it
❌ No manual Redis install         → uses in-memory event bus
❌ No manual PostgreSQL install    → uses SQLite by default
❌ No separate `galaxy studio`     → starts WITH `galaxy run`
❌ No separate pip install[studio] → Studio included by default
```

### Quick Start
```bash
# Initialize with a blueprint
galaxy init --blueprint fullstack-web-app

# Build something (CLI + dashboard start together)
galaxy run "Build a REST API with authentication"

# Check status
galaxy status

# Pause work
galaxy pause

# Resume later (even with different models)
galaxy resume
galaxy resume --worker-model deepseek-coder:7b

# Checkpoint
galaxy checkpoint

# Hibernate for long-term storage
galaxy hibernate

# Wake up later
galaxy wake
```

### Configuration (auto-generated, edit if you want)
```bash
# Galaxy creates .galaxy/ directory in your project:
my-app/
├── .galaxy/
│   ├── galaxy.config.yaml     # Main configuration (auto-generated)
│   ├── memory/                # Persistent memory
│   ├── checkpoints/           # State snapshots
│   ├── logs/                  # Execution logs
│   └── plugins/               # Installed plugins

# OR just edit config through the web dashboard!
# http://localhost:8420 → Settings → Configuration Editor
```

### Using Cloud Models (optional)
```yaml
# galaxy.config.yaml — or configure via web dashboard
galaxy:
  models:
    master:
      provider: openai
      model: gpt-4o
      api_key_env: OPENAI_API_KEY  # Reads from environment
    worker:
      provider: ollama
      model: qwen2.5-coder:7b     # Local for parallel workers
```

---

## COMPLETE FILE COUNT SUMMARY

| Phase | New Files | Key Additions | Cumulative |
|-------|----------|---------------|------------|
| 1 | ~55 files | Core, Orchestrator, Terminal, Tools, Studio, Forge | 55 |
| 2 | ~25 files | Memory, Cortex, Vault | 80 |
| 3 | ~30 files | Sentinel, Governance, Trust, **Scribe (10 files)** | 110 |
| 4 | ~25 files | Sync, Forge Labs, Refiner, Distiller, Ledger | 135 |
| 5 | ~45 files | Plugins, Blueprints, Cluster, Studio advanced, **Compass (6 files)** | 180 |
| 6 | ~20 files | Autonomous extensions for Refiner, Compass, Scribe | 200 |

**Total: ~200 Python source files + tests + configs + templates**

**27 Subsystems including Galaxy Scribe (docs) and Galaxy Compass (intent)**

**Repository: https://github.com/VishalGovindasamy-15/galaxy-ai**

---

## TESTING STRATEGY

```
Unit tests:     pytest (every module, every file gets a paired test)
Integration:    Full pipeline tests (boot → plan → execute → validate)
E2E:            "Build a REST API" test with real Ollama models
Coverage:       Target 80%+ (enforced by quality gates)
CI:             GitHub Actions (lint + type check + unit tests)
Repo:           https://github.com/VishalGovindasamy-15/galaxy-ai

Key test scenarios:
1. Single worker task (file generation + validation)
2. Multi-worker parallel execution (no conflicts)
3. Crash recovery (kill process mid-execution, restart)
4. Pause/resume (pause, swap models, resume)
5. Model fallback (local model fails → cloud escalation)
6. Memory persistence (stop, restart, memories intact)
7. Trust scoring accuracy (high trust = good code)
8. Policy enforcement (blocked action = actually blocked)
9. Escalation chain (Worker → Domain → Master → Fallback)
10. Unified startup (CLI + Studio start together)
11. Scribe doc generation (file created → docs auto-generated)
12. Scribe drift detection (code changed → stale docs detected + repaired)
13. Compass intent alignment (security intent → blocks insecure code)
14. Compass model routing (budget: minimal → all-local models selected)
15. Compass intent evolution (project grows → intent update suggested)
```

---

**This completes the Galaxy Implementation Guide (Parts 1–5).**
All 27 subsystems are covered with exact file paths, class definitions, method signatures, data models, and build order.
**Repository: https://github.com/VishalGovindasamy-15/galaxy-ai**
