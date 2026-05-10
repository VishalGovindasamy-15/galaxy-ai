# Galaxy Implementation Guide — Part 1: Project Foundation

> This is Part 1 of 5. Each part covers one or more development phases.

---

## 1. Package Identity

```
Name:        galaxy-ai
Language:    Python 3.11+
Type:        pip-installable CLI + library
License:     MIT
Repository:  github.com/VishalGovindasamy-15/galaxy-ai
Entry point: galaxy (CLI command)
```

**Install & Run (ONE command each):**
```bash
# Install — handles ALL dependencies automatically
pip install galaxy-ai

# First-time setup — auto-detects GPU, installs Ollama if needed, pulls models
galaxy setup

# Run — starts BOTH terminal CLI + web dashboard together
galaxy run "Build a REST API with user auth"
#  → Terminal: live progress in CLI
#  → Browser: auto-opens http://localhost:8420 (Galaxy Studio)

# That's it. No separate commands needed.
```

**What `galaxy setup` does automatically:**
```
1. Check Python version (≥3.11)             ✅
2. Check/install tmux                       ✅ (apt/brew auto-install)
3. Check/install Ollama                     ✅ (curl install script)
4. Pull default models via Ollama           ✅ (qwen2.5-coder:7b)
5. Detect GPU + available VRAM              ✅ (nvidia-smi)
6. Auto-select best models for your hardware ✅
7. Generate galaxy.config.yaml              ✅
8. Ready to go!                             🚀
```

**No manual dependency installation needed:**
- ❌ No manual Redis install (uses in-memory event bus by default)
- ❌ No manual PostgreSQL install (uses SQLite by default)
- ❌ No manual tmux install (`galaxy setup` handles it)
- ❌ No manual Ollama install (`galaxy setup` handles it)
- ❌ No manual model pulling (`galaxy setup` handles it)

---

## 2. Project Directory Structure

