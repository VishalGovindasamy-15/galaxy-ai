# Galaxy Implementation Guide — Part 4: Phase 3 & 4

---

## PHASE 3: Quality & Governance

### 1. Sentinel — `sentinel/`

```python
# sentinel/engine.py
class SentinelEngine:
    """Consistency governance daemon. Runs in background."""

    style_enforcer: StyleEnforcer
    arch_detector: ArchitectureDriftDetector
    naming_governor: NamingGovernor
    duplication_detector: DuplicationDetector
    api_enforcer: APIConsistencyEnforcer

    async def scan_project(self) -> ConsistencyReport:
        """Full project consistency scan. Returns score 0-100."""

    async def check_output(self, files: list[str]) -> list[Violation]:
        """Check specific files (called after worker output)."""

    async def learn_style(self, project_path: str) -> StyleProfile:
        """Analyze existing code to learn project style."""

# sentinel/style.py
class StyleEnforcer:
    profile: StyleProfile  # Learned from codebase

    async def learn(self, project_path: str) -> StyleProfile:
        """
        Scan existing files → extract:
        - Naming convention (camelCase/snake_case/PascalCase)
        - Quote style (single/double)
        - Indentation (tabs/spaces, width)
        - Import ordering pattern
        - Docstring style
        """

    async def check(self, file_path: str, content: str) -> list[Violation]:
        """Check file against learned style profile."""

@dataclass
class StyleProfile:
    naming: dict[str, str]     # {functions: "snake_case", classes: "PascalCase"}
    quotes: str                # "single" | "double"
    indent: dict               # {style: "spaces", width: 4}
    import_order: list[str]    # ["stdlib", "third_party", "local"]

# sentinel/architecture.py
class ArchitectureDriftDetector:
    """Detects import boundary violations using Cortex import graph."""

    rules: list[ArchRule]      # From blueprint or config

    async def check(self, file_path: str) -> list[Violation]:
        """
        For each import in file:
        1. Determine file's layer (presentation/api/service/repo/domain)
        2. Determine imported module's layer
        3. Check against architecture rules
        4. Flag violations
        """

@dataclass
class Violation:
    severity: str             # error | warning | info
    file: str
    line: int | None
    rule: str
    message: str
    suggestion: str | None
```

### 2. Governance — `governance/`

```python
# governance/engine.py
class GovernanceEngine:
    """Policy evaluation pipeline. Checks every agent action."""

    policies: list[Policy]

    async def evaluate(self, action: AgentAction) -> PolicyResult:
        """
        1. Match applicable policies (by domain, scope, tier)
        2. Evaluate each matching rule
        3. Return PASS/FAIL with enforcement mode
        """

    async def load_policies(self, config_path: str) -> None:
        """Load policy YAML files."""

# governance/policy.py
@dataclass
class Policy:
    name: str
    domain: str               # security | compliance | access_control | quality
    severity: str             # critical | error | warning
    enforcement: str          # block | warn | audit | escalate
    rules: list[PolicyRule]

@dataclass
class PolicyRule:
    check: str                # pattern | data_model | deploy_target | etc.
    match: dict               # Conditions to match
    require: dict | None      # Requirements to satisfy
    message: str

@dataclass
class PolicyResult:
    allowed: bool
    violations: list[PolicyViolation]
    enforcement: str

# governance/domains/security.py
class SecurityPolicyChecker:
    async def check_no_secrets(self, content: str) -> list[PolicyViolation]
    async def check_no_eval(self, content: str) -> list[PolicyViolation]
    async def check_sql_injection(self, content: str) -> list[PolicyViolation]

# governance/audit.py
class AuditLogger:
    async def log(self, evaluation: PolicyResult, action: AgentAction) -> None:
        """Log every policy evaluation to audit trail (database)."""
```

### 3. Trust — `trust/`

```python
# trust/scorer.py
class TrustScorer:
    """Compute 4-dimension trust profile for every agent output."""

    async def score(self, task: Task, result: TaskResult, agent: BaseAgent) -> TrustProfile:
        """
        1. generation_confidence: task clarity, retry count, context completeness
        2. validation_quality: which checks passed (build, type, lint, test, sentinel)
        3. risk_score: file criticality, blast radius (from Cortex), data sensitivity
        4. stability_estimate: dependency volatility, pattern maturity
        5. composite = weighted combination
        6. band = high/medium/low/critical
        """

@dataclass
class TrustProfile:
    generation_confidence: int   # 0-100
    validation_quality: int      # 0-100
    risk_score: int              # 0-100 (HIGH = dangerous)
    stability_estimate: int      # 0-100
    composite_trust: int         # 0-100
    band: str                    # high | medium | low | critical

# trust/reputation.py
class ReputationTracker:
    """Per-agent trust history."""

    async def record(self, agent_id: str, trust: TrustProfile) -> None
    async def get_reputation(self, agent_id: str) -> AgentReputation
    async def get_strengths(self, agent_id: str) -> dict[str, float]:
        """What task types does this agent excel at?"""

# trust/automation.py
class TrustAutomation:
    """Trust-driven decisions: auto-merge, block, escalate.
    Integrates with EscalationManager for failure handling."""

    async def decide(self, trust: TrustProfile, task: Task) -> TrustDecision:
        """
        - composite >= 85 → auto_merge
        - 65-84 → domain_review
        - 40-64 → master_review
        - < 40 → human_review (via Studio dashboard)

        On failure, triggers EscalationManager:
        Worker fails → Domain Agent intervenes → Master Agent restructures
        → Fallback model → User (presented in Studio with full context)
        """
```

