# Galaxy AI — Complete Implementation Plan & TODO

**Repository:** https://github.com/VishalGovindasamy-15/galaxy-ai
**Total:** 27 subsystems · ~200 files · 6 phases · 15 test scenarios

---

## Execution Strategy

### How We Build
```
1. Every file gets a paired test BEFORE moving to the next file
2. Every module passes integration test BEFORE next module
3. Every phase passes E2E test BEFORE next phase
4. Fail early → fix immediately → never accumulate debt
```

### Gate Rules
```
FILE GATE:    Write file → Write test → Test passes     → ✅ Next file
MODULE GATE:  All files tested → Integration test passes → ✅ Next module
PHASE GATE:   All modules tested → E2E test passes       → ✅ Next phase
```

### Tech Stack
```
Language:     Python 3.11+
CLI:          Typer + Rich
Web:          FastAPI + Vite (React)
Database:     SQLite (default) / PostgreSQL (optional)
Event Bus:    In-memory async (default) / Redis (optional)
Models:       Ollama (local) + OpenAI/Anthropic/etc (cloud optional)
Testing:      pytest + mypy + ruff
Terminal:     tmux
```

---

## PROJECT TODO — PHASE 1: Foundation (Weeks 1-10)

> **Goal:** End-to-end Galaxy running: boot → plan → execute → validate → output

### Week 1-2: Core Foundation ✅ COMPLETE (215 tests passing)

- [x] **pyproject.toml** — Package config, dependencies, entry points ✅
- [x] **README.md** — Project overview ✅
- [x] **Makefile** — Dev commands (test, lint, build) ✅
- [x] **.env.example** — Environment template ✅
- [x] **src/galaxy/__init__.py** — Version, exports ✅
- [x] **src/galaxy/__main__.py** — `python -m galaxy` ✅

---

- [x] **core/constants.py** — System constants, defaults ✅
  - [x] test_constants.py ✅ (27 tests)
- [x] **core/exceptions.py** — All custom exceptions ✅
  - [x] test_exceptions.py ✅ (42 tests)
- [x] **core/types.py** — Shared type definitions (AgentTier, TaskStatus, etc.) ✅
  - [x] test_types.py ✅ (71 tests)
- [x] **core/config.py** — Configuration loader (YAML + env vars) ✅
  - [x] test_config.py ✅ (18 tests)
- [x] **core/version.py** — Version info ✅
- [x] **events/events.py** — Event data models ✅
  - [x] test_events.py ✅ (13 tests)
- [x] **events/bus.py** — In-memory async EventBus ✅
  - [x] test_bus.py ✅ (18 tests)
- [x] **core/kernel.py** — GalaxyKernel (skeleton) ✅
  - [x] test_kernel.py ✅ (12 tests)
- [x] ✅ **MODULE GATE:** test_core_integration.py ✅
  - [x] test_kernel_boots_with_default_config() ✅
  - [x] test_event_bus_works_after_boot() ✅
  - [x] test_kernel_boot_and_shutdown_lifecycle() ✅

### Week 3-4: Model + Agent Layer ✅ COMPLETE (288 total tests passing)

- [x] **models/vram.py** — VRAM detection + monitoring ✅
  - [x] test_vram.py ✅ (18 tests)
- [x] **models/providers/base.py** — BaseProvider interface ✅
- [x] **models/providers/ollama.py** — Ollama provider ✅
  - [x] test_ollama_provider.py ✅ (in test_router.py)
- [x] **models/providers/openai_compat.py** — OpenAI + Groq + DeepSeek + vLLM + LiteLLM + Custom ✅
  - [x] test_openai_provider.py ✅ (in test_router.py)
- [x] **models/router.py** — ModelRouter + ProviderRegistry ✅
  - [x] test_router.py ✅ (27 tests: routing, fallback, swap, factories)
- [x] **agents/base.py** — BaseAgent ✅
  - [x] test_base_agent.py ✅ (15 tests: creation, LLM, events, checkpoint)
- [x] **agents/worker.py** — WorkerAgent ✅
  - [x] test_worker.py ✅ (7 tests: execute, events, failure, code extraction)