```
galaxy-ai/
├── pyproject.toml                    # Package config, dependencies, entry points
├── README.md
├── LICENSE
├── Makefile                          # Dev commands (test, lint, build, publish)
├── docker-compose.yml                # Redis + PostgreSQL for dev
├── .env.example
│
├── src/
│   └── galaxy/
│       ├── __init__.py               # Version, package exports
│       ├── __main__.py               # python -m galaxy
│       │
│       ├── cli/                      # CLI Interface (Click/Typer)
│       │   ├── __init__.py
│       │   ├── app.py                # Main CLI app (typer)
│       │   ├── commands/
│       │   │   ├── setup_cmd.py     # galaxy setup (auto-install deps)
│       │   │   ├── init_cmd.py       # galaxy init
│       │   │   ├── run_cmd.py        # galaxy run (starts CLI + Studio together)
│       │   │   ├── pause_cmd.py      # galaxy pause / resume
│       │   │   ├── status_cmd.py     # galaxy status
│       │   │   ├── checkpoint_cmd.py # galaxy checkpoint
│       │   │   ├── export_cmd.py     # galaxy export / import
│       │   │   ├── hibernate_cmd.py  # galaxy hibernate / wake
│       │   │   ├── plugin_cmd.py     # galaxy plugin install/list/remove
│       │   │   └── blueprint_cmd.py  # galaxy blueprint search/install
│       │   ├── setup_helper.py       # Auto-detect hardware, install tmux/Ollama
│       │   └── formatters.py         # Rich console output formatting
│       │
│       ├── core/                     # Galaxy Core (The Kernel)
│       │   ├── __init__.py
│       │   ├── kernel.py             # GalaxyKernel — main lifecycle
│       │   ├── config.py             # Configuration loader (YAML)
│       │   ├── constants.py          # System constants, defaults
│       │   ├── exceptions.py         # All custom exceptions
│       │   ├── types.py              # Shared type definitions
│       │   └── version.py            # Version info
│       │
│       ├── events/                   # Event Bus (in-memory default, Redis optional)
│       │   ├── __init__.py
│       │   ├── bus.py                # EventBus class
│       │   ├── topics.py             # Event topic definitions
│       │   ├── events.py             # Event dataclasses
│       │   └── handlers.py           # Base event handler
│       │
│       ├── agents/                   # Agent Runtime
│       │   ├── __init__.py
│       │   ├── base.py               # BaseAgent abstract class
│       │   ├── master.py             # MasterAgent
│       │   ├── domain.py             # DomainAgent
│       │   ├── worker.py             # WorkerAgent
│       │   ├── lifecycle.py          # Agent lifecycle manager
│       │   ├── registry.py           # Active agent registry
│       │   ├── communication.py      # Agent message protocol
│       │   └── prompts/              # System prompts per tier
│       │       ├── master_prompt.py
│       │       ├── domain_prompt.py
│       │       └── worker_prompt.py
│       │
│       ├── orchestrator/             # Orchestration Engine
│       │   ├── __init__.py
│       │   ├── orchestrator.py       # Main orchestration loop
│       │   ├── planner.py            # Task decomposition (Master → Domains → Workers)
│       │   ├── task_graph.py         # DAG engine
│       │   ├── task.py               # Task dataclass + state machine
│       │   ├── scheduler.py          # VRAM-aware task scheduler
│       │   ├── executor.py           # Parallel task executor
│       │   ├── escalation.py         # Hierarchical escalation: Worker→Domain→Master→User
│       │   └── validator.py          # Architecture verification pipeline
│       │
│       ├── tools/                    # Tool Execution Layer
│       │   ├── __init__.py
│       │   ├── base.py               # BaseTool abstract class
│       │   ├── registry.py           # Tool registry (discover + register)
│       │   ├── permission.py         # Permission checker
│       │   ├── sandbox.py            # Sandbox execution environment
│       │   ├── builtin/              # Built-in tools
│       │   │   ├── file_read.py
│       │   │   ├── file_write.py
│       │   │   ├── file_edit.py
│       │   │   ├── terminal.py       # Command execution
│       │   │   ├── search.py         # ripgrep/grep search
│       │   │   ├── git.py            # Git operations
│       │   │   ├── browser.py        # Web browsing (future)
│       │   │   └── tree.py           # Directory tree listing
│       │   └── schemas.py            # Tool input/output schemas
│       │
│       ├── models/                   # Model Routing Layer
│       │   ├── __init__.py
│       │   ├── router.py             # ModelRouter — pick best model per task
│       │   ├── providers/
│       │   │   ├── base.py           # BaseProvider abstract
│       │   │   ├── ollama.py         # Ollama local provider
│       │   │   ├── openai.py         # OpenAI cloud provider
│       │   │   ├── anthropic.py      # Anthropic cloud provider
│       │   │   ├── google.py         # Google Gemini provider
│       │   │   ├── groq.py           # Groq cloud provider
│       │   │   ├── deepseek.py       # DeepSeek cloud provider
│       │   │   ├── vllm.py           # vLLM self-hosted provider
│       │   │   ├── openai_compat.py  # Any OpenAI-compatible (LM Studio, Jan)
│       │   │   └── litellm.py        # LiteLLM universal proxy (100+ providers)
│       │   ├── registry.py           # ProviderRegistry (auto-discover)
│       │   ├── vram.py               # VRAM detection + monitoring
│       │   └── pool.py               # Model pool manager (load/unload)
│       │
│       ├── terminal/                 # Terminal Orchestration (tmux)
│       │   ├── __init__.py
│       │   ├── manager.py            # TerminalManager
│       │   ├── session.py            # TmuxSession wrapper
│       │   ├── executor.py           # Command executor within session
│       │   └── parser.py             # Output parser
│       │
│       ├── memory/                   # Memory System (Phase 2)
│       │   ├── __init__.py
│       │   ├── manager.py            # MemoryManager
│       │   ├── store.py              # MemoryStore (file-based)
│       │   ├── types.py              # Memory type definitions
│       │   ├── embeddings.py         # Embedding generator
│       │   ├── vector_store.py       # Vector similarity search
│       │   └── hierarchy.py          # 5-level memory hierarchy
│       │
│       ├── cortex/                   # Semantic Code Intelligence (Phase 2)
│       │   ├── __init__.py
│       │   ├── engine.py             # CortexEngine — main entry
│       │   ├── parser.py             # tree-sitter multi-language parser
│       │   ├── graphs/
│       │   │   ├── ast_graph.py
│       │   │   ├── symbol_graph.py
│       │   │   ├── import_graph.py
│       │   │   ├── call_graph.py
│       │   │   ├── api_graph.py
│       │   │   └── dataflow_graph.py
│       │   └── query.py              # Graph query API
│       │
│       ├── vault/                    # Persistence & Recovery (Phase 1 basic, Phase 2 full)
│       │   ├── __init__.py
│       │   ├── checkpoint.py         # Checkpoint engine
│       │   ├── recovery.py           # Crash recovery manager
│       │   ├── snapshot.py           # State serializer
│       │   ├── hibernate.py          # Hibernation manager
│       │   ├── export.py             # Cross-hardware export/import
│       │   └── wal.py                # Write-ahead log
│       │
│       ├── sentinel/                 # Consistency Governance (Phase 3)
│       │   ├── __init__.py
│       │   ├── engine.py             # SentinelEngine — daemon
│       │   ├── style.py              # Style profile learning + enforcement
│       │   ├── architecture.py       # Architecture drift detection
│       │   ├── naming.py             # Naming governance
│       │   ├── duplication.py        # Abstraction duplication
│       │   └── api_consistency.py    # API contract enforcement
│       │
│       ├── governance/               # Policy Engine (Phase 3)
│       │   ├── __init__.py
│       │   ├── engine.py             # GovernanceEngine
│       │   ├── policy.py             # Policy loader + evaluator
│       │   ├── domains/
│       │   │   ├── security.py
│       │   │   ├── compliance.py
│       │   │   ├── deployment.py
│       │   │   ├── access_control.py
│       │   │   ├── quality_gates.py
│       │   │   └── operational.py
│       │   └── audit.py              # Audit trail logger
│       │
│       ├── trust/                    # Confidence & Trust Scoring (Phase 3)
│       │   ├── __init__.py
│       │   ├── scorer.py             # TrustScorer — 4 dimensions
│       │   ├── reputation.py         # Agent reputation tracker
│       │   ├── calibration.py        # Confidence calibration
│       │   ├── decay.py              # Trust decay over time
│       │   └── automation.py         # Trust-driven merge/block decisions
│       │
│       ├── sync/                     # Transaction Consistency (Phase 4)
│       │   ├── __init__.py
│       │   ├── lock_manager.py       # File-level locking
│       │   ├── changeset.py          # Atomic changeset transactions
│       │   ├── intent.py             # Intent-based coordination
│       │   ├── conflict.py           # Merge conflict resolution
│       │   └── commit_order.py       # Dependency-aware commit ordering
│       │
│       ├── forge/                    # Validation + Experiments (Phase 1 basic → Phase 3 full)
│       │   ├── __init__.py
│       │   ├── validator.py          # ContinuousValidator — validates EVERY generated file
│       │   ├── checks/              # Individual validation steps
│       │   │   ├── syntax.py         # Language-aware syntax checking
│       │   │   ├── imports.py        # Import resolution verification
│       │   │   ├── types.py          # Type checking (mypy/pyright/tsc)
│       │   │   ├── lint.py           # Linting (ruff/eslint) + auto-fix
│       │   │   ├── build.py          # Incremental build verification
│       │   │   └── tests.py          # Related test runner
│       │   ├── auto_fix.py           # Auto-fix trivial issues (formatting, imports)
│       │   ├── retry_context.py      # Build error context for retry prompts
│       │   ├── labs.py               # Experimental branching (Forge Labs)
│       │   ├── scorer.py             # Experiment scoring
│       │   └── promotion.py          # Winner promotion
│       │
│       ├── refiner/                  # Autonomous Optimization (Phase 4)
│       │   ├── __init__.py
│       │   ├── engine.py             # RefinerEngine
│       │   ├── detectors/
│       │   │   ├── performance.py
│       │   │   ├── architecture.py
│       │   │   ├── code_quality.py
│       │   │   ├── resources.py
│       │   │   └── dependencies.py
│       │   └── optimizer.py          # Safe optimization executor
│       │
│       ├── distiller/                # Knowledge Compression (Phase 4)
│       │   ├── __init__.py
│       │   ├── engine.py             # DistillerEngine
│       │   ├── summarizer.py         # Summarization pipeline
│       │   ├── compactor.py          # Memory compaction
│       │   ├── pruner.py             # Semantic pruning
│       │   └── tiering.py            # Archive tiering (hot/warm/cold)
│       │
│       ├── ledger/                   # Cost Accounting (Phase 4)
│       │   ├── __init__.py
│       │   ├── tracker.py            # Cost tracker
│       │   ├── budget.py             # Budget enforcement
│       │   ├── reports.py            # Cost reports + optimization suggestions
│       │   └── models.py             # Cost data models
│       │
│       ├── plugins/                  # Plugin SDK (Phase 5)
│       │   ├── __init__.py
│       │   ├── sdk.py                # Plugin SDK
│       │   ├── loader.py             # Plugin loader + validator
│       │   ├── sandbox.py            # Plugin sandbox (subprocess/docker)
│       │   ├── registry.py           # Plugin registry
│       │   ├── permissions.py        # Plugin permission system
│       │   └── health.py             # Plugin health monitoring
│       │
│       ├── blueprints/               # Workflow Templates (Phase 5)
│       │   ├── __init__.py
│       │   ├── loader.py             # Blueprint loader
│       │   ├── generator.py          # Project scaffold generator
│       │   ├── detector.py           # Auto-detect existing project type
│       │   └── templates/            # Built-in templates (YAML)
│       │       ├── fullstack_web.yaml
│       │       ├── rest_api.yaml
│       │       ├── ml_pipeline.yaml
│       │       ├── realtime_app.yaml
│       │       ├── cli_tool.yaml
│       │       └── mobile_backend.yaml
│       │
│       ├── cluster/                  # Distributed Execution (Phase 5)
│       │   ├── __init__.py
│       │   ├── topology.py           # Cluster topology manager
│       │   ├── node.py               # Node representation
│       │   ├── communication.py      # Cross-node event bus
│       │   └── gpu_manager.py        # Multi-GPU cluster management
│       │
│       └── studio/                   # Web Dashboard (Phase 5)
│           ├── __init__.py
│           ├── server.py             # FastAPI server
│           ├── websocket.py          # Real-time WebSocket updates
│           ├── api/                   # REST API endpoints
│           │   ├── tasks.py
│           │   ├── agents.py
│           │   ├── models_api.py     # Model management endpoints
│           │   ├── checkpoints.py    # Checkpoint management endpoints
│           │   ├── config_api.py     # Configuration management endpoints
│           │   ├── memory.py
│           │   ├── trust.py
│           │   ├── policies.py
│           │   ├── costs.py
│           │   ├── plugins_api.py    # Plugin management endpoints
│           │   ├── blueprints_api.py # Blueprint management endpoints
│           │   └── validation.py     # Validation status endpoints
│           └── frontend/             # React/Vite dashboard (built separately)
│
├── tests/
│   ├── conftest.py                   # Shared fixtures
│   ├── unit/                         # Unit tests (mirror src/ structure)
│   │   ├── test_core/
│   │   ├── test_agents/
│   │   ├── test_orchestrator/
│   │   ├── test_tools/
│   │   ├── test_models/
│   │   └── ...
│   ├── integration/                  # Integration tests
│   │   ├── test_agent_lifecycle.py
│   │   ├── test_task_execution.py
│   │   └── test_full_pipeline.py
│   └── e2e/                          # End-to-end tests
│       └── test_build_project.py
│
└── docs/
    ├── architecture.md
    ├── getting-started.md
    ├── configuration.md
    ├── plugins.md
    └── api-reference.md
```

