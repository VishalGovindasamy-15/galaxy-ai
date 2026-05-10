# GALAXY — Complete Project Specification

> **An AI-Native Hierarchical Multi-Agent Software Engineering Operating System**
> Local-first · Resource-aware · Fully observable · Self-healing

---

## 1. Vision

Galaxy is NOT a chatbot or simple AI coding assistant. It is a **distributed autonomous engineering platform** that mirrors a real software company:
- A **Master Agent** (CTO) architects and orchestrates
- **Domain Agents** (Team Leads) manage specialized areas
- **Worker Agents** (Engineers) execute scoped tasks
- All coordinated by an **intelligent runtime** with full observability

---

## 2. Core Principles

| Principle | Description |
|-----------|-------------|
| **Hierarchical Delegation** | Master → Domain → Worker. Never flat chaos. |
| **Context Isolation** | Workers see ONLY their scoped task. No context overload. |
| **Architecture-First** | Full verification BEFORE any code generation begins. |
| **Local-First** | Most compute runs locally. Cloud only when needed. |
| **Resource-Aware** | VRAM/RAM/CPU monitoring drives scheduling decisions. |
| **Full Observability** | Every action, decision, and message is traceable. |
| **Self-Healing** | Fault reconstruction, not brute-force regeneration. |
| **Human-in-the-Loop** | Users can inspect, pause, override, and control everything. |

---

## 3. Agent Hierarchy

### Level 1 — Master Agent (CEO/CTO)
- **Model**: Strongest available (cloud Claude/GPT or local 70B+)
- **Responsibilities**: Understand full project vision, create architecture, split into domains, define interfaces, validate integration, resolve conflicts, final decisions
- **Rules**: NEVER writes most code. Acts as architect + orchestrator.

### Level 2 — Domain Agents (Team Leads)
- **Model**: Medium (7B–14B local)
- **Examples**: Frontend, Backend, Database, DevOps, Security, AI/ML, Testing
- **Responsibilities**: Understand ONLY their domain, break modules into tasks, generate implementation plans, validate worker outputs, retry/fix failed generations, maintain domain consistency
- **Created dynamically** by Master based on project needs

### Level 3 — Worker Agents (Engineers)
- **Model**: Small (1B–7B local)
- **Responsibilities**: Generate one function, one class, one API route, one test, one component
- **Rules**: Do NOT know the whole project, business logic, architecture, or unrelated files. Only receive precise scoped tasks with exact parameters.
- **Created dynamically** by Domain Agents based on workload

### Agent Lifecycle
- Agents **terminate after task** completion
- Idle agents are **cleaned up** to free resources
- Successful patterns are **cached as reusable skills**
- Only important memory is **persisted**

### Agent Limits (Prevent Explosion)

| Limit | Default |
|-------|---------|
| Max domain agents | 10 |
| Max workers per domain | 50 |
| Max recursion depth | 3 |
| Max retry loops | 5 |
| Max parallel execution | Hardware-based |

---

## 4. System Architecture

```
                        GALAXY CORE
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
       ▼                     ▼                     ▼
 Control Plane         Agent Runtime         Monitoring Plane
       │                     │                     │
       ▼                     ▼                     ▼
 Config/Policies       Domain Agents         Logs/Metrics
       │                     │                     │
       ▼                     ▼                     ▼
 Permission System     Worker Agents         Dashboard UI
       │                     │
       ▼                     ▼
   Sandbox Layer       Tool Execution Layer
                             │
                             ▼
                     Model Routing Layer
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
     Fast LLM         Reasoning LLM        Embedding Model
                             │
                             ▼
                        Memory System
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   Structured          Semantic/Vector       Graph Memory
   Memory              Memory               (Dependencies)
```

---

## 5. Core Subsystems

### 5.1 Galaxy Core (The Kernel)
The brain of the entire platform.

**Responsibilities:**
- Initialize all subsystems
- Load configurations
- Start agent runtimes
- Connect event bus
- Start monitoring
- Manage full lifecycle

### 5.2 Orchestration Engine

The backbone. Manages the entire execution pipeline:

```
User Request
    ↓
Master Planning
    ↓
Domain Architecture Design
    ↓
Worker Task Design
    ↓
GLOBAL ARCHITECTURE VERIFICATION
    ↓
Dependency Validation
    ↓
Parameter Validation
    ↓
Data Flow Validation
    ↓
Contract Validation
    ↓
Conflict Detection
    ↓
Execution Approval
    ↓
Code Generation (parallel workers)
    ↓
Continuous Build/Test Loop
    ↓
Fault Reconstruction (if needed)
    ↓
Targeted Regeneration
    ↓
Integration
    ↓
Final Project
```

**Key feature: Architecture Freeze Before Execution** — like a compiler's semantic analysis phase, the master verifies ALL architecture, interfaces, schemas, and dependencies BEFORE any worker starts coding.

### 5.3 Task Graph Engine

Not linear tasks. Uses **Directed Acyclic Graphs (DAGs)**.

**Features:**
- Dependency-aware execution ordering
- Priority queues for critical-path tasks
- Parallel execution of independent tasks
- Bottleneck detection
- Dynamic re-prioritization

**Task States:**

| State | Meaning |
|-------|---------|
| `idle` | Waiting for assignment |
| `planning` | Agent is reasoning |
| `generating` | Agent is coding |
| `validating` | Checking output |
| `testing` | Running tests |
| `blocked` | Dependency not met |
| `failed` | Error occurred |
| `retrying` | Reconstruction in progress |
| `completed` | Finished successfully |

### 5.4 Tool Execution Layer

Isolated from agents. Every tool is a self-contained module.

```
Agent
  ↓
Tool Request
  ↓
Permission Check
  ↓
Sandbox
  ↓
Execution Engine
  ↓
Result Normalizer
  ↓
Agent
```

**Built-in Tools:**
- `TerminalTool` — Shell command execution
- `FileReadTool` — Read files
- `FileWriteTool` — Create/overwrite files
- `FileEditTool` — Partial file modification
- `SearchTool` — Code search (grep/glob)
- `WebFetchTool` — Fetch URL content
- `GitTool` — Git operations
- `TestTool` — Run tests
- `CompileTool` — Build/compile
- `LintTool` — Code linting
- `PackageManagerTool` — npm/pip/cargo operations

**Tool Design (inspired by Claude Code):**
- Each tool has: `inputSchema` (Zod validation), `call()`, `checkPermissions()`, `validateInput()`, `isReadOnly()`, `isDestructive()`, `isConcurrencySafe()`
- `buildTool()` factory provides safe defaults (fail-closed)
- Tools are registered in a central registry
- Feature flags enable conditional tool loading

### 5.5 Permission & Sandbox Layer

**Command Governance:**

```
Agent
  ↓
Execution Validator
  ↓
Permission Layer
  ↓
Terminal Runtime
```

**Permission Modes:**
- `restricted` — Workers: minimal permissions, ask for everything
- `standard` — Domain agents: broader but controlled
- `elevated` — Master agent: most permissions
- `user-approved` — Requires human approval

**Command Policies:**

| Command | Allowed? |
|---------|----------|
| `npm install` | Yes |
| `pytest` / `npm test` | Yes |
| `git commit` | Domain+ only |
| `docker compose up` | Configurable |
| `rm -rf /` | **NEVER** |
| `sudo` | Restricted |
| Network access | Configurable |

**Pattern-based rules:** e.g., `Bash(git *)` allows all git commands, `Bash(rm -rf *)` always denied.

**Sandbox Features:**
- Isolated workspace per agent
- Environment variable scoping
- Process tracking (kill runaway tasks)
- Filesystem scope restrictions
- Resource limits (CPU/RAM caps)

### 5.6 Model Routing Layer

**Hierarchical Defaults with Per-Agent Overrides:**

```yaml
models:
  master_default:
    provider: openai       # or ollama
    model: gpt-5           # or qwen-72b
  domain_default:
    provider: ollama
    model: deepseek-coder-v2-16b
  worker_default:
    provider: ollama
    model: qwen2.5-coder-7b

overrides:
  security_domain:
    model: security-specialized-model
  ai_domain:
    model: large-reasoning-model
```

**Features:**
- **Role separated from Model** — don't hardcode `backend_worker = specific_model`
- **Capability-based routing** — simple CRUD → small model, complex architecture → large model
- **Automatic escalation** — worker fails 3x → try stronger model → escalate to domain → escalate to master
- **Local + Cloud hybrid** — master on cloud, workers on local
- **Dynamic hardware awareness** — 8GB VRAM → use 7B workers; 24GB → use 14B workers
- **Hot model pooling** — keep frequently used models warm in memory, reuse across workers

### 5.7 VRAM-Aware Scheduler

```
Task Queue
    ↓
VRAM/RAM/CPU Monitor
    ↓
Scheduler
    ├── Parallel Execution (enough resources)
    └── Queue Execution (insufficient resources)
```

**Scheduler Responsibilities:**
1. **Parallel vs Queue** — Check resources before spawning agents
2. **Dynamic Scaling** — GPU freed → spawn additional workers
3. **Model Swapping** — Low VRAM → switch worker from 14B → 7B
4. **Task Prioritization** — Critical dependency tasks first
5. **Idle Agent Cleanup** — Kill inactive workers, idle models, unused contexts
6. **Predictive Scheduling** — Estimate task complexity + model size + context before execution

**Scheduling Modes:**

| Mode | Behavior |
|------|----------|
| Performance | Aggressive parallelism, max hardware usage |
| Balanced | Speed/resource tradeoff |
| Power Saver | Minimal GPU, queue more tasks |
| Enterprise | Strict resource governance |

**Monitored Metrics:**
- GPU: VRAM used/free, utilization, model allocations, inference queue
- CPU: compilation load, test execution, terminal processes
- RAM: model spill, build consumption, vector DB usage
- Disk/IO: repo size, embeddings, logging, checkpoints
- Agent Load: active, waiting, blocked, execution priority

### 5.8 Memory System

**Hierarchy:**

```
Global System Memory (reusable patterns, framework knowledge)
    ↓
Workspace Memory (project-specific brain — MOST IMPORTANT)
    ↓
Domain Memory (domain-specific context)
    ↓
Task Memory (active subtasks, temporary — auto-expires)
    ↓
Temporary Agent Context (minimal, scoped to exact task)
```

**Memory Types:**

| Type | Storage | Purpose |
|------|---------|---------|
| **Structured** | JSON/YAML/schemas | Architecture, APIs, contracts, dependencies |
| **Semantic** | Vector DB (Qdrant/Chroma) | Semantic retrieval, reasoning history, docs |
| **Graph** | Graph structure | Dependency graphs, module relationships, task DAGs |
| **Temporal** | Event log | Changes over time, architecture evolution, regressions |

**Memory Taxonomy (per file, frontmatter-based):**
- `user` — User role, preferences, knowledge level
- `feedback` — Corrections and confirmed approaches
- `project` — Ongoing work, goals, decisions not in code
- `reference` — Pointers to external systems

**Key Features:**
- **Workspace isolation** — Each project gets its own memory. No cross-contamination.
- **Event-driven updates** — API change → dependency graph updated → agents notified → tests regenerated
- **Selective retention** — Summarization, compression, pruning, importance scoring
- **Workspace snapshots** — Git-like checkpoints for memory state (rollback, recovery, branching)
- **Cross-workspace learning** — Abstracted reusable patterns (NOT raw project data) can flow to global memory
- **Memory search** — Grep + vector similarity for retrieval
- **MEMORY.md index** — Lightweight index file, detailed topic files for depth

**Retention Policy:**

| Type | Retention |
|------|-----------|
| Architecture | Permanent |
| API contracts | Permanent |
| Build logs | Temporary |
| Terminal logs | Compressed |
| Failed retries | Summarized |
| Temporary reasoning | Discard |
| Successful patterns | Reusable (→ global) |

### 5.9 Terminal Execution Layer

Agents control **real terminal sessions** using existing system tools.

```
AI System
   ↓
Controls terminal sessions (tmux)
   ↓
Uses existing compilers, runtimes, package managers
```

**Multi-Terminal Concurrency:**
```
Terminal 1 → frontend build
Terminal 2 → backend tests
Terminal 3 → database migration
Terminal 4 → linting
Terminal 5 → security scan
Terminal 6 → AI model inference
```

Each agent terminal has:
- Isolated workspace
- Environment variables
- Process tracking
- Command history
- Filesystem scope
- Resource limits

**Reasoning separated from Execution:**
```
Reasoning Agent → Creates Execution Plan → Execution Agent → Runs exact commands
```

### 5.10 Validation Pipeline

Before code reaches master, it passes through:

| Validation | What it checks |
|------------|----------------|
| **Build Agent** | Compilation succeeds |
| **Type Agent** | Type safety (TypeScript, Python types) |
| **Security Agent** | Vulnerabilities, secrets exposure |
| **Integration Agent** | API compatibility between services |
| **Performance Agent** | Bottlenecks, resource issues |
| **Architecture Agent** | Structural consistency |
| **Dependency Agent** | Package conflicts, version issues |
| **Test Agent** | Test generation + execution |

**Continuous validation** — compile, test, lint, static analysis, security analysis run as **first-class agents**, not optional tools.

### 5.11 Fault Reconstruction Engine

When something breaks:

```
Detect exact fault region
    ↓
Trace dependency chain
    ↓
Isolate responsible agents/files
    ↓
Regenerate ONLY affected parts
    ↓
Retest affected dependency graph
```

**Example:**
```
Frontend API call fails
    ↓
Trace: Frontend component → API contract → Backend route → Schema mismatch → DB model
    ↓
Identify: DB domain responsible
    ↓
Regenerate: Only DB model + backend route
    ↓
Retest: Only affected dependency chain
```

**Self-healing capabilities:** verification, rollback, reconstruction, dependency tracing, targeted repair.

### 5.12 Event Bus

Event-driven architecture (NOT direct agent calls):

```
Task Created → Scheduler Event → Worker Assigned → Execution Started
→ Tool Completed → Memory Updated → Dashboard Updated
```

**Implementation:** Redis Streams (initial), NATS or Kafka (later)

**Event Types:**
- Agent lifecycle (created, started, completed, failed, killed)
- Task state changes
- Tool executions
- Memory updates
- Validation results
- Resource alerts
- Architecture changes

### 5.13 Agent Communication Protocol

