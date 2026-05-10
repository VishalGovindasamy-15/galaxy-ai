# Galaxy AI ✦ The AI Engineering Operating System

[![Tests](https://img.shields.io/badge/tests-380%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-purple)]()

> **Galaxy** is a fully autonomous AI-powered software engineering OS that turns natural language into production-ready codebases. Give it a prompt → get a complete, tested, deployable project.

```
galaxy run "Build a FastAPI blog with auth, CRUD, and tests"
```

---

## 🌌 Architecture

Galaxy uses a **3-tier agent hierarchy** inspired by real engineering teams:

```
┌───────────────────────────────────────┐
│             MASTER AGENT              │  ← Architect: plans, delegates
│          (14B model · reasoning)      │
└─────────────┬─────────────────────────┘
              │ Domain Plans
    ┌─────────┼─────────────┐
    ▼         ▼             ▼
┌───────┐ ┌───────┐   ┌───────┐
│DOMAIN │ │DOMAIN │   │DOMAIN │        ← Tech Leads: decompose, coordinate
│  API  │ │  DB   │   │  UI   │
└──┬──┬─┘ └──┬────┘   └──┬────┘
   │  │      │           │
   ▼  ▼      ▼           ▼
  Workers  Workers     Workers         ← Engineers: write code, run tools
```

### Core Subsystems

| Subsystem | Purpose |
|-----------|---------|
| **Kernel** | Boot/shutdown lifecycle, subsystem registration |
| **EventBus** | Async pub/sub for inter-agent communication |
| **Models** | Multi-provider LLM routing (Ollama, OpenAI, Groq, DeepSeek) |
| **Agents** | 3-tier hierarchy with checkpoint/restore |
| **Tools** | File I/O, terminal, search, git — with tier-based permissions |
| **Orchestrator** | DAG-based task scheduling with 5-level escalation |
| **Vault** | Checkpoint/recovery with crash markers |
| **Forge** | Continuous code validation (syntax, imports, lint) |
| **CLI** | Rich terminal UI with ASCII boot sequence |

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
galaxy run "Create a REST API with user authentication, CRUD endpoints, and tests"
```

---

## 🧪 Testing

```bash
# Run all tests (380 tests)
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
│   ├── __init__.py     # Event dataclass
│   └── bus.py          # Async EventBus (pub/sub, wildcards, request/reply)
├── models/             # LLM provider layer
│   ├── vram.py         # GPU detection, model selection
│   ├── router.py       # Tier-based routing with fallback
│   └── providers/      # Ollama, OpenAI, Groq, DeepSeek
├── agents/             # 3-tier agent system
│   ├── base.py         # BaseAgent with LLM, events, checkpoint
│   ├── worker.py       # Code generation worker
│   ├── domain.py       # Domain decomposer
│   ├── master.py       # Architecture planner
│   └── registry.py     # Agent lifecycle + limit enforcement
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
    ├── setup_helper.py # Auto-detect hardware
    └── views/          # Boot, dashboard, etc.
```

---

## ⚡ Key Features

### 5-Level Escalation Chain
When a task fails, Galaxy automatically escalates:
1. **Worker retry** — Retry with error context
2. **Domain intervention** — Restructure the subtask
3. **Master restructure** — Re-plan the approach
4. **Model fallback** — Switch to a stronger model
5. **User intervention** — Pause and ask for help

### VRAM-Aware Scheduling
Galaxy auto-detects your GPU and selects optimal models:
- **24GB+**: 14B master + 7B workers
- **12-24GB**: 7B for all tiers
- **8-12GB**: 3B for all tiers
- **No GPU**: CPU mode or cloud providers

### Live Updates
Modify the plan mid-execution by talking to the Master agent. Changes propagate through the task graph without losing progress.

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

- [x] **Phase 1**: Foundation (Core, Events, Models, Agents, Tools, Orchestrator, CLI)
- [ ] **Phase 2**: Memory & Intelligence (Embeddings, Vector Store, Code AST)
- [ ] **Phase 3**: Intent Engine (Compass, Scribe)
- [ ] **Phase 4**: Galaxy Studio (Web Dashboard)
- [ ] **Phase 5**: Performance & Scale
- [ ] **Phase 6**: Ecosystem (Plugins, Marketplace)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
