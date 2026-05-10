# Galaxy Implementation Guide — Part 3: Phase 2 (Memory, Cortex, Vault)

---

## 1. Memory System — `memory/`

### `memory/types.py`
```python
class MemoryLevel(str, Enum):
    GLOBAL = "global"          # Cross-project knowledge
    WORKSPACE = "workspace"    # Project-specific
    DOMAIN = "domain"          # Domain-scoped (backend, frontend)
    TASK = "task"              # Task-specific context
    AGENT = "agent"            # Agent personal notes

class MemoryType(str, Enum):
    STRUCTURED = "structured"  # Architecture, decisions, configs (markdown)
    SEMANTIC = "semantic"      # Embeddings for similarity search
    GRAPH = "graph"            # Entity relationships

@dataclass
class MemoryEntry:
    memory_id: str
    level: MemoryLevel
    type: MemoryType
    title: str
    content: str
    tags: list[str]
    metadata: dict             # created_by, task_id, domain, etc.
    embedding: list[float] | None  # Vector for semantic search
    access_count: int = 0
    created_at: datetime
    updated_at: datetime
    accessed_at: datetime | None
```

### `memory/manager.py`
```python
class MemoryManager:
    store: MemoryStore           # File-based persistence
    vector_store: VectorStore    # Embedding index
    embedding_model: EmbeddingModel

    async def store_memory(
        self, level: MemoryLevel, type: MemoryType,
        title: str, content: str, tags: list[str] = None
    ) -> str:
        """
        1. Create MemoryEntry
        2. Generate embedding (if semantic type)
        3. Save to file store (.galaxy/memory/{level}/{id}.md)
        4. Index in vector store
        5. Publish MEMORY_CREATED event
        6. Return memory_id
        """

    async def retrieve(self, memory_id: str) -> MemoryEntry:
        """Get specific memory by ID. Increment access_count."""

    async def search(
        self, query: str, level: MemoryLevel = None,
        tags: list[str] = None, limit: int = 10
    ) -> list[MemoryEntry]:
        """
        1. Generate query embedding
        2. Vector similarity search (filtered by level/tags)
        3. Return top-K results ranked by relevance
        """

    async def search_structured(
        self, level: MemoryLevel, tags: list[str]
    ) -> list[MemoryEntry]:
        """Non-semantic search by level + tags."""

    async def get_context_for_agent(self, agent: BaseAgent) -> list[MemoryEntry]:
        """
        Assemble relevant memories for an agent:
        - Architecture decisions (workspace level)
        - Domain patterns (domain level)
        - Task-specific context (task level)
        Respects context window limits.
        """

    async def update(self, memory_id: str, content: str) -> None
    async def delete(self, memory_id: str) -> None
    def get_stats(self) -> MemoryStats
```

### `memory/store.py`
```python
class MemoryStore:
    """File-based memory persistence using markdown files with frontmatter."""

    base_path: str  # .galaxy/memory/

    # File format:
    # .galaxy/memory/workspace/arch_decisions_001.md
    # ---
    # id: mem_abc123
    # level: workspace
    # type: structured
    # tags: [architecture, database]
    # created_at: 2026-05-10
    # ---
    # # Database Architecture Decision
    # We chose PostgreSQL because...

    async def save(self, entry: MemoryEntry) -> str
    async def load(self, memory_id: str) -> MemoryEntry
    async def list_all(self, level: MemoryLevel = None) -> list[MemoryEntry]
    async def delete(self, memory_id: str) -> None
```

### `memory/vector_store.py`
```python
class VectorStore:
    """In-process vector similarity search using numpy."""

    embeddings: dict[str, np.ndarray]  # memory_id → embedding vector

    async def add(self, memory_id: str, embedding: list[float]) -> None
    async def search(self, query_embedding: list[float], top_k: int = 10,
                     filter_ids: set[str] = None) -> list[tuple[str, float]]:
        """Cosine similarity search. Returns (memory_id, score) pairs."""
    async def remove(self, memory_id: str) -> None
    async def save_index(self, path: str) -> None
    async def load_index(self, path: str) -> None
```

### `memory/embeddings.py`
```python
class EmbeddingModel:
    """Generate embeddings using local model (Ollama) or sentence-transformers."""

    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector for text."""

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding generation."""
```