---

## 3. Dependencies (pyproject.toml)

```toml
[project]
name = "galaxy-ai"
version = "0.1.0"
description = "AI-Native Hierarchical Multi-Agent Software Engineering OS"
requires-python = ">=3.11"
license = {text = "MIT"}

dependencies = [
    # CLI
    "typer[all]>=0.12",
    "rich>=13.0",

    # LLM Providers (local + cloud)
    "httpx>=0.27",                # HTTP client for API calls
    "openai>=1.40",               # OpenAI + compatible APIs (also used for vLLM, Groq, etc.)
    "anthropic>=0.34",            # Anthropic API
    "ollama>=0.3",                # Ollama Python client
    "google-generativeai>=0.7",   # Google Gemini API

    # Database (SQLite by default — zero setup)
    "sqlalchemy>=2.0",            # ORM
    "aiosqlite>=0.20",            # Async SQLite driver (default)
    "alembic>=1.13",              # Database migrations

    # Configuration
    "pyyaml>=6.0",                # YAML config parsing
    "pydantic>=2.5",              # Data validation + settings
    "pydantic-settings>=2.1",     # Environment-based config

    # Terminal
    "libtmux>=0.37",              # tmux Python API

    # Web Dashboard (Studio — included by default, starts with `galaxy run`)
    "fastapi>=0.115",             # Studio REST API
    "uvicorn>=0.30",              # ASGI server
    "websockets>=12.0",           # Real-time Studio events

    # Code Intelligence
    "tree-sitter>=0.22",          # AST parsing
    "tree-sitter-languages>=1.10", # Language grammars

    # Memory + Embeddings
    "numpy>=1.26",                # Vector operations

    # File operations
    "watchfiles>=0.21",           # File change monitoring
    "gitpython>=3.1",             # Git operations

    # Async
    "anyio>=4.0",                 # Async compatibility

    # Utilities
    "python-dotenv>=1.0",         # .env loading
    "tenacity>=8.2",              # Retry logic
    "structlog>=24.0",            # Structured logging
    "psutil>=5.9",                # System resource monitoring
]

[project.optional-dependencies]
enterprise = [
    "redis>=5.0",                 # Redis event bus (for multi-machine clusters)
    "asyncpg>=0.29",              # PostgreSQL driver (for enterprise databases)
]
embeddings = [
    "sentence-transformers>=3.0", # Local embedding models (optional, Ollama used by default)
]

[project.scripts]
galaxy = "galaxy.cli.app:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

---

## 4. Core Configuration Schema

```yaml
# galaxy.config.yaml — Default configuration