- [x] **agents/domain.py** — DomainAgent ✅
- [x] **agents/master.py** — MasterAgent ✅
- [x] **agents/registry.py** — AgentRegistry ✅
  - [x] test_registry.py ✅ (10 tests: register, tiers, limits, cleanup, summary)
- [x] ✅ **MODULE GATE:** test_agent_model_integration.py ✅
  - [x] test_agent_calls_model_via_router() ✅
  - [x] test_worker_generates_code() ✅
  - [x] test_agent_lifecycle_spawn_to_terminate() ✅


### Week 5-6: Tools + Terminal ✅ COMPLETE (328 total tests passing)

- [x] **tools/base.py** — BaseTool interface ✅
  - [x] test_base_and_registry.py ✅ (10 tests: schema, validation, permissions)
- [x] **tools/registry.py** — ToolRegistry ✅
- [x] **tools/builtin/file_read.py** — FileRead tool ✅
  - [x] test_file_tools.py ✅ (12 tests: read, write, edit, sandboxing)
- [x] **tools/builtin/file_write.py** — FileWrite tool ✅
- [x] **tools/builtin/file_edit.py** — FileEdit tool ✅
- [x] **tools/builtin/terminal.py** — Terminal tool ✅
  - [x] test_terminal.py ✅ (7 tests: execution, timeout, blocking)
- [x] **tools/builtin/search.py** — Search tool ✅
- [x] **tools/builtin/git.py** — Git tool ✅
- [x] **tools/builtin/tree.py** — Directory tree tool ✅
  - [x] test_tree.py ✅ (3 tests: display, ignore, security)
- [x] **terminal/manager.py** — TerminalManager + TerminalSession (tmux) ✅
- [x] ✅ **MODULE GATE:** test_tools_integration.py ✅
  - [x] test_agent_uses_file_tools() ✅
  - [x] test_agent_runs_terminal_command() ✅
  - [x] test_permission_blocks_unauthorized_tool() ✅

### Week 7-8: Orchestrator + Vault + CLI + Terminal UX ✅ COMPLETE (372 total tests passing)

- [x] **orchestrator/task_graph.py** — DAG manager ✅
  - [x] test_task_graph.py ✅ (14 tests: add, ready, critical path, serialization, dynamic insert)
- [x] **orchestrator/scheduler.py** — VRAM-aware scheduler ✅
- [x] **orchestrator/orchestrator.py** — Orchestrator engine ✅
- [x] **orchestrator/escalation.py** — 5-level EscalationManager ✅
  - [x] test_escalation.py ✅ (9 tests: all 5 levels, max, history, retries)
- [x] **forge/validator.py** — ContinuousValidator ✅
  - [x] test_validator.py ✅ (6 tests: syntax, imports, lint, file validation)
- [x] **vault/checkpoint.py** — Checkpoint engine ✅
  - [x] test_vault.py ✅ (7 tests: create, load, crash marker, recovery)
- [x] **cli/app.py** — Main CLI app (typer) ✅
- [x] **cli/colors.py** — GalaxyColors design constants ✅
- [x] **cli/views/boot.py** — BootRenderer (ASCII logo + steps) ✅
- [x] **cli/setup_helper.py** — Auto-detect hardware ✅
- [x] ✅ **MODULE GATE:** test_orchestrator_integration.py ✅
  - [x] test_full_pipeline_plan_to_execute() ✅
  - [x] test_checkpoint_and_resume() ✅
  - [x] test_orchestrator_events() ✅

### Week 9-10: E2E Testing + Polish ✅ COMPLETE (380 total tests passing)

- [x] ✅ **PHASE GATE:** test_e2e_phase1.py ✅
  - [x] test_build_simple_python_script() ✅
  - [x] test_build_rest_api() ✅ (multi-file with dependency chain)
  - [x] test_crash_and_recover() ✅
  - [x] test_pause_swap_model_resume() ✅
  - [x] test_multi_worker_parallel() ✅ (5 tasks, 3 workers)
  - [x] test_tool_and_validator() ✅
  - [x] test_full_lifecycle() ✅ (boot → plan → execute → checkpoint → shutdown)
  - [x] test_event_propagation() ✅
- [x] README.md — Complete documentation ✅
- [x] pip package configured (pyproject.toml scripts entry) ✅

