# Galaxy AI — Implementation Plan (v3)

## Architectural Upgrades (v1 → v3)

| # | Upgrade | Impact |
|---|---------|--------|
| 1 | **Chunk-based workers** | Workers generate patches/snippets, not full files. New Integrator merges chunks |
| 2 | **Structured contracts** | Domain agents output formal specs (signatures, params, types, constraints) |
| 3 | **Cloud worker scaling** | Unlimited cloud agents with permission gates and cost estimates |
| 4 | **Brainstorming engine** | Pre-execution cognitive layer: temp ideas ↔ permanent ideas with approval |
| 5 | **Project source-of-truth** | `.galaxy/project.yaml` defines entire project state, portable and rebuildable |
| 6 | **Cognitive pipeline** | Master uses: Expander → Planner → Retriever → Reflection → Synthesizer |
| 7 | **Normal vs Reasoning modes** | Fast mode (cheap) vs Reasoning mode (deep cognitive pipeline) |
| 8 | **Autonomous Audit System** | Engineering + Security + Production audit with remediation (standalone capable) |

---

## Revised Architecture

```
USER
  ↓
BRAINSTORM ENGINE
  ├── Temp Ideas (exploration)
  ├── Permanent Ideas (approved truth)
  └── Decision Logger (timestamps, history)
  ↓
MASTER COGNITIVE PIPELINE
  ├── [Normal Mode] Direct planning
  └── [Reasoning Mode]
      ├── Prompt Expander → structured spec
      ├── Planner → dependency-aware DAG
      ├── Retriever → context assembly
      ├── Reflection → validate plan
      └── Synthesizer → final plan
  ↓
DOMAIN AGENTS → Execution Contracts
  { target_file, function, signature, dependencies, constraints, validation }
  ↓
WORKERS → Code Chunks
  { target_file, target_symbol, operation, content, dependencies }
  ↓
INTEGRATOR → Merges chunks into files
  ↓
FORGE → BUILD/TEST/FIX → OUTPUT
  ↓ (optional, or standalone)
AUDIT SYSTEM
  ├── Engineering Audit (quality, architecture, maintainability)
  ├── Security Audit (OWASP, CVEs, secrets, injection, auth)
  ├── Production Audit (CI/CD, monitoring, scaling, config)
  └── Remediation Pipeline (fix → verify → report)
```

---

## PHASE 1: Foundation ✅ COMPLETE

> 52 source files, 36 test files, **381 tests passing**

Working Galaxy: `galaxy run "prompt"` → Master → Domain → Workers → Files → Validation

---

## PHASE 2: Cognitive Engine (Weeks 11-20) ✅ COMPLETE

> **Goal:** Galaxy thinks before it acts — brainstorming, contracts, chunks, cognitive pipeline
> **Result:** 92 source files, 75 test files, **784 tests passing**

### Week 11-12: Brainstorming Engine ✅

- [x] **brainstorm/types.py** — Idea, IdeaStatus, BrainstormSession models
  - [x] test_brainstorm_types.py
- [x] **brainstorm/temp_store.py** — Temp ideas store (exploration)
  - [x] test_temp_store.py
- [x] **brainstorm/permanent_store.py** — Permanent ideas store (approved truth)
  - [x] test_permanent_store.py
- [x] **brainstorm/decision_log.py** — Decision logger with timestamps/history
  - [x] test_decision_log.py
- [x] **brainstorm/engine.py** — BrainstormEngine (orchestrates session)
  - [x] test_brainstorm_engine.py
- [x] **brainstorm/interviewer.py** — Master asks clarifying questions
- [x] **cli/commands/brainstorm.py** — `galaxy brainstorm` CLI command
- [x] ✅ **MODULE GATE:** test_brainstorm_integration.py

### Week 13-14: Structured Contracts + Chunk-Based Workers ✅

- [x] **contracts/types.py** — ExecutionContract, CodeChunk, ChunkOperation models
  - [x] test_contract_types.py
- [x] **contracts/builder.py** — ContractBuilder (Domain agent uses this)
  - [x] test_contract_builder.py
- [x] **agents/domain.py** [UPGRADE] — Outputs ExecutionContracts
  - [x] test_domain_contracts.py
- [x] **agents/worker.py** [UPGRADE] — Generates CodeChunks from contracts
  - [x] test_worker_chunks.py
- [x] **integrator/types.py** — MergeOperation, FileState, ConflictInfo
- [x] **integrator/merger.py** — Merges code chunks into files
  - [x] test_merger.py
- [x] **integrator/conflict.py** — Conflict detection + resolution
  - [x] test_conflict.py
- [x] **integrator/engine.py** — IntegratorEngine
  - [x] test_integrator_engine.py