---

## PHASE 4: Collaboration & Scale

### 4. Sync — `sync/`

```python
# sync/lock_manager.py
class LockManager:
    """File-level locking to prevent concurrent write conflicts."""

    locks: dict[str, Lock]  # file_path → Lock (stored in Redis/DB)

    async def acquire(self, file_path: str, agent_id: str,
                      mode: str = "exclusive", timeout: int = 60) -> bool:
        """Acquire lock. Returns True if granted, False if denied."""

    async def release(self, file_path: str, agent_id: str) -> None
    async def check_deadlocks(self) -> list[DeadlockCycle]
    async def force_release_expired(self) -> int:
        """Release locks held by dead/timed-out agents."""

# sync/changeset.py
class ChangesetManager:
    """Atomic multi-file transactions."""

    async def create(self, name: str, files: list[FileOp]) -> Changeset:
        """Create changeset, reserve all files."""

    async def commit(self, changeset_id: str) -> CommitResult:
        """Validate all files → commit atomically or rollback all."""

    async def rollback(self, changeset_id: str) -> None:
        """Discard all changes in changeset."""

# sync/intent.py
class IntentCoordinator:
    """Intent-based conflict detection (uses Cortex)."""

    async def declare_intent(self, agent_id: str, intent: Intent) -> None
    async def detect_conflicts(self) -> list[Conflict]:
        """Analyze all declared intents for file/symbol/contract overlap."""
    async def build_execution_order(self) -> list[list[str]]:
        """Return parallelizable groups respecting dependencies."""

# sync/conflict.py
class ConflictResolver:
    async def classify(self, conflict: MergeConflict) -> str:
        """trivial | mechanical | semantic | structural"""
    async def auto_resolve(self, conflict: MergeConflict) -> str | None:
        """Attempt auto-resolution. Returns merged content or None."""
```

### 5. Forge Labs — `forge/labs.py`

```python
class ForgeLabs:
    """A/B testing for code. Run competing implementations in parallel."""

    async def create_experiment(self, name: str,
                                branches: list[BranchConfig]) -> Experiment:
        """Create git worktrees for each branch."""

    async def run_experiment(self, experiment_id: str) -> ExperimentResult:
        """Execute all branches in parallel, score each."""

    async def score_branch(self, branch: str) -> BranchScore:
        """Build success, test pass rate, performance, code quality."""

    async def promote_winner(self, experiment_id: str) -> None:
        """Merge winning branch, delete losers."""
```

### 6. Refiner — `refiner/`

```python
# refiner/engine.py
class RefinerEngine:
    """Autonomous optimization. Scans → detects → plans → fixes."""

    detectors: list[BaseDetector]

    async def scan(self) -> list[Optimization]:
        """Run all detectors, return prioritized list of optimizations."""

    async def execute_safe(self, optimization: Optimization) -> OptResult:
        """
        1. Create checkpoint (recovery point)
        2. Apply optimization
        3. Run tests
        4. If tests pass → keep changes
        5. If tests fail → rollback to checkpoint
        """

# refiner/detectors/performance.py
class PerformanceDetector:
    async def detect(self) -> list[Optimization]:
        """Find N+1 queries, sync blocking, missing indexes, bundle bloat."""

# refiner/detectors/architecture.py
class ArchitectureDetector:
    async def detect(self) -> list[Optimization]:
        """Find dead code, god classes, circular deps, duplicate abstractions."""

# refiner/detectors/code_quality.py
class CodeQualityDetector:
    async def detect(self) -> list[Optimization]:
        """Find missing error handling, missing validation, missing tests."""
```

### 7. Distiller — `distiller/`

