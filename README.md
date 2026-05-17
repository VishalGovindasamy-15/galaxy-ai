# Galaxy AI ✦ The AI Engineering Operating System

[![Tests](https://img.shields.io/badge/tests-784%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-purple)]()
[![Phase](https://img.shields.io/badge/phase-2%20complete-blueviolet)]()

> **Galaxy** is a fully autonomous AI-powered software engineering OS that turns natural language into production-ready codebases. Give it a prompt → get a complete, tested, deployable project.

```
galaxy run "Build a FastAPI blog with auth, CRUD, and tests"
```

---

## 🌌 Architecture

Galaxy uses a **3-tier agent hierarchy** with a **5-stage cognitive pipeline**:

```
USER
  ↓
BRAINSTORM ENGINE
  ├── Temp Ideas (exploration)
  ├── Permanent Ideas (approved truth)
  └── Decision Logger (timestamps, history)
  ↓
MASTER COGNITIVE PIPELINE
  ├── [Normal Mode] Direct planning (fast, 2 stages)
  └── [Reasoning Mode] Deep analysis (5 stages)
      ├── Prompt Expander → structured spec
      ├── Planner → dependency-aware DAG
      ├── Retriever → context assembly
      ├── Reflection → validate plan
      └── Synthesizer → final plan
  ↓
DOMAIN AGENTS → Execution Contracts
  { target_file, function, signature, dependencies, constraints }
  ↓
WORKERS → Code Chunks
  { target_file, target_symbol, operation, content }
  ↓
INTEGRATOR → Merges chunks into files
  ↓
FORGE → BUILD/TEST/FIX → OUTPUT
```

### Core Subsystems

| Subsystem | Purpose |
|-----------|---------|
| **Kernel** | Boot/shutdown lifecycle, subsystem registration |
| **EventBus** | Async pub/sub for inter-agent communication |
| **Models** | Multi-provider LLM routing (Ollama, OpenAI, Groq, DeepSeek) |
| **Agents** | 3-tier hierarchy with checkpoint/restore + contract/chunk support |
| **Tools** | File I/O, terminal, search, git — with tier-based permissions |
| **Orchestrator** | DAG-based task scheduling with 5-level escalation |
| **Brainstorm** | Pre-execution cognitive layer: temp ideas ↔ permanent ideas |
| **Cognitive** | 5-stage reasoning pipeline (Expand → Plan → Retrieve → Reflect → Synthesize) |
| **Contracts** | Structured execution contracts with typed parameters |
| **Integrator** | Chunk-based code merger with conflict detection |
| **Project** | Source-of-truth (`.galaxy/project.yaml`) with analyzer + reconstructor |
| **Scaling** | Rate limiting, cost estimation, GPU-aware resource management |
| **Vault** | Checkpoint/recovery with crash markers |
| **Forge** | Continuous code validation (syntax, imports, lint) |
| **CLI** | Rich terminal UI with dashboard, activity feed, task graph |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) (for local models)
- tmux (for terminal management)

### Install

```bash
# Clone
git clone https://github.com/VishalGovindasamy-15/galaxy-ai
cd galaxy-ai

# Create virtualenv
python -m venv .venv
source .venv/bin/activate

# Install (editable mode with dev tools)
pip install -e ".[dev]"

# Setup (auto-detect GPU, check dependencies)
galaxy setup
```

### Initialize a Project

```bash
mkdir my-project && cd my-project
galaxy init
```

### Build Something

```bash
# Full autonomous generation
galaxy run "Create a REST API with user authentication, CRUD endpoints, and tests"

# Interactive brainstorming first
galaxy brainstorm "Build an e-commerce platform"

# Chat with the master agent
galaxy chat

# Chat with specific model and reasoning mode
galaxy chat --model qwen2.5-coder:7b --mode reasoning
```

### Manage Configuration

```bash
# Show current config
galaxy config

# Check project status
galaxy status
```

---

## 🧪 Testing

```bash
# Run all tests (784 tests)
make test

# With coverage
make test-cov

# Only unit tests
pytest tests/unit/ -v

# Only integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v
```

---

## 📐 Project Structure

```
src/galaxy/
├── core/               # Foundation layer
│   ├── constants.py    # All system constants
│   ├── exceptions.py   # 30+ exception hierarchy
│   ├── types.py        # Core data structures
│   ├── config.py       # Pydantic config management
│   ├── kernel.py       # Boot/shutdown lifecycle
│   └── version.py      # Version management
├── events/             # Event infrastructure
│   ├── events.py       # Event dataclass
│   └── bus.py          # Async EventBus (pub/sub, wildcards, request/reply)
├── models/             # LLM provider layer
│   ├── vram.py         # GPU detection, model selection
│   ├── router.py       # Tier-based routing with fallback
│   └── providers/      # Ollama, OpenAI, Groq, DeepSeek
├── agents/             # 3-tier agent system
│   ├── base.py         # BaseAgent with LLM, events, checkpoint
│   ├── worker.py       # Code generation worker (+ contract chunks)
│   ├── domain.py       # Domain decomposer (+ contract planning)
│   ├── master.py       # Architecture planner (+ cognitive pipeline)
│   └── registry.py     # Agent lifecycle + limit enforcement
├── brainstorm/         # Pre-execution cognitive layer
│   ├── types.py        # Idea, IdeaStatus, BrainstormSession
│   ├── temp_store.py   # Temp ideas store (exploration)
│   ├── permanent_store.py  # Approved ideas (truth)
│   ├── decision_log.py # Decision logger with history
│   ├── engine.py       # BrainstormEngine orchestrator
│   └── interviewer.py  # Clarifying question generator
├── cognitive/          # 5-stage reasoning pipeline
│   ├── types.py        # CognitiveMode, PipelineStage, ExecutionPlan
│   ├── expander.py     # PromptExpander (vague → structured spec)
│   ├── planner.py      # CognitivePlanner (spec → dependency DAG)
│   ├── retriever.py    # ContextRetriever (fetch relevant context)
│   ├── reflection.py   # ReflectionEngine (critique + verify)
│   ├── synthesizer.py  # SynthesizerEngine (final plan assembly)
│   └── pipeline.py     # CognitivePipeline (orchestrates the chain)
├── contracts/          # Structured execution contracts
│   ├── types.py        # ExecutionContract, CodeChunk, ChunkOperation
│   └── builder.py      # ContractBuilder (fluent API)
├── integrator/         # Chunk-based code merger
│   ├── merger.py       # Merges code chunks into files
│   ├── conflict.py     # Conflict detection + resolution
│   └── engine.py       # IntegratorEngine
├── project/            # Project source-of-truth
│   ├── spec.py         # ProjectSpec (.galaxy/project.yaml)
│   ├── loader.py       # Load/save project spec (YAML)
│   ├── analyzer.py     # Read existing project → generate spec
│   └── reconstructor.py # Rebuild project from spec
├── scaling/            # Cloud scaling + cost management
│   ├── limiter.py      # Rate limiter + resource limits
│   └── cost_estimator.py # Token cost estimation
├── tools/              # Agent tool system
│   ├── base.py         # BaseTool + OpenAI schema generation
│   ├── registry.py     # Tier-based tool registry
│   └── builtin/        # file_read, file_write, file_edit, terminal, search, git, tree
├── terminal/           # Terminal management
│   └── manager.py      # tmux session lifecycle
├── orchestrator/       # Execution engine
│   ├── task_graph.py   # DAG with dynamic insertion
│   ├── scheduler.py    # VRAM-aware parallelism
│   ├── orchestrator.py # Plan → execute pipeline
│   └── escalation.py   # 5-level failure handling
├── vault/              # Persistence + recovery
│   └── checkpoint.py   # Checkpoint engine + crash markers
├── forge/              # Code validation
│   └── validator.py    # Syntax, imports, lint checks
└── cli/                # Terminal UI
    ├── app.py          # Typer CLI commands
    ├── colors.py       # Design tokens
    ├── confirm.py      # Permission/approval gate
    ├── keyboard.py     # Hotkey controller
    ├── setup_helper.py # Auto-detect hardware
    ├── commands/       # brainstorm, chat, config
    └── views/          # boot, dashboard, activity, taskgraph
```

---

## ⚡ Key Features

### 5-Stage Cognitive Pipeline
Before generating code, Galaxy *thinks*:
1. **Expand** — Vague prompt → structured project specification
2. **Plan** — Specification → dependency-aware DAG of tasks
3. **Retrieve** — Fetch relevant workspace context
4. **Reflect** — Validate plan integrity (cycle detection, coverage)
5. **Synthesize** — Assemble actionable documentation

### Brainstorming Engine
Explore ideas before committing:
- **Temp Store** — Try ideas freely, categorize, refine
- **Permanent Store** — Approve the best ideas as project truth
- **Decision Log** — Full history with timestamps and rationale

### Contract-Based Generation
Domain agents output **ExecutionContracts** with:
- Target file, function name, operation type
- Typed parameters, return specs, dependencies
- Constraints and validation rules

Workers produce **CodeChunks** that the Integrator merges into files.

### 5-Level Escalation Chain
When a task fails, Galaxy automatically escalates:
1. **Worker retry** — Retry with error context
2. **Domain intervention** — Restructure the subtask
3. **Master restructure** — Re-plan the approach
4. **Model fallback** — Switch to a stronger model
5. **User intervention** — Pause and ask for help

### VRAM-Aware Scheduling
Galaxy auto-detects your GPU and selects optimal models:
- **24GB+**: 14B master + 7B workers (8 concurrent agents)
- **12-24GB**: 7B for all tiers (5 concurrent agents)
- **6-12GB**: 3B for all tiers (3 concurrent agents)
- **No GPU**: CPU mode or cloud providers

### Project Source-of-Truth
`.galaxy/project.yaml` defines your entire project state:
- All files, domains, tech stack, features
- Progress tracking per file
- Portable — rebuild the project from the spec alone

### Live Terminal Dashboard
Rich-based terminal UI with:
- Agent status monitoring
- Activity feed with timestamps
- ASCII task graph (DAG visualization)
- Keyboard shortcuts: [Tab] switch, [Space] approve, [Q] quit

### Crash Recovery
Galaxy checkpoints automatically. If it crashes, run `galaxy resume` to pick up exactly where it left off.

---

## 📋 Configuration

Galaxy uses `galaxy.config.yaml`:

```yaml
models:
  master:
    provider: ollama
    model: qwen2.5-coder:14b
  worker:
    provider: ollama
    model: qwen2.5-coder:7b
  embedding:
    provider: ollama
    model: nomic-embed-text

scheduler:
  mode: balanced  # speed | balanced | quality

agent_limits:
  max_domain_agents: 10
  max_workers_per_domain: 50
```

---

## 🗺️ Roadmap

- [x] **Phase 1**: Foundation (Core, Events, Models, Agents, Tools, Orchestrator, CLI) — 381 tests
- [x] **Phase 2**: Cognitive Engine (Brainstorm, Contracts, Chunks, Pipeline, Dashboard) — 784 tests
- [ ] **Phase 3**: Intelligence (Memory, Code AST, Build/Test/Fix, Auto-docs)
- [ ] **Phase 4**: Quality & Audit (Governance, Trust, Scale, Security Audit)
- [ ] **Phase 5**: Enterprise (Plugins, Blueprints, Compass, Galaxy Studio)
- [ ] **Phase 6**: Autonomous (Self-improvement, Skills, Marketplace)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