**Phase 1 COMPLETE: 40+ source files + 30+ test files, 380 tests passing in 11.5s**

---

## PROJECT TODO — PHASE 2: Memory & Intelligence (Weeks 11-18)

> **Goal:** Galaxy remembers context, understands code structure, recovers from crashes

### Week 11-12: Memory Foundation

- [ ] **memory/types.py** — Memory data models (MemoryEntry, MemoryLevel, etc.)
  - [ ] test_memory_types.py
- [ ] **memory/store.py** — File-based persistence
  - [ ] test_store.py
- [ ] **memory/embeddings.py** — Ollama embedding integration
  - [ ] test_embeddings.py
- [ ] **memory/vector_store.py** — Numpy cosine similarity search
  - [ ] test_vector_store.py
- [ ] **memory/manager.py** — MemoryManager API
  - [ ] test_manager.py → test_store_retrieve(), test_search_by_embedding(), test_scoped_memory()
- [ ] **memory/hierarchy.py** — 5-level memory scoping
  - [ ] test_hierarchy.py → test_level_isolation(), test_cross_level_search()

### Week 13-14: Cortex Foundation

- [ ] **cortex/parser.py** — tree-sitter multi-language parser
  - [ ] test_parser.py → test_parse_python(), test_parse_typescript(), test_parse_invalid()
- [ ] **cortex/graphs/ast_graph.py** — AST graph
  - [ ] test_ast_graph.py
- [ ] **cortex/graphs/symbol_graph.py** — Symbol graph
  - [ ] test_symbol_graph.py
- [ ] **cortex/graphs/import_graph.py** — Import/dependency graph
  - [ ] test_import_graph.py
- [ ] **cortex/graphs/call_graph.py** — Call graph
  - [ ] test_call_graph.py
- [ ] **cortex/graphs/api_graph.py** — API route graph
- [ ] **cortex/graphs/dataflow_graph.py** — Data flow graph
- [ ] **cortex/query.py** — Graph query API
  - [ ] test_query.py
- [ ] **cortex/engine.py** — CortexEngine (ties all graphs)
  - [ ] test_engine.py

### Week 15-16: Full Vault

- [ ] **vault/wal.py** — Write-ahead log
  - [ ] test_wal.py
- [ ] **vault/checkpoint.py** — Full + incremental checkpoints (upgrade)
- [ ] **vault/recovery.py** — Crash recovery manager
  - [ ] test_recovery.py → test_detect_crash(), test_recover_state(), test_replay_events()
- [ ] **vault/snapshot.py** — State serializer (upgrade)
- [ ] Integrate memory state into checkpoints
- [ ] Integrate cortex state into checkpoints
- [ ] Terminal reattach on resume

### Week 17-18: Integration

- [ ] Memory → Agent integration (context assembly)
- [ ] Cortex → Orchestrator integration (dependency-aware planning)
- [ ] Cortex → Scribe integration hooks (Phase 3 prep)
- [ ] Memory → Compass integration hooks (Phase 5 prep)
- [ ] Vault → Kernel integration (automatic checkpointing)
- [ ] ✅ **PHASE GATE:** test_e2e_phase2.py
  - [ ] test_memory_persistence_across_sessions()
  - [ ] test_crash_recovery_full()
  - [ ] test_model_swap_on_resume()
  - [ ] test_cortex_dependency_aware_planning()

**Phase 2 Total: ~25 source files + ~20 test files**

---

## PROJECT TODO — PHASE 3: Quality & Governance (Weeks 19-24)

> **Goal:** Galaxy enforces consistency, scores trust, auto-generates documentation

### Week 19-20: Sentinel

- [ ] **sentinel/style.py** — Style profile learning
  - [ ] test_style.py
- [ ] **sentinel/architecture.py** — Drift detection (via Cortex)
  - [ ] test_architecture.py
- [ ] **sentinel/naming.py** — Vocabulary governance
  - [ ] test_naming.py
- [ ] **sentinel/duplication.py** — Duplicate detection
  - [ ] test_duplication.py
- [ ] **sentinel/engine.py** — SentinelEngine daemon
  - [ ] test_sentinel_engine.py