- [x] ✅ **MODULE GATE:** test_contract_integration.py

### Week 15-16: Cognitive Pipeline (Normal + Reasoning Modes) ✅

- [x] **cognitive/types.py** — CognitiveMode (NORMAL, REASONING), PipelineStage
- [x] **cognitive/expander.py** — PromptExpander (vague → structured spec)
  - [x] test_expander.py
- [x] **cognitive/planner.py** — CognitivePlanner (spec → dependency DAG)
  - [x] test_planner.py
- [x] **cognitive/retriever.py** — ContextRetriever (fetch relevant context)
  - [x] test_retriever.py
- [x] **cognitive/reflection.py** — ReflectionAgent (critique + verify)
  - [x] test_reflection.py
- [x] **cognitive/synthesizer.py** — FinalSynthesizer
- [x] **cognitive/pipeline.py** — CognitivePipeline (orchestrates the chain)
  - [x] test_pipeline.py
- [x] **agents/master.py** [UPGRADE] — Master uses CognitivePipeline
  - [x] test_master_cognitive.py
- [x] ✅ **MODULE GATE:** test_cognitive_integration.py

### Week 17-18: Project Source-of-Truth + Interactive CLI ✅

- [x] **project/spec.py** — ProjectSpec data model (`.galaxy/project.yaml`)
  - [x] test_project_spec.py
- [x] **project/loader.py** — Load/save project spec (YAML)
  - [x] test_loader.py
- [x] **project/reconstructor.py** — Rebuild project from spec
  - [x] test_reconstructor.py
- [x] **project/analyzer.py** — Read existing project → generate spec
  - [x] test_analyzer.py
- [x] **cli/commands/chat.py** — `galaxy chat` interactive mode
- [x] **cli/commands/config.py** — `galaxy config set/get/show`
- [x] **cli/confirm.py** — Permission/approval gate before execution
  - [x] test_confirm.py

### Week 19-20: Cloud Scaling + Terminal Dashboard + Integration ✅

- [x] **scaling/limiter.py** — Soft limits + permission escalation for cloud
  - [x] test_limiter.py
- [x] **scaling/cost_estimator.py** — Estimate token cost before execution
- [x] **cli/views/dashboard.py** — Live terminal dashboard (Rich Live)
- [x] **cli/views/activity.py** — Activity feed view
- [x] **cli/views/taskgraph.py** — ASCII DAG view
- [x] **cli/keyboard.py** — Hotkey controller ([Tab], [Space], [Q])
- [x] Wire: brainstorm → cognitive → contracts → chunks → integrator → forge
- [x] ✅ **PHASE GATE:** test_e2e_phase2.py

**Phase 2 Total: 40 new source + 39 new test files, 784 tests passing**

---

## PHASE 3: Intelligence Layer (Weeks 21-28)

> **Goal:** Memory, code intelligence, build/test/fix loop, auto-docs

### Week 21-22: Memory Foundation

- [ ] **memory/types.py** — MemoryEntry, MemoryLevel, MemoryScope
- [ ] **memory/store.py** — File-based persistence
- [ ] **memory/embeddings.py** — Ollama embedding integration
- [ ] **memory/vector_store.py** — Numpy cosine similarity search
- [ ] **memory/manager.py** — MemoryManager API
- [ ] **memory/hierarchy.py** — 5-level memory scoping

### Week 23-24: Cortex (Code Intelligence)