---

## 2. Cortex — Semantic Code Intelligence — `cortex/`

### `cortex/engine.py`
```python
class CortexEngine:
    """Semantic code intelligence. Builds and queries code graphs."""

    parser: CodeParser            # tree-sitter
    ast_graph: ASTGraph
    symbol_graph: SymbolGraph
    import_graph: ImportGraph
    call_graph: CallGraph

    async def index_project(self, project_path: str) -> IndexReport:
        """
        Full project scan:
        1. Walk all source files
        2. Parse each file with tree-sitter
        3. Extract symbols (functions, classes, variables)
        4. Extract imports
        5. Build call graph (static analysis)
        6. Store in graph structures
        """

    async def index_file(self, file_path: str) -> None:
        """Incremental: re-index a single changed file."""

    async def query(self, query_type: str, **params) -> QueryResult:
        """
        Supported queries:
        - "what_imports": file X → list of files that import from X
        - "imported_by": symbol Y → list of files importing Y
        - "callers_of": function Z → list of call sites
        - "dependencies_of": file X → transitive dependency tree
        - "symbols_in": file X → all symbols defined in X
        - "blast_radius": file X → all files affected if X changes
        """

    def get_stats(self) -> CortexStats
    def to_snapshot(self) -> dict:
        """Serialize for Vault checkpoint."""
```

### `cortex/parser.py`
```python
class CodeParser:
    """Multi-language parser using tree-sitter."""

    # Supported languages (Phase 2):
    LANGUAGES = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".jsx": "javascript", ".tsx": "typescript",
        ".go": "go", ".rs": "rust", ".java": "java",
        ".rb": "ruby", ".php": "php", ".c": "c", ".cpp": "cpp",
    }

    def parse_file(self, file_path: str) -> ParseResult:
        """
        1. Detect language from extension
        2. Read file contents
        3. Parse with tree-sitter
        4. Extract: functions, classes, imports, exports, variables
        5. Return structured ParseResult
        """

@dataclass
class ParseResult:
    file_path: str
    language: str
    functions: list[FunctionDef]    # name, params, return_type, line range
    classes: list[ClassDef]         # name, methods, properties, line range
    imports: list[ImportDef]        # module, symbols, alias
    exports: list[ExportDef]        # name, type
    variables: list[VariableDef]    # name, type, scope
```

### `cortex/graphs/symbol_graph.py`
```python
class SymbolGraph:
    """Index of all symbols in the project."""

    symbols: dict[str, SymbolInfo]  # qualified_name → info

    def add_symbol(self, symbol: SymbolInfo) -> None
    def get_symbol(self, name: str) -> SymbolInfo | None
    def find_symbols(self, pattern: str) -> list[SymbolInfo]
    def get_symbols_in_file(self, file_path: str) -> list[SymbolInfo]
    def get_dependents(self, symbol_name: str) -> list[SymbolInfo]:
        """Who uses this symbol?"""

@dataclass
class SymbolInfo:
    name: str
    qualified_name: str        # module.ClassName.method_name
    kind: str                  # function | class | variable | constant
    file_path: str
    line_start: int
    line_end: int
    params: list[str] | None   # For functions
    return_type: str | None    # For functions
    parent: str | None         # Enclosing class/module
```

### `cortex/graphs/import_graph.py`
```python
class ImportGraph:
    """Tracks import relationships between files."""

    # Adjacency list: file → list of (imported_file, imported_symbols)
    edges: dict[str, list[ImportEdge]]

    def add_import(self, from_file: str, to_file: str, symbols: list[str]) -> None
    def get_imports(self, file_path: str) -> list[ImportEdge]
    def get_importers(self, file_path: str) -> list[str]:
        """Who imports from this file? (reverse lookup)"""
    def get_dependency_tree(self, file_path: str) -> dict:
        """Full transitive dependency tree."""
    def detect_circular(self) -> list[list[str]]:
        """Find circular import chains."""
```

---

## 3. Vault (Full) — `vault/`