galaxy:
  version: "0.1.0"
  project_name: ""
  workspace: "."

  # Model Configuration
  models:
    master:
      provider: ollama
      model: qwen2.5-coder:14b
      temperature: 0.3
    domain:
      provider: ollama
      model: qwen2.5-coder:14b
      temperature: 0.4
    worker:
      provider: ollama
      model: qwen2.5-coder:7b
      temperature: 0.2
    embedding:
      provider: ollama
      model: nomic-embed-text
    fallback:
      provider: null  # Set to openai/anthropic for cloud fallback

  # Scheduler
  scheduler:
    mode: balanced  # speed | balanced | quality
    max_parallel_workers: auto  # auto = VRAM-based
    vram_reserve_mb: 512

  # Agent Limits
  agents:
    max_domain_agents: 10
    max_workers_per_domain: 50
    max_retry_loops: 5
    max_recursion_depth: 3
    idle_timeout_seconds: 300

  # Persistence
  vault:
    checkpoint_interval_minutes: 5
    crash_recovery: true
    max_snapshots: 10

  # Paths
  paths:
    galaxy_dir: ".galaxy"
    memory_dir: ".galaxy/memory"
    checkpoints_dir: ".galaxy/checkpoints"
    plugins_dir: ".galaxy/plugins"
    logs_dir: ".galaxy/logs"

  # Database — SQLite by default (zero setup needed)
  database:
    url: "sqlite+aiosqlite:///.galaxy/galaxy.db"  # Default: SQLite (no install needed)
    # url: "postgresql+asyncpg://localhost/galaxy"  # Optional: PostgreSQL for enterprise

  # Event Bus — in-memory by default (zero setup needed)
  event_bus:
    backend: memory              # memory (default, zero setup) | redis
    # redis_url: "redis://localhost:6379/0"  # Optional: Redis for multi-machine

  # Studio (Web Dashboard) — starts WITH Galaxy, not separately
  studio:
    enabled: true                # Dashboard auto-starts with `galaxy run`
    port: 8420
    auto_open_browser: true      # Auto-open browser on start
    host: "127.0.0.1"            # localhost only by default

  # Logging
  logging:
    level: INFO
    file: ".galaxy/logs/galaxy.log"
    structured: true