### Week 21-22: Governance + Trust

- [ ] **governance/policy.py** — Policy loader/evaluator
  - [ ] test_policy.py
- [ ] **governance/domains/security.py** — Security policy
- [ ] **governance/domains/access_control.py** — Access control
- [ ] **governance/domains/quality_gates.py** — Quality gates
- [ ] **governance/engine.py** — GovernanceEngine
  - [ ] test_governance_engine.py
- [ ] **governance/audit.py** — Audit trail
  - [ ] test_audit.py
- [ ] **trust/scorer.py** — 4-dimension trust scoring
  - [ ] test_scorer.py → test_score_calculation(), test_dimension_weights()
- [ ] **trust/reputation.py** — Agent reputation tracker
  - [ ] test_reputation.py
- [ ] **trust/automation.py** — Trust-driven auto-merge/block
  - [ ] test_automation.py

### Week 23-24: Integration + Scribe

- [ ] Wire Sentinel → Orchestrator (check every output)
- [ ] Wire Governance → Tool execution (check every action)
- [ ] Wire Trust → Merge decisions
- [ ] Forge validator upgrade (full pipeline)
- [ ] **scribe/engine.py** — ScribeEngine (auto-doc daemon)
  - [ ] test_scribe_engine.py
- [ ] **scribe/sync.py** — DocSyncManager (drift detection)
  - [ ] test_scribe_sync.py
- [ ] **scribe/generators/readme.py** — README.md generator
- [ ] **scribe/generators/api_doc.py** — OpenAPI + Markdown
- [ ] **scribe/generators/architecture.py** — Architecture + Mermaid diagrams
- [ ] **scribe/generators/changelog.py** — CHANGELOG.md
- [ ] **scribe/generators/docstring.py** — Inline docstrings
- [ ] **scribe/generators/diagram.py** — Mermaid via Cortex
- [ ] **scribe/generators/module_doc.py** — Per-module docs
- [ ] Wire Scribe → Cortex, Forge, Sentinel
- [ ] ✅ **PHASE GATE:** test_e2e_phase3.py
  - [ ] test_sentinel_detects_style_drift()
  - [ ] test_governance_blocks_unsafe_action()
  - [ ] test_trust_auto_merge()
  - [ ] test_scribe_generates_docs()
  - [ ] test_scribe_detects_drift()

**Phase 3 Total: ~30 source files + ~20 test files**

---

## PROJECT TODO — PHASE 4: Collaboration & Scale (Weeks 25-32)

> **Goal:** Parallel workers coordinate safely, costs tracked, code auto-optimized

### Week 25-26: Sync

- [ ] **sync/lock_manager.py** — File-level locking
  - [ ] test_lock_manager.py
- [ ] **sync/changeset.py** — Changeset tracking
  - [ ] test_changeset.py
- [ ] **sync/intent.py** — Write intent declarations
- [ ] **sync/conflict.py** — Conflict detection/resolution
  - [ ] test_conflict.py
- [ ] **sync/commit_order.py** — Deterministic commit ordering
  - [ ] test_commit_order.py

### Week 27-28: Forge Labs + Refiner

- [ ] **forge/labs.py** — Experiment branching (A/B)
  - [ ] test_labs.py
- [ ] **forge/scorer.py** — Branch scoring
- [ ] **forge/promotion.py** — Winner promotion
- [ ] **refiner/detectors/dead_code.py** — Dead code detector
- [ ] **refiner/detectors/complexity.py** — Complexity detector
- [ ] **refiner/detectors/duplication.py** — Duplication detector
- [ ] **refiner/detectors/performance.py** — Performance detector
- [ ] **refiner/detectors/security.py** — Security detector
- [ ] **refiner/engine.py** — RefinerEngine
  - [ ] test_refiner_engine.py
- [ ] **refiner/optimizer.py** — Safe execution with rollback

### Week 29-30: Distiller + Ledger

- [ ] **distiller/summarizer.py** — Memory summarization
- [ ] **distiller/compactor.py** — Vector compaction
- [ ] **distiller/pruner.py** — Memory pruning
- [ ] **distiller/tiering.py** — Hot/warm/cold/frozen tiering
- [ ] **distiller/engine.py** — DistillerEngine
  - [ ] test_distiller_engine.py