Structured messages between agents (inspired by Claude Code's `<task-notification>` pattern):

```json
{
  "agent_id": "backend_worker_12",
  "event": "task_completed",
  "status": "completed",
  "task": "Generate JWT middleware",
  "result_summary": "Created auth/middleware.py with JWT validation",
  "files_changed": ["auth/middleware.py"],
  "tests_passed": true,
  "duration_ms": 12500
}
```

**Rules:**
- Workers CANNOT see coordinator's conversation
- Every worker prompt must be **self-contained**
- Domain agents **synthesize** findings before delegating (never "based on your findings")
- Continue vs. Spawn decision based on context overlap

### 5.14 Skill System

Reusable workflows stored as skill files:

- Common patterns (auth setup, CRUD generation, test scaffolding)
- User-defined custom skills
- Skills discovered and loaded dynamically
- Skills can be shared across workspaces (via global memory)

### 5.15 Plugin Architecture

Extensibility for:
- Custom tools
- Custom models / providers
- Custom domain agent types
- Custom validation rules
- Custom UI panels

---

## 6. User Interface

### 6.1 CLI (Phase 1 — Primary)
- Robust CLI runtime built first
- Master/domain/worker orchestration
- tmux terminal management
- Task graph visualization (ASCII)
- Configuration management

### 6.2 Web Dashboard (Phase 2 — AI Engineering Control Center)

**NOT a chatbot UI. An operations control center.**

#### Views:

**A. Chat View** — Conversational interface with Master Agent
- Ask status, give commands, approve actions, modify plans
- The "executive interface"

**B. Live Agent Dashboard** — Real-time agent monitoring
- Active agents with status badges
- Model usage per agent
- Progress bars, retry counts, failure alerts
- Resource consumption per agent

**C. Task Graph View** — Visual DAG
- Domains, dependencies, execution order, bottlenecks
- Color-coded by status (idle/running/blocked/failed/completed)

**D. Terminal View** — Live terminal streams
- Each worker's terminal viewable in real-time
- Commands, outputs, failures, installations, tests
- Like VSCode integrated terminal monitoring

**E. Memory Explorer** — Inspect project memory
- Architecture memory, contracts, summaries
- Dependency graphs, domain-specific memory
- Search across memory types

**F. Architecture View** — System visualization
- Services, APIs, database schemas, dependencies, pipelines
- Live health status per component

**G. Resource Monitor** — Hardware dashboard
- CPU, GPU, VRAM, RAM usage
- Active models, terminal processes
- Token usage by agent tier

**H. Global Live Feed** — Event stream
```
[12:01] Master created backend domain
[12:02] Backend assigned auth middleware to worker_12
[12:03] Worker_12 started tests
[12:04] Validation failed — schema mismatch
[12:05] Fault reconstruction triggered
[12:06] Worker_12 regenerated DB model
[12:07] All tests passing
```

**I. Agent Inspector** — Click any agent to see:
- Current task, reasoning summary
- Assigned work, terminal, logs
- Memory usage, model used
- Retries, dependencies, communication history

**J. Manual Intervention Controls:**
- Stop/pause/restart agents
- Reroute tasks, reassign domains
- Swap models mid-run
- Edit architecture, reject outputs
- Restart pipelines

### 6.3 Visibility Levels

| Level | Audience | Shows |
|-------|----------|-------|
| Executive | Simple progress | High-level status |
| Developer | Tasks + logs | Detailed work view |
| Advanced | Terminals + memory | Full system internals |
| Debug | Raw internal events | Everything |

### 6.4 Agent Status Updates

Each agent continuously publishes:
```json
{
  "agent_id": "backend_worker_12",
  "status": "running",
  "task": "Generating auth middleware",
  "progress": 65,
  "current_file": "auth/middleware.py",
  "last_action": "Running unit tests",
  "errors": [],
  "model": "qwen2.5-coder-7b"
}
```

### 6.5 Chat With Master Agent

User can ask:
> "What are the backend agents doing?"

Master replies:
> "3 backend workers active:
> - auth API generation (75%)
> - websocket integration (40%)
> - Redis cache setup (90%)
>
> Current blocker: database schema conflict in session table."

### 6.6 Event-Sourced Architecture

Every important event stored:
```json
{
  "timestamp": "2026-05-10T12:00:00",
  "agent": "backend_domain",
  "event": "task_assigned",
  "target": "worker_12",
  "task": "Generate JWT middleware"
}
```

Enables: history, replay, debugging, auditing, analytics, **time-travel debugging**.

### 6.7 File Change Tracking

Every generated file shows:

| Field | Example |
|-------|---------|
| Created by | worker_12 |
| Approved by | backend_domain |
| Validated by | test_agent |
| Modified when | timestamp |
| Linked tasks | task IDs |

---

## 7. Configuration System

```yaml
# galaxy.config.yaml

project:
  name: "my-saas-app"
  workspace: "./my-saas-app"

models:
  master: { provider: openai, model: gpt-5 }
  domain: { provider: ollama, model: deepseek-coder-v2-16b }
  worker: { provider: ollama, model: qwen2.5-coder-7b }

limits:
  max_domain_agents: 10
  max_workers_per_domain: 50
  max_recursion_depth: 3
  max_retry_loops: 5

scheduling:
  mode: balanced  # performance | balanced | power_saver | enterprise

permissions:
  worker_level: restricted
  domain_level: standard
  master_level: elevated

memory:
  auto_enabled: true
  vector_db: qdrant
  workspace_isolation: true

overrides:
  security_domain:
    model: { provider: ollama, model: security-specialized }
```

All configurable through Web UI or CLI.

---

## 8. Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI (Python), asyncio, WebSockets |
| **Agent Runtime** | Python async + event bus |
| **Event Bus** | Redis Streams (Phase 1), NATS (Phase 3) |
| **Database** | PostgreSQL |
| **Vector Memory** | Qdrant or Chroma |
| **Frontend** | React, Next.js, Tailwind, WebSockets |
| **Local LLM** | Ollama, vLLM |
| **Terminal Control** | tmux, subprocess, pexpect, asyncio.create_subprocess_exec |
| **Schema Validation** | Pydantic (backend), Zod (frontend) |
| **Process Management** | Custom scheduler + resource monitor |

---

## 9. Development Phases

### Phase 1 — Foundation (Core Kernel + MVP CLI)

**Duration estimate: 4-6 weeks**

The absolute minimum to run Galaxy end-to-end on a single machine.

- [ ] Galaxy Core initialization and lifecycle
- [ ] Master Agent with project understanding
- [ ] Domain Agent creation and management
- [ ] Worker Agent spawning and task execution
- [ ] Tool Execution Layer (terminal, file, search, git)
- [ ] Permission & Sandbox Layer (basic)
- [ ] Task Graph Engine (basic DAG)
- [ ] tmux terminal orchestration
- [ ] Model Routing (Ollama integration)
- [ ] Basic VRAM-aware scheduler
- [ ] Agent communication protocol (Event Bus — Redis)
- [ ] CLI interface with status/control
- [ ] Basic logging and event tracking
- [ ] Configuration system (YAML)
- [ ] **Vault — Basic Checkpointing** (task graph persistence only)
- [ ] **Vault — Crash Marker** (detect unclean shutdown)

**Deliverable:** Build small-medium projects end-to-end via CLI. Survives restarts with basic task state recovery.

**Success criteria:**
- `galaxy run "Build a REST API with auth"` → produces working code
- Master decomposes → Domain plans → Workers execute → code compiles + tests pass
- `galaxy pause` / `galaxy resume` preserves task progress

---

### Phase 2 — Memory & Intelligence

**Duration estimate: 4-6 weeks**

Galaxy gains persistent knowledge and deep code understanding.

- [ ] **Memory System** — 5-level hierarchy (global, workspace, domain, task, agent)
- [ ] **Memory System** — Structured + semantic + graph memory types
- [ ] **Memory System** — Architecture verification from memory
- [ ] **Cortex — AST Graph** (tree-sitter parsing, multi-language)
- [ ] **Cortex — Symbol Graph** (function/class/variable index)
- [ ] **Cortex — Import Graph** (dependency tracking)
- [ ] **Cortex — Call Graph** (runtime call analysis)
- [ ] **Vault — Full Checkpoints** (task graph + agent states + memory + scheduler)
- [ ] **Vault — Crash Recovery** (event replay, damage assessment)
- [ ] **Vault — Pause/Resume** (graceful pause with safe points)
- [ ] **Vault — Model Independence** (role-based state, model-swappable)
- [ ] **Vault — Terminal Persistence** (tmux reattach on resume)
- [ ] Continuous testing integration
- [ ] Fault reconstruction engine (targeted, not brute-force)
- [ ] File change tracking and workspace snapshots
- [ ] Workspace memory isolation

**Deliverable:** Galaxy remembers across sessions. Understands codebase semantics. Survives crashes and model switches without losing progress.

**Success criteria:**
- Pause a project, switch models, resume → project continues seamlessly
- Kill Galaxy process → restart → recovers from checkpoint within 30 seconds
- Cortex can answer: "What imports this function?" "What calls this API?"
- Memory carries architecture decisions across sessions

---

### Phase 3 — Quality & Governance

**Duration estimate: 4-6 weeks**

Galaxy enforces consistency, trust, and policies — code quality that doesn't degrade.

- [ ] **Sentinel — Style Enforcement** (learned style profiles per language)
- [ ] **Sentinel — Architecture Drift Detection** (import boundary violations)
- [ ] **Sentinel — Abstraction Duplication** (detect duplicate patterns)
- [ ] **Sentinel — Naming Governance** (vocabulary consistency)
- [ ] **Sentinel — API Consistency** (contract enforcement)
- [ ] **Governance — Security Policies** (no hardcoded secrets, auth enforcement)
- [ ] **Governance — Access Control** (per-tier filesystem/tool/network restrictions)
- [ ] **Governance — Quality Gates** (coverage, type safety, lint, build)
- [ ] **Governance — Policy Evaluation Pipeline** (match → evaluate → enforce)
- [ ] **Governance — Audit Trail** (every policy evaluation logged)
- [ ] **Trust — Generation Confidence** (scoring per output)
- [ ] **Trust — Validation Quality** (additive score from checks)
- [ ] **Trust — Risk Score** (blast radius, file criticality)
- [ ] **Trust — Composite Trust Score** (4 dimensions → trust bands)
- [ ] **Trust — Trust-Driven Automation** (auto-merge high trust, block low trust)
- [ ] Validation pipeline (architecture-first, continuous verification)

**Deliverable:** Galaxy actively prevents code quality degradation. Every output carries quantified trust. Policies block dangerous operations before they happen.

**Success criteria:**
- Sentinel detects and blocks architecture violations in real-time
- Security policies block hardcoded secrets, `eval()`, missing auth
- Trust scores accurately predict which outputs need human review
- Agent with 3+ consecutive low-trust outputs → auto-escalated to stronger model

---

### Phase 4 — Collaboration & Scale

**Duration estimate: 6-8 weeks**

Multiple agents work safely in parallel. Galaxy optimizes itself.

- [ ] **Sync — File-Level Locking** (shared/exclusive/intent locks)
- [ ] **Sync — Changeset Transactions** (atomic multi-file commits)
- [ ] **Sync — Intent-Based Coordination** (conflict detection before execution)
- [ ] **Sync — Merge Conflict Resolution** (auto-resolve trivial, escalate semantic)
- [ ] **Sync — Dependency-Aware Commit Ordering** (Cortex-powered)
- [ ] **Cortex — API Contract Graph** (endpoint/payload tracking)
- [ ] **Cortex — Data Flow Graph** (variable lineage analysis)
- [ ] **Forge Labs — Experiment Branching** (git worktree-based A/B testing)
- [ ] **Forge Labs — Automated Scoring** (benchmark competing implementations)
- [ ] **Forge Labs — Winner Promotion** (auto-merge best branch)
- [ ] **Refiner — Performance Optimization** (N+1 queries, sync blocking, bundle bloat)
- [ ] **Refiner — Architecture Optimization** (dead code, god classes, circular deps)
- [ ] **Refiner — Code Quality Optimization** (missing error handling, validation, tests)
- [ ] **Refiner — Safety Guardrails** (dry-run, atomic rollback, test gates)
- [ ] **Distiller — Summarization Pipeline** (compress verbose memories)
- [ ] **Distiller — Memory Compaction** (merge related memories)
- [ ] **Distiller — Semantic Pruning** (remove stale/duplicate memories)
- [ ] **Distiller — Archive Tiering** (hot → warm → cold → frozen)
- [ ] **Ledger — Inference Cost Tracking** (tokens in/out per model per task)
- [ ] **Ledger — Compute Cost Tracking** (GPU-hours, CPU-hours, VRAM usage)
- [ ] **Ledger — Budget Enforcement** (alerts and hard caps)
- [ ] **Trust — Agent Reputation** (per-agent trust history, strength/weakness)
- [ ] **Trust — Confidence Calibration** (predicted vs actual, overconfidence penalty)
- [ ] **Trust — Trust Decay** (scores degrade over time without reverification)
- [ ] Dynamic agent scaling (auto-create/destroy workers)
- [ ] Adaptive model routing (capability-based)
- [ ] Predictive scheduling

**Deliverable:** 15+ parallel workers without conflicts. Galaxy optimizes its own code and memory. Full cost visibility.

**Success criteria:**
- 15 workers modifying related files → zero merge conflicts via Sync coordination
- Forge Labs runs 2 competing implementations → picks winner automatically
- Refiner identifies and fixes N+1 queries with zero human intervention
- Distiller keeps memory under 200 files despite weeks of operation
- Ledger shows cost-per-task breakdown and model efficiency comparison

---

### Phase 5 — Extensibility & Enterprise

**Duration estimate: 6-8 weeks**

Galaxy becomes extensible, templated, and distributed.

- [ ] **Plugin SDK — Manifest System** (galaxy-plugin.yaml)
- [ ] **Plugin SDK — Subprocess Isolation** (sandboxed execution)
- [ ] **Plugin SDK — Permission System** (granular filesystem/network/tool/resource)
- [ ] **Plugin SDK — Versioning** (semver compatibility, version pinning)
- [ ] **Plugin SDK — Lifecycle Management** (install, load, execute, update, uninstall)
- [ ] **Plugin SDK — Health Monitoring** (crash isolation, auto-disable)
- [ ] **Plugin SDK — Docker Isolation** (high-security mode for untrusted plugins)
- [ ] **Blueprints — Built-in Templates** (Full-Stack, API, ML, Real-Time, CLI, Mobile)
- [ ] **Blueprints — Template Anatomy** (stack, architecture, domains, sentinel rules)
- [ ] **Blueprints — Customization & Inheritance** (extend templates)
- [ ] **Blueprints — Auto-Detection** (infer template from existing project)
- [ ] **Cluster — Multi-Node Topology** (control, compute, inference nodes)
- [ ] **Cluster — Cross-Node Communication** (Event Bus over network)
- [ ] **Cluster — GPU Cluster Management** (multi-GPU inference)
- [ ] **Cluster — Shared Workspace** (NFS/S3/distributed filesystem)
- [ ] **Vault — Project Hibernation** (compress state, unload models, resume later)
- [ ] **Vault — Cross-Hardware Resume** (export/import .vault files)
- [ ] **Governance — Compliance Policies** (GDPR, HIPAA, SOC2 rules)
- [ ] **Governance — Deployment Policies** (staging gates, approval chains)
- [ ] **Governance — Policy Inheritance** (Galaxy → Organization → Project)
- [ ] **Studio — Web Dashboard** (full orchestration UI)
- [ ] **Studio — Chat Interface** (chat with Master Agent)
- [ ] **Studio — Agent Inspector** (watch agents in real-time)
- [ ] **Studio — Resource Monitor** (GPU/VRAM/CPU dashboard)
- [ ] **Studio — Trust Dashboard** (project trust overview, low-trust alerts)
- [ ] **Studio — Policy Dashboard** (compliance status, violation history)

**Deliverable:** Galaxy runs across machines, supports plugins, uses templates, and has a full web UI. Enterprise-ready governance.

**Success criteria:**
- Install a community plugin → runs sandboxed, can't access unauthorized files
- `galaxy init --blueprint fullstack-web-app` → project scaffolded with Sentinel rules in 30 seconds
- Pause on laptop (12GB VRAM) → resume on workstation (24GB VRAM) → auto-upgrades models
- `galaxy hibernate` → resume 2 weeks later with different models → no progress lost
- Multi-node cluster with 3 machines → tasks distributed across GPUs

---

### Phase 6 — Autonomous Operations

**Duration estimate: Ongoing**

Galaxy reaches full autonomy — self-improving, self-healing, self-optimizing.

- [ ] **Refiner — Dependency Optimization** (unused packages, lighter alternatives)
- [ ] **Refiner — Proactive Optimization** (scan → detect → plan → execute autonomously)
- [ ] **Refiner — Optimization Budget** (time limits, auto-approve thresholds)
- [ ] **Distiller — Hierarchical Embeddings** (4-level multi-resolution search)
- [ ] **Distiller — Compression Quality Verification** (ensure no knowledge loss)
- [ ] **Plugin SDK — WASM Isolation** (maximum security, capability-based)
- [ ] **Plugin SDK — Community Registry** (galaxy plugin search/install)
- [ ] **Blueprints — Community Registry** (galaxy blueprint search/install)
- [ ] **Ledger — Cost Optimization Recommendations** (auto-suggest savings)
- [ ] **Ledger — Model Efficiency Analytics** (historical cost-per-success trends)
- [ ] Self-healing and auto-reconstruction (autonomous fault recovery)
- [ ] Cross-workspace learning (transfer knowledge between projects)
- [ ] Hot model pooling (pre-loaded model rotation)
- [ ] Time-travel debugging (event replay investigation)
- [ ] Galaxy Marketplace (plugins + blueprints + skills ecosystem)
- [ ] Skill system (reusable agent workflows, shareable)

**Deliverable:** Galaxy operates with minimal human intervention — optimizes itself, learns from mistakes, and improves over time.

**Success criteria:**
- Galaxy detects performance regression → fixes it → verifies fix → merges — all without human intervention
- Memory stays optimal for months (Distiller compresses automatically)
- Community plugins/blueprints available via marketplace
- Galaxy produces better code on day 30 than day 1 (measurable via Trust calibration)

---

### Phase Summary

```
Phase 1: Foundation          → Galaxy WORKS (single machine, CLI)
Phase 2: Memory & Intel      → Galaxy REMEMBERS and UNDERSTANDS
Phase 3: Quality & Gov       → Galaxy ENFORCES standards
Phase 4: Collaboration       → Galaxy SCALES (parallel agents, self-optimizes)
Phase 5: Enterprise          → Galaxy EXTENDS (plugins, templates, clusters, UI)
Phase 6: Autonomous          → Galaxy EVOLVES (self-improving, self-healing)
```

| Phase | New Subsystems | Cumulative |
|-------|---------------|------------|
| 1 | Core, Runtime, Orchestrator, Scheduler, Terminal, Tools | 6 |
| 2 | Memory, Cortex (partial), Vault | 9 |
| 3 | Sentinel, Governance, Trust, Forge (validation) | 13 |
| 4 | Sync, Forge Labs, Refiner, Distiller, Ledger | 18 |
| 5 | Plugin SDK, Blueprints, Cluster, Studio | 22 |
| 6 | Marketplace, Skills, Full Autonomy | 25 |

---

## 10. What Makes Galaxy Unique

| Feature | Current Systems | Galaxy |
|---------|----------------|--------|
| Agent structure | Flat / 2 levels max | 3+ level strict hierarchy |
| Context handling | Everything shared | Isolated, scoped per agent |
| Model usage | Same model everywhere | Tiered: strong→medium→cheap |
| Execution | Cloud-dependent | Local-first, resource-aware |
| Scheduling | None | VRAM/GPU-aware intelligent scheduler |
| Fault handling | Regenerate everything | Targeted reconstruction |
| Observability | Black box | Full transparency, every action traced |
| User control | Minimal | Inspect, pause, override, manage everything |
| Memory | Global flat store | 5-level hierarchical, multi-type, isolated |
| Validation | Hope it works | Architecture-first, continuous verification |
| Resource optimization | Brute force | Dynamic hardware-aware allocation |
| Consistency | None | Sentinel immune system — always on |
| Crash recovery | Lose everything | Vault checkpoints + event replay |
| Model switching | Restart from scratch | Swap models mid-project, zero progress loss |
| Code quality | Manual review | Trust scoring + auto-merge/block |
| Concurrency | Single agent | Sync-coordinated parallel workers |
| Extensibility | Monolithic | Plugin SDK with sandboxed isolation |
| Project setup | From scratch every time | Blueprint templates with proven patterns |
| Cost awareness | None | Full Ledger with budget enforcement |
| Self-improvement | None | Refiner + Distiller auto-optimization |

---

## 11. Galaxy Branding Structure

```
GalaxyOS
 ├── Galaxy Core           — System kernel and lifecycle
 ├── Galaxy Runtime        — Agent execution engine
 ├── Galaxy Orchestrator   — Task graph + coordination
 ├── Galaxy Memory         — Multi-level memory system
 ├── Galaxy Scheduler      — VRAM-aware resource manager
 ├── Galaxy Terminal       — Multi-terminal execution (tmux)
 ├── Galaxy Forge          — Validation + build pipeline
 ├── Galaxy Studio         — Web dashboard / control center
 ├── Galaxy Workers        — Worker agent framework
 ├── Galaxy Cluster        — Distributed multi-machine execution
 ├── Galaxy Sentinel       — Consistency governance engine
 ├── Galaxy Cortex         — Semantic code intelligence
 ├── Galaxy Forge Labs     — Experimental execution (A/B testing)
 ├── Galaxy Refiner        — Autonomous optimization
 ├── Galaxy Governance     — Formal policy engine
 ├── Galaxy Sync           — Distributed transaction consistency
 ├── Galaxy Trust          — Confidence & trust scoring
 ├── Galaxy Vault          — Persistence & recovery engine
 ├── Galaxy Plugin SDK     — Plugin runtime isolation
 ├── Galaxy Distiller      — Knowledge compression
 ├── Galaxy Ledger         — Cost accounting system
 └── Galaxy Blueprints     — Workflow templates
```

---

## 12. Architecture Patterns Borrowed from Claude Code

| Pattern | Source | Galaxy Application |
|---------|--------|-------------------|
| Tool Registry + `buildTool()` | `Tool.ts`, `tools.ts` | Every Galaxy tool module |
| Permission system (layered modes) | `hooks/toolPermission/` | Agent command governance |
| State management (external store) | `state/AppStateStore.ts` | Centralized orchestration state |
| Context compression | `services/compact/` | Worker context scoping |
| Memory taxonomy (4 types) | `memdir/memoryTypes.ts` | Galaxy memory categories |
| Coordinator pattern | `coordinator/coordinatorMode.ts` | Galaxy orchestrator (expanded to 3+ tiers) |
| Feature flags | `bun:bundle` | Conditional feature loading |
| Skill system | `skills/` | Reusable agent behaviors |
| Task lifecycle | `tasks/` | Galaxy task state machine |
| MCP protocol | `services/mcp/` | Galaxy tool extensibility |

> [!IMPORTANT]
> These are **architectural patterns** extracted from Claude Code, NOT copied code. Galaxy is built from scratch in Python with a completely different architecture (multi-agent hierarchical OS vs. single-agent CLI tool).

---

## 13. Distributed Multi-Machine Execution (Galaxy Cluster)

> [!NOTE]
> Phase 3+ feature. Galaxy starts single-machine. This section defines the architecture for when scaling demands multi-node execution.

### 13.1 Why This Matters

Single-machine Galaxy hits limits:
- **GPU bottleneck** — one machine's VRAM can only hold so many models
- **CPU saturation** — compilation, testing, linting compete for cores
- **I/O contention** — many workers reading/writing the same disk
- **Scale ceiling** — enterprise projects need dozens of parallel agents

Galaxy Cluster solves this by distributing agents across machines while maintaining the same hierarchical orchestration model.

### 13.2 Cluster Topology

```
                    ┌─────────────────────────┐
                    │    GALAXY CONTROL NODE   │
                    │  (Master Agent + Core)   │
                    │  Orchestrator, Scheduler │
                    │  Event Bus, Dashboard    │
                    └────────┬────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │  COMPUTE   │  │  COMPUTE   │  │  COMPUTE   │
     │  NODE A    │  │  NODE B    │  │  NODE C    │
     │            │  │            │  │            │
     │ Frontend   │  │ Backend    │  │ Inference  │
     │ Workers    │  │ Workers    │  │ Cluster    │
     │ Build/Test │  │ Build/Test │  │ LLM Models │
     └────────────┘  └────────────┘  └────────────┘
```

### 13.3 Node Types

| Node Type | Role | Requirements |
|-----------|------|-------------|
| **Control Node** | Master agent, orchestrator, scheduler, event bus, dashboard, memory DB | High RAM, moderate CPU, optional GPU |
| **Compute Node** | Domain/worker agents, terminal execution, build/test | High CPU, moderate RAM, optional GPU |
| **Inference Node** | LLM model hosting (Ollama/vLLM), embedding generation | **High VRAM GPU**, moderate CPU |
| **Storage Node** | Shared filesystem, vector DB, PostgreSQL, Redis | High disk I/O, moderate RAM |
| **Hybrid Node** | Any combination of the above | Varies |

> [!TIP]
> Most users start with a single **Hybrid Node** (everything on one machine). The cluster architecture means you can **split later** without rewriting anything.

### 13.4 Agent Placement Strategy

The scheduler decides WHERE an agent runs, not just WHEN:

```
New Task Arrives
      ↓
Scheduler evaluates:
  1. Task type (inference? build? test?)
  2. Required model (what VRAM needed?)
  3. Required tools (compiler? runtime? GPU?)
  4. File locality (which node has the repo?)
  5. Current load per node
      ↓
Place agent on optimal node
```

**Placement Rules:**

| Agent Type | Preferred Node | Reason |
|-----------|----------------|--------|
| Master Agent | Control Node | Needs access to orchestrator, event bus |
| Domain Agent (reasoning) | Inference Node | Needs strong LLM |
| Worker Agent (coding) | Inference Node | Needs LLM for generation |
| Worker Agent (build/test) | Compute Node | Needs CPU, compilers |
| Validation Agent | Compute Node | Needs CPU for linting/testing |
| Memory/Embedding Agent | Storage Node | Needs vector DB access |

**Affinity rules** — keep agents that share files on the same node to minimize network I/O.

### 13.5 Cross-Machine Communication

All communication goes through the **Event Bus** (Redis Streams / NATS), NOT direct agent-to-agent calls:

```
Agent on Node A
      ↓
Publishes event to Event Bus (Redis/NATS)
      ↓
Scheduler on Control Node receives event
      ↓
Routes to appropriate agent on Node B
      ↓
Agent on Node B processes and publishes result
```

**Protocol:**
```json
{
  "event_id": "evt_abc123",
  "source_node": "compute-a",
  "source_agent": "frontend_worker_3",
  "target": "backend_domain",
  "type": "task_completed",
  "payload": {
    "task_id": "task_789",
    "files_changed": ["src/components/Auth.tsx"],
    "status": "completed"
  },
  "timestamp": "2026-05-10T12:00:00Z"
}
```

**No direct RPC between nodes** — event bus is the ONLY communication channel. This means:
- Nodes can join/leave without breaking agents
- Events are persisted (replay, debugging)
- Natural load balancing
- Fault tolerance (event bus retries)

### 13.6 Shared Workspace

All nodes need access to the same project files:

| Strategy | Mechanism | Tradeoff |
|----------|-----------|----------|
| **NFS/Network Mount** | Shared filesystem | Simple but slow for heavy I/O |
| **Git Sync** | Each node has a clone, sync via commits | Eventually consistent, good for parallel writes |
| **rsync** | Periodic file sync | Lightweight, configurable frequency |
| **Object Storage** | S3/MinIO for artifacts | Good for build outputs, logs |

**Recommended approach (Phase 3):**
- **Git as source of truth** — each worker commits to feature branches
- **NFS for shared read** — all nodes mount the project read-only
- **Local writes** — workers write to local disk, commit to shared repo
- **Artifact storage** — build outputs, logs, checkpoints go to object storage

### 13.7 GPU Cluster Scheduling

When multiple inference nodes exist, the scheduler becomes a **GPU cluster manager**:

```
Model Request: "Load deepseek-coder-v2-16b for backend_worker_5"
      ↓
GPU Scheduler checks:
  - Node C: 24GB VRAM, 18GB used → 6GB free → TOO SMALL
  - Node D: 24GB VRAM, 8GB used  → 16GB free → FITS
      ↓
Route inference to Node D
```

**GPU-Aware Features:**
- **Model placement** — keep frequently-used models warm on specific GPUs
- **Model migration** — move a model from saturated GPU to free GPU
- **Model sharing** — multiple agents share one loaded model instance (batched inference)
- **Spill management** — if VRAM is full, offload least-used model to RAM/disk
- **Multi-GPU split** — large models (70B+) split across multiple GPUs on one node

### 13.8 Node Discovery and Registration

Nodes register with the Control Node on startup:

```json
{
  "node_id": "compute-a",
  "hostname": "192.168.1.10",
  "capabilities": {
    "gpus": [
      { "name": "RTX 4090", "vram_gb": 24, "available_gb": 20 }
    ],
    "cpu_cores": 16,
    "ram_gb": 64,
    "disk_gb": 500,
    "tools": ["node", "python", "rust", "docker"],
    "models_loaded": ["qwen2.5-coder-7b"]
  },
  "status": "ready",
  "heartbeat_interval_ms": 5000
}
```

**Health monitoring:**
- Heartbeat every 5 seconds
- If a node misses 3 heartbeats → mark as `unhealthy`
- Reschedule that node's agents to healthy nodes
- When node recovers → gradually reassign work

### 13.9 Failure Handling in Cluster

| Failure | Response |
|---------|----------|
| Compute node dies | Reschedule agents to other nodes, replay from last checkpoint |
| Inference node dies | Fail over to backup inference node, or queue requests |
| Control node dies | **Critical** — secondary control node takes over (leader election) |
| Network partition | Agents continue local work, sync when reconnected |
| Event bus dies | Agents buffer locally, replay when bus recovers |

### 13.10 Cluster Configuration

```yaml
# galaxy.config.yaml — cluster section

cluster:
  enabled: true
  mode: multi-node  # single-node | multi-node
  
  control_node:
    host: "192.168.1.1"
    port: 8500
    
  nodes:
    - id: compute-a
      host: "192.168.1.10"
      role: compute
      tags: [frontend, build]
      
    - id: compute-b
      host: "192.168.1.11"
      role: compute
      tags: [backend, test]
      
    - id: inference-a
      host: "192.168.1.20"
      role: inference
      gpus: 2
      
  shared_storage:
    type: nfs  # nfs | git | rsync
    mount: "/shared/projects"
    
  event_bus:
    type: nats  # redis | nats
    url: "nats://192.168.1.1:4222"
```

### 13.11 Security in Cluster

- **mTLS** between all nodes (mutual TLS authentication)
- **Agent tokens** — each agent gets a scoped JWT for its permissions
- **Network policies** — compute nodes can't talk to each other directly, only through event bus
- **Secrets management** — API keys, credentials stored on control node only, distributed on-demand
- **Audit log** — every cross-node event logged for compliance

---

## 14. Consistency Governance Engine (Galaxy Sentinel)

> [!IMPORTANT]
> This is arguably the **most critical long-term subsystem**. Without it, every project Galaxy builds will slowly degrade — style drifts, abstractions duplicate, naming diverges, architecture erodes. Galaxy Sentinel is the immune system that prevents entropy.

### 14.1 The Problem

When dozens of agents generate code independently:
- **Worker A** names it `getUserById()`, **Worker B** names it `fetch_user()`
- **Worker C** creates a `BaseService` class, **Worker D** creates an identical `AbstractHandler`
- **Domain A** uses REST with camelCase, **Domain B** uses REST with snake_case
- Week 1 architecture says "microservices" — by Week 4 agents have created a monolith
- Unused imports, dead functions, orphan files accumulate silently

No human team survives this without code review. Galaxy's agents won't either.

### 14.2 Architecture

```
                  ┌──────────────────────┐
                  │   GALAXY SENTINEL    │
                  │  Consistency Engine   │
                  └──────────┬───────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   Style Layer         Structure Layer       Contract Layer
        │                    │                    │
        ▼                    ▼                    ▼
   Naming Rules        Arch. Patterns        API Schemas
   Format Rules        Dependency Rules      Interface Contracts
   Convention Rules    Duplication Rules      Type Consistency
```

Galaxy Sentinel operates as a **persistent background daemon** — not a one-shot linter. It watches every file change, every agent output, every commit.

### 14.3 Six Governance Domains

#### Domain 1: Coding Style Enforcement

**What it governs:**
- Naming conventions (camelCase, snake_case, PascalCase — per language)
- File naming patterns (`user.service.ts`, `user_service.py`)
- Directory structure conventions
- Import ordering and grouping
- Comment style and documentation format
- Indentation, line length, bracket style

**How it works:**
```
Agent generates code
      ↓
Sentinel Style Analyzer runs
      ↓
Compares against project style rules
      ↓
Violations? → Auto-fix OR reject with feedback
```

**Style rules are learned, not just configured:**
- On project start, Sentinel scans existing code to **infer** the style
- Builds a `style_profile.yaml` automatically
- User can override/customize any rule
- New agent output must match the profile

**Example style profile (auto-generated):**
```yaml
style_profile:
  language: typescript
  naming:
    variables: camelCase
    functions: camelCase
    classes: PascalCase
    constants: UPPER_SNAKE
    files: kebab-case
    directories: kebab-case
  imports:
    order: [builtin, external, internal, relative]
    grouping: true
    blank_lines_between_groups: 1
  formatting:
    indent: 2_spaces
    max_line_length: 100
    trailing_comma: always
    semicolons: never
    quotes: single
  documentation:
    functions: jsdoc
    classes: jsdoc
    min_description_length: 10
```

#### Domain 2: Architecture Drift Detection

**What it governs:**
- Defined architecture patterns are maintained over time
- No unauthorized layer violations (e.g., UI calling DB directly)
- Module boundaries respected
- Dependency direction enforced

**How it works:**
```
Master defines architecture
      ↓
Sentinel builds architecture model:
  - Layer definitions (UI → API → Service → Repository → DB)
  - Module boundaries
  - Allowed dependency directions
  - Forbidden cross-cuts
      ↓
Every generated file is checked:
  - Does this import violate layer rules?
  - Does this create a circular dependency?
  - Does this cross a module boundary?
      ↓
Violation? → Block + notify domain agent
```

**Architecture rules (auto-generated + customizable):**
```yaml
architecture:
  layers:
    - name: presentation
      paths: ["src/components/**", "src/pages/**"]
      can_import: [application]
      cannot_import: [infrastructure, domain_internals]
      
    - name: application
      paths: ["src/services/**", "src/usecases/**"]
      can_import: [domain, infrastructure]
      
    - name: domain
      paths: ["src/models/**", "src/entities/**"]
      can_import: []  # domain is pure, no external deps
      
    - name: infrastructure
      paths: ["src/db/**", "src/external/**"]
      can_import: [domain]

  forbidden:
    - from: presentation
      to: infrastructure
      reason: "UI must never access DB directly"
    - pattern: circular
      reason: "No circular dependencies allowed"
```

**Drift scoring:**
```
Architecture Drift Score: 12% (threshold: 20%)
  - 3 layer violations detected
  - 1 circular dependency introduced
  - 2 unauthorized cross-module imports
  
  Recommendation: Fix before continuing generation
```

#### Domain 3: Abstraction Duplication Detection

**What it governs:**
- No two classes/functions doing the same thing
- No duplicated utility patterns
- No copy-paste code across domains
- Shared patterns extracted into common modules

**How it works:**
```
New code generated
      ↓
Sentinel Duplication Analyzer:
  1. Semantic similarity check (embedding comparison)
  2. Structural similarity check (AST comparison)
  3. Functional similarity check (input/output signature matching)
      ↓
Match found (>80% similarity)?
      ↓
  - If same domain: merge into shared utility
  - If cross-domain: extract to shared module
  - Alert domain agent with specific recommendation
```

**Duplication report:**
```
DUPLICATION ALERT:
  File A: src/auth/validateToken.ts (line 15-45)
  File B: src/api/middleware/checkAuth.ts (line 8-38)
  Similarity: 87% (semantic), 72% (structural)
  
  Recommendation: Extract to src/shared/auth/tokenValidator.ts
  Affected agents: auth_worker_3, api_worker_7
```

#### Domain 4: Naming Governance

**Beyond basic style — semantic naming consistency:**

**What it governs:**
- Same concept = same name everywhere
- Consistent domain vocabulary (e.g., `user` not sometimes `account` sometimes `member`)
- Consistent verb patterns (`get`, `fetch`, `find`, `retrieve` — pick ONE)
- Consistent suffixes (`Service`, `Handler`, `Controller`, `Manager` — pick ONE per role)

**How it works:**
```
Project vocabulary built over time:
  - user (NOT: account, member, person, profile)
  - create (NOT: add, insert, make, generate)
  - Service (NOT: Handler, Manager, Controller)
      ↓
New code uses "fetchAccount"
      ↓
Sentinel flags: "Project uses 'get' + 'user', not 'fetch' + 'account'"
      ↓
Auto-rename OR reject with suggestion
```

**Vocabulary registry (auto-built):**
```yaml
vocabulary:
  entities:
    user: [user]          # canonical: user. rejected: account, member
    order: [order]        # canonical: order. rejected: purchase, transaction
    product: [product]    # canonical: product. rejected: item, listing
    
  verbs:
    read: get             # canonical: get. rejected: fetch, find, retrieve, load
    write: create         # canonical: create. rejected: add, insert, make
    delete: delete        # canonical: delete. rejected: remove, destroy, purge
    update: update        # canonical: update. rejected: modify, patch, change
    
  suffixes:
    business_logic: Service     # rejected: Handler, Manager, Controller
    data_access: Repository     # rejected: DAO, Store, DataSource
    api_handler: Controller     # rejected: Router, Handler, Endpoint
```

#### Domain 5: Dependency Governance

**What it governs:**
- No duplicate packages serving the same purpose
- Version consistency across the project
- No unnecessary dependencies
- License compliance
- Security vulnerability tracking

**How it works:**
```
Agent installs a package
      ↓
Sentinel checks:
  1. Does an existing dependency already do this? (e.g., lodash vs underscore)
  2. Is this version compatible with existing deps?
  3. Does this license conflict with project license?
  4. Are there known vulnerabilities?
  5. Is this dependency actually needed?
      ↓
Violation? → Block install + suggest alternative
```

**Dependency rules:**
```yaml
dependencies:
  forbidden:
    - name: "moment"
      reason: "Use date-fns instead (smaller, tree-shakeable)"
    - name: "request"
      reason: "Deprecated. Use axios or fetch"
      
  preferred:
    http_client: axios
    date_library: date-fns
    validation: zod
    orm: prisma
    
  constraints:
    max_direct_dependencies: 50
    max_dependency_depth: 6
    allowed_licenses: [MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC]
    block_on_critical_vulnerability: true
```

#### Domain 6: API Consistency

**What it governs:**
- All endpoints follow same patterns
- Consistent error response format
- Consistent pagination, filtering, sorting
- Consistent auth patterns
- Consistent HTTP methods usage
- Consistent request/response schemas

**How it works:**
```
API contract defined by Master:
  - RESTful conventions
  - Error format: { error: { code, message, details } }
  - Pagination: { data: [], meta: { page, limit, total } }
  - Auth: Bearer token in Authorization header
      ↓
Worker generates new endpoint
      ↓
Sentinel API Analyzer checks:
  - Does response format match contract?
  - Does error handling match pattern?
  - Does pagination work like other endpoints?
  - Are HTTP methods used correctly?
      ↓
Violation? → Reject + show expected format
```

### 14.4 Sentinel Daemon Lifecycle

Sentinel is NOT a one-time check. It runs continuously:

```
Project starts
      ↓
Sentinel scans existing codebase (if any)
      ↓
Builds initial profiles:
  - style_profile.yaml
  - architecture_model.yaml
  - vocabulary_registry.yaml
  - dependency_rules.yaml
  - api_contract.yaml
      ↓
Watches for events:
  - file_created
  - file_modified
  - dependency_added
  - agent_output_ready
      ↓
On each event:
  - Run relevant analyzers
  - Score consistency
  - Report violations
  - Auto-fix where possible
  - Block if severity >= threshold
      ↓
Periodic full scan (every N tasks):
  - Architecture drift score
  - Duplication report
  - Naming consistency report
  - Dead code detection
  - Dependency audit
```

### 14.5 Violation Severity Levels

| Level | Name | Action |
|-------|------|--------|
| 1 | `info` | Log only. Agent proceeds. |
| 2 | `warning` | Log + notify domain agent. Agent proceeds. |
| 3 | `error` | Block agent output. Require fix before merge. |
| 4 | `critical` | Block + escalate to Master. Halt related workers. |

**Configurable thresholds:**
```yaml
sentinel:
  severity_thresholds:
    style_violation: warning       # naming wrong → warning
    layer_violation: error         # UI imports DB → error
    duplication: warning           # similar code → warning
    architecture_drift: error      # drift > 20% → error
    security_vulnerability: critical
    circular_dependency: critical
```

### 14.6 Consistency Score Dashboard

Galaxy Studio shows a **live project health score:**

```
┌─────────────────────────────────────┐
│       PROJECT CONSISTENCY: 87%      │
├─────────────────────────────────────┤
│ Style Compliance      ████████░░ 82%│
│ Architecture Integrity████████░░ 90%│
│ Naming Consistency    ████████░░ 85%│
│ Duplication Score     █████████░ 94%│
│ Dependency Health     ████████░░ 88%│
│ API Consistency       ████████░░ 80%│
├─────────────────────────────────────┤
│ Violations: 3 errors, 12 warnings  │
│ Drift trend: ↗ +2% this session    │
└─────────────────────────────────────┘
```

### 14.7 Self-Learning Consistency

Sentinel gets smarter over time:
- User overrides a rule → Sentinel learns the preference
- User consistently rejects a suggestion → Sentinel adjusts threshold
- New patterns emerge in codebase → Sentinel updates profiles
- Cross-project patterns → Sentinel adds to global knowledge

### 14.8 Integration with Other Subsystems

| Subsystem | How Sentinel Integrates |
|-----------|----------------------|
| **Orchestrator** | Sentinel approves/blocks before task completion |
| **Fault Reconstruction** | Sentinel detects consistency-caused failures |
| **Memory** | Style profiles, vocabulary stored in workspace memory |
| **Validation Pipeline** | Sentinel is a validation stage (after build, before merge) |
| **Event Bus** | Sentinel subscribes to file_change, agent_output events |
| **Task Graph** | Consistency fixes become auto-generated tasks |
| **Agent Communication** | Sentinel feedback sent as structured messages to agents |

---

## 15. Semantic Code Intelligence Layer (Galaxy Cortex)

> [!NOTE]
> Galaxy Cortex is the **deep understanding engine** that gives Galaxy true code comprehension — not just text matching, but structural and semantic awareness of what every symbol, function, module, and dependency actually IS and how it connects to everything else.

### 15.1 Why This Matters

Without semantic code intelligence, Galaxy agents are essentially doing **text manipulation** — they read files as strings, grep for patterns, and hope for the best. Cortex transforms Galaxy from a "text generator that happens to write code" into a system that **understands code the way a compiler does**.

**Critical for:**
- **Fault Reconstruction** — trace exactly which functions are affected by a change
- **Refactoring** — rename a symbol and know every usage across the entire project
- **Consistency** — detect duplicate abstractions even when names differ
- **Architecture verification** — enforce layer boundaries at the symbol level
- **Worker scoping** — give workers exactly the context they need, nothing more

### 15.2 The Six Graphs

Cortex maintains **six interconnected graphs** that together form a complete semantic model of the codebase:

```
┌──────────────────────────────────────────────────┐
│                  GALAXY CORTEX                    │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌─────────┐  ┌─────────┐  ┌──────────────────┐ │
│  │   AST   │  │ Symbol  │  │  Import/Dependency│ │
│  │  Graph  │←→│  Graph  │←→│     Graph        │ │
│  └────┬────┘  └────┬────┘  └────────┬─────────┘ │
│       │            │                │            │
│       ▼            ▼                ▼            │
│  ┌─────────┐  ┌─────────┐  ┌──────────────────┐ │
│  │  Call   │  │   API   │  │    Data Flow     │ │
│  │  Graph  │←→│Contract │←→│     Graph        │ │
│  │         │  │  Graph  │  │                  │ │
│  └─────────┘  └─────────┘  └──────────────────┘ │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

#### Graph 1: AST Graph (Abstract Syntax Tree)

**What it captures:** The structural skeleton of every source file — parsed into a tree of nodes representing statements, expressions, declarations, and blocks.

**Node types:**
```
File → Module → Class → Method → Statement → Expression
                  │        │
                  ├→ Field  ├→ Parameter
                  ├→ Constructor  ├→ ReturnType
                  └→ Decorator    └→ LocalVariable
```

**What it enables:**
- Structural similarity detection (two functions with identical AST shape = likely duplicates)
- Code complexity scoring (depth, branching, nesting)
- Pattern matching (find all functions that follow try/catch/log pattern)
- Safe code transformations (rename, extract, inline)

**Example query:**
```
"Find all methods in src/services/ that have more than 3 nested if-statements"
→ AST traversal: depth(if_statement) > 3 within method nodes in path src/services/
→ Returns: [{file, method, line, depth}]
```

**Storage:** Each file's AST is parsed on save/creation, stored as a JSON tree, and indexed by file path + node type.

---

#### Graph 2: Symbol Graph

**What it captures:** Every named entity in the codebase — functions, classes, variables, types, interfaces, enums, constants — and their **definitions** vs **references**.

**Node schema:**
```json
{
  "symbol_id": "sym_user_service_get_by_id",
  "name": "getById",
  "kind": "method",
  "parent": "sym_user_service",
  "defined_in": {
    "file": "src/services/UserService.ts",
    "line": 42,
    "column": 3
  },
  "type_signature": "(id: string) => Promise<User | null>",
  "visibility": "public",
  "references": [
    { "file": "src/routes/users.ts", "line": 18, "kind": "call" },
    { "file": "src/controllers/AuthController.ts", "line": 55, "kind": "call" },
    { "file": "src/tests/UserService.test.ts", "line": 12, "kind": "call" }
  ],
  "exported": true,
  "deprecated": false
}
```

**What it enables:**
- **"Find all usages"** — every reference to any symbol
- **"Go to definition"** — instant jump from usage to declaration
- **Safe rename** — rename a symbol and update every reference
- **Dead code detection** — symbols with 0 references (except exports)
- **Impact analysis** — "if I change this type, what breaks?"

**Example query:**
```
"What calls UserService.getById()?"
→ Symbol graph lookup: references where kind=call for sym_user_service_get_by_id
→ Returns: [users.ts:18, AuthController.ts:55, UserService.test.ts:12]
```

---

#### Graph 3: Import / Dependency Graph

**What it captures:** Every `import`/`require`/`from` statement, mapping which files depend on which other files and which external packages.

**Edge schema:**
```json
{
  "from_file": "src/routes/users.ts",
  "to_file": "src/services/UserService.ts",
  "imported_symbols": ["UserService", "UserCreateDTO"],
  "import_type": "named",
  "is_external": false
}
```

**What it enables:**
- **Dependency tree** — what does this file depend on? (recursive)
- **Reverse dependency tree** — what depends on this file?
- **Circular dependency detection** — find cycles in the import graph
- **Bundle analysis** — what's the total weight of importing this module?
- **Layer violation detection** — does this import cross an architecture boundary?
- **Minimal rebuild** — which files need recompilation after a change?

**Example query:**
```
"What happens if I delete src/utils/formatDate.ts?"
→ Reverse dependency lookup: all files importing formatDate.ts
→ Returns: [Invoice.tsx, OrderSummary.tsx, DatePicker.tsx, 3 test files]
→ Impact: 6 files will break. Suggest: migrate to date-fns before deletion.
```

**External dependency tracking:**
```json
{
  "package": "axios",
  "version": "^1.7.0",
  "imported_by": ["src/services/api.ts", "src/utils/http.ts"],
  "total_importers": 2,
  "alternatives_in_project": [],
  "license": "MIT",
  "vulnerabilities": []
}
```

---

#### Graph 4: Call Graph

**What it captures:** Which functions call which other functions at runtime — the dynamic execution flow of the application.

**Edge schema:**
```json
{
  "caller": "sym_auth_controller_login",
  "callee": "sym_user_service_get_by_email",
  "call_site": { "file": "src/controllers/AuthController.ts", "line": 28 },
  "is_async": true,
  "is_conditional": false,
  "arguments_passed": ["email"]
}
```

**What it enables:**
- **Execution tracing** — follow the full call chain from HTTP request to DB query
- **Hot path detection** — which functions are called most frequently (static estimation)
- **Blast radius** — "if this function throws, what catches it?"
- **Test coverage mapping** — which tests exercise which call paths
- **Performance bottleneck candidates** — deep call chains, synchronous blocking in async paths

**Example query:**
```
"Trace the call chain from POST /api/login to the database"
→ Call graph traversal from AuthController.login():
   AuthController.login()
     → UserService.getByEmail()
       → UserRepository.findOne()
         → prisma.user.findUnique()
→ 4 hops, 3 files, all async
```

---

#### Graph 5: API Contract Graph

**What it captures:** Every API boundary in the system — HTTP endpoints, GraphQL resolvers, gRPC services, WebSocket handlers, event handlers — with their request/response schemas.

**Node schema:**
```json
{
  "endpoint_id": "api_post_auth_login",
  "method": "POST",
  "path": "/api/auth/login",
  "handler": "sym_auth_controller_login",
  "request_schema": {
    "body": { "email": "string", "password": "string" }
  },
  "response_schema": {
    "200": { "token": "string", "user": "User" },
    "401": { "error": { "code": "string", "message": "string" } }
  },
  "auth_required": false,
  "rate_limited": true,
  "consumed_by": ["frontend/src/api/auth.ts"]
}
```

**What it enables:**
- **Contract verification** — does the frontend expect what the backend returns?
- **Breaking change detection** — "removing this field will break 3 consumers"
- **API documentation generation** — auto-generate OpenAPI/Swagger from the graph
- **Mock generation** — generate test mocks from contract schemas
- **Cross-domain validation** — frontend and backend agree on types

**Example query:**
```
"Which frontend components will break if I change the User response schema?"
→ API contract graph: find all consumers of endpoints returning User
→ Cross-reference with import graph: which components use the API client
→ Returns: [ProfilePage.tsx, UserSettings.tsx, AdminPanel.tsx]
```

---

#### Graph 6: Data Flow Graph

**What it captures:** How data moves through the system — from user input through validation, transformation, storage, and response.

**What it tracks:**
- Variable assignments and reassignments
- Function parameter passing
- Database reads and writes
- API request/response data paths
- State mutations (Redux/Zustand/context)
- Environment variable usage

**What it enables:**
- **Taint analysis** — track user input through the system (security)
- **Data lineage** — "where does this value come from originally?"
- **Side effect detection** — which functions mutate external state?
- **Schema propagation** — a type change at the DB level: what transforms apply before it reaches the UI?

**Example query:**
```
"Trace user email from signup form to database"
→ Data flow: 
   SignupForm.email (user input)
     → validateEmail() (validation)
       → UserService.create({ email }) (business logic)
         → UserRepository.insert() (data access)
           → prisma.user.create({ data: { email } }) (DB write)
→ 5 steps, email is validated at step 2, never escaped for HTML
→ Security note: missing XSS sanitization before storage
```

---

### 15.3 How Graphs Are Built

Cortex builds graphs **incrementally**, not from scratch on every change:

```
File saved / Agent output ready
      ↓
Cortex File Watcher detects change
      ↓
Parse ONLY the changed file
      ↓
Update affected graph nodes/edges:
  - Re-parse AST for that file
  - Update symbol definitions/references
  - Recalculate import edges
  - Update call graph for changed functions
  - Re-validate API contracts if route file
      ↓
Propagate changes to dependent graphs:
  - New import? → update dependency graph
  - Symbol renamed? → update all reference edges
  - Function signature changed? → update call graph + API contract
      ↓
Notify subscribers (Sentinel, Scheduler, Dashboard)
```

**Full rebuild** only on:
- First project scan (initial indexing)
- Major restructuring (>30% of files changed)
- User-requested re-index
- Graph corruption recovery

### 15.4 Language Support Strategy

Cortex needs **parsers per language**. Strategy:

| Language | Parser | Priority |
|----------|--------|----------|
| TypeScript/JavaScript | `tree-sitter-typescript` | Phase 1 |
| Python | `tree-sitter-python` | Phase 1 |
| Go | `tree-sitter-go` | Phase 2 |
| Rust | `tree-sitter-rust` | Phase 2 |
| Java | `tree-sitter-java` | Phase 2 |
| C/C++ | `tree-sitter-c`, `tree-sitter-cpp` | Phase 3 |
| Ruby | `tree-sitter-ruby` | Phase 3 |

**tree-sitter** is the foundation — fast incremental parsing, supports all major languages, produces concrete syntax trees that can be traversed uniformly.

**Cross-language understanding:**
```
Frontend (TypeScript) calls → API endpoint (path string)
      ↓
Cortex matches path to → Backend (Python) route handler
      ↓
Linked via API Contract Graph
      ↓
Now: "rename this Python endpoint" → Cortex knows to update the TypeScript API client too
```

### 15.5 Graph Storage

| Graph | Storage | Reason |
|-------|---------|--------|
| AST | File-based JSON (per source file) | Large, file-scoped, rarely queried cross-file |
| Symbol | SQLite or PostgreSQL | Relational queries (find by name, kind, file) |
| Import/Dependency | In-memory graph + persisted adjacency list | Fast traversal, small size |
| Call Graph | In-memory graph + persisted | Traversal-heavy queries |
| API Contract | Structured JSON + PostgreSQL | Schema validation, versioning |
| Data Flow | In-memory (computed on demand) | Expensive, query-driven |

### 15.6 Graph Query API

All Galaxy subsystems query Cortex through a unified API:

```python
# Find all references to a symbol
refs = cortex.symbol_graph.find_references("UserService.getById")

# Get dependency tree for a file
deps = cortex.import_graph.dependents_of("src/services/UserService.ts")

# Trace call chain
chain = cortex.call_graph.trace("AuthController.login", depth=5)

# Check for circular dependencies
cycles = cortex.import_graph.find_cycles()

# Impact analysis: what breaks if this file changes?
impact = cortex.impact_analysis("src/models/User.ts")
# Returns: { files_affected: 12, functions_affected: 34, tests_affected: 8 }

# Find dead code
dead = cortex.symbol_graph.find_unreferenced(kind="function", exclude_exports=True)
```

### 15.7 Integration with Galaxy Subsystems

| Subsystem | How Cortex Powers It |
|-----------|---------------------|
| **Sentinel** | Duplication detection via AST similarity, layer violations via import graph |
| **Fault Reconstruction** | Trace dependency chain to isolate exact failure scope |
| **Orchestrator** | Worker scoping — give workers only the symbols/files they need |
| **Scheduler** | Estimate task complexity from AST depth + call graph size |
| **Memory** | Architecture snapshots include graph summaries |
| **Refactoring** | Safe rename, extract, inline — all backed by symbol + call graphs |
| **Validation** | Breaking change detection via API contract graph |
| **Dashboard** | Architecture visualization, dependency explorer, call chain viewer |

---

## 16. Branching & Experimental Execution (Galaxy Forge Labs)

> [!NOTE]
> This is one of Galaxy's most powerful advanced features — the ability to **try multiple competing implementations in parallel** and pick the best one. Like A/B testing, but for code architecture.

### 16.1 The Concept

Instead of committing to one approach and hoping it works:

```
Traditional:
  "Use FastAPI for the backend" → build everything → discover it was wrong → rewrite

Galaxy Forge Labs:
  Branch A: FastAPI implementation (3 workers)
  Branch B: Django implementation (3 workers)
  Branch C: Express.js implementation (3 workers)
      ↓
  All build in parallel, isolated
      ↓
  Automated comparison: performance, code quality, test coverage, complexity
      ↓
  Winner promoted to main. Losers archived (knowledge preserved).
```

This turns architecture decisions from **bets** into **experiments**.

### 16.2 When to Use Experiments

Not every task needs this. Experiments are triggered when:

| Trigger | Example |
|---------|---------|
| **Ambiguous requirement** | "Build an auth system" — JWT vs sessions vs OAuth? |
| **Framework choice** | FastAPI vs Django vs Flask for the API layer |
| **Algorithm selection** | Different sorting/search/caching strategies |
| **Architecture debate** | Monolith vs microservices vs serverless |
| **Performance optimization** | Try 3 different DB query strategies |
| **User request** | "Try it both ways and show me which is better" |
| **Master uncertainty** | Master agent confidence < 70% on approach |

### 16.3 Experiment Lifecycle

```
┌─────────────────────────────────────────────┐
│              EXPERIMENT LIFECYCLE            │
└─────────────────────────────────────────────┘

1. HYPOTHESIS
   Master defines the experiment:
   - What's being tested
   - What branches to create
   - What criteria determine the winner
   - Resource budget per branch
   - Time limit
        ↓
2. BRANCH CREATION
   Galaxy creates isolated environments:
   - Git worktree per branch
   - Separate workspace directory
   - Independent agent group per branch
   - Shared read-only access to common code
        ↓
3. PARALLEL EXECUTION
   Each branch executes independently:
   - Own domain agents
   - Own workers
   - Own terminal sessions
   - Own build/test pipeline
   - No cross-branch interference
        ↓
4. AUTOMATED SCORING
   When all branches complete (or time limit hit):
   - Run scoring criteria
   - Generate comparison report
   - Rank branches
        ↓
5. WINNER SELECTION
   - Auto-select if scores are clear
   - Ask user if scores are close
   - Master can override with reasoning
        ↓
6. PROMOTION
   Winner branch merged to main:
   - Code integrated
   - Tests merged
   - Architecture memory updated
   - Losing branches archived
        ↓
7. KNOWLEDGE EXTRACTION
   From ALL branches (including losers):
   - What worked? → skill/pattern
   - What failed? → anti-pattern memory
   - Performance data → future reference
```

### 16.4 Branch Isolation

Each experiment branch runs in **complete isolation**:

```
Project Root: /workspace/my-app/
    │
    ├── main/                    (main codebase)
    ├── .galaxy/experiments/
    │   ├── exp_001_auth_strategy/
    │   │   ├── branch_a_jwt/    (git worktree)
    │   │   │   ├── src/
    │   │   │   ├── tests/
    │   │   │   └── .galaxy_branch_meta.yaml
    │   │   ├── branch_b_session/
    │   │   │   ├── src/
    │   │   │   ├── tests/
    │   │   │   └── .galaxy_branch_meta.yaml
    │   │   └── experiment.yaml
    │   └── exp_002_db_optimization/
    │       └── ...
```

**Isolation guarantees:**
- Each branch has its own **git worktree** (real git branch, real files)
- Each branch has its own **terminal sessions**
- Each branch has its own **agent group** (domain + workers)
- Branches share **read-only** access to unchanged files
- No branch can modify another branch's files
- Each branch has its own **build/test artifacts**

### 16.5 Experiment Types

#### Type 1: Framework Showdown
```yaml
experiment:
  name: "API Framework Selection"
  type: framework_comparison
  branches:
    - name: fastapi
      config:
        framework: fastapi
        workers: 3
      instructions: "Implement the user CRUD API using FastAPI with Pydantic models"
    - name: django
      config:
        framework: django
        workers: 3
      instructions: "Implement the user CRUD API using Django REST Framework"
  scoring:
    - metric: test_pass_rate
      weight: 30
    - metric: response_time_p95
      weight: 25
    - metric: code_complexity
      weight: 20
    - metric: lines_of_code
      weight: 15
    - metric: dependency_count
      weight: 10
```

#### Type 2: Algorithm Comparison
```yaml
experiment:
  name: "Search Implementation"
  type: algorithm_comparison
  branches:
    - name: elasticsearch
      instructions: "Implement full-text search using Elasticsearch"
    - name: postgres_fts
      instructions: "Implement full-text search using PostgreSQL tsvector"
    - name: meilisearch
      instructions: "Implement full-text search using Meilisearch"
  scoring:
    - metric: query_latency_ms
      weight: 35
    - metric: indexing_speed
      weight: 20
    - metric: relevance_quality
      weight: 25
    - metric: infrastructure_complexity
      weight: 20
```

#### Type 3: Architecture Experiment
```yaml
experiment:
  name: "State Management"
  type: architecture_experiment
  branches:
    - name: redux
      instructions: "Implement global state using Redux Toolkit"
    - name: zustand
      instructions: "Implement global state using Zustand"
    - name: context
      instructions: "Implement global state using React Context + useReducer"
  scoring:
    - metric: bundle_size_impact
      weight: 25
    - metric: boilerplate_ratio
      weight: 20
    - metric: type_safety
      weight: 20
    - metric: devtools_support
      weight: 15
    - metric: learning_curve
      weight: 20
```

#### Type 4: Optimization Race
```yaml
experiment:
  name: "DB Query Optimization"
  type: optimization
  baseline: current  # compare against existing implementation
  branches:
    - name: raw_sql
      instructions: "Rewrite the dashboard query using raw SQL with CTEs"
    - name: materialized_view
      instructions: "Create a materialized view for the dashboard data"
    - name: cached_aggregation
      instructions: "Add Redis caching layer for aggregated dashboard data"
  scoring:
    - metric: query_time_ms
      weight: 40
    - metric: memory_usage_mb
      weight: 20
    - metric: cache_invalidation_complexity
      weight: 20
    - metric: maintenance_burden
      weight: 20
```

### 16.6 Automated Scoring

Each branch is scored on **configurable weighted criteria**:

| Metric Category | Measurable Metrics |
|----------------|-------------------|
| **Correctness** | Test pass rate, type check pass, lint pass |
| **Performance** | Response time, throughput, memory usage, CPU usage |
| **Code Quality** | Complexity score, duplication ratio, dead code % |
| **Size** | Lines of code, file count, dependency count, bundle size |
| **Consistency** | Sentinel score (style, naming, architecture compliance) |
| **Maintainability** | Readability score, documentation coverage, test coverage |

**Scoring output:**
```
┌─────────────────────────────────────────────┐
│  EXPERIMENT: API Framework Selection        │
├─────────────────────────────────────────────┤
│                                             │
│  Criteria        FastAPI  Django  Express   │
│  ─────────────   ───────  ──────  ───────   │
│  Tests (30%)       95%     92%     88%      │
│  Perf (25%)       4ms     12ms    6ms       │
│  Complexity (20%)  Low     Med     Low      │
│  LOC (15%)        420     680     510       │
│  Deps (10%)        8       15      12       │
│  ─────────────   ───────  ──────  ───────   │
│  TOTAL SCORE      92.3    78.5    81.2      │
│                                             │
│  🏆 WINNER: FastAPI (92.3/100)              │
│                                             │
│  Confidence: HIGH (14-point lead)           │
│  Recommendation: Auto-promote               │
└─────────────────────────────────────────────┘
```

### 16.7 Resource Budgeting

Experiments can be expensive. Controls:

```yaml
experiment_limits:
  max_concurrent_experiments: 2
  max_branches_per_experiment: 5
  max_workers_per_branch: 5
  max_duration_minutes: 60
  max_total_agent_minutes: 180  # across all branches combined
  
  # If a branch is clearly losing, stop early
  early_termination:
    enabled: true
    check_interval_minutes: 10
    min_score_threshold: 40  # kill branch if score < 40% of leader
```

**Smart resource allocation:**
- If hardware is limited → run branches **sequentially** instead of parallel
- If one branch finishes early → reallocate its resources to remaining branches
- If time limit approaching → run scoring on partial results

### 16.8 Experiment Dashboard

Galaxy Studio shows experiments as a dedicated view:

```
┌──────────────────────────────────────────┐
│  🔬 ACTIVE EXPERIMENTS                    │
├──────────────────────────────────────────┤
│                                          │
│  exp_001: Auth Strategy                  │
│  ├── Branch A: JWT      [████░░] 65%     │
│  ├── Branch B: Session  [██████] 90%     │
│  └── Branch C: OAuth2   [███░░░] 45%     │
│  Time remaining: 22 min                  │
│  Leading: Branch B (Session)             │
│                                          │
│  exp_002: DB Optimization                │
│  Status: SCORING                         │
│  Winner pending...                       │
│                                          │
└──────────────────────────────────────────┘
```

Users can:
- Watch branches execute in real-time
- Inspect any branch's terminal/code/tests
- Stop a branch early
- Add a new branch mid-experiment
- Override scoring weights
- Force-select a winner

### 16.9 Winner Promotion

When a winner is selected:

```
Winner branch selected (e.g., branch_a_jwt)
      ↓
Pre-merge validation:
  - All tests pass
  - Sentinel consistency check
  - No conflicts with main
      ↓
Merge strategy:
  - Squash merge (clean single commit)
  - OR full merge (preserve branch history)
      ↓
Post-merge:
  - Update architecture memory
  - Update Cortex graphs
  - Clean up experiment worktrees
  - Archive losing branches (keep for reference)
      ↓
Notify:
  - User: "JWT auth selected and merged (score: 92.3)"
  - Master: Update architecture model
  - Sentinel: Re-baseline consistency profiles
```

### 16.10 Knowledge from Failed Branches

Losing branches are NOT deleted blindly. Galaxy extracts:

- **Why it lost** — specific metrics that were worse
- **What was good** — any sub-component worth keeping
- **Anti-patterns** — approaches that led to poor scores
- **Performance data** — benchmark numbers for future reference

Stored in workspace memory:
```markdown
---
name: auth_experiment_results
type: project
---

## Auth Strategy Experiment (2026-05-10)

**Winner:** JWT (FastAPI + python-jose)
**Why:** 4ms response vs 12ms session lookup. 60% less code.

**Rejected: Session-based**
- Higher latency due to Redis session store
- More infrastructure complexity
- BUT: better for server-rendered apps (note for future)

**Rejected: OAuth2-only**
- Incomplete: didn't finish in time budget
- Over-engineered for internal API
```

### 16.11 Integration with Subsystems

| Subsystem | Integration |
|-----------|------------|
| **Orchestrator** | Creates experiment task groups, manages branch lifecycle |
| **Scheduler** | Allocates resources per branch, handles early termination |
| **Task Graph** | Each branch gets its own sub-DAG within the main task graph |
| **Sentinel** | Scores consistency per branch independently |
| **Cortex** | Indexes each branch separately, merges winner's graphs |
| **Memory** | Stores experiment results, extracts knowledge from all branches |
| **Event Bus** | Branch progress events, scoring events, winner events |
| **Dashboard** | Dedicated experiment comparison UI |
| **Validation** | Runs full validation pipeline per branch independently |

---

## 17. Autonomous Optimization Layer (Galaxy Refiner)

> [!NOTE]
> Galaxy Refiner goes beyond "make it work" to "make it better." Once code is correct, Refiner autonomously identifies and applies improvements across performance, architecture, resources, code quality, and dependencies — without breaking anything.

### 17.1 Why This Matters

Current AI coding tools stop at correctness: "Does the code compile? Do tests pass? Ship it."

But production code needs more:
- The N+1 query nobody noticed until 10,000 users hit it
- The unused dependency bloating the bundle by 300KB
- The synchronous call blocking the event loop
- The 5 duplicate utility functions across 3 domains
- The dead code from a feature removed 2 months ago

Galaxy Refiner **finds and fixes these proactively** — like having a senior engineer doing continuous code review.

### 17.2 Five Optimization Domains

```
                    GALAXY REFINER
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   Performance      Architecture      Resource
   Optimization     Optimization      Optimization
        │                │                │
        ▼                ▼                ▼
   Code Quality     Dependency
   Optimization     Optimization
```

---

#### Domain 1: Performance Optimization

**What it detects and fixes:**

| Problem | Detection Method | Auto-Fix |
|---------|-----------------|----------|
| N+1 queries | Call graph: loop containing DB call | Batch query / eager loading |
| Synchronous blocking in async code | AST: `await` inside `for` loop | `Promise.all` / `asyncio.gather` |
| Missing database indexes | Query analysis + schema inspection | `CREATE INDEX` suggestion |
| Unoptimized re-renders (React) | AST: component re-creating objects in render | `useMemo`/`useCallback` wrapping |
| Missing caching | Call graph: identical expensive calls | Cache layer insertion |
| Unbounded queries | API contract: no pagination | Add limit/offset |
| Large bundle imports | Import graph: full library import | Tree-shake / named import |
| Redundant API calls | Data flow: same endpoint called multiple times | Request deduplication |

**Example optimization:**
```
DETECTED: N+1 Query in src/services/OrderService.ts:34
  
  for (const order of orders) {
    order.user = await db.user.findUnique({ where: { id: order.userId } })
  }
  
  Impact: 100 orders = 101 DB queries
  
OPTIMIZED:
  const userIds = orders.map(o => o.userId)
  const users = await db.user.findMany({ where: { id: { in: userIds } } })
  const userMap = new Map(users.map(u => [u.id, u]))
  orders.forEach(o => o.user = userMap.get(o.userId))
  
  Impact: 100 orders = 2 DB queries (99% reduction)
```

---

#### Domain 2: Architecture Optimization

**What it detects and fixes:**

| Problem | Detection Method | Auto-Fix |
|---------|-----------------|----------|
| Dead code | Symbol graph: 0 references, not exported | Remove file/function |
| Duplicate abstractions | AST + semantic similarity > 80% | Merge into shared utility |
| God classes (>500 lines) | AST: class node line count | Split into focused classes |
| Deep nesting (>4 levels) | AST: nesting depth analysis | Extract helper functions |
| Circular dependencies | Import graph: cycle detection | Restructure imports, introduce interface |
| Layer violations | Import graph + architecture rules | Move file to correct layer |
| Over-abstraction | Symbol graph: wrapper with 1 caller | Inline the abstraction |
| Under-abstraction | AST: repeated code blocks > 3 times | Extract to shared function |

**Technical debt score:**
```
┌──────────────────────────────────────┐
│     TECHNICAL DEBT SCORE: 23/100     │
├──────────────────────────────────────┤
│ Dead code:           4 files, 312 LOC│
│ Duplicate functions: 7 pairs         │
│ God classes:         2 (>500 LOC)    │
│ Circular deps:       1 cycle         │
│ Deep nesting:        11 functions    │
│ Over-abstracted:     3 wrappers      │
│                                      │
│ Estimated cleanup:   ~45 min         │
│ Risk level:          LOW             │
│                                      │
│ [Run Cleanup] [Review First] [Skip]  │
└──────────────────────────────────────┘
```

---

#### Domain 3: Resource Optimization

**Optimizing Galaxy's own resource usage:**

| Problem | Detection Method | Auto-Fix |
|---------|-----------------|----------|
| Oversized model for simple tasks | Task complexity vs model size mismatch | Downgrade model |
| Context window waste | Large irrelevant context sent to agents | Compress/trim context |
| Idle agents consuming VRAM | Agent idle time tracking | Unload model, free VRAM |
| Sequential tasks that could be parallel | Task graph: independent tasks queued | Parallelize |
| Redundant agent spawning | Same task re-assigned after minor change | Reuse existing agent context |
| Excessive retries | Retry loop > 3 with same approach | Change strategy, escalate |

**Resource efficiency report:**
```
SESSION RESOURCE EFFICIENCY:
  Model utilization:     78% (good)
  Context efficiency:    62% (room for improvement — 38% of context was unused)
  Agent reuse rate:      45% (low — consider continuing workers more)
  Parallel utilization:  83% (good)
  
  Suggestions:
  - 12 worker tasks used 14B model but were simple CRUD → use 7B next time
  - 3 agents spawned fresh when existing agents had relevant context
  - Backend domain ran 4 tasks sequentially that had no dependencies
```

---

#### Domain 4: Code Quality Optimization

| Problem | Detection Method | Auto-Fix |
|---------|-----------------|----------|
| Missing error handling | Call graph: unhandled async calls | Add try/catch with proper errors |
| Inconsistent error types | AST: different error patterns per file | Standardize error classes |
| Missing input validation | API contract: no validation on params | Add Zod/Pydantic schemas |
| Low test coverage | Coverage report: functions < 80% | Generate missing tests |
| Missing documentation | Symbol graph: public exports without JSDoc | Generate documentation |
| Magic numbers | AST: literal numbers in logic | Extract to named constants |
| Long functions (>50 lines) | AST: function body line count | Extract sub-functions |
| Unused variables | Symbol graph: assigned but never read | Remove declarations |

---

#### Domain 5: Dependency Optimization

| Problem | Detection Method | Auto-Fix |
|---------|-----------------|----------|
| Unused dependencies | Import graph: package never imported | `npm uninstall` / `pip uninstall` |
| Heavy alternatives exist | Package size analysis + alternatives DB | Suggest lighter package |
| Duplicate purpose packages | Import graph: 2 packages for same job | Consolidate to one |
| Outdated versions | Version comparison + changelog analysis | Upgrade with breaking change check |
| Dev deps in production | Package.json analysis | Move to devDependencies |
| Transitive vulnerability | Dependency tree vulnerability scan | Upgrade or replace chain |

**Example:**
```
DEPENDENCY AUDIT:
  ✗ lodash (72KB) — only using _.debounce → replace with 1KB debounce function
  ✗ moment (290KB) — replace with date-fns (tree-shakeable, 12KB used)
  ✗ uuid — only used once → use crypto.randomUUID() (built-in)
  ✓ axios — used in 8 files, no lighter alternative
  ✗ @types/express — installed but using Fastify
  
  Potential savings: 362KB bundle, 3 fewer dependencies
```

### 17.3 Optimization Lifecycle

```
Refiner runs (triggered or scheduled)
      ↓
SCAN phase:
  - Cortex graph analysis
  - Sentinel consistency data
  - Test coverage reports
  - Bundle/build analysis
  - Dependency audit
      ↓
DETECT phase:
  - Identify all optimizable patterns
  - Score each by impact (high/medium/low)
  - Score each by risk (safe/moderate/risky)
  - Estimate effort (minutes)
      ↓
PLAN phase:
  - Group related optimizations
  - Order by: high impact + low risk first
  - Calculate total effort
  - Generate optimization plan
      ↓
APPROVAL phase:
  - Present plan to user OR
  - Auto-approve if all changes are safe (configurable)
      ↓
EXECUTE phase:
  - Create optimization branch
  - Apply changes via worker agents
  - Run full test suite after each change
  - Rollback individual changes if tests break
      ↓
VERIFY phase:
  - Compare before/after metrics
  - Confirm no regressions
  - Merge to main if all green
      ↓
LEARN phase:
  - Record what worked → reusable patterns
  - Record what broke → avoid next time
  - Update optimization profiles
```

### 17.4 Safety Guardrails

Optimization must NEVER break working code:

| Guardrail | How |
|-----------|-----|
| **Dry-run mode** | Show what WOULD change without changing anything |
| **Atomic rollback** | Each optimization is a separate commit — rollback individually |
| **Test gate** | Full test suite must pass after EVERY change, not just at the end |
| **Diff approval** | User can review and approve/reject each optimization |
| **Risk scoring** | High-risk changes require explicit approval |
| **Blast radius limit** | No single optimization can touch > 10 files |
| **Regression detection** | Performance benchmarks run before AND after |

**Risk classification:**

| Risk | Examples | Approval |
|------|---------|----------|
| `safe` | Remove unused import, extract constant | Auto-approve |
| `low` | Add missing error handling, rename variable | Auto-approve (configurable) |
| `moderate` | Refactor function, change query pattern | User review recommended |
| `high` | Change architecture pattern, swap dependency | User approval required |
| `critical` | Modify auth logic, change data model | User approval + Master review |

### 17.5 Optimization Budget

Prevent Refiner from consuming all resources:

```yaml
refiner:
  enabled: true
  mode: suggest  # suggest | auto_safe | auto_all
  
  schedule:
    # Run after every N completed tasks
    after_tasks: 20
    # OR on explicit trigger
    on_command: true
    # OR on idle (no active tasks for 5 min)
    on_idle_minutes: 5
  
  budget:
    max_duration_minutes: 30
    max_files_per_run: 20
    max_optimizations_per_run: 15
    
  auto_approve:
    safe_changes: true
    low_risk_changes: false
    moderate_risk_changes: false
    
  focus_areas:
    performance: true
    architecture: true
    resources: true
    code_quality: true
    dependencies: true
```

### 17.6 Integration with Subsystems

| Subsystem | How Refiner Uses It |
|-----------|-------------------|
| **Cortex** | All graph analysis — AST, symbols, imports, calls, data flow |
| **Sentinel** | Consistency data, style compliance, architecture drift scores |
| **Validation** | Test suite execution, type checking, lint verification |
| **Task Graph** | Optimization tasks added as low-priority background tasks |
| **Forge Labs** | Complex optimizations can use experimental branching |
| **Memory** | Optimization history, successful patterns, avoided anti-patterns |
| **Scheduler** | Runs during idle time, yields to production tasks immediately |
| **Dashboard** | Optimization reports, before/after metrics, approval UI |

---

## 18. Formal Policy Engine (Galaxy Governance)

> [!NOTE]
> Galaxy Governance is the **enterprise rule enforcement layer**. It ensures that agents operate within defined organizational boundaries — security constraints, compliance requirements, deployment restrictions, and operational policies. Think of it as the company rulebook that every agent must follow, no exceptions.

### 18.1 Why This Matters

AI agents with access to terminals, files, networks, and APIs are **powerful but dangerous** without governance:
- An agent installs a package with a GPL license in a proprietary project
- A worker writes user passwords to a log file
- An agent deploys directly to production without approval
- A model sends proprietary code to a cloud API
- An agent creates a public S3 bucket with customer data

Galaxy Governance prevents all of this through **policy-as-code** — formal, machine-enforceable rules.

### 18.2 Six Policy Domains

```
                  GALAXY GOVERNANCE
                        │
       ┌────────────────┼────────────────┐
       │                │                │
       ▼                ▼                ▼
   Security         Compliance       Deployment
   Policies         Policies         Policies
       │                │                │
       ▼                ▼                ▼
   Access            Quality          Operational
   Control           Gates            Policies
```

---

#### Domain 1: Security Policies

**What they enforce:**

| Policy | Rule | Action on Violation |
|--------|------|-------------------|
| **No hardcoded secrets** | Scan all generated code for API keys, passwords, tokens | Block file write + alert |
| **Auth on all endpoints** | Every HTTP route must have auth middleware | Block merge |
| **Input sanitization** | All user inputs must pass through validation | Block merge |
| **No eval/exec** | Forbid `eval()`, `exec()`, `Function()` in production code | Block + suggest alternative |
| **HTTPS only** | No `http://` URLs in production config | Auto-fix to https |
| **SQL injection prevention** | No string concatenation in SQL queries | Block + suggest parameterized |
| **Dependency security** | Block packages with known critical CVEs | Block install |
| **No sensitive data in logs** | Scan log statements for PII patterns | Block + redact |

**Example policy (YAML):**
```yaml
policies:
  - name: no-hardcoded-secrets
    domain: security
    severity: critical
    enforcement: block
    
    rules:
      - pattern: "regex:(api[_-]?key|password|secret|token)\\s*[:=]\\s*['\"][^'\"]{8,}"
        scope: all_files
        exclude: ["*.test.*", "*.spec.*", "*.example.*"]
        message: "Hardcoded secret detected. Use environment variables."
        
      - pattern: "regex:-----BEGIN (RSA |EC )?PRIVATE KEY-----"
        scope: all_files
        message: "Private key in source code. Move to secrets manager."
```

---

#### Domain 2: Compliance Policies

**For regulated industries and enterprise requirements:**

| Policy | Rule | Standard |
|--------|------|----------|
| **Data handling** | PII must be encrypted at rest and in transit | GDPR, HIPAA |
| **Audit logging** | All data mutations must produce audit events | SOC2 |
| **Data retention** | User data must have TTL and deletion capability | GDPR |
| **Geographic restrictions** | Data must stay within specified regions | Data sovereignty |
| **Access logging** | All API access must be logged with user identity | SOC2, ISO 27001 |
| **Privacy by design** | User consent must be checked before data collection | GDPR |
| **License compliance** | Only approved open-source licenses allowed | Legal |
| **Export control** | No encryption algorithms restricted by export laws | EAR/ITAR |

**Example policy:**
```yaml
policies:
  - name: gdpr-data-handling
    domain: compliance
    severity: critical
    enforcement: block
    standard: GDPR
    
    rules:
      - check: data_model_fields
        match:
          field_names: [email, phone, address, name, ssn, dob]
        require:
          - encryption: at_rest
          - deletion_endpoint: exists
          - consent_check: before_collection
          - audit_log: on_access
        message: "PII field must be encrypted, deletable, consent-gated, and audit-logged"
        
      - check: data_export
        match:
          destination: external_api
        require:
          - data_processing_agreement: documented
          - transfer_mechanism: approved  # SCCs, adequacy decision, etc.
        message: "External data transfer requires documented DPA"
```

---

#### Domain 3: Deployment Policies

| Policy | Rule | Action |
|--------|------|--------|
| **No direct production deploy** | All deploys must go through staging first | Block deploy command |
| **Rollback plan required** | Every deploy must have documented rollback steps | Block without plan |
| **Health check mandatory** | Deployed services must have health endpoints | Block deploy |
| **Canary/blue-green required** | No big-bang deploys for critical services | Enforce deployment strategy |
| **Database migration review** | Schema changes require explicit approval | Block + escalate |
| **Feature flags for new features** | New user-facing features must be flag-gated | Block merge |
| **Change window enforcement** | Deploys only during approved maintenance windows | Block outside window |
| **Approval chain** | Require N approvers before production deploy | Block until approved |

**Example policy:**
```yaml
policies:
  - name: deployment-gates
    domain: deployment
    severity: error
    enforcement: block
    
    rules:
      - check: deploy_target
        match:
          environment: production
        require:
          - staging_deploy: passed_within_24h
          - all_tests: passing
          - security_scan: clean
          - rollback_plan: documented
          - approvals: { min: 2, from: [tech_lead, devops] }
          - change_window: true
        message: "Production deploy requires staging validation, approvals, and change window"
```

---

#### Domain 4: Access Control Policies

**Governing what agents CAN and CANNOT do:**

| Policy | Rule | Scope |
|--------|------|-------|
| **Worker filesystem scope** | Workers can only write within their assigned directory | Per-agent |
| **Network restrictions** | Workers cannot make outbound network calls (unless tool requires it) | Per-agent |
| **Tool restrictions per tier** | Workers can't use GitTool directly — only domain+ | Per-tier |
| **Cloud API restrictions** | Only Master can call cloud LLM APIs | Per-tier |
| **Secret access** | Only specific agents can read `.env` files | Per-agent |
| **Database access** | Only DB domain agents can run migrations | Per-domain |
| **Admin commands** | No agent can run `sudo`, `chmod 777`, etc. | Global |

**Example policy:**
```yaml
policies:
  - name: agent-access-control
    domain: access_control
    
    tiers:
      worker:
        filesystem:
          write: ["{assigned_directory}/**"]
          read: ["{project_root}/src/**", "{assigned_directory}/**"]
          forbidden: [".env*", "*.pem", "*.key", "secrets/**"]
        tools:
          allowed: [FileRead, FileWrite, FileEdit, Terminal, Search]
          forbidden: [GitTool, DeployTool, DatabaseMigrate]
        network:
          outbound: deny
        commands:
          forbidden: ["sudo *", "chmod *", "rm -rf /*", "curl *"]
          
      domain:
        filesystem:
          write: ["{domain_directory}/**", "shared/**"]
          read: ["{project_root}/**"]
          forbidden: ["*.pem", "*.key"]
        tools:
          allowed: [all]
          forbidden: [DeployTool]
        network:
          outbound: allow_approved_hosts
          
      master:
        filesystem:
          write: ["{project_root}/**"]
          read: ["{project_root}/**"]
        tools:
          allowed: [all]
        network:
          outbound: allow
```

---

#### Domain 5: Quality Gates

**Minimum quality bars that must be met:**

| Gate | Threshold | When Checked |
|------|-----------|-------------|
| **Test coverage** | ≥ 80% line coverage | Before merge |
| **Type safety** | 0 TypeScript/mypy errors | Before merge |
| **Lint clean** | 0 lint errors (warnings configurable) | Before merge |
| **Build success** | Clean compilation | Before merge |
| **No TODO/FIXME in production** | Scan for unresolved markers | Before deploy |
| **Documentation coverage** | Public exports must have docs | Before merge |
| **Max file size** | No file > 500 lines | Before merge |
| **Max function complexity** | Cyclomatic complexity ≤ 15 | Before merge |
| **Sentinel score** | Project consistency ≥ 75% | Before merge |

**Example policy:**
```yaml
policies:
  - name: quality-gates
    domain: quality
    severity: error
    enforcement: block
    
    gates:
      - name: test_coverage
        check: coverage_report
        threshold: { min: 80, metric: line_coverage_percent }
        
      - name: type_safety
        check: type_checker
        threshold: { max_errors: 0 }
        
      - name: build
        check: build_command
        threshold: { exit_code: 0 }
        
      - name: sentinel_score
        check: sentinel_consistency
        threshold: { min: 75 }
        
      - name: file_size
        check: max_file_lines
        threshold: { max: 500 }
        exceptions: ["*.generated.*", "migrations/**"]
```

---

#### Domain 6: Operational Policies

| Policy | Rule | Purpose |
|--------|------|---------|
| **Resource limits** | No agent can use > 8GB RAM | Prevent runaway processes |
| **Timeout enforcement** | All external calls must have timeouts | Prevent hanging |
| **Rate limiting** | Max 100 LLM API calls per minute | Prevent cost explosion |
| **Log rotation** | Logs must rotate at 100MB | Prevent disk fill |
| **Graceful shutdown** | All services must handle SIGTERM | Clean deployment |
| **Error budget** | Max 5% error rate before auto-pause | Prevent cascading failures |
| **Concurrency limits** | Max N parallel workers per domain | Resource governance |

### 18.3 Policy Evaluation Pipeline

Every agent action passes through the policy engine:

```
Agent requests action (file write, command, deploy, install)
      ↓
Policy Engine receives request
      ↓
Match applicable policies:
  - By domain (security, compliance, etc.)
  - By scope (file path, command, agent tier)
  - By environment (dev, staging, production)
      ↓
Evaluate each matching rule:
  - PASS → continue
  - FAIL → check enforcement mode
      ↓
Enforcement mode:
  - "audit"   → log violation, allow action
  - "warn"    → log + notify, allow action
  - "block"   → reject action, return error to agent
  - "escalate"→ reject + notify user/master for decision
      ↓
Action proceeds or is blocked
      ↓
Audit log entry created (always, regardless of outcome)
```

### 18.4 Policy Inheritance

Policies can be layered:

```
Galaxy Default Policies (built-in safety)
      ↓
Organization Policies (company-wide rules)
      ↓
Project Policies (project-specific rules)
      ↓
Domain Policies (domain-specific overrides)
```

**Conflict resolution:**
- More specific policy wins (project overrides organization)
- `severity: critical` policies CANNOT be overridden by lower levels
- User can never override Galaxy's built-in safety policies (e.g., no `rm -rf /`)

### 18.5 Policy Violation Dashboard

```
┌─────────────────────────────────────────┐
│       POLICY COMPLIANCE: 96.2%          │
├─────────────────────────────────────────┤
│ Security:      ██████████ 100% ✓        │
│ Compliance:    █████████░  94% ⚠        │
│ Deployment:    ██████████ 100% ✓        │
│ Access Control:██████████  98% ✓        │
│ Quality Gates: █████████░  92% ⚠        │
│ Operational:   ██████████  97% ✓        │
├─────────────────────────────────────────┤
│ Violations (last 24h):                  │
│  2 warnings  (compliance: missing DPA)  │
│  1 blocked   (quality: coverage 78%)    │
│  0 critical                             │
├─────────────────────────────────────────┤
│ [View All Violations] [Edit Policies]   │
└─────────────────────────────────────────┘
```

### 18.6 Audit Trail

Every policy evaluation is logged:

```json
{
  "timestamp": "2026-05-10T12:00:00Z",
  "policy": "no-hardcoded-secrets",
  "domain": "security",
  "agent": "backend_worker_12",
  "action": "file_write",
  "target": "src/config/database.ts",
  "result": "BLOCKED",
  "violation": "Hardcoded database password on line 14",
  "severity": "critical",
  "remediation": "Move password to DB_PASSWORD environment variable"
}
```

**Audit trail enables:**
- Compliance reporting (SOC2, ISO 27001 evidence)
- Forensic analysis (what happened, when, who)
- Policy effectiveness tracking (which policies trigger most)
- Agent behavior analysis (which agents violate most)

### 18.7 Integration with Subsystems

| Subsystem | How Governance Integrates |
|-----------|-------------------------|
| **Permission Layer** | Governance is the source of truth for permissions |
| **Sandbox** | Governance rules define sandbox boundaries |
| **Tool Execution** | Every tool call checked against policies before execution |
| **Sentinel** | Quality gates feed into Sentinel's consistency checks |
| **Event Bus** | Policy violations published as events |
| **Memory** | Policy configurations stored in workspace memory |
| **Dashboard** | Real-time compliance dashboard, violation alerts |
| **Cluster** | Policies enforced identically across all nodes |

---

## 19. Distributed Transaction Consistency (Galaxy Sync)

> [!IMPORTANT]
> When multiple agents modify related files simultaneously, things WILL break — merge conflicts, schema mismatches, broken imports, half-applied changes. Galaxy Sync prevents this by treating multi-agent file modifications as **transactions** with coordination, locking, and atomic commit semantics.

### 19.1 The Problem

Consider this real scenario:

```
Worker A: Modifying User model — adding "avatarUrl" field
Worker B: Modifying User API — adding new endpoint
Worker C: Modifying User tests — adding test for new field
Worker D: Modifying shared types — updating UserDTO

All working simultaneously on related files.
```

**What can go wrong:**
- Worker B reads the User model BEFORE Worker A adds avatarUrl → stale schema
- Worker C writes tests for a field that Worker A hasn't committed yet → test fails
- Worker D updates UserDTO but Worker A uses a different field name → contract mismatch
- Two workers edit the same file at the same line → merge conflict

### 19.2 Collision Scenarios

| Scenario | Example | Severity |
|----------|---------|----------|
| **Same file, same region** | Two workers editing `User.ts` lines 10-20 | Critical — guaranteed conflict |
| **Same file, different regions** | Worker A edits function at top, Worker B edits function at bottom | Moderate — git can sometimes auto-merge |
| **Shared dependency** | Worker A changes `UserModel`, Worker B imports `UserModel` | High — stale reference |
| **Shared contract** | Backend changes API response, frontend reads old format | High — runtime breakage |
| **Shared type** | Worker A renames `UserDTO.name` to `UserDTO.fullName`, Worker B uses `.name` | Critical — compile error |
| **Shared test fixture** | Two workers modify test setup in same test file | Moderate — test instability |

### 19.3 Three Concurrency Strategies

Galaxy Sync provides **three levels** of coordination, chosen based on project size and parallelism:

```
┌─────────────────────────────────────────────┐
│           GALAXY SYNC STRATEGIES            │
├─────────────────────────────────────────────┤
│                                             │
│  Level 1: File-Level Locking                │
│  (Simple, small projects)                   │
│                                             │
│  Level 2: Changeset Transactions            │
│  (Medium projects, domain-level grouping)   │
│                                             │
│  Level 3: Intent-Based Coordination         │
│  (Large projects, full semantic awareness)  │
│                                             │
└─────────────────────────────────────────────┘
```

---

### 19.4 Level 1: File-Level Locking

The simplest approach — agents acquire locks before writing.

```
Worker A wants to edit User.ts
      ↓
Request lock: LOCK("src/models/User.ts", agent="worker_a", mode="exclusive")
      ↓
Lock Manager checks:
  - Is this file already locked? → NO
  - Grant exclusive lock to worker_a
      ↓
Worker A edits User.ts
      ↓
Worker A commits and releases lock
      ↓
UNLOCK("src/models/User.ts", agent="worker_a")
```

**Lock types:**

| Lock Type | Allows | Use Case |
|-----------|--------|----------|
| `shared` (read) | Multiple readers, no writers | Multiple agents reading same file |
| `exclusive` (write) | Single writer, no readers | Agent modifying a file |
| `intent` (advisory) | Declares planned modification | Agent planning to modify soon |

**What happens when locked:**
```
Worker B wants to edit User.ts (already locked by Worker A)
      ↓
Lock Manager: DENIED — file locked by worker_a
      ↓
Options:
  1. WAIT — queue until worker_a releases (with timeout)
  2. WORK_ELSEWHERE — pick a different task
  3. ESCALATE — ask domain agent to coordinate
```

**Deadlock detection:**
```
Worker A locks User.ts, wants UserDTO.ts
Worker B locks UserDTO.ts, wants User.ts
      ↓
Lock Manager detects cycle
      ↓
Force-release the lower-priority lock
      ↓
Victim worker retries
```

**Lock timeout:**
- Default: 60 seconds
- If agent dies while holding lock → auto-release after timeout
- Heartbeat-based: lock holder must ping every 10 seconds

---

### 19.5 Level 2: Changeset Transactions

Groups related file changes into an **atomic unit** — either ALL changes apply, or NONE do.

```
Domain Agent creates a changeset:
  Changeset CS_001: "Add avatar feature"
    - Modify: src/models/User.ts (add avatarUrl field)
    - Modify: src/types/UserDTO.ts (add avatarUrl to DTO)
    - Modify: src/routes/users.ts (add upload endpoint)
    - Create: src/services/AvatarService.ts (new file)
    - Modify: src/tests/user.test.ts (add avatar tests)
      ↓
All files in changeset are RESERVED
      ↓
Workers execute their assigned files within the changeset
      ↓
When ALL workers complete:
  - Validate changeset as a unit (build + test)
  - If valid → COMMIT all changes atomically
  - If invalid → ROLLBACK all changes, nothing merged
```

**Changeset lifecycle:**

```
CREATED → RESERVED → IN_PROGRESS → VALIDATING → COMMITTED
                                        ↓
                                    ROLLED_BACK
```

**Changeset schema:**
```json
{
  "changeset_id": "cs_001",
  "name": "Add avatar feature",
  "created_by": "backend_domain",
  "status": "in_progress",
  "files": [
    {
      "path": "src/models/User.ts",
      "operation": "modify",
      "assigned_to": "worker_a",
      "status": "completed",
      "lock_type": "exclusive"
    },
    {
      "path": "src/types/UserDTO.ts",
      "operation": "modify",
      "assigned_to": "worker_b",
      "status": "in_progress",
      "lock_type": "exclusive"
    }
  ],
  "dependencies": ["cs_000_user_model_base"],
  "timeout_minutes": 30,
  "rollback_on_failure": true
}
```

**Cross-changeset dependencies:**
```
Changeset A: "Create User model" (must complete first)
      ↓
Changeset B: "Add User API routes" (depends on A)
      ↓
Changeset C: "Add User frontend" (depends on B)

Scheduler enforces ordering: A → B → C
Within each changeset: workers run in parallel
```

---

### 19.6 Level 3: Intent-Based Coordination

The most sophisticated approach — agents **declare their intent** before making changes, and the coordinator detects conflicts proactively.

```
Worker A declares intent:
  INTENT: "I will add field 'avatarUrl: string' to User model at line 15"
      ↓
Worker B declares intent:
  INTENT: "I will import User from src/models/User.ts and call User.findById()"
      ↓
Coordinator analyzes:
  - Worker A is modifying User → Worker B depends on User
  - Worker B should wait for Worker A to finish
  - Worker B can proceed with OTHER work while waiting
      ↓
Coordinator creates execution order:
  1. Worker A modifies User (other workers can do unrelated tasks)
  2. Worker B proceeds (reads updated User)
```

**Intent declaration protocol:**
```json
{
  "agent": "worker_a",
  "intent": {
    "action": "modify",
    "target": "src/models/User.ts",
    "description": "Add avatarUrl field to User interface",
    "affected_symbols": ["User", "UserCreateInput"],
    "estimated_duration_seconds": 30
  }
}
```

**Coordinator conflict detection (powered by Cortex):**
```
All declared intents collected
      ↓
Cortex analyzes:
  1. File overlap: Do any intents target the same file?
  2. Symbol overlap: Do any intents modify symbols others depend on?
  3. Contract overlap: Do any intents change API contracts others consume?
  4. Type overlap: Do any intents change shared types?
      ↓
Build execution graph:
  - No conflict → parallel execution
  - Read-after-write → sequence (writer first)
  - Write-after-write (same file) → sequence OR merge
  - Circular → split one intent, re-plan
```

**Intent conflict resolution:**

| Conflict Type | Resolution |
|---------------|-----------|
| Two writers, same file, same region | Serialize: higher-priority worker goes first |
| Two writers, same file, different regions | Parallel with auto-merge attempt |
| Writer + reader, same file | Reader waits for writer to finish |
| Two writers, shared type/contract | Serialize + validate after both complete |
| No conflict detected | Full parallel execution |

---

### 19.7 Merge Conflict Resolution

When conflicts DO occur despite coordination:

```
Conflict detected during merge
      ↓
Classify conflict:
  - TRIVIAL: whitespace, import ordering → auto-resolve
  - MECHANICAL: non-overlapping changes in same file → auto-merge
  - SEMANTIC: overlapping logic changes → needs resolution
  - STRUCTURAL: incompatible architecture changes → needs domain agent
      ↓
Resolution strategy:
  - TRIVIAL/MECHANICAL: Galaxy auto-resolves
  - SEMANTIC: Domain agent resolves (has context of both workers)
  - STRUCTURAL: Escalate to Master agent
```

**Auto-resolvable conflicts (no human needed):**
- Different functions added to same file → both kept
- Same import added by two workers → deduplicate
- Non-overlapping edits in same function → merge
- Formatting-only differences → apply project style

**Unresolvable conflicts (require intelligence):**
- Two workers implement same feature differently → pick one, discard other
- Contradictory type changes → domain agent decides canonical type
- Breaking API change + consumer code → coordinate fix

### 19.8 Dependency-Aware Commit Ordering

Cortex ensures commits happen in the right order:

```
Changes ready to commit:
  1. User model (modified)
  2. User API routes (depends on User model)
  3. User tests (depends on User model + API routes)
  4. Frontend User page (depends on User API routes)
      ↓
Cortex builds commit order from import/dependency graph:
  Commit 1: User model → build + type check
  Commit 2: User API routes → build + type check
  Commit 3: User tests → run tests
  Commit 4: Frontend User page → build + type check
      ↓
Each commit validates before next proceeds
If commit 2 fails → halt 3 and 4, fix 2 first
```

### 19.9 Optimistic vs Pessimistic Concurrency

Galaxy supports both modes:

| Mode | How | When to Use |
|------|-----|-------------|
| **Optimistic** | Let agents work freely, resolve conflicts at merge time | Few agents, low collision probability |
| **Pessimistic** | Lock files before modification, prevent conflicts entirely | Many agents, high collision probability |
| **Hybrid** (default) | Lock shared/critical files, optimistic for isolated files | Most projects |

**Auto-selection:**
```
Scheduler evaluates:
  - < 5 parallel workers → optimistic (low collision risk)
  - 5-15 parallel workers → hybrid
  - > 15 parallel workers → pessimistic (high collision risk)
  - Shared types/contracts being modified → always pessimistic for those files
```

### 19.10 Configuration

```yaml
sync:
  strategy: hybrid  # optimistic | pessimistic | hybrid | intent_based
  
  locking:
    enabled: true
    timeout_seconds: 60
    heartbeat_interval_seconds: 10
    deadlock_detection: true
    
  changesets:
    enabled: true
    max_files_per_changeset: 20
    rollback_on_failure: true
    timeout_minutes: 30
    
  conflict_resolution:
    auto_resolve_trivial: true
    auto_merge_non_overlapping: true
    escalation_order: [domain_agent, master_agent, user]
    
  commit_ordering:
    dependency_aware: true
    validate_after_each_commit: true
    
  critical_files:
    # Always use pessimistic locking for these
    always_lock:
      - "*.schema.*"
      - "*.migration.*"
      - "src/types/**"
      - "package.json"
      - "*.lock"
```

### 19.11 Integration with Subsystems

| Subsystem | How Sync Integrates |
|-----------|-------------------|
| **Cortex** | Dependency/import/symbol graphs power conflict detection |
| **Scheduler** | Scheduling respects lock state and changeset dependencies |
| **Task Graph** | Tasks within a changeset form a sub-DAG |
| **Sentinel** | Post-merge consistency validation |
| **Event Bus** | Lock acquired/released/conflict events |
| **Fault Reconstruction** | Failed changesets trigger targeted reconstruction |
| **Cluster** | Lock manager distributed across nodes via event bus |
| **Dashboard** | Live lock visualization, changeset status, conflict alerts |

---

## 20. Confidence & Trust Scoring (Galaxy Trust)

> [!NOTE]
> Every piece of output Galaxy produces — every file, function, test, decision — should carry a **trust profile**. This transforms Galaxy from "hope it works" to "know how much to trust it." Trust scoring enables automated decision-making: high-trust outputs auto-merge, low-trust outputs require review.

### 20.1 Why This Matters

Without confidence scoring, all agent outputs are treated equally:
- A simple `console.log` fix gets the same scrutiny as a complex auth rewrite
- A worker's first attempt gets the same trust as its 5th verified iteration
- A generated test that passes gets the same trust whether it covers edge cases or just the happy path
- A human has NO signal about which outputs to review carefully vs. which to trust

Galaxy Trust attaches **quantified confidence** to everything, enabling intelligent automation and human attention allocation.

### 20.2 The Four Trust Dimensions

Every agent output carries a **trust profile** with four scores:

```
┌──────────────────────────────────────────────┐
│              TRUST PROFILE                    │
├──────────────────────────────────────────────┤
│                                              │
│  Generation Confidence    ████████░░  82%    │
│  How sure is the agent about its output?     │
│                                              │
│  Validation Quality       █████████░  91%    │
│  How thoroughly was it verified?             │
│                                              │
│  Risk Score               ██░░░░░░░░  18%    │
│  How much damage if wrong?                   │
│                                              │
│  Stability Estimate       ███████░░░  72%    │
│  How likely to need changes later?           │
│                                              │
├──────────────────────────────────────────────┤
│  COMPOSITE TRUST:         ████████░░  84%    │
└──────────────────────────────────────────────┘
```

---

#### Dimension 1: Generation Confidence

**"How sure is the agent that its output is correct?"**

Measured by:

| Signal | High Confidence | Low Confidence |
|--------|----------------|----------------|
| Task clarity | Precise, well-scoped prompt | Ambiguous, under-specified |
| Context availability | All needed files/types provided | Missing dependencies, guessing |
| Pattern familiarity | Common CRUD, standard patterns | Novel algorithm, unfamiliar domain |
| Model certainty | Low token perplexity, decisive output | Hedging language, multiple revisions |
| Retry count | First attempt succeeded | Took 3+ retries to pass |
| Output consistency | Same output on re-generation | Different output each time |

**Scoring formula:**
```
generation_confidence = (
    task_clarity_score × 0.20 +
    context_completeness × 0.25 +
    pattern_familiarity × 0.15 +
    retry_penalty × 0.20 +        # 100% if first try, -15% per retry
    output_consistency × 0.20
)
```

---

#### Dimension 2: Validation Quality

**"How thoroughly was this output verified?"**

| Validation Level | Score Boost | Description |
|-----------------|------------|-------------|
| None | 0% | Output not validated at all |
| Syntax check | +10% | Parses without errors |
| Build pass | +20% | Compiles successfully |
| Type check | +15% | No type errors |
| Lint pass | +10% | Meets style rules |
| Unit tests pass | +20% | Tests written and passing |
| Integration test | +15% | Works with connected modules |
| Sentinel approved | +10% | Consistency checks passed |

**Scoring formula:**
```
validation_quality = sum(passed_validation_scores)
# Capped at 100%

Example:
  Syntax ✓ (+10) + Build ✓ (+20) + Types ✓ (+15) + Lint ✓ (+10) + Unit ✓ (+20) = 75%
  + Integration ✓ (+15) + Sentinel ✓ (+10) = 100%
```

**Validation depth also considers test quality:**
```
Test Quality Modifiers:
  - Tests cover happy path only → -10%
  - Tests cover edge cases → +0% (expected)
  - Tests cover error handling → +5%
  - Tests cover boundary conditions → +5%
  - Mutation testing survival rate > 80% → +5%
```

---

#### Dimension 3: Risk Score

**"How much damage could this cause if it's wrong?"**

| Factor | High Risk | Low Risk |
|--------|-----------|----------|
| File criticality | Auth, payments, DB migrations | README, comments, formatting |
| Scope of change | Modifies public API, shared types | Local function, single file |
| Reversibility | Database migration, deployment | Code edit (git revert) |
| Data sensitivity | Handles PII, credentials | Static content, UI styling |
| Blast radius | 50+ files depend on this | 0-2 files depend on this |
| Security surface | Network-facing, user input handling | Internal utility, no I/O |

**Scoring formula:**
```
risk_score = (
    file_criticality × 0.25 +
    change_scope × 0.20 +
    reversibility_risk × 0.15 +
    data_sensitivity × 0.15 +
    blast_radius × 0.15 +
    security_surface × 0.10
)
```

> [!TIP]
> Risk score is INVERTED for trust — high risk = LOW trust. A 90% risk score means "be very careful with this."

---

#### Dimension 4: Stability Estimate

**"How likely is this to need changes in the near future?"**

| Signal | High Stability | Low Stability |
|--------|---------------|---------------|
| Dependency volatility | Depends on stable, mature APIs | Depends on changing/unstable interfaces |
| Feature maturity | Well-understood requirement | Requirements still evolving |
| Pattern stability | Established project pattern | First use of new pattern |
| External dependency | Stable library, locked version | Alpha library, frequent breaking changes |
| Architecture alignment | Fits existing architecture | Edge case, workaround needed |

**Scoring formula:**
```
stability_estimate = (
    dependency_stability × 0.25 +
    requirement_clarity × 0.25 +
    pattern_maturity × 0.20 +
    external_dep_stability × 0.15 +
    architecture_fit × 0.15
)
```

---

### 20.3 Composite Trust Score

All four dimensions combine into a single **composite trust score:**

```
composite_trust = (
    generation_confidence × 0.25 +
    validation_quality × 0.35 +      # Validation is most important
    (100 - risk_score) × 0.25 +      # Inverted: low risk = high trust
    stability_estimate × 0.15
)
```

**Trust bands:**

| Band | Score | Meaning | Default Action |
|------|-------|---------|---------------|
| 🟢 **High Trust** | 85-100% | Strong confidence, well-validated, low risk | Auto-merge |
| 🟡 **Medium Trust** | 65-84% | Reasonable confidence, some gaps | Domain agent review |
| 🟠 **Low Trust** | 40-64% | Uncertain, poorly validated, or high risk | Master agent review |
| 🔴 **Critical** | 0-39% | Very uncertain or very risky | Human review required |

### 20.4 Trust Profile Per Output

Every agent output carries this metadata:

```json
{
  "output_id": "out_abc123",
  "agent": "backend_worker_12",
  "task": "Generate JWT middleware",
  "files_produced": ["src/auth/middleware.ts"],
  "trust_profile": {
    "generation_confidence": 82,
    "validation_quality": 91,
    "risk_score": 45,
    "stability_estimate": 72,
    "composite_trust": 79,
    "band": "medium",
    "signals": {
      "retry_count": 1,
      "tests_passed": 12,
      "tests_failed": 0,
      "lint_clean": true,
      "type_check_clean": true,
      "sentinel_approved": true,
      "build_passed": true,
      "blast_radius_files": 8
    }
  },
  "recommended_action": "domain_review",
  "timestamp": "2026-05-10T12:00:00Z"
}
```

### 20.5 Agent Trust History (Reputation)

Each agent builds a **trust reputation** over time:

```
┌────────────────────────────────────────────┐
│  AGENT REPUTATION: backend_worker_12       │
├────────────────────────────────────────────┤
│  Total tasks:           47                 │
│  Average trust score:   81%                │
│  First-attempt success: 78%                │
│  Validation pass rate:  94%                │
│  Outputs requiring fix: 6 (12%)            │
│                                            │
│  Trust trend:  ↗ Improving (+3% this week) │
│                                            │
│  Best at:  CRUD operations (avg 92%)       │
│  Weak at:  Complex auth logic (avg 61%)    │
│                                            │
│  Recommendation:                           │
│  Route CRUD tasks here. Escalate auth to   │
│  stronger model or domain agent.           │
└────────────────────────────────────────────┘
```

**Reputation affects future scheduling:**
- High-reputation agents → assigned harder tasks
- Low-reputation agents → assigned simpler tasks or upgraded to stronger model
- Consistently low reputation → model swap recommendation
- Domain-specific reputation → route tasks to agent's strengths

### 20.6 Project-Level Trust Dashboard

Galaxy Studio shows overall project trust:

```
┌─────────────────────────────────────────────┐
│         PROJECT TRUST OVERVIEW              │
├─────────────────────────────────────────────┤
│                                             │
│  Overall Trust:          ████████░░  83%    │
│                                             │
│  By Domain:                                 │
│    Frontend:             █████████░  88%    │
│    Backend:              ████████░░  82%    │
│    Database:             █████████░  90%    │
│    Auth/Security:        ██████░░░░  65%  ⚠ │
│    Tests:                ████████░░  85%    │
│                                             │
│  Recent Outputs:                            │
│    🟢 High trust:     42 files (61%)        │
│    🟡 Medium trust:   22 files (32%)        │
│    🟠 Low trust:       4 files (6%)         │
│    🔴 Critical:        1 file  (1%)   ⚠    │
│                                             │
│  ⚠ Attention needed:                       │
│  - src/auth/oauth.ts (trust: 38%)           │
│  - src/security/encryption.ts (trust: 42%)  │
│                                             │
│  [Review Low-Trust Files] [Trust Report]    │
└─────────────────────────────────────────────┘
```

### 20.7 Trust-Driven Automation

Trust scores drive automated decision-making:

```yaml
trust_automation:
  auto_merge:
    min_composite_trust: 85
    required_validations: [build, type_check, lint, unit_tests]
    excluded_paths: ["src/auth/**", "*.migration.*"]  # Always review these
    
  domain_review:
    trust_range: [65, 84]
    action: domain_agent_reviews_before_merge
    
  master_review:
    trust_range: [40, 64]
    action: master_agent_reviews_and_may_regenerate
    
  human_review:
    max_composite_trust: 39
    action: block_until_human_approves
    notify: true
    
  auto_escalate:
    # If an agent produces 3+ low-trust outputs in a row
    consecutive_low_trust_threshold: 3
    action: swap_to_stronger_model
```

**Example flow:**
```
Worker generates auth middleware → trust: 38% (critical)
      ↓
Auto-blocked. Human review required.
      ↓
Reason: high risk (auth), low generation confidence (novel pattern),
        moderate validation (unit tests pass but no integration test)
      ↓
User reviews, approves with modifications
      ↓
Trust system learns: "auth middleware patterns need stronger model"
      ↓
Next auth task → automatically routed to domain agent or stronger model
```

### 20.8 Confidence Calibration

Trust scores must be **calibrated** — an 80% confidence should mean the output is correct 80% of the time.

**Calibration process:**
```
Collect historical data:
  - All outputs with their trust scores
  - Which outputs actually needed fixes later
      ↓
Compare predicted vs actual:
  - Score 80-90%: were 85% of these actually correct? → well-calibrated
  - Score 80-90%: were only 60% correct? → overconfident, reduce scores
  - Score 40-50%: were 70% correct? → underconfident, increase scores
      ↓
Adjust scoring weights per signal:
  - If retry_count is a strong predictor → increase its weight
  - If lint_pass doesn't predict correctness → decrease its weight
      ↓
Retrain calibration model periodically
```

**Overconfidence penalty:**
- If Galaxy marks output as 90% trust but it breaks → large penalty
- System learns to be more conservative on similar tasks
- Better to be slightly underconfident than overconfident

### 20.9 Trust Decay

Trust scores decay over time as code ages without reverification:

```
Initial generation → Trust: 85%
After 1 week → Trust: 83% (minor decay)
After 1 month → Trust: 78% (moderate decay)
After 3 months → Trust: 70% (significant decay)
After 6 months → Trust: 60% (major decay — re-review recommended)

Decay accelerators:
  - Dependencies updated → faster decay
  - Related files changed → faster decay
  - No test coverage → faster decay
  
Decay preventors:
  - Tests still passing → slow decay
  - No related changes → slow decay
  - Recently re-validated → reset decay timer
```

### 20.10 Configuration

```yaml
trust:
  enabled: true
  
  scoring:
    generation_confidence_weight: 0.25
    validation_quality_weight: 0.35
    risk_score_weight: 0.25
    stability_estimate_weight: 0.15
    
  bands:
    high: { min: 85, action: auto_merge }
    medium: { min: 65, action: domain_review }
    low: { min: 40, action: master_review }
    critical: { min: 0, action: human_review }
    
  decay:
    enabled: true
    daily_decay_percent: 0.1
    dependency_change_decay_percent: 2.0
    test_pass_decay_reduction: 0.5
    
  calibration:
    enabled: true
    recalibrate_after_tasks: 100
    overconfidence_penalty: 1.5
    
  reputation:
    track_per_agent: true
    track_per_model: true
    influence_scheduling: true
    
  always_review_paths:
    - "src/auth/**"
    - "src/security/**"
    - "*.migration.*"
    - "src/payments/**"
```

### 20.11 Integration with Subsystems

| Subsystem | How Trust Integrates |
|-----------|---------------------|
| **Orchestrator** | Trust scores determine merge/review/block decisions |
| **Scheduler** | Agent reputation influences task assignment |
| **Model Routing** | Low-trust patterns trigger model escalation |
| **Sentinel** | Sentinel approval is a validation quality signal |
| **Cortex** | Blast radius from dependency graph feeds risk score |
| **Validation** | Each validation stage contributes to validation quality |
| **Forge Labs** | Experiment branch comparison uses trust scores |
| **Refiner** | Low-trust files prioritized for optimization |
| **Memory** | Trust history stored in workspace memory |
| **Dashboard** | Trust dashboard, agent reputation, low-trust alerts |
| **Governance** | Trust thresholds enforced as quality gate policies |
| **Fault Reconstruction** | Low-trust files checked first during fault tracing |

---

## 21. Persistence & Recovery Engine (Galaxy Vault)

> [!IMPORTANT]
> This is NOT optional. This is what separates Galaxy from toy agent systems. **Real infrastructure must survive crashes, reboots, power loss, model switches, and paused work without losing a single byte of progress.** Galaxy Vault is the durability backbone that makes everything else production-grade.

### 21.1 The Fundamental Principle

```
PROJECT STATE MUST SURVIVE BEYOND PROCESS LIFETIME.
PROJECT STATE MUST BE MODEL-INDEPENDENT.
```

At ANY moment, Galaxy must be able to:
- **Stop** (user pauses)
- **Crash** (power loss, OOM, GPU failure)
- **Restart** (reboot, update, migration)
- **Switch models** (swap GPT-5 → Claude → DeepSeek)
- **Switch machines** (laptop → workstation → server)

WITHOUT losing:
- Project progress
- Task graph state
- Memory/architecture
- Agent assignments
- Terminal history
- Validation progress
- Execution DAG
- Checkpoint history

### 21.2 Architecture

```
┌──────────────────────────────────────────┐
│             GALAXY VAULT                  │
├──────────────────────────────────────────┤
│                                          │
│  ┌────────────┐  ┌────────────────────┐  │
│  │  Checkpoint │  │  Recovery Manager  │  │
│  │  Engine     │  │                    │  │
│  └─────┬──────┘  └────────┬───────────┘  │
│        │                  │              │
│        ▼                  ▼              │
│  ┌────────────┐  ┌────────────────────┐  │
│  │  Snapshot   │  │  Event Replay     │  │
│  │  Store      │  │  Engine           │  │
│  └─────┬──────┘  └────────┬───────────┘  │
│        │                  │              │
│        ▼                  ▼              │
│  ┌────────────┐  ┌────────────────────┐  │
│  │  State      │  │  Hibernation      │  │
│  │  Serializer │  │  Manager          │  │
│  └────────────┘  └────────────────────┘  │
│                                          │
└──────────────────────────────────────────┘
```

### 21.3 Pause / Resume System

#### Explicit Pause

User triggers pause (CLI command or dashboard button):

```
User: "galaxy pause"
      ↓
Vault receives PAUSE signal
      ↓
1. Notify all agents: "PAUSE — finish current atomic operation"
      ↓
2. Wait for agents to reach safe pause points:
   - Workers: finish current file write OR save partial progress
   - Domain agents: save reasoning state
   - Master: save orchestration plan
   - Validators: save validation progress
      ↓
3. Create full checkpoint (see 21.5)
      ↓
4. Persist all state to disk
      ↓
5. Gracefully terminate agents
      ↓
6. Unload models from VRAM (optional — configurable)
      ↓
7. Report: "Project paused. Checkpoint: cp_184. Resume anytime."
```

#### Resume

```
User: "galaxy resume"
      ↓
Vault loads latest checkpoint
      ↓
1. Restore task graph state
      ↓
2. Restore memory state
      ↓
3. Restore scheduler state
      ↓
4. Load required models (may be DIFFERENT from before)
      ↓
5. Recreate agent instances
      ↓
6. Reattach terminal sessions (tmux)
      ↓
7. Resume tasks from their saved states:
   - completed tasks: skip
   - in_progress tasks: resume from checkpoint or restart
   - blocked tasks: re-evaluate dependencies
   - failed tasks: retry with current model
      ↓
8. Report: "Project resumed from cp_184. 12 tasks remaining."
```

#### Resume with Different Models

```
User: "galaxy resume --master-model claude-4 --worker-model deepseek-v3-7b"
      ↓
Vault loads checkpoint
      ↓
Model routing layer maps new models to agent roles
      ↓
ALL project state is preserved
ONLY the inference engines change
      ↓
Execution continues seamlessly
```

### 21.4 Crash Recovery

When Galaxy doesn't get a clean shutdown:

```
CRASH DETECTED (process died, no clean pause)
      ↓
On next startup:
      ↓
1. Vault checks for crash marker:
   - File: .galaxy/runtime/crash_recovery_needed
   - Created on startup, deleted on clean shutdown
   - If present → crash recovery mode
      ↓
2. Load last valid checkpoint
      ↓
3. Replay events since checkpoint:
   - Read event log from checkpoint timestamp
   - Reconstruct state changes
   - Identify incomplete operations
      ↓
4. Assess damage:
   - Which tasks were mid-execution? → mark for retry
   - Which files were mid-write? → check git status, discard partial writes
   - Which terminals died? → recreate
   - Which models were loaded? → reload needed ones
      ↓
5. Recovery report:
   "Crash recovery from cp_182 (14 min ago)
    - 3 tasks need retry
    - 1 partial file write discarded
    - 2 terminals recreated
    - All memory intact"
      ↓
6. Resume execution
```

### 21.5 Galaxy Checkpoints

The checkpoint is the **core persistence primitive** — a serializable snapshot of the entire Galaxy runtime state.

**What a checkpoint contains:**

```json
{
  "checkpoint_id": "cp_184",
  "timestamp": "2026-05-10T12:00:00Z",
  "trigger": "task_completed",
  "version": "1.0.0",
  
  "task_graph": {
    "tasks": [
      {
        "task_id": "backend_auth_api",
        "status": "completed",
        "assigned_agent": "worker_12",
        "progress": 100,
        "dependencies": ["db_schema"],
        "files_produced": ["src/auth/middleware.ts"],
        "trust_score": 85
      },
      {
        "task_id": "frontend_login",
        "status": "in_progress",
        "assigned_agent": "worker_15",
        "progress": 65,
        "partial_output": "ref:partial/worker_15_output.diff",
        "dependencies": ["backend_auth_api"]
      }
    ],
    "dag_edges": [["db_schema", "backend_auth_api"], ["backend_auth_api", "frontend_login"]]
  },
  
  "agent_states": [
    {
      "agent_id": "worker_12",
      "role": "backend_worker",
      "status": "idle",
      "model_used": "qwen2.5-coder-7b",
      "current_task": null,
      "tasks_completed": 5,
      "trust_reputation": 81,
      "workspace": "/workspace/auth"
    },
    {
      "agent_id": "worker_15",
      "role": "frontend_worker",
      "status": "paused",
      "model_used": "qwen2.5-coder-7b",
      "current_task": "frontend_login",
      "last_action": "Writing LoginForm.tsx",
      "workspace": "/workspace/frontend/auth"
    }
  ],
  
  "memory_state": {
    "architecture_hash": "sha256:abc123",
    "workspace_memory_path": ".galaxy/memory/",
    "memory_files_count": 14,
    "last_memory_update": "2026-05-10T11:55:00Z"
  },
  
  "scheduler_state": {
    "mode": "balanced",
    "active_models": ["qwen2.5-coder-7b"],
    "vram_used_mb": 6144,
    "queued_tasks": 4,
    "parallel_workers": 3
  },
  
  "sentinel_state": {
    "consistency_score": 87,
    "style_profile_hash": "sha256:def456",
    "vocabulary_hash": "sha256:ghi789",
    "pending_violations": 2
  },
  
  "cortex_state": {
    "index_version": 42,
    "files_indexed": 156,
    "last_full_scan": "2026-05-10T10:00:00Z"
  },
  
  "sync_state": {
    "active_locks": [],
    "pending_changesets": ["cs_003"],
    "last_commit": "git:abc123def"
  },
  
  "terminal_sessions": [
    {
      "tmux_session": "galaxy_worker_12",
      "agent_id": "worker_12",
      "status": "detached",
      "last_command": "npm test",
      "cwd": "/workspace/auth"
    }
  ]
}
```

### 21.6 Checkpoint Triggers

| Trigger | Type | Why |
|---------|------|-----|
| Task completed | Automatic | Natural progress milestone |
| Architecture changed | Automatic | Critical state change |
| Validation passed | Automatic | Verified stable state |
| Every N minutes | Periodic | Safety net (default: 5 min) |
| Before dangerous operation | Pre-emptive | Recovery point before risk |
| Before model swap | Pre-emptive | State before infrastructure change |
| User-requested | Manual | "galaxy checkpoint" command |
| Before experiment | Pre-emptive | Recovery if experiment goes wrong |
| Domain completed | Automatic | Major milestone |
| Before shutdown | Automatic | Clean pause state |

### 21.7 Incremental Checkpointing

Full checkpoints are expensive. Galaxy uses **incremental saves:**

```
Checkpoint cp_180 (FULL — 12MB)
    ↓
Checkpoint cp_181 (INCREMENTAL — 200KB)
  Only: 2 task status changes, 1 new memory file
    ↓
Checkpoint cp_182 (INCREMENTAL — 350KB)
  Only: 3 file writes, scheduler state update
    ↓
Checkpoint cp_183 (INCREMENTAL — 150KB)
  Only: 1 task completed, trust scores updated
    ↓
Checkpoint cp_184 (FULL — 14MB) ← periodic full snapshot
```

**Compaction:**
- Full snapshot every 20 incremental checkpoints
- Old incremental checkpoints discarded after compaction
- Retention policy: keep last 10 full snapshots

### 21.8 Checkpoint Storage

| Data | Storage | Reason |
|------|---------|--------|
| Task graph | PostgreSQL | Relational, queryable, transactional |
| Agent states | PostgreSQL | Structured, indexed |
| Events/log | PostgreSQL + Redis | Event replay, hot cache |
| Memory files | Filesystem | Already file-based |
| Snapshots | Filesystem (compressed) | Large, infrequent access |
| Terminal state | tmux server | Native persistence |
| Cortex graphs | SQLite / filesystem | Pre-built indexes |
| Configuration | YAML files | Human-readable, version-controlled |

### 21.9 Model Independence

**The most critical design principle:**

```
Project State ≠ Model State
```

Models are **interchangeable reasoning engines.** Project state is **persistent orchestration truth.**

**What is model-dependent (MUST NOT persist):**
- Internal model weights
- KV cache
- Token probabilities
- Model-specific conversation format

**What is model-independent (MUST persist):**
- Task definitions and status
- Architecture decisions and contracts
- Generated code and files
- Memory and knowledge
- Validation results
- Trust scores
- Execution DAG
- Agent assignments (role, not model)

**Agent state stores ROLE, not MODEL:**
```json
{
  "agent_id": "worker_12",
  "role": "backend_worker",
  "tier": "worker",
  "capabilities_required": ["code_generation", "python"],
  
  "model_used": "qwen2.5-coder-7b"
}
```

On resume with different model:
```json
{
  "agent_id": "worker_12",
  "role": "backend_worker",        
  "tier": "worker",                
  "capabilities_required": ["code_generation", "python"],
  
  "model_used": "deepseek-coder-v3-7b"
}
```

Role stays. Model swaps. Project continues.

### 21.10 Terminal Session Persistence

tmux is key — sessions survive process death:

```
Galaxy startup
      ↓
Check for existing tmux sessions:
  $ tmux list-sessions | grep galaxy_
      ↓
Found sessions?
  YES → reattach agents to existing sessions
        Restore agent-terminal mapping from checkpoint
        Resume command history
  NO  → create new sessions as needed
```

**Terminal state recovery:**
```json
{
  "tmux_session": "galaxy_worker_12",
  "agent_id": "worker_12",
  "cwd": "/workspace/auth",
  "env_vars": { "NODE_ENV": "test" },
  "last_command": "npm test",
  "last_exit_code": 0,
  "scrollback_lines": 500
}
```

### 21.11 Event Replay Recovery

Because Galaxy is event-driven, state can be **reconstructed from the event log:**

```
Load last full checkpoint (cp_180)
      ↓
Replay events from cp_180 to crash point:
  event_001: task_assigned(worker_12, "auth_api")
  event_002: file_written("src/auth/middleware.ts")
  event_003: test_passed("auth.test.ts", 12/12)
  event_004: task_completed("auth_api", trust=85)
  event_005: task_assigned(worker_15, "frontend_login")
  event_006: file_written("src/components/LoginForm.tsx")  ← PARTIAL
  --- CRASH ---
      ↓
Reconstructed state:
  task "auth_api": completed ✓
  task "frontend_login": in_progress (partial write detected)
      ↓
Recovery action:
  Discard partial LoginForm.tsx write
  Restart "frontend_login" task from scratch
```

**Event log persistence:**
- Events written to **write-ahead log (WAL)** before execution
- WAL survives crashes (fsync'd to disk)
- Event format is model-independent (actions + results, not prompts)

### 21.12 Project Hibernation

For long-term storage when a project is paused for days/weeks/months:

```
User: "galaxy hibernate"
      ↓
1. Create full checkpoint
      ↓
2. Unload ALL models from VRAM/RAM
      ↓
3. Compress state:
   - Task graph → compressed JSON
   - Memory → compressed archive
   - Cortex graphs → compressed SQLite
   - Event log → compressed + rotated
   - Terminal history → compressed text
      ↓
4. Store compressed snapshot:
   .galaxy/hibernate/
     ├── checkpoint.json.zst     (compressed checkpoint)
     ├── memory.tar.zst          (compressed memory files)
     ├── cortex.db.zst           (compressed graph DB)
     ├── events.log.zst          (compressed event log)
     └── manifest.json           (metadata, version, timestamp)
      ↓
5. Release ALL resources (GPU, RAM, CPU, terminals)
      ↓
6. Report: "Project hibernated. Snapshot: 48MB. Resume anytime."
```

**Wake from hibernation:**
```
User: "galaxy wake"
      ↓
1. Decompress snapshot
2. Restore checkpoint
3. Load models (may be completely different)
4. Rebuild Cortex indexes (incremental from snapshot)
5. Recreate terminals
6. Resume execution
      ↓
Report: "Project resumed from hibernation (paused 12 days ago).
         Using new models. 8 tasks remaining."
```

### 21.13 Cross-Hardware Resume

Migrate a project from one machine to another:

```
Machine A (laptop, RTX 3060, 12GB VRAM):
  galaxy export --output galaxy_project.vault
      ↓
Creates portable snapshot:
  galaxy_project.vault (contains all state, NO model weights)
      ↓
Machine B (workstation, RTX 4090, 24GB VRAM):
  galaxy import galaxy_project.vault
      ↓
1. Load checkpoint
2. Scheduler detects new hardware:
   "24GB VRAM detected (was 12GB). Upgrading worker models."
3. Auto-adjust:
   - Workers: 7B → 14B (more VRAM available)
   - Parallelism: 2 → 5 (more resources)
   - Scheduling mode: unchanged
4. Resume with better hardware
      ↓
Report: "Project imported. Hardware upgrade detected.
         Workers upgraded to 14B. 5x parallelism enabled."
```

**What's in the .vault export:**
- Full checkpoint (JSON)
- Memory files
- Cortex graph snapshots
- Event log
- Configuration
- Git repo reference (NOT the repo itself — git clone on target)
- **NO model weights** (downloaded/loaded on target)

### 21.14 Recovery Policies

After any restart, the Recovery Manager applies policies:

| Situation | Policy | Action |
|-----------|--------|--------|
| Task was `in_progress` | **Retry safely** | Restart task from last clean output |
| Task was `validating` | **Rerun validation** | Validation is idempotent, just rerun |
| Task was `generating` | **Restart generation** | Partial generation discarded, regenerate |
| Terminal died | **Recreate** | New tmux session, restore cwd + env |
| Model unavailable | **Reroute** | Use alternative model of same tier |
| Lock held by dead agent | **Force release** | Release lock, reassign task |
| Changeset incomplete | **Resume or rollback** | Complete remaining files or rollback all |
| Experiment mid-run | **Resume branches** | Continue from branch checkpoints |
| Node missing (cluster) | **Reschedule** | Move tasks to available nodes |
| Event bus was down | **Replay buffer** | Agents replayed buffered events |

### 21.15 Configuration

```yaml
vault:
  enabled: true
  
  checkpointing:
    periodic_interval_minutes: 5
    full_snapshot_every_n_incremental: 20
    on_task_complete: true
    on_architecture_change: true
    on_validation_pass: true
    before_model_swap: true
    before_dangerous_ops: true
    
  retention:
    max_full_snapshots: 10
    max_incremental_per_full: 20
    compress_old_snapshots: true
    
  crash_recovery:
    enabled: true
    crash_marker_file: ".galaxy/runtime/crash_recovery_needed"
    event_replay: true
    discard_partial_writes: true
    
  hibernation:
    compression: zstd
    unload_models: true
    compress_cortex: true
    compress_events: true
    
  pause_resume:
    graceful_timeout_seconds: 30  # max wait for agents to reach safe point
    unload_models_on_pause: false  # keep models warm for quick resume
    
  model_independence:
    store_role_not_model: true
    allow_model_swap_on_resume: true
    auto_adapt_to_hardware: true
    
  export:
    include_memory: true
    include_cortex: true
    include_events: true
    include_git_repo: false  # reference only, not full clone
    compression: zstd
```

### 21.16 Integration with Subsystems

| Subsystem | How Vault Integrates |
|-----------|---------------------|
| **Orchestrator** | Vault saves/restores task graph and execution plan |
| **Scheduler** | Vault saves/restores scheduler state, adapts to new hardware on resume |
| **Task Graph** | DAG persisted to PostgreSQL, restored on resume |
| **Model Routing** | Models are interchangeable — routing adapts on resume |
| **Memory** | Memory files already persistent — Vault ensures consistency |
| **Sentinel** | Style profiles, vocabulary saved with checkpoint |
| **Cortex** | Graph indexes snapshot and restored (incremental rebuild if stale) |
| **Sync** | Lock state and changeset state saved/restored |
| **Trust** | Trust scores and reputation history persisted |
| **Terminal** | tmux sessions survive process death, reattached on resume |
| **Event Bus** | WAL ensures event durability, enables replay recovery |
| **Cluster** | Vault enables cross-node and cross-machine migration |
| **Dashboard** | Shows checkpoint history, recovery status, hibernation state |
| **Governance** | Policies persist across restarts unchanged |

---

## 22. Plugin Runtime Isolation (Galaxy Plugin SDK)

> [!NOTE]
> Plugins are how Galaxy becomes extensible without becoming unstable. Third-party and custom plugins MUST run in isolation — they cannot crash Galaxy, access unauthorized data, or interfere with other plugins. This section defines the full plugin architecture: SDK, sandboxing, permissions, versioning, and lifecycle.

### 22.1 Why This Matters

Plugins are powerful but dangerous:
- A buggy plugin can crash the entire Galaxy runtime
- A malicious plugin can exfiltrate code or secrets
- An outdated plugin can break after Galaxy updates
- Two plugins can conflict (same tool name, same event handler)
- A resource-hungry plugin can starve the main system

Galaxy Plugin SDK solves all of this with **sandboxed execution, granular permissions, and strict lifecycle management**.

### 22.2 Plugin Types

| Type | Purpose | Example |
|------|---------|---------|
| **Tool Plugin** | Adds new tools agents can use | Docker tool, AWS CLI tool, Figma integration |
| **Agent Plugin** | Adds specialized agent behaviors | Security auditor agent, Accessibility checker |
| **Provider Plugin** | Adds new LLM/embedding providers | Custom Ollama config, API gateway, fine-tuned model |
| **Analyzer Plugin** | Adds new code analysis capabilities | Custom linter, framework-specific checker |
| **UI Plugin** | Adds dashboard widgets/views | Custom metrics panel, team activity feed |

### 22.3 Plugin SDK & Manifest

Every plugin has a `galaxy-plugin.yaml` manifest:

```yaml
# galaxy-plugin.yaml
plugin:
  name: docker-tool
  version: "1.2.0"
  type: tool
  author: "galaxy-community"
  description: "Docker container management tool for Galaxy agents"
  license: MIT
  
  # Galaxy version compatibility
  compatibility:
    galaxy_min: "1.0.0"
    galaxy_max: "2.x"
    
  # What this plugin needs
  permissions:
    filesystem:
      read: ["{project_root}/Dockerfile", "{project_root}/docker-compose.yml"]
      write: []
    network:
      outbound: ["unix:///var/run/docker.sock"]
    tools:
      requires: [Terminal]
    resources:
      max_memory_mb: 512
      max_cpu_percent: 25
      
  # Entry point
  runtime:
    language: python
    entry: "plugin/main.py"
    isolation: subprocess  # subprocess | docker | wasm
    
  # Dependencies
  dependencies:
    python: ["docker>=7.0", "pyyaml>=6.0"]
    system: ["docker"]
    
  # Exported tools/capabilities
  exports:
    tools:
      - name: DockerBuild
        description: "Build a Docker image from Dockerfile"
        input_schema: { context: "string", tag: "string" }
      - name: DockerRun
        description: "Run a Docker container"
        input_schema: { image: "string", ports: "object", env: "object" }
      - name: DockerCompose
        description: "Run docker-compose commands"
        input_schema: { command: "string", file: "string" }
```

### 22.4 Sandbox Execution

Plugins NEVER run in the Galaxy main process. Three isolation levels:

#### Level 1: Subprocess Isolation (Default)

```
Galaxy Main Process
      │
      ├── Plugin subprocess (separate PID)
      │     ├── Own memory space
      │     ├── Stdin/stdout communication
      │     ├── Resource limits (ulimit)
      │     └── Killed on timeout/crash
      │
      └── Galaxy continues even if plugin dies
```

- **How:** `subprocess.Popen` with resource limits
- **Communication:** JSON-RPC over stdin/stdout
- **Crash isolation:** Plugin crash = subprocess dies, Galaxy unaffected
- **Resource limits:** `ulimit` for memory, CPU, file descriptors

#### Level 2: Docker Isolation (High Security)

```
Galaxy Main Process
      │
      └── Docker container
            ├── Own filesystem (no access to host)
            ├── Network restricted (only allowed endpoints)
            ├── Resource limits (cgroups)
            ├── Read-only root filesystem
            └── No privileged operations
```

- **How:** Plugin runs inside a Docker container
- **Communication:** HTTP API or Unix socket
- **Security:** Full filesystem isolation, network policies
- **Use case:** Untrusted/community plugins

#### Level 3: WASM Isolation (Future — Maximum Security)

```
Galaxy Main Process
      │
      └── WASM sandbox (Wasmtime/Wasmer)
            ├── No filesystem access (unless explicitly granted)
            ├── No network access (unless explicitly granted)
            ├── Memory sandboxed
            ├── CPU sandboxed
            └── Capability-based security
```

- **How:** Plugin compiled to WebAssembly, runs in WASM runtime
- **Security:** Strongest isolation — capability-based security model
- **Performance:** Near-native speed
- **Use case:** Future default for all plugins

### 22.5 Permission System

Every plugin declares what it needs. Galaxy enforces strictly:

```
Plugin requests: "I need to read Dockerfile"
      ↓
Galaxy checks manifest permissions:
  filesystem.read includes "Dockerfile"? → YES
      ↓
ALLOWED
```

```
Plugin requests: "I need to read .env"
      ↓
Galaxy checks manifest permissions:
  filesystem.read includes ".env"? → NO
      ↓
BLOCKED + logged
```

**Permission categories:**

| Category | Granularity | Examples |
|----------|-------------|---------|
| **Filesystem** | Per-path read/write | Read `src/**`, write `build/**` |
| **Network** | Per-host/port outbound | `docker.sock`, `api.github.com:443` |
| **Tools** | Which Galaxy tools plugin can invoke | Terminal, FileRead |
| **Agent Tiers** | Which agent tiers can use this plugin | Workers only, all tiers |
| **Resources** | CPU, memory, disk limits | Max 512MB RAM, 25% CPU |
| **Secrets** | Which env vars plugin can access | `DOCKER_HOST`, NOT `API_KEY` |
| **Events** | Which event bus topics plugin can subscribe to | `file_changed`, NOT `agent_output` |

**Permission escalation:**
- Plugin can REQUEST additional permissions at runtime
- Galaxy prompts user: "Plugin 'docker-tool' requests network access to registry.hub.docker.com. Allow?"
- User can allow once, always, or deny
- Decisions cached in plugin permission store

### 22.6 Plugin Versioning

**Semver enforced:**
```
plugin: 1.2.0
galaxy: 1.5.0

Compatible? Check compatibility matrix:
  plugin.compatibility.galaxy_min = 1.0.0 → 1.5.0 >= 1.0.0 ✓
  plugin.compatibility.galaxy_max = 2.x   → 1.5.0 < 2.0.0  ✓
  → COMPATIBLE
```

**Breaking change detection:**
```
Plugin update: 1.2.0 → 2.0.0 (major version bump)
      ↓
Galaxy warns: "Major version update. May have breaking changes."
      ↓
Check changelog for breaking changes
      ↓
User must explicitly approve major updates
```

**Version pinning:**
```yaml
# galaxy.config.yaml
plugins:
  docker-tool:
    version: "~1.2.0"    # patch updates only
  security-scanner:
    version: "^2.0.0"    # minor + patch updates
  custom-linter:
    version: "3.1.2"     # exact version pinned
```

### 22.7 Plugin Lifecycle

```
DISCOVERY → INSTALL → VALIDATE → LOAD → READY → EXECUTE → UPDATE → UNINSTALL
                                                    ↓
                                              DISABLED / CRASHED
```

| Phase | What Happens |
|-------|-------------|
| **Discovery** | Search plugin registry, local directories, git repos |
| **Install** | Download, verify checksum, install dependencies |
| **Validate** | Check manifest, verify permissions, compatibility check |
| **Load** | Start sandbox, initialize plugin, health check |
| **Ready** | Register exported tools/capabilities with Galaxy |
| **Execute** | Agent invokes plugin tool → routed to sandbox |
| **Update** | Check for updates, validate compatibility, hot-reload if possible |
| **Uninstall** | Stop sandbox, remove files, deregister tools |
| **Disabled** | Plugin exists but is deactivated (user choice or failure) |
| **Crashed** | Plugin crashed — sandbox killed, auto-disabled after 3 crashes |

### 22.8 Plugin Registry

**Local plugins:**
```
.galaxy/plugins/
  ├── docker-tool/
  │   ├── galaxy-plugin.yaml
  │   ├── plugin/
  │   │   └── main.py
  │   └── README.md
  └── security-scanner/
      ├── galaxy-plugin.yaml
      └── plugin/
          └── main.py
```

**Community registry (future):**
```
galaxy plugin search "docker"
  → docker-tool (v1.2.0) — Docker container management ⭐ 4.8
  → docker-compose (v2.0.1) — Docker Compose integration ⭐ 4.5
  → dockerfile-lint (v1.0.3) — Dockerfile best practices ⭐ 4.2

galaxy plugin install docker-tool
  → Installing docker-tool@1.2.0...
  → Permissions requested: filesystem(read), network(docker.sock)
  → Approve? [y/N]
```

### 22.9 Inter-Plugin Communication

Plugins communicate through the event bus, NOT directly:

```
Plugin A publishes event:
  { type: "docker_image_built", payload: { tag: "myapp:latest" } }
      ↓
Event Bus routes to subscribers
      ↓
Plugin B (deployment plugin) receives event:
  → Triggers deployment workflow
```

**Plugins CANNOT:**
- Call other plugins directly
- Access other plugins' memory/state
- Read other plugins' configuration
- Interfere with other plugins' sandbox

### 22.10 Plugin Health Monitoring

```
Plugin health check loop (every 30 seconds):
      ↓
Ping plugin sandbox → response within 5 seconds?
  YES → healthy
  NO  → mark unhealthy
      ↓
3 consecutive unhealthy → auto-disable plugin
      ↓
Notify user: "Plugin 'docker-tool' disabled (unresponsive)"
      ↓
All agents using that plugin's tools → graceful degradation
  "DockerBuild tool unavailable. Skipping Docker steps."
```

**Crash isolation:**
- Plugin crash → ONLY that plugin dies
- Galaxy main process → unaffected
- Other plugins → unaffected
- Agent using that tool → receives error, continues with other tasks

### 22.11 Configuration

```yaml
plugins:
  enabled: true
  
  directories:
    local: ".galaxy/plugins"
    global: "~/.galaxy/global-plugins"
    
  security:
    default_isolation: subprocess  # subprocess | docker | wasm
    allow_community_plugins: true
    require_permission_approval: true
    max_plugins: 20
    
  resource_limits:
    per_plugin:
      max_memory_mb: 512
      max_cpu_percent: 25
      max_disk_mb: 100
      execution_timeout_seconds: 300
      
  health:
    check_interval_seconds: 30
    unhealthy_threshold: 3
    auto_disable_on_crash: true
    max_crash_count: 3
    
  updates:
    auto_check: true
    auto_install_patches: true
    require_approval_for_major: true
```

### 22.12 Integration with Subsystems

| Subsystem | How Plugins Integrate |
|-----------|---------------------|
| **Tool Registry** | Plugin tools registered alongside built-in tools |
| **Governance** | Plugin permissions enforced by policy engine |
| **Sandbox** | Plugin isolation layers parallel Galaxy's own sandbox |
| **Event Bus** | Plugins communicate via event bus subscriptions |
| **Dashboard** | Plugin management UI: install, configure, monitor |
| **Vault** | Plugin state saved/restored with checkpoints |
| **Sentinel** | Analyzer plugins feed into consistency scoring |
| **Cluster** | Plugins distributed to nodes that need them |

---

## 23. Knowledge Compression (Galaxy Distiller)

> [!NOTE]
> As Galaxy works on projects over days, weeks, and months, memory grows unbounded. Without compression, retrieval slows, context windows fill with noise, and agents receive irrelevant information. Galaxy Distiller keeps knowledge dense, relevant, and fast.

### 23.1 The Problem

Memory growth without compression:

```
Day 1:   50 memory files,   2MB  → retrieval: 50ms  → context: clean
Day 7:   300 memory files,  15MB → retrieval: 200ms → context: noisy
Day 30:  2000 memory files, 80MB → retrieval: 2s    → context: polluted
Day 90:  8000 memory files, 300MB→ retrieval: 8s    → context: unusable
```

**Problems:**
- **Retrieval latency** — vector search over 8000 documents is slow
- **Context pollution** — agent receives 20 related but outdated memories
- **Contradictions** — old decisions conflict with new decisions
- **Token waste** — filling context with verbose debugging logs from weeks ago
- **Storage cost** — embedding 300MB of memory uses significant GPU time

### 23.2 Five Compression Strategies

```
              GALAXY DISTILLER
                    │
       ┌────────────┼────────────┐
       │            │            │
       ▼            ▼            ▼
  Summarization  Compaction   Hierarchical
  Pipeline       Engine       Embeddings
       │            │            │
       ▼            ▼            ▼
  Semantic       Archive
  Pruning        Tiering
```

---

#### Strategy 1: Summarization Pipeline

**Convert verbose memories into dense summaries.**

```
BEFORE (raw memory — 450 tokens):
  "Spent 2 hours debugging CORS issue. First tried adding
   Access-Control-Allow-Origin: * but that didn't work because
   the browser was sending preflight OPTIONS requests. Then tried
   configuring cors middleware in Express. The issue was that the
   middleware was added AFTER the routes, not before. Moving
   app.use(cors()) above the route definitions fixed it. Also
   needed to add credentials: true for the auth cookie to work."

AFTER (compressed — 85 tokens):
  "CORS fix: Express cors() middleware must be placed BEFORE route
   definitions. Required credentials: true for auth cookies.
   Preflight OPTIONS handling requires explicit middleware ordering."
```

**Summarization triggers:**

| Trigger | When | Action |
|---------|------|--------|
| Memory age > 7 days | Periodic | Summarize verbose memories |
| Memory accessed < 2 times | Low value | Summarize or archive |
| Task completed | Milestone | Summarize task debug logs into lesson |
| Domain completed | Major milestone | Summarize domain learnings into patterns |
| Project phase change | Phase transition | Summarize entire phase into knowledge |

**Summarization preserves:**
- Key decisions and their reasoning
- Patterns and anti-patterns
- Configuration values and settings
- Error causes and fixes
- Architecture constraints

**Summarization discards:**
- Step-by-step debugging narratives
- Redundant descriptions
- Temporary state information
- Superseded decisions
- Verbose error stack traces

---

#### Strategy 2: Memory Compaction

**Merge multiple related memories into one consolidated memory.**

```
BEFORE (5 separate memories):
  memory_001: "User model has fields: id, name, email"
  memory_002: "Added phone field to User model"
  memory_003: "Added avatarUrl field to User model"
  memory_004: "Renamed 'name' to 'fullName' in User model"
  memory_005: "Added role field (enum: admin, user, guest) to User"

AFTER (1 compacted memory):
  memory_001_compacted: "User model fields:
    id, fullName, email, phone, avatarUrl, role (enum: admin|user|guest)"
```

**Compaction rules:**
- Same entity modified multiple times → merge into latest state
- Superseded decisions → keep only final decision + brief history
- Incremental additions → consolidate into complete description
- Conflicting memories → keep latest, note the change

---

#### Strategy 3: Hierarchical Embeddings

**Build multi-resolution vector indexes for faster, more relevant retrieval.**

```
Level 0 (Most detailed):
  8000 individual memory embeddings
  Searched for: precise, specific queries

Level 1 (File-level summaries):
  500 file/component summary embeddings
  Searched for: "how does the auth system work?"

Level 2 (Domain-level summaries):
  10-20 domain summary embeddings
  Searched for: "what architecture decisions did we make?"

Level 3 (Project-level summary):
  1 project summary embedding
  Searched for: "what is this project about?"
```

**Search strategy:**
```
Agent query: "How does JWT validation work?"
      ↓
Search Level 2 first (domain summaries) → identify: "auth domain"
      ↓
Search Level 1 within auth domain → identify: "JWT middleware file"
      ↓
Search Level 0 within JWT → precise memories about token validation
      ↓
Return only relevant Level 0 memories (not all 8000)
```

**Benefit:** Instead of searching 8000 vectors, search ~30 → 10x faster, much more relevant.

---

#### Strategy 4: Semantic Pruning

**Remove memories that no longer provide value.**

| Prune Target | Detection | Action |
|-------------|-----------|--------|
| **Duplicate memories** | Embedding similarity > 95% | Keep best, delete duplicates |
| **Superseded memories** | Newer memory contradicts older | Archive old with "superseded" tag |
| **Stale memories** | About deleted/replaced code | Archive with "stale" tag |
| **Trivial memories** | Low information density (< 20 tokens of substance) | Delete |
| **Orphan memories** | Reference files/symbols that no longer exist | Archive or delete |

**Pruning safety:**
- NEVER delete memories about architecture decisions
- NEVER delete memories about failure causes
- NEVER delete memories tagged as "critical" or "permanent"
- Always archive before deleting (soft delete first)

---

#### Strategy 5: Archive Tiering

**Move cold memories to cheaper, slower storage.**

```
HOT tier (in-memory + vector DB):
  - Recent memories (< 7 days)
  - Frequently accessed (> 3 accesses)
  - Critical/permanent memories
  Search speed: < 50ms

WARM tier (vector DB only):
  - Older memories (7-30 days)
  - Occasionally accessed
  - Summarized versions
  Search speed: < 200ms

COLD tier (compressed filesystem):
  - Old memories (> 30 days)
  - Rarely accessed
  - Full archives, superseded memories
  Search speed: 1-5s (on-demand load)

FROZEN tier (object storage):
  - Historical memories (> 90 days)
  - Never auto-searched
  - Available for explicit retrieval only
  Search speed: manual load required
```

### 23.3 Compression Lifecycle

```
Distiller runs (periodic or triggered)
      ↓
SCAN: Analyze all memories
  - Count, size, age, access frequency
  - Identify candidates for each strategy
      ↓
PLAN: Build compression plan
  - Which memories to summarize
  - Which to compact
  - Which to prune
  - Which to tier-shift
      ↓
EXECUTE: Apply compressions
  - Summarize verbose memories
  - Compact related memories
  - Rebuild hierarchical embeddings
  - Prune dead/duplicate memories
  - Move cold memories to lower tiers
      ↓
VERIFY: Ensure no knowledge loss
  - Key facts still retrievable
  - Architecture knowledge preserved
  - Retrieval quality test (sample queries)
      ↓
REPORT:
  "Compression complete:
   - 300 memories → 180 (40% reduction)
   - Storage: 15MB → 8MB
   - Avg retrieval: 200ms → 80ms
   - 0 critical memories affected"
```

### 23.4 Memory Budget

Each memory level has a **budget** — max memories before compression is forced:

```yaml
memory_budget:
  global:
    max_memories: 200
    max_size_mb: 20
  workspace:
    max_memories: 500
    max_size_mb: 50
  domain:
    max_memories: 100
    max_size_mb: 10
  task:
    max_memories: 50
    max_size_mb: 5
  agent:
    max_memories: 30
    max_size_mb: 3
```

When budget exceeded → trigger compression cycle for that level.

### 23.5 Compression Quality

How to verify compression didn't lose knowledge:

```
Before compression:
  Query: "How do we handle auth?"
  Results: [memory_23, memory_45, memory_67, memory_89]
  Relevance: [0.95, 0.88, 0.82, 0.71]

After compression:
  Query: "How do we handle auth?"
  Results: [memory_23_compacted, memory_45_summarized]
  Relevance: [0.96, 0.90]

Quality check:
  - Key facts preserved? ✓
  - Retrieval relevance maintained/improved? ✓
  - No contradictions introduced? ✓
  → COMPRESSION APPROVED
```

### 23.6 Configuration

```yaml
distiller:
  enabled: true
  
  schedule:
    periodic_hours: 24
    on_memory_budget_exceeded: true
    on_phase_complete: true
    
  summarization:
    min_age_days: 7
    min_token_count: 200  # only summarize verbose memories
    preserve_tags: [critical, permanent, architecture]
    
  compaction:
    similarity_threshold: 0.80  # merge if > 80% similar
    max_merge_group: 10
    
  pruning:
    duplicate_threshold: 0.95
    min_access_count: 0  # prune if never accessed after 30 days
    stale_after_days: 30
    
  tiering:
    hot_max_age_days: 7
    warm_max_age_days: 30
    cold_max_age_days: 90
    frozen_after_days: 90
    
  hierarchical_embeddings:
    levels: 4
    rebuild_on_compression: true

  safety:
    soft_delete_first: true
    archive_before_prune: true
    never_delete_tags: [critical, permanent, architecture, failure]
```

### 23.7 Integration with Subsystems

| Subsystem | How Distiller Integrates |
|-----------|------------------------|
| **Memory System** | Distiller IS the memory maintenance engine |
| **Cortex** | Stale memory detection uses Cortex symbol/file existence |
| **Vault** | Compression state saved in checkpoints |
| **Scheduler** | Distiller runs as low-priority background task |
| **Event Bus** | Memory created/accessed events trigger budget checks |
| **Dashboard** | Memory health visualization, compression reports |
| **Trust** | Low-trust memories deprioritized during compression |

---

## 24. Cost Accounting System (Galaxy Ledger)

> [!NOTE]
> Galaxy Ledger tracks every resource Galaxy consumes — inference tokens, GPU hours, compute time, storage, and operational costs. Essential for understanding efficiency, budgeting projects, and optimizing resource usage.

### 24.1 Why This Matters

Without cost tracking:
- No idea how much a project costs to build
- No way to compare model efficiency (7B vs 14B — which was cheaper per correct output?)
- No visibility into wasted resources (retries, failed experiments, idle agents)
- Cannot set budgets or alerts
- Cannot optimize (which tasks waste the most resources?)

### 24.2 Five Cost Categories

```
              GALAXY LEDGER
                    │
       ┌────────────┼────────────┐
       │            │            │
       ▼            ▼            ▼
   Inference     Compute      Storage
   Costs         Costs        Costs
       │            │
       ▼            ▼
   Time          Operational
   Costs         Costs
```

---

#### Category 1: Inference Costs

**The primary cost — LLM token usage:**

```json
{
  "inference_event": {
    "model": "qwen2.5-coder-14b",
    "agent": "backend_worker_12",
    "task": "Generate JWT middleware",
    "tokens_in": 3200,
    "tokens_out": 850,
    "total_tokens": 4050,
    "latency_ms": 2400,
    "cost_estimate_usd": 0.00,
    "provider": "local_ollama",
    "timestamp": "2026-05-10T12:00:00Z"
  }
}
```

**Tracking granularity:**

| Level | What's Tracked |
|-------|---------------|
| Per-request | Individual LLM call tokens/latency |
| Per-task | Total inference for one task |
| Per-agent | Lifetime inference usage |
| Per-domain | Domain-level aggregation |
| Per-session | Full session totals |
| Per-project | Lifetime project cost |

**Model cost comparison:**
```
MODEL EFFICIENCY REPORT:
  qwen2.5-coder-7b:
    Total tokens: 450,000
    Successful tasks: 38
    Failed tasks: 5
    Cost per successful task: 10,465 tokens
    First-attempt success: 72%

  qwen2.5-coder-14b:
    Total tokens: 280,000
    Successful tasks: 42
    Failed tasks: 1
    Cost per successful task: 6,512 tokens
    First-attempt success: 93%

  → 14B model costs 38% fewer tokens per success despite being larger.
  → Recommendation: Use 14B for complex tasks, 7B for simple CRUD.
```

---

#### Category 2: Compute Costs

| Resource | Metric | Unit |
|----------|--------|------|
| GPU time | Active inference duration | GPU-seconds |
| GPU VRAM | Memory occupied by loaded models | GB-hours |
| CPU time | Build, test, lint, terminal commands | CPU-seconds |
| RAM | Peak and average memory usage | GB-hours |
| Disk I/O | Read/write operations | MB transferred |

**GPU utilization tracking:**
```
GPU UTILIZATION (last hour):
  RTX 4090 — 24GB VRAM
  ├── qwen2.5-coder-14b:  9.2GB (38%)  — active 45 min
  ├── nomic-embed-text:    0.5GB (2%)   — active 12 min
  └── idle:                14.3GB (60%) — 3 min idle
  
  GPU compute utilization: 72%
  VRAM utilization: 40%
  
  Recommendation: Load a second model into free VRAM for parallelism.
```

---

#### Category 3: Storage Costs

| Storage | Size | Growth Rate |
|---------|------|-------------|
| Memory files | 8MB | +200KB/day |
| Cortex indexes | 45MB | +1MB per 100 files |
| Event log | 120MB | +5MB/day |
| Checkpoints | 280MB | +14MB per full snapshot |
| Build artifacts | 500MB | varies |

---

#### Category 4: Time Costs

| Metric | What It Measures |
|--------|-----------------|
| Wall clock time | Total elapsed time from start to finish |
| Agent active time | Time agents spent actually generating/reasoning |
| Agent idle time | Time agents were loaded but waiting for tasks |
| Queue wait time | Time tasks spent waiting for an agent |
| Build/test time | Time spent on compilation and testing |
| Validation time | Time spent on Sentinel, Cortex, policy checks |

**Time cost attribution per task:**
```json
{
  "task": "Generate JWT middleware",
  "time_breakdown": {
    "queue_wait_seconds": 5,
    "agent_reasoning_seconds": 12,
    "code_generation_seconds": 8,
    "build_seconds": 3,
    "test_seconds": 6,
    "validation_seconds": 2,
    "total_seconds": 36
  }
}
```

---

#### Category 5: Operational Costs

| Cost | Tracking |
|------|---------|
| Cloud API calls | Per-call cost (if using cloud LLMs) |
| Network bandwidth | Data transfer for cluster communication |
| External services | Docker Hub pulls, npm installs, git operations |
| Electricity (estimated) | GPU power draw × time |

### 24.3 Cost Dashboard

```
┌──────────────────────────────────────────────┐
│           SESSION COST SUMMARY               │
├──────────────────────────────────────────────┤
│                                              │
│  Duration:        2h 14m                     │
│  Tasks completed: 28                         │
│                                              │
│  INFERENCE                                   │
│    Total tokens:     1,240,000               │
│    Input tokens:       890,000               │
│    Output tokens:      350,000               │
│    Cloud API cost:     $0.00 (local models)  │
│                                              │
│  COMPUTE                                     │
│    GPU time:           1h 48m                │
│    GPU VRAM avg:       12.4 GB               │
│    CPU time:           3h 22m (multi-core)   │
│                                              │
│  EFFICIENCY                                  │
│    Tokens per task:    44,286 avg             │
│    First-attempt rate: 82%                   │
│    Retry overhead:     14% of total tokens   │
│    Idle time:          12% of session        │
│                                              │
│  [Detailed Breakdown] [Export CSV] [Compare] │
└──────────────────────────────────────────────┘
```

### 24.4 Budget Enforcement

```yaml
budget:
  session:
    max_tokens: 5000000       # 5M tokens per session
    max_duration_hours: 8
    max_gpu_hours: 4
    
  project:
    max_tokens: 50000000      # 50M tokens per project
    max_cloud_cost_usd: 100
    
  alerts:
    warn_at_percent: 75       # warn when 75% of budget used
    pause_at_percent: 95      # pause when 95% used
    
  actions:
    on_budget_warn: notify_user
    on_budget_exceeded: pause_and_ask
```

**Budget alert flow:**
```
Token usage reaches 75% of budget
      ↓
Dashboard alert: "Warning: 75% of token budget consumed"
      ↓
Token usage reaches 95%
      ↓
Galaxy pauses: "Budget nearly exhausted. Continue? [y/N]"
      ↓
User approves → continue with extended budget
User denies → save checkpoint, stop gracefully
```

### 24.5 Cost Optimization Recommendations

Ledger analyzes patterns and suggests savings:

```
COST OPTIMIZATION SUGGESTIONS:
  
  1. Model downgrade opportunity:
     12 simple CRUD tasks used 14B model (avg 8,500 tokens)
     Estimated with 7B: 6,200 tokens (27% savings)
     → Route simple tasks to 7B model
  
  2. Retry reduction:
     5 tasks required 3+ retries (68,000 wasted tokens)
     Root cause: insufficient context provided
     → Improve context assembly for auth-related tasks
  
  3. Idle agent detected:
     Worker_08 idle for 35 minutes while loaded in VRAM
     → Unload after 10 min idle, reload on demand
     → Savings: 0.8 GPU-hours
  
  4. Duplicate inference:
     3 workers independently generated similar utility functions
     → Use shared context to avoid duplicate work
     → Estimated savings: 25,000 tokens
```

### 24.6 Configuration

```yaml
ledger:
  enabled: true
  
  tracking:
    inference: true
    compute: true
    storage: true
    time: true
    operational: true
    
  granularity:
    per_request: true
    per_task: true
    per_agent: true
    per_domain: true
    per_session: true
    per_project: true
    
  export:
    format: [json, csv]
    auto_export_on_session_end: true
    
  cloud_pricing:
    # Only needed for cloud model providers
    openai_gpt4: { input_per_1m: 10.00, output_per_1m: 30.00 }
    anthropic_claude: { input_per_1m: 8.00, output_per_1m: 24.00 }
    local_ollama: { input_per_1m: 0.00, output_per_1m: 0.00 }
```

### 24.7 Integration with Subsystems

| Subsystem | How Ledger Integrates |
|-----------|---------------------|
| **Scheduler** | Cost data informs model selection (cheapest capable model) |
| **Refiner** | Resource optimization domain uses Ledger data |
| **Trust** | Cost-per-successful-output feeds efficiency scoring |
| **Vault** | Cost summaries saved in checkpoints |
| **Dashboard** | Real-time cost dashboard, budget alerts |
| **Governance** | Budget limits enforced as operational policies |
| **Forge Labs** | Per-branch cost tracking for experiments |
| **Cluster** | Per-node cost attribution |

---

## 25. Workflow Templates (Galaxy Blueprints)

> [!NOTE]
> Blueprints are **pre-built project templates** that encode proven architecture patterns, domain decomposition, tech stack decisions, and quality rules. Instead of the Master Agent figuring everything out from scratch every time, Blueprints give it a massive head start.

### 25.1 Why This Matters

Without templates, every project starts from zero:
- Master must invent architecture from scratch
- Common patterns (auth, CRUD, API) regenerated every time
- Quality varies between projects — no consistent baseline
- New project setup takes 30+ minutes of planning

With Blueprints:
- Master starts with proven architecture
- Common patterns pre-defined, just customized
- Consistent quality across projects
- New project setup in minutes, not hours

### 25.2 Built-in Templates

| Template | Type | Stack |
|----------|------|-------|
| **Full-Stack Web App** | Web application | Next.js/React + Node/FastAPI + PostgreSQL |
| **REST API Microservice** | Backend API | FastAPI/Express + PostgreSQL + Redis |
| **ML/AI Pipeline** | Machine learning | Python + PyTorch/TensorFlow + MLflow |
| **Real-Time App** | WebSocket application | Node.js + Socket.io + Redis PubSub |
| **CLI Tool** | Command-line tool | Python (Click/Typer) or Node.js (Commander) |
| **Mobile Backend** | Mobile API backend | FastAPI + PostgreSQL + Firebase/Push |

### 25.3 Template Anatomy

Every Blueprint defines the complete project skeleton:

```yaml
# blueprints/fullstack-web-app.yaml

blueprint:
  name: Full-Stack Web Application
  version: "1.0.0"
  description: "Modern full-stack web app with auth, CRUD, and real-time features"
  
  # ─── Technology Stack ───
  stack:
    frontend:
      framework: next.js
      language: typescript
      styling: tailwindcss
      state: zustand
      
    backend:
      framework: fastapi
      language: python
      orm: prisma
      
    database:
      primary: postgresql
      cache: redis
      search: meilisearch  # optional
      
    infrastructure:
      containerization: docker
      ci: github-actions
      
  # ─── Architecture Pattern ───
  architecture:
    pattern: layered
    layers:
      - name: presentation
        path: "frontend/src"
        responsibility: "UI components, pages, routing"
      - name: api
        path: "backend/src/routes"
        responsibility: "HTTP endpoints, request validation"
      - name: service
        path: "backend/src/services"
        responsibility: "Business logic, orchestration"
      - name: repository
        path: "backend/src/repositories"
        responsibility: "Data access, queries"
      - name: domain
        path: "backend/src/models"
        responsibility: "Entities, value objects, types"
        
  # ─── Domain Decomposition ───
  domains:
    - name: auth
      description: "Authentication and authorization"
      includes:
        - JWT token management
        - Login/register/logout
        - Password hashing
        - Role-based access control
      files:
        - "backend/src/routes/auth.py"
        - "backend/src/services/auth_service.py"
        - "backend/src/models/user.py"
        - "frontend/src/components/auth/*"
        
    - name: core
      description: "Core business entities and CRUD"
      includes:
        - Entity CRUD operations
        - Pagination, filtering, sorting
        - Validation
      files:
        - "backend/src/routes/{entity}.py"
        - "backend/src/services/{entity}_service.py"
        
    - name: shared
      description: "Shared utilities and configuration"
      includes:
        - Error handling
        - Logging
        - Configuration
        - Common types
        
  # ─── Sentinel Rules ───
  sentinel:
    style_profile:
      backend:
        language: python
        naming: snake_case
        quotes: double
      frontend:
        language: typescript
        naming: camelCase
        quotes: single
        
    architecture_rules:
      - from: presentation
        cannot_import: [repository, domain]
      - from: api
        can_import: [service]
      - from: service
        can_import: [repository, domain]
      - from: repository
        can_import: [domain]
        
    api_contract:
      format: rest
      error_format: "{ error: { code, message, details } }"
      pagination: "{ data: [], meta: { page, limit, total } }"
      auth: "Bearer token in Authorization header"
      
  # ─── Directory Structure ───
  structure:
    - path: "frontend/"
      files:
        - "package.json"
        - "tsconfig.json"
        - "next.config.js"
        - "src/app/layout.tsx"
        - "src/app/page.tsx"
        - "src/components/"
        - "src/lib/"
        - "src/hooks/"
        - "src/types/"
    - path: "backend/"
      files:
        - "pyproject.toml"
        - "src/main.py"
        - "src/config.py"
        - "src/routes/"
        - "src/services/"
        - "src/repositories/"
        - "src/models/"
        - "src/middleware/"
        - "tests/"
    - path: "/"
      files:
        - "docker-compose.yml"
        - "Makefile"
        - "README.md"
        - ".env.example"
        
  # ─── Validation Criteria ───
  validation:
    required_before_complete:
      - build_passes: [frontend, backend]
      - type_check: [frontend, backend]
      - lint_clean: [frontend, backend]
      - test_coverage_min: 80
      - api_contract_consistent: true
      - sentinel_score_min: 75
```

### 25.4 How Templates Are Used

```
User: "galaxy init --blueprint fullstack-web-app"
      ↓
1. Load blueprint definition
      ↓
2. Generate directory structure
      ↓
3. Create configuration files (package.json, pyproject.toml, etc.)
      ↓
4. Configure Sentinel with blueprint's style/architecture rules
      ↓
5. Configure Cortex with blueprint's layer definitions
      ↓
6. Set up domain decomposition for task planning
      ↓
7. Master uses blueprint as architecture foundation:
   "I'm building a Full-Stack Web App.
    Architecture: layered (presentation → api → service → repository → domain)
    Domains: auth, core, shared.
    Stack: Next.js + FastAPI + PostgreSQL.
    Now: decompose the user's request into tasks within this structure."
```

### 25.5 Template Customization

Users can customize any blueprint:

```
User: "galaxy init --blueprint fullstack-web-app 
       --frontend vue --backend express --database mongodb"
      ↓
Blueprint loaded, then customized:
  frontend.framework: next.js → vue
  backend.framework: fastapi → express
  backend.language: python → typescript
  database.primary: postgresql → mongodb
      ↓
Architecture rules, file paths, and patterns adjusted accordingly
```

**Template inheritance:**
```yaml
# blueprints/saas-app.yaml
blueprint:
  name: SaaS Application
  extends: fullstack-web-app    # inherit everything from fullstack
  
  # Add SaaS-specific domains
  domains:
    - name: billing
      description: "Subscription and payment management"
      includes: [Stripe integration, subscription tiers, invoicing]
    - name: tenancy
      description: "Multi-tenant data isolation"
      includes: [tenant context, data scoping, tenant settings]
    - name: onboarding
      description: "User onboarding flow"
      includes: [signup wizard, team invites, initial setup]
```

### 25.6 Community Templates

```
galaxy blueprint search "e-commerce"
  → ecommerce-app (v2.1.0) — Full e-commerce with cart, payments, inventory ⭐ 4.7
  → shopify-clone (v1.0.0) — Shopify-style multi-vendor marketplace ⭐ 4.2
  → headless-store (v1.3.0) — Headless commerce API + any frontend ⭐ 4.5

galaxy blueprint install ecommerce-app
  → Installing ecommerce-app@2.1.0...
  → Domains: auth, products, cart, checkout, payments, orders, inventory
  → Stack: Next.js + FastAPI + PostgreSQL + Stripe
  → Ready.
```

### 25.7 Auto-Detection for Existing Projects

When Galaxy opens an existing project (no blueprint):

```
galaxy init (in existing project directory)
      ↓
Cortex scans existing code:
  - Detected: package.json (Next.js)
  - Detected: requirements.txt (FastAPI)
  - Detected: docker-compose.yml (PostgreSQL, Redis)
      ↓
Auto-match: "This looks like a Full-Stack Web App"
      ↓
Generate inferred blueprint:
  - Architecture: layered (based on directory structure)
  - Domains: auth, users, posts (based on route files)
  - Style: camelCase TypeScript, snake_case Python
      ↓
User confirms or adjusts
```

### 25.8 Template + Master Agent

When the Master Agent plans a project, it references the blueprint:

```
Master's planning context includes:
  "Blueprint: Full-Stack Web App
   Architecture: layered (5 layers defined)
   Domains: auth (4 subtasks), core (3 subtasks per entity), shared (2 subtasks)
   Constraints: No presentation → repository imports.
   API pattern: REST, standard error format, Bearer auth.
   Validation: 80% coverage, lint clean, type check clean."

This means:
  - Master doesn't reinvent architecture → it adapts the blueprint
  - Domain agents know their boundaries → from blueprint domain definitions
  - Workers know the patterns → from blueprint style/architecture rules
  - Sentinel knows what to enforce → from blueprint sentinel config
```

### 25.9 Configuration

```yaml
blueprints:
  directory: ".galaxy/blueprints"
  community_registry: "https://blueprints.galaxy.dev"  # future
  
  defaults:
    auto_detect_existing: true
    suggest_on_init: true
    
  custom:
    # User's own templates
    templates_dir: "~/.galaxy/blueprints"
```

### 25.10 Integration with Subsystems

| Subsystem | How Blueprints Integrate |
|-----------|------------------------|
| **Orchestrator** | Master uses blueprint for initial architecture plan |
| **Sentinel** | Blueprint provides initial style/architecture rules |
| **Cortex** | Blueprint defines expected layers and boundaries |
| **Task Graph** | Blueprint's domain decomposition seeds the initial task DAG |
| **Memory** | Blueprint's architecture stored as foundational memory |
| **Dashboard** | Template selection UI during project initialization |
| **Governance** | Blueprint can include default policies |
| **Forge Labs** | Blueprint defines which decisions are experiment-worthy |