```

---

## 5. Module Dependency Order (Build Sequence)

```
Layer 0 (Zero deps):     core, events, types
Layer 1 (Core only):     tools, models, terminal, vault(basic)
Layer 2 (Layer 0+1):     agents, orchestrator
Layer 3 (Layer 0-2):     memory, cortex
Layer 4 (Layer 0-3):     sentinel, governance, trust, forge
Layer 5 (Layer 0-4):     sync, refiner, distiller, ledger
Layer 6 (Layer 0-5):     plugins, blueprints, cluster, studio
Layer 7 (Everything):    cli (ties it all together)
```

This is the order we build. Each layer only depends on layers below it.

---

## 6. Database Schema (SQLAlchemy Models)

```
Tables (created via Alembic migrations):

tasks              — Task graph nodes (id, status, agent, progress, deps)
task_edges          — DAG edges (from_task, to_task)
agents              — Agent registry (id, role, tier, model, status)
checkpoints         — Checkpoint metadata (id, timestamp, trigger, path)
events              — Event log / WAL (id, timestamp, type, payload)
trust_scores        — Per-output trust profiles
agent_reputation    — Per-agent historical trust
cost_records        — Inference/compute cost tracking
policy_violations   — Governance audit trail
memory_index        — Memory file metadata + access tracking
lock_state          — Active file locks (Sync)
changesets          — Active changesets (Sync)
```

---

**Next: Part 2 — Phase 1 Implementation (every class, interface, and method)**