```python
# distiller/engine.py
class DistillerEngine:
    """Knowledge compression. Keeps memory lean and relevant."""

    async def run_compression_cycle(self) -> CompressionReport:
        """
        1. Scan all memories (count, size, age, access frequency)
        2. Identify candidates for summarization, compaction, pruning
        3. Execute compressions
        4. Verify no knowledge loss (sample queries before/after)
        5. Return report
        """

# distiller/summarizer.py
class Summarizer:
    async def summarize(self, memory: MemoryEntry) -> MemoryEntry:
        """Compress verbose memory into dense summary using LLM."""

# distiller/compactor.py
class Compactor:
    async def compact_group(self, memories: list[MemoryEntry]) -> MemoryEntry:
        """Merge multiple related memories into one consolidated entry."""

# distiller/pruner.py
class Pruner:
    async def find_duplicates(self, threshold: float = 0.95) -> list[list[str]]
    async def find_stale(self, cortex: CortexEngine) -> list[str]:
        """Memories referencing deleted files/symbols."""
    async def prune(self, memory_ids: list[str], archive: bool = True) -> int

# distiller/tiering.py
class TieringManager:
    async def evaluate_tiers(self) -> list[TierAction]:
        """Determine which memories should move between hot/warm/cold/frozen."""
    async def execute_tier_moves(self, actions: list[TierAction]) -> int
```

### 8. Ledger — `ledger/`

```python
# ledger/tracker.py
class CostTracker:
    """Tracks all resource consumption."""

    async def record_inference(self, event: InferenceEvent) -> None:
        """Record tokens used, model, agent, task, latency."""

    async def record_compute(self, event: ComputeEvent) -> None:
        """Record GPU-hours, CPU-hours, VRAM usage."""

    async def get_session_summary(self) -> SessionCostSummary
    async def get_task_cost(self, task_id: str) -> TaskCost
    async def get_model_efficiency(self) -> dict[str, ModelEfficiency]

# ledger/budget.py
class BudgetEnforcer:
    async def check_budget(self) -> BudgetStatus:
        """Check if any budget limits are approaching/exceeded."""
    async def enforce(self, status: BudgetStatus) -> BudgetAction:
        """warn | pause | continue"""

# ledger/reports.py
class CostReporter:
    async def generate_optimization_suggestions(self) -> list[CostSuggestion]:
        """Analyze patterns, suggest model downgrades, retry reductions, etc."""
    async def export_csv(self, path: str) -> None
```

---

## Phase 3 Build Order (6 weeks)

```
Week 1-2: Sentinel
  ├── sentinel/style.py          — Style profile learning
  ├── sentinel/architecture.py   — Drift detection (uses Cortex)
  ├── sentinel/naming.py         — Vocabulary governance
  ├── sentinel/duplication.py    — Duplicate detection
  ├── sentinel/engine.py         — SentinelEngine daemon
  └── tests

Week 3-4: Governance + Trust
  ├── governance/policy.py       — Policy loader/evaluator
  ├── governance/domains/*.py    — Security, access control, quality gates
  ├── governance/engine.py       — GovernanceEngine
  ├── governance/audit.py        — Audit trail
  ├── trust/scorer.py            — 4-dimension trust scoring
  ├── trust/reputation.py        — Agent reputation tracker
  ├── trust/automation.py        — Trust-driven decisions
  └── tests

Week 5-6: Integration
  ├── Wire Sentinel into orchestrator (check every output)
  ├── Wire Governance into tool execution (check every action)
  ├── Wire Trust into merge decisions
  ├── Forge validator integration
  └── Full pipeline tests with quality enforcement
```

## Phase 4 Build Order (8 weeks)

```
Week 1-2: Sync
  ├── sync/lock_manager.py
  ├── sync/changeset.py
  ├── sync/intent.py
  ├── sync/conflict.py
  ├── sync/commit_order.py
  └── tests (parallel worker conflict scenarios)

Week 3-4: Forge Labs + Refiner
  ├── forge/labs.py              — Experiment branching
  ├── forge/scorer.py            — Branch scoring
  ├── forge/promotion.py         — Winner promotion
  ├── refiner/detectors/*.py     — All 5 detector types
  ├── refiner/engine.py          — RefinerEngine
  ├── refiner/optimizer.py       — Safe execution with rollback
  └── tests

Week 5-6: Distiller + Ledger
  ├── distiller/summarizer.py
  ├── distiller/compactor.py
  ├── distiller/pruner.py
  ├── distiller/tiering.py
  ├── distiller/engine.py
  ├── ledger/tracker.py
  ├── ledger/budget.py
  ├── ledger/reports.py
  └── tests

Week 7-8: Integration
  ├── Sync → Orchestrator (locking during parallel execution)
  ├── Distiller → Memory (automatic compression)
  ├── Ledger → every inference call (automatic tracking)
  ├── Refiner → scheduled background runs
  ├── 15+ parallel worker stress test
  └── Full pipeline tests
```

---

**Next: Part 5 — Phase 5 & 6 (Plugins, Blueprints, Cluster, Studio, Autonomous)**