- [ ] **ledger/tracker.py** — Token/cost tracking
  - [ ] test_tracker.py
- [ ] **ledger/budget.py** — Budget enforcement
  - [ ] test_budget.py
- [ ] **ledger/reports.py** — Cost reports + suggestions

### Week 31-32: Integration

- [ ] Sync → Orchestrator (locking during parallel execution)
- [ ] Distiller → Memory (automatic compression)
- [ ] Ledger → Every inference call (automatic tracking)
- [ ] Refiner → Scheduled background runs
- [ ] 15+ parallel worker stress test
- [ ] ✅ **PHASE GATE:** test_e2e_phase4.py

**Phase 4 Total: ~25 source files + ~15 test files**

---

## PROJECT TODO — PHASE 5: Enterprise & Extensibility (Weeks 33-40)

> **Goal:** Plugin ecosystem, blueprints, cluster mode, Studio dashboard, strategic intent

### Week 33-34: Plugin SDK

- [ ] **plugins/sdk.py** — Plugin SDK interface
- [ ] **plugins/loader.py** — Plugin loader
- [ ] **plugins/sandbox.py** — Process isolation
- [ ] **plugins/permissions.py** — Capability permissions
- [ ] **plugins/health.py** — Plugin health monitoring
- [ ] **plugins/registry.py** — Plugin registry
  - [ ] test_plugin_sdk.py → test_load_plugin(), test_sandbox_isolation(), test_permission_enforcement()

### Week 35-36: Blueprints

- [ ] **blueprints/loader.py** — Blueprint loader
- [ ] **blueprints/generator.py** — Project scaffold generator
- [ ] **blueprints/detector.py** — Auto-detect project type
- [ ] **blueprints/templates/fullstack_web.yaml**
- [ ] **blueprints/templates/rest_api.yaml**
- [ ] **blueprints/templates/ml_pipeline.yaml**
- [ ] **blueprints/templates/realtime_app.yaml**
- [ ] **blueprints/templates/cli_tool.yaml**
- [ ] **blueprints/templates/mobile_backend.yaml**
  - [ ] test_blueprints.py → test_load_template(), test_generate_scaffold(), test_detect_project()

### Week 37-38: Cluster + Vault Extensions + Compass

- [ ] **cluster/topology.py** — Cluster topology manager
- [ ] **cluster/node.py** — Node representation
- [ ] **cluster/communication.py** — Cross-node event bus
- [ ] **cluster/gpu_manager.py** — Multi-GPU cluster management
- [ ] **vault/hibernate.py** — Project hibernation
- [ ] **vault/export.py** — Cross-hardware .vault export/import
- [ ] **compass/engine.py** — CompassEngine (intent processing)
  - [ ] test_compass_engine.py → test_load_intent(), test_get_context(), test_evaluate_alignment()
- [ ] **compass/intent.py** — Intent data models + .galaxy/intent.yaml
  - [ ] test_intent.py → test_parse_intent_yaml(), test_priority_stack()
- [ ] **compass/advisor.py** — StrategyAdvisor (per-subsystem guidance)
  - [ ] test_advisor.py → test_advise_model_router(), test_advise_worker()
- [ ] **compass/alignment.py** — AlignmentChecker (output scoring)
  - [ ] test_alignment.py → test_security_violation_detected(), test_budget_violation()
- [ ] **compass/evolution.py** — IntentEvolution (adapt over time)
  - [ ] test_evolution.py → test_suggest_updates(), test_detect_conflicts()
- [ ] Wire Compass → Orchestrator, Model Router, Workers, Trust, Governance, Scribe

### Week 39-40: Studio Dashboard

- [ ] **studio/server.py** — FastAPI server
- [ ] **studio/websocket.py** — Real-time WebSocket updates
- [ ] **studio/api/agents.py** — Agent endpoints
- [ ] **studio/api/tasks.py** — Task endpoints
- [ ] **studio/api/models.py** — Model management endpoints
- [ ] **studio/api/memory.py** — Memory endpoints
- [ ] **studio/api/policies.py** — Policy endpoints
- [ ] **studio/api/budget.py** — Budget endpoints
- [ ] **studio/api/config.py** — Configuration endpoints
- [ ] Studio Intent Dashboard view
- [ ] Studio Documentation browser (Scribe output)
- [ ] Studio frontend (React/Vite)
- [ ] ✅ **PHASE GATE:** test_e2e_phase5.py
  - [ ] test_plugin_load_and_execute()
  - [ ] test_blueprint_scaffold()
  - [ ] test_compass_intent_alignment()
  - [ ] test_studio_api_endpoints()