### `vault/checkpoint.py` (expanded from Phase 1)
```python
class VaultEngine:
    """Full persistence: checkpoints, crash recovery, pause/resume, model independence."""

    async def create_checkpoint(self, trigger: str) -> Checkpoint:
        """
        Full checkpoint includes:
        - task_graph: all tasks, statuses, DAG edges
        - agent_states: all agents, roles (NOT model-specific state)
        - memory_state: memory file hashes, index version
        - scheduler_state: loaded models, VRAM allocation, queue
        - cortex_state: index version, files indexed
        - terminal_sessions: tmux session → agent mapping
        - git_state: current HEAD, branch, uncommitted changes
        """

    async def create_incremental(self, last_full: str) -> Checkpoint:
        """Only save what changed since last full checkpoint."""

    async def load_checkpoint(self, checkpoint_id: str = None) -> Checkpoint:
        """Load specific or latest. Handles both full and incremental."""

    async def recover_from_crash(self) -> RecoveryReport:
        """
        1. Load last valid checkpoint
        2. Replay events from WAL since checkpoint
        3. Identify incomplete tasks → mark for retry
        4. Identify partial file writes → git checkout to discard
        5. Reattach tmux sessions
        6. Return recovery report
        """

@dataclass
class Checkpoint:
    checkpoint_id: str
    timestamp: datetime
    trigger: str
    version: str
    is_incremental: bool
    parent_checkpoint: str | None  # For incremental
    task_graph: dict
    agent_states: list[dict]
    memory_state: dict
    scheduler_state: dict
    cortex_state: dict
    terminal_sessions: list[dict]
    git_state: dict
```

### `vault/wal.py`
```python
class WriteAheadLog:
    """Event log that survives crashes. Written before actions execute."""

    log_path: str  # .galaxy/wal/events.log

    async def append(self, event: Event) -> None:
        """Append event to WAL with fsync (crash-safe)."""

    async def replay_since(self, timestamp: datetime) -> list[Event]:
        """Read all events after given timestamp."""

    async def truncate_before(self, timestamp: datetime) -> None:
        """Remove events before timestamp (after checkpoint)."""
```

---

## 4. Phase 2 Build Order

```
Week 1-2: Memory Foundation
  ├── memory/types.py            — Data models
  ├── memory/store.py            — File-based persistence
  ├── memory/embeddings.py       — Ollama embedding integration
  ├── memory/vector_store.py     — Numpy cosine similarity
  ├── memory/manager.py          — MemoryManager API
  ├── memory/hierarchy.py        — 5-level scoping
  └── tests

Week 3-4: Cortex Foundation
  ├── cortex/parser.py           — tree-sitter integration
  ├── cortex/graphs/ast_graph.py
  ├── cortex/graphs/symbol_graph.py
  ├── cortex/graphs/import_graph.py
  ├── cortex/graphs/call_graph.py
  ├── cortex/query.py            — Query API
  ├── cortex/engine.py           — CortexEngine (ties graphs together)
  └── tests

Week 5-6: Full Vault
  ├── vault/wal.py               — Write-ahead log
  ├── vault/checkpoint.py        — Full + incremental checkpoints
  ├── vault/recovery.py          — Crash recovery
  ├── vault/snapshot.py          — State serializer
  ├── Integrate memory state into checkpoints
  ├── Integrate cortex state into checkpoints
  ├── Terminal reattach on resume
  └── tests (crash simulation, pause/resume, model swap)

Week 7-8: Integration
  ├── Memory → Agent integration (context assembly)
  ├── Cortex → Orchestrator integration (dependency-aware planning)
  ├── Cortex → Scribe integration hooks (diagram data export for Phase 3)
  ├── Memory → Compass integration hooks (intent stored as foundational memory)
  ├── Vault → Kernel integration (automatic checkpointing)
  ├── Full pipeline test with memory persistence
  ├── Crash recovery end-to-end test
  └── Model swap on resume test
```

---

> [!NOTE]
> **Subsystems built on top of Phase 2 foundations:**
> - **Galaxy Scribe (Phase 3)** — Uses Cortex's code graph to auto-generate architecture diagrams, module docs, and API references. Memory stores doc style preferences.
> - **Galaxy Compass (Phase 5-6)** — Intent declarations stored in Memory as foundational context. Cortex's code intelligence validates intent alignment (e.g., detects security-priority violations in code patterns).

---

**Next: Part 4 — Phase 3 (Sentinel, Governance, Trust, Scribe) + Phase 4 (Sync, Refiner, Distiller, Ledger)**
