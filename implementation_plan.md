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

### Week 3-4: Model + Agent Layer

- [ ] **models/vram.py** — VRAM detection + monitoring
  - [ ] test_vram.py → test_detect_gpus(), test_get_free_vram(), test_estimate_model_vram(), test_no_gpu_returns_zero()
- [ ] **models/providers/base.py** — BaseProvider interface
- [ ] **models/providers/ollama.py** — Ollama provider
  - [ ] test_ollama_provider.py → test_is_available(), test_list_models(), test_chat_completion(), test_chat_with_tools(), test_timeout()
- [ ] **models/providers/openai.py** — OpenAI provider
  - [ ] test_openai_provider.py → test_api_key_from_env(), test_chat_completion_mock(), test_handles_rate_limit()
- [ ] **models/providers/anthropic.py** — Anthropic provider
- [ ] **models/providers/google.py** — Google Gemini provider
- [ ] **models/providers/groq.py** — Groq provider
- [ ] **models/providers/deepseek.py** — DeepSeek provider
- [ ] **models/providers/vllm.py** — vLLM provider
- [ ] **models/providers/custom.py** — Custom OpenAI-compatible
- [ ] **models/providers/litellm.py** — LiteLLM proxy
- [ ] **models/registry.py** — ProviderRegistry (auto-discover)
- [ ] **models/router.py** — ModelRouter (tier-based + task-based)
  - [ ] test_router.py → test_route_by_tier(), test_route_by_task_type(), test_fallback_on_failure(), test_swap_model(), test_detect_all_providers()
- [ ] **models/pool.py** — Model pool manager
- [ ] **agents/base.py** — BaseAgent
  - [ ] test_base_agent.py → test_agent_creation(), test_invoke_llm(), test_use_tool(), test_checkpoint_serialization(), test_from_checkpoint_restoration()
- [ ] **agents/worker.py** — WorkerAgent
  - [ ] test_worker.py → test_worker_executes_simple_task(), test_worker_writes_file(), test_worker_handles_failure()
- [ ] **agents/domain.py** — DomainAgent
  - [ ] test_domain.py
- [ ] **agents/master.py** — MasterAgent
  - [ ] test_master.py
- [ ] **agents/registry.py** — AgentRegistry
  - [ ] test_registry.py → test_register_agent(), test_get_agents_by_tier(), test_cleanup_idle_agents(), test_agent_limits_enforced()
- [ ] ✅ **MODULE GATE:** test_agent_model_integration.py
  - [ ] test_agent_calls_model_via_router()
  - [ ] test_worker_generates_code_with_ollama()
  - [ ] test_agent_lifecycle_spawn_to_terminate()

### Week 5-6: Tools + Terminal

- [ ] **tools/base.py** — BaseTool interface
  - [ ] test_base_tool.py → test_tool_input_validation(), test_tool_result_structure()
- [ ] **tools/registry.py** — ToolRegistry
  - [ ] test_tool_registry.py → test_register_tool(), test_get_tools_for_tier(), test_generate_openai_schemas()
- [ ] **tools/builtin/file_read.py** — FileRead tool
  - [ ] test_file_read.py → test_read_full_file(), test_read_line_range(), test_read_nonexistent(), test_permission_denied()
- [ ] **tools/builtin/file_write.py** — FileWrite tool
  - [ ] test_file_write.py → test_write_new(), test_creates_directories(), test_overwrite(), test_blocked_outside_workspace()
- [ ] **tools/builtin/file_edit.py** — FileEdit tool
  - [ ] test_file_edit.py → test_replace_content(), test_nonexistent_file(), test_target_not_found()
- [ ] **tools/builtin/terminal.py** — Terminal tool
  - [ ] test_terminal_tool.py → test_execute_command(), test_timeout(), test_blocked_dangerous()
- [ ] **tools/builtin/search.py** — Search tool
  - [ ] test_search.py
- [ ] **tools/builtin/git.py** — Git tool
  - [ ] test_git.py
- [ ] **tools/builtin/tree.py** — Directory tree tool
  - [ ] test_tree.py
- [ ] **terminal/manager.py** — TerminalManager (tmux)
  - [ ] test_terminal_manager.py → test_create_tmux_session(), test_execute_in_session(), test_cleanup_session(), test_reattach()