- [ ] **cortex/parser.py** — tree-sitter multi-language parser
- [ ] **cortex/graphs/** — AST, symbol, import, call, API, dataflow graphs
- [ ] **cortex/query.py** — Graph query API
- [ ] **cortex/engine.py** — CortexEngine
- [ ] Wire Cortex → Integrator + Retriever

### Week 25-26: Build/Test/Fix Loop

- [ ] **forge/runner.py** — Run generated code (pip install, pytest, uvicorn)
- [ ] **forge/fixer.py** — Auto-fix failures → re-test
- [ ] **forge/pipeline.py** — Generate → Test → Fix → Re-test → Deploy loop
- [ ] Wire Forge → Escalation → Reflection

### Week 27-28: Auto-Documentation + Integration

- [ ] **scribe/engine.py** — ScribeEngine (auto-doc daemon)
- [ ] **scribe/generators/** — README, API doc, architecture, changelog
- [ ] Wire Memory → Brainstorm, Cortex → Domain
- [ ] ✅ **PHASE GATE:** test_e2e_phase3.py

**Phase 3 Total: ~35 source + ~25 test files**

---

## PHASE 4: Quality, Scale & Audit (Weeks 29-38)

> **Goal:** Governance, trust, parallel scale, cost tracking, **autonomous audit system**

### Week 29-30: Sentinel + Governance + Trust

- [ ] **sentinel/** — Style enforcement, architecture drift, duplication detection
- [ ] **governance/** — Policy engine, security, access control, quality gates
- [ ] **trust/** — 4-dimension trust scoring, agent reputation, auto-merge

### Week 31-32: Sync + Refiner

- [ ] **sync/** — File locking, changeset tracking, conflict resolution
- [ ] **refiner/** — Dead code, complexity, duplication, performance, security detectors

### Week 33-34: Ledger + Distiller

- [ ] **ledger/** — Token/cost tracking, budget enforcement, cost reports
- [ ] **distiller/** — Memory summarization, compaction, hot/warm/cold tiering

### Week 35-36: Audit System — Engineering & Security

> **NEW** — Autonomous production-grade audit, usable standalone or post-project

- [ ] **audit/types.py** — Finding, Severity, AuditReport, AuditMode data models
  - [ ] test_audit_types.py
- [ ] **audit/scanner.py** — Base scanner interface (scoped code region analysis)
  - [ ] test_scanner.py
- [ ] **audit/engineering/quality.py** — Code quality analysis (complexity, duplication, dead code)
  - [ ] test_engineering_quality.py
- [ ] **audit/engineering/architecture.py** — Architecture analysis (patterns, dependencies, drift)
  - [ ] test_engineering_architecture.py
- [ ] **audit/engineering/coverage.py** — Test coverage analysis + gap detection
  - [ ] test_engineering_coverage.py
- [ ] **audit/security/vulnerability.py** — Vulnerability scanner (SQL injection, XSS, CSRF, path traversal)
  - [ ] test_security_vulnerability.py
- [ ] **audit/security/auth.py** — Authentication/authorization analysis
  - [ ] test_security_auth.py
- [ ] **audit/security/secrets.py** — Leaked credentials/API key detection
  - [ ] test_security_secrets.py
- [ ] **audit/security/dependencies.py** — Dependency CVE scanning
  - [ ] test_security_dependencies.py
- [ ] **audit/production/readiness.py** — Production readiness checks (logging, monitoring, error handling)
  - [ ] test_production_readiness.py
- [ ] **audit/production/config.py** — Configuration hardening analysis
  - [ ] test_production_config.py

### Week 37-38: Audit Orchestration + Remediation

- [ ] **audit/orchestrator.py** — AuditOrchestrator (Master → Domain → Worker audit pipeline)
  - [ ] test_audit_orchestrator.py
- [ ] **audit/validator.py** — Multi-pass finding validation (removes hallucinations)
  - [ ] test_audit_validator.py → test_removes_false_positives(), test_confidence_scoring()
- [ ] **audit/remediation.py** — Auto-fix vulnerabilities + verify fixes
  - [ ] test_remediation.py → test_fix_sql_injection(), test_fix_xss(), test_verify_fix()
- [ ] **audit/reporter.py** — Generate structured audit reports (JSON + Markdown)
  - [ ] test_reporter.py
- [ ] **cli/commands/audit.py** — `galaxy audit` CLI command (standalone mode)
  - `galaxy audit ./project` — Full audit
  - `galaxy audit ./project --mode security` — Security only
  - `galaxy audit ./project --mode engineering` — Engineering only
  - `galaxy audit ./project --mode production` — Production readiness
  - `galaxy audit ./project --fix` — Auto-remediate findings
- [ ] Wire Audit → post-project-completion (optional step after `galaxy run`)
- [ ] Wire Audit → Cortex (uses code graphs for deeper analysis)
- [ ] Wire Audit → Sentinel/Governance (shares findings)
- [ ] ✅ **PHASE GATE:** test_e2e_phase4.py
  - [ ] test_engineering_audit_detects_issues()
  - [ ] test_security_audit_finds_vulnerabilities()
  - [ ] test_remediation_fixes_and_verifies()
  - [ ] test_standalone_audit_on_existing_project()
  - [ ] test_audit_confidence_filtering()

**Phase 4 Total: ~55 source + ~30 test files**

---

## Audit System — Detailed Flow

```
┌─ galaxy audit ./project ─────────────────────────────────┐
│                                                          │
│  Phase 1: Cortex Scan                                    │
│    → Build dependency/API/auth/secrets graphs            │
│                                                          │
│  Phase 2: Master Creates Audit Domains                   │
│    → Engineering Domain                                  │
│    → Security Domain                                     │
│    → Production Domain                                   │
│                                                          │
│  Phase 3: Scoped Workers Analyze Code Regions            │
│    ┌──────────────┬────────────────┬───────────────┐     │
│    │ auth_worker  │ api_worker     │ db_worker     │     │
│    │ config_worker│ secrets_worker │ deps_worker   │     │
│    └──────────────┴────────────────┴───────────────┘     │
│    Each worker → structured finding with confidence      │
│                                                          │
│  Phase 4: Domain Validates Findings                      │
│    → Remove hallucinations                               │
│    → Verify correctness                                  │
│    → Correlate vulnerabilities                           │
│    → Estimate blast radius                               │
│                                                          │
│  Phase 5: Master Creates Remediation Plan                │
│    → Prioritize fixes by severity                        │
│    → Assign repair workers                               │
│    → Validate fixes                                      │
│    → Re-scan to verify                                   │
│                                                          │
│  Phase 6: Generate Report                                │
│    → JSON (machine-readable)                             │
│    → Markdown (human-readable)                           │
│    → Severity summary + fix status                       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Worker Finding Format

```json
{
  "id": "SEC-042",
  "severity": "HIGH",
  "confidence": 0.91,
  "category": "SQL Injection",
  "file": "backend/routes/users.py",
  "line": 82,
  "code_snippet": "query = f\"SELECT * FROM users WHERE id={user_id}\"",
  "description": "Unsanitized user input in SQL query",
  "exploitability": "Remote, unauthenticated",
  "recommended_fix": "Use parameterized queries",
  "fix_content": "query = \"SELECT * FROM users WHERE id=?\"\ncursor.execute(query, (user_id,))"
}
```

---

## PHASE 5: Enterprise & Extensibility (Weeks 39-46)

> **Goal:** Plugin ecosystem, blueprints, web dashboard, strategic intent

### Week 39-40: Plugins + Blueprints

- [ ] **plugins/** — SDK, loader, sandbox, permissions, registry
- [ ] **blueprints/** — Template loader, scaffold generator, auto-detect

### Week 41-42: Compass (Strategic Intent)

- [ ] **compass/** — Intent engine, strategy advisor, alignment checker, evolution

### Week 43-44: Galaxy Studio (Web Dashboard)

- [ ] **studio/server.py** — FastAPI backend
- [ ] **studio/websocket.py** — Real-time WebSocket updates
- [ ] **studio/api/** — Agents, tasks, models, memory, brainstorm, audit, config
- [ ] **studio/frontend/** — React/Vite dashboard
  - Brainstorm view (temp/permanent ideas)
  - Task graph visualization
  - Agent status monitoring
  - Audit results dashboard
  - Cost dashboard
  - Configuration UI

### Week 45-46: Integration

- [ ] ✅ **PHASE GATE:** test_e2e_phase5.py

**Phase 5 Total: ~50 source + ~15 test files**

---

## PHASE 6: Autonomous Operations (Weeks 47-52)

> **Goal:** Self-improvement, learning, community ecosystem

- [ ] ProactiveRefiner, SkillManager, KnowledgeTransfer
- [ ] AutonomousCompass, AutonomousScribe
- [ ] Community plugin/blueprint marketplace
- [ ] WASM sandbox isolation
- [ ] ✅ **PHASE GATE:** test_e2e_phase6.py

**Phase 6 Total: ~20 source + ~10 test files**

---

## Updated Summary

| Phase | Weeks | Source+Test | What You Get |
|-------|-------|-------------|-------------|
| **1** ✅ | 1-10 | 52+36 | Working Galaxy: prompt → 3-tier → code generation |
| **2** ✅ | 11-20 | 92+75 | Brainstorming, Cognitive Pipeline, Contracts, Chunks, Dashboard |
| **3** | 21-28 | ~35+25 | Memory, Code Intelligence, Build/Test/Fix loop, Auto-docs |
| **4** | 29-38 | ~55+30 | Governance, Trust, Scale, Cost, **Audit System** |
| **5** | 39-46 | ~50+15 | Plugins, Blueprints, Compass, Galaxy Studio (Web) |
| **6** | 47-52 | ~20+10 | Self-improvement, Skills, Marketplace |
| **Total** | **52 weeks** | **~284+191** | **Full Galaxy AI Cognitive Engineering OS** |

---

## Open Questions

> [!IMPORTANT]
> ### 1. Chunk granularity
> Function-level (safest) or block-level (flexible)? Recommend: start function-level.

> [!IMPORTANT]
> ### 2. Brainstorming storage format
> YAML (human readable) or JSON? Recommend: YAML.

> [!IMPORTANT]
> ### 3. Project spec file name
> Recommend: `.galaxy/project.yaml`

> [!WARNING]
> ### 4. Cognitive pipeline cost
> Reasoning mode = 5 LLM calls per task. Show cost estimate + require approval?

> [!IMPORTANT]
> ### 5. Audit hallucination prevention
> Multi-pass validation is critical. Recommend: minimum 2 verification passes + confidence threshold (≥0.7) before reporting findings.