**Phase 5 Total: ~45 source files + ~15 test files**

---

## PROJECT TODO — PHASE 6: Autonomous Operations (Weeks 41-46)

> **Goal:** Galaxy self-improves, learns skills, community ecosystem

- [ ] **ProactiveRefiner** — Scheduled idle-time optimization
- [ ] **HierarchicalIndex** — Multi-level vector search (L0-L3)
- [ ] **WASMSandbox** — WASM plugin isolation
- [ ] **PluginRegistry** — Community plugin marketplace
- [ ] **BlueprintRegistry** — Community blueprint marketplace
- [ ] **KnowledgeTransfer** — Cross-workspace learning
- [ ] **SkillManager** — Record + replay successful task patterns
- [ ] **AutonomousCompass** — Auto-evolve intent, cross-project learning
- [ ] **AutonomousScribe** — Scheduled drift repair, cross-reference audit
- [ ] ✅ **PHASE GATE:** test_e2e_phase6.py

**Phase 6 Total: ~20 source files + ~10 test files**

---

## VERIFICATION PLAN

### Automated Tests (every phase)
```bash
pytest tests/unit/ -v                        # Unit tests
pytest tests/integration/ -v                 # Integration tests
pytest tests/e2e/ -v --slow                  # E2E tests (requires Ollama)
pytest --cov=galaxy --cov-report=html        # Coverage (target 80%+)
mypy src/galaxy/ --strict                    # Type checking
ruff check src/galaxy/ && ruff format src/   # Linting
```

### Key E2E Test Scenarios
```
 1. Single worker file generation + validation
 2. Multi-worker parallel execution (no conflicts)
 3. Crash recovery (kill mid-execution, restart)
 4. Pause/resume (pause, swap models, resume)
 5. Model fallback (local fails → cloud escalation)
 6. Memory persistence (stop, restart, memories intact)
 7. Trust scoring accuracy
 8. Policy enforcement (blocked = actually blocked)
 9. Escalation chain (Worker → Domain → Master → Fallback → User)
10. Unified startup (CLI + Studio together)
11. Scribe doc generation (file created → docs auto-generated)
12. Scribe drift detection (code changed → stale docs repaired)
13. Compass intent alignment (security intent → blocks insecure code)
14. Compass model routing (budget: minimal → local models)
15. Compass intent evolution (project grows → update suggested)
```

### Manual Verification
- `pip install .` → `galaxy setup` → `galaxy run "Build a REST API"` works end-to-end
- Studio dashboard opens and shows live data
- Crash mid-build → `galaxy resume` recovers cleanly

---

## SUMMARY

| Phase | Weeks | Files | What You Get |
|-------|-------|-------|-------------|
| **1** | 1-10 | ~65 | Working Galaxy: boot → plan → execute → validate → output |
| **2** | 11-18 | ~25 | Memory, code intelligence, crash recovery |
| **3** | 19-24 | ~30 | Quality enforcement, trust scoring, auto-docs |
| **4** | 25-32 | ~25 | Safe parallel workers, cost tracking, optimization |
| **5** | 33-40 | ~45 | Plugins, blueprints, Compass intent, Studio dashboard |
| **6** | 41-46 | ~20 | Self-improvement, skills, community marketplace |
| **Total** | **46 weeks** | **~200** | **Full Galaxy AI Operating System** |

> [!IMPORTANT]
> **We start with Phase 1.** After Phase 1 completes, you'll have a working Galaxy that can plan a project, spawn agents, generate code, validate it, and output results. Each subsequent phase adds intelligence layers on top.

> [!NOTE]
> **First file we create:** `pyproject.toml` → then `core/constants.py` → then `core/exceptions.py` → building up layer by layer with tests at every step.