- [ ] **terminal/session.py** — TmuxSession wrapper
- [ ] **terminal/executor.py** — Command executor
- [ ] **terminal/parser.py** — Output parser
- [ ] ✅ **MODULE GATE:** test_tools_integration.py
  - [ ] test_agent_uses_file_tools()
  - [ ] test_agent_runs_terminal_command()
  - [ ] test_permission_blocks_unauthorized_tool()

### Week 7-8: Orchestrator + Vault + CLI + Terminal UX

- [ ] **orchestrator/task.py** — Task data models
  - [ ] test_task.py → test_task_creation(), test_status_transitions(), test_serialization()
- [ ] **orchestrator/task_graph.py** — DAG manager
  - [ ] test_task_graph.py → test_add_tasks(), test_get_ready_tasks(), test_critical_path(), test_circular_dependency(), test_mark_completed(), test_graph_serialization()
- [ ] **orchestrator/scheduler.py** — VRAM-aware scheduler
  - [ ] test_scheduler.py → test_schedule_respects_vram(), test_calculate_parallelism(), test_evict_least_used()
- [ ] **orchestrator/orchestrator.py** — Orchestrator engine
  - [ ] test_orchestrator.py → test_planning_phase(), test_execution_phase(), test_failure_retry(), test_checkpoint_on_milestone()
- [ ] **orchestrator/escalation.py** — 5-level EscalationManager
  - [ ] test_escalation.py → test_worker_retry(), test_domain_intervention(), test_master_restructure(), test_model_fallback(), test_user_escalation()
- [ ] **forge/validator.py** — ContinuousValidator (basic)
  - [ ] test_validator.py → test_syntax_check(), test_import_check(), test_lint_check()
- [ ] **vault/checkpoint.py** — Checkpoint engine (basic)
  - [ ] test_vault.py → test_create_checkpoint(), test_load_checkpoint(), test_crash_marker(), test_recover_from_crash()
- [ ] **vault/snapshot.py** — State serializer
- [ ] **cli/app.py** — Main CLI app (typer)
  - [ ] test_cli.py → test_setup(), test_init(), test_run(), test_pause(), test_resume(), test_status()
- [ ] **cli/renderer.py** — GalaxyRenderer (master rendering engine)
  - [ ] test_renderer.py → test_start_stop(), test_switch_view(), test_cycle_verbosity()
- [ ] **cli/colors.py** — GalaxyColors design constants
- [ ] **cli/keyboard.py** — KeyboardController (hotkey listener)
  - [ ] test_keyboard.py → test_key_map(), test_handle_view_switch()
- [ ] **cli/views/boot.py** — BootRenderer (ASCII logo + steps)
  - [ ] test_boot_view.py
- [ ] **cli/views/dashboard.py** — DashboardView (live in-place)
  - [ ] test_dashboard_view.py
- [ ] **cli/views/activity.py** — ActivityFeedView (scrolling log)
- [ ] **cli/views/taskgraph.py** — TaskGraphView (ASCII DAG)
- [ ] **cli/views/escalation.py** — EscalationRenderer
- [ ] **cli/views/completion.py** — CompletionReport (final summary)
- [ ] **cli/views/status.py** — StatusRenderer
- [ ] **cli/setup_helper.py** — Auto-detect hardware, install deps
  - [ ] test_setup_helper.py → test_detect_gpu(), test_install_tmux(), test_install_ollama()
- [ ] ✅ **MODULE GATE:** test_orchestrator_integration.py
  - [ ] test_full_pipeline_plan_to_execute()
  - [ ] test_checkpoint_and_resume()
  - [ ] test_parallel_worker_execution()

### Week 9-10: E2E Testing + Polish

- [ ] ✅ **PHASE GATE:** test_e2e_phase1.py
  - [ ] test_build_simple_python_script()
  - [ ] test_build_rest_api()
  - [ ] test_crash_and_recover()
  - [ ] test_pause_swap_model_resume()
  - [ ] test_multi_worker_parallel()
  - [ ] test_pip_install_and_cli()
- [ ] pip package build + test install
- [ ] Documentation pass

**Phase 1 Total: ~65 source files + ~45 test files**

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
