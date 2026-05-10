# Galaxy Implementation Guide — Part 2: Phase 1 Implementation

> Phase 1 = Foundation. Every class, interface, and method needed to run Galaxy end-to-end.

---

## 1. Galaxy Core — `core/kernel.py`

```python
class GalaxyKernel:
    """The main entry point. Boots all subsystems, manages lifecycle."""

    config: GalaxyConfig
    event_bus: EventBus
    agent_registry: AgentRegistry
    tool_registry: ToolRegistry
    model_router: ModelRouter
    scheduler: Scheduler
    orchestrator: Orchestrator
    terminal_manager: TerminalManager
    vault: VaultEngine

    async def boot(self, project_path: str, user_config: dict) -> None:
        """
        1. Load config (galaxy.config.yaml + defaults + env vars)
        2. Initialize event bus (in-memory default, Redis if configured)
        3. Initialize database (SQLite default, PostgreSQL if configured)
        4. Run migrations (Alembic)
        5. Initialize tool registry (discover + register built-in tools)
        6. Initialize model router (detect providers, probe VRAM)
        7. Initialize terminal manager (auto-detect/install tmux)
        8. Initialize vault (check for crash marker, recover if needed)
        9. Initialize scheduler (VRAM budget, parallelism limits)
        10. Initialize orchestrator (task graph engine)
        11. Start Studio web dashboard (FastAPI + WebSocket on port 8420)
        12. Auto-open browser to Galaxy Studio
        13. Publish event: GALAXY_BOOTED
        14. Write crash marker file
        """
        # Studio starts WITH Galaxy — no separate command needed
        # Both CLI output AND web dashboard are active simultaneously

    async def run(self, user_request: str) -> ProjectResult:
        """
        1. Create MasterAgent
        2. Master analyzes request → produces architecture plan
        3. Master decomposes → creates Domain tasks
        4. Orchestrator builds task DAG
        5. Scheduler assigns tasks to agents (VRAM-aware)
        6. Executor runs tasks in parallel (respecting DAG deps)
        7. Validation pipeline checks outputs
        8. Escalation chain handles failures (Worker → Domain → Master)
        9. Return results
        """

    async def pause(self) -> str:
        """Graceful pause → checkpoint → return checkpoint_id."""

    async def resume(self, checkpoint_id: str = None) -> None:
        """Load checkpoint → restore state → continue execution."""

    async def shutdown(self) -> None:
        """Stop Studio server → checkpoint → remove crash marker → stop."""
```

---

## 2. Configuration — `core/config.py`

```python
from pydantic_settings import BaseSettings
from pydantic import BaseModel

class ModelConfig(BaseModel):
    """Universal model configuration — works with ANY provider."""
    provider: str = "ollama"
    # Supported providers:
    #   "ollama"         — Local Ollama server (default)
    #   "openai"         — OpenAI API (GPT-4o, GPT-4, etc.)
    #   "anthropic"      — Anthropic API (Claude 4, Sonnet, Haiku)
    #   "google"         — Google Gemini API
    #   "groq"           — Groq cloud (fast inference)
    #   "deepseek"       — DeepSeek API
    #   "vllm"           — Self-hosted vLLM server
    #   "openai_compat"  — Any OpenAI-compatible API (LM Studio, Jan, etc.)
    #   "litellm"        — LiteLLM universal proxy (routes to 100+ providers)

    model: str = "qwen2.5-coder:7b"
    temperature: float = 0.3
    max_tokens: int = 8192
    base_url: str | None = None    # Custom endpoint URL (required for vllm, openai_compat)
    api_key: str | None = None     # API key (from config or env var)
    api_key_env: str | None = None # Environment variable name for API key
    headers: dict[str, str] | None = None  # Custom headers (auth tokens, etc.)
    timeout_seconds: int = 120
    retry_count: int = 3
    supports_tools: bool = True    # Whether this model supports function calling
    supports_vision: bool = False  # Whether this model supports image input
    context_window: int = 8192     # Max context window size

    def resolve_api_key(self) -> str | None:
        """Get API key from config, env var, or None for local."""
        if self.api_key:
            return self.api_key
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return None

class FallbackConfig(BaseModel):
    """Fallback model when primary model fails."""
    enabled: bool = False
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key_env: str = "OPENAI_API_KEY"
    trigger_after_failures: int = 2  # Escalate after N consecutive failures
    base_url: str | None = None

class TaskRoutingRule(BaseModel):
    """Route specific task types to specific models."""
    task_type: str              # architecture | code_generation | testing | security
    complexity: str | None = None  # simple | complex
    model: ModelConfig

class ModelsConfig(BaseModel):
    """Complete model configuration for all tiers."""
    master: ModelConfig          # Strongest model (reasoning, architecture)
    domain: ModelConfig          # Medium model (planning, coordination)
    worker: ModelConfig          # Fast model (code generation)
    embedding: ModelConfig       # Embedding model (memory search)
    fallback: FallbackConfig = FallbackConfig()  # Fallback when primary fails
    routing_rules: list[TaskRoutingRule] = []     # Task-specific model overrides

class AgentLimits(BaseModel):
    max_domain_agents: int = 10
    max_workers_per_domain: int = 50
    max_retry_loops: int = 5
    max_recursion_depth: int = 3
    idle_timeout_seconds: int = 300

class SchedulerConfig(BaseModel):
    mode: str = "balanced"        # speed | balanced | quality
    max_parallel_workers: int | str = "auto"
    vram_reserve_mb: int = 512

class VaultConfig(BaseModel):
    checkpoint_interval_minutes: int = 5
    crash_recovery: bool = True
    max_snapshots: int = 10

class GalaxyConfig(BaseSettings):
    project_name: str = ""
    workspace: str = "."
    models: ModelsConfig         # All model configurations
    scheduler: SchedulerConfig
    agents: AgentLimits
    vault: VaultConfig
    database_url: str = "sqlite+aiosqlite:///.galaxy/galaxy.db"
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"

    @classmethod
    def load(cls, project_path: str) -> "GalaxyConfig":
        """Load from galaxy.config.yaml → env vars → defaults."""
```

### Model Configuration Examples (galaxy.config.yaml)

```yaml
# Example 1: Fully Local (no internet needed)
models:
  master:  { provider: ollama, model: qwen2.5-coder:14b }
  domain:  { provider: ollama, model: qwen2.5-coder:14b }
  worker:  { provider: ollama, model: qwen2.5-coder:7b }
  embedding: { provider: ollama, model: nomic-embed-text }

# Example 2: Fully Cloud
models:
  master:  { provider: openai, model: gpt-4o, api_key_env: OPENAI_API_KEY }
  domain:  { provider: anthropic, model: claude-sonnet-4-20250514, api_key_env: ANTHROPIC_API_KEY }
  worker:  { provider: groq, model: llama-3.1-70b, api_key_env: GROQ_API_KEY }
  embedding: { provider: openai, model: text-embedding-3-small, api_key_env: OPENAI_API_KEY }

# Example 3: Hybrid (Best of both)
models:
  master:  { provider: openai, model: gpt-4o, api_key_env: OPENAI_API_KEY }
  domain:  { provider: ollama, model: qwen2.5-coder:14b }
  worker:  { provider: ollama, model: qwen2.5-coder:7b }
  embedding: { provider: ollama, model: nomic-embed-text }
  fallback:
    enabled: true
    provider: openai
    model: gpt-4o
    api_key_env: OPENAI_API_KEY
    trigger_after_failures: 2

# Example 4: Self-Hosted vLLM / TGI
models:
  master:
    provider: openai_compat
    model: deepseek-coder-v2
    base_url: http://gpu-server:8000/v1
  worker:
    provider: vllm
    model: codellama-34b
    base_url: http://inference-cluster:8080

# Example 5: LM Studio / Jan / LocalAI (OpenAI-compatible)
models:
  master:
    provider: openai_compat
    model: deepseek-coder-v3
    base_url: http://localhost:1234/v1  # LM Studio
  worker:
    provider: openai_compat
    model: qwen2.5-coder-7b
    base_url: http://localhost:1337/v1  # Jan

# Example 6: Task-Based Routing (smart routing)
models:
  master:  { provider: ollama, model: qwen2.5-coder:14b }
  domain:  { provider: ollama, model: qwen2.5-coder:14b }
  worker:  { provider: ollama, model: qwen2.5-coder:7b }
  embedding: { provider: ollama, model: nomic-embed-text }
  routing_rules:
    - task_type: security_review
      model: { provider: openai, model: gpt-4o, api_key_env: OPENAI_API_KEY }
    - task_type: code_generation
      complexity: complex
      model: { provider: anthropic, model: claude-sonnet-4-20250514, api_key_env: ANTHROPIC_API_KEY }
    - task_type: test_generation
      model: { provider: ollama, model: qwen2.5-coder:3b }  # Fast & cheap for tests

# Example 7: Google Gemini
models:
  master:  { provider: google, model: gemini-2.5-pro, api_key_env: GOOGLE_API_KEY }
  worker:  { provider: google, model: gemini-2.5-flash, api_key_env: GOOGLE_API_KEY }

# Example 8: DeepSeek
models:
  master:  { provider: deepseek, model: deepseek-coder, api_key_env: DEEPSEEK_API_KEY }
  worker:  { provider: deepseek, model: deepseek-coder, api_key_env: DEEPSEEK_API_KEY }

# Example 9: LiteLLM Proxy (routes to ANY provider)
models:
  master:
    provider: litellm
    model: openai/gpt-4o          # LiteLLM format: provider/model
    base_url: http://localhost:4000
  worker:
    provider: litellm
    model: ollama/qwen2.5-coder:7b
    base_url: http://localhost:4000
```

---

## 3. Event Bus — `events/bus.py`

```python
class EventBus:
    """Redis-backed pub/sub event bus. Falls back to in-memory for dev."""

    async def publish(self, topic: str, event: Event) -> None:
        """Publish event to topic. All subscribers receive it."""

    async def subscribe(self, topic: str, handler: Callable) -> str:
        """Subscribe to topic. Returns subscription_id."""

    async def unsubscribe(self, subscription_id: str) -> None:
        """Remove subscription."""

    async def request_reply(self, topic: str, event: Event, timeout: float) -> Event:
        """Publish and wait for response (for synchronous coordination)."""

# Event topics (events/topics.py):
GALAXY_BOOTED = "galaxy.booted"
TASK_CREATED = "task.created"
TASK_ASSIGNED = "task.assigned"
TASK_STARTED = "task.started"
TASK_COMPLETED = "task.completed"
TASK_FAILED = "task.failed"
AGENT_SPAWNED = "agent.spawned"
AGENT_TERMINATED = "agent.terminated"
FILE_WRITTEN = "file.written"
FILE_CHANGED = "file.changed"
CHECKPOINT_CREATED = "checkpoint.created"
VALIDATION_PASSED = "validation.passed"
VALIDATION_FAILED = "validation.failed"

# Event dataclass (events/events.py):
@dataclass
class Event:
    id: str                    # UUID
    topic: str
    timestamp: datetime
    source: str                # agent_id or subsystem name
    payload: dict[str, Any]
```

---

## 4. Agents — `agents/base.py`

```python
class BaseAgent(ABC):
    """Abstract base for all agents (Master, Domain, Worker)."""

    agent_id: str              # Unique ID (uuid4)
    role: str                  # "master" | "backend_domain" | "frontend_worker" etc.
    tier: AgentTier            # MASTER | DOMAIN | WORKER
    status: AgentStatus        # IDLE | WORKING | PAUSED | TERMINATED
    model_config: ModelConfig  # Which model this agent uses
    workspace: str             # Assigned working directory
    tools: list[str]           # Allowed tool names
    created_at: datetime
    task_history: list[str]    # Completed task IDs

    @abstractmethod
    async def execute(self, task: Task) -> TaskResult:
        """Execute a task. Implemented by each tier."""

    async def invoke_llm(self, messages: list[dict], tools: list[dict] = None) -> str:
        """Call model via ModelRouter. Handles retries, tool calling."""

    async def use_tool(self, tool_name: str, params: dict) -> ToolResult:
        """Execute a tool through the ToolRegistry (permission-checked)."""

    def to_checkpoint(self) -> dict:
        """Serialize agent state for Vault checkpoint."""

    @classmethod
    def from_checkpoint(cls, data: dict) -> "BaseAgent":
        """Restore agent from checkpoint data."""
```

### `agents/master.py`
```python
class MasterAgent(BaseAgent):
    tier = AgentTier.MASTER
    tools = ["FileRead", "Search", "Tree", "Git", "Terminal"]

    async def execute(self, task: Task) -> TaskResult:
        """
        Master execution loop:
        1. Analyze user request
        2. Read existing codebase (if any) using tools
        3. Create architecture plan (stored in memory)
        4. Decompose into domains
        5. For each domain: create DomainTask with:
           - Domain description
           - Assigned files/directories
           - Interfaces/contracts
           - Dependencies on other domains
        6. Return list of DomainTasks
        """
```

### `agents/domain.py`
```python
class DomainAgent(BaseAgent):
    tier = AgentTier.DOMAIN
    domain: str                # "backend" | "frontend" | "database" etc.
    tools = ["FileRead", "FileWrite", "FileEdit", "Search", "Terminal", "Git"]

    async def execute(self, task: Task) -> TaskResult:
        """
        Domain execution loop:
        1. Receive domain task from Master
        2. Analyze domain scope
        3. Break into worker tasks with:
           - Exact file path to create/modify
           - Exact function/class signature
           - Input/output contracts
           - Dependencies
        4. Validate worker outputs
        5. Run domain-level tests
        6. Report results to orchestrator
        """
```

### `agents/worker.py`
```python
class WorkerAgent(BaseAgent):
    tier = AgentTier.WORKER
    tools = ["FileRead", "FileWrite", "FileEdit", "Search", "Terminal"]

    async def execute(self, task: Task) -> TaskResult:
        """
        Worker execution loop:
        1. Receive scoped task (one file, one function, one component)
        2. Read context files (only what's provided)
        3. Generate code
        4. Write to file using FileWrite/FileEdit tool
        5. Run task-specific tests (if any)
        6. Return result with files_produced, test_results
        """
```

---

## 5. Task Graph — `orchestrator/task.py` + `task_graph.py`

```python
# orchestrator/task.py
@dataclass
class Task:
    task_id: str
    title: str
    description: str
    tier: AgentTier              # Which tier handles this
    domain: str | None           # Domain name (for domain/worker tasks)
    status: TaskStatus           # idle → planning → generating → validating → completed
    assigned_agent: str | None
    parent_task: str | None      # Parent task ID
    dependencies: list[str]      # Task IDs that must complete first
    context_files: list[str]     # Files this task can read
    target_files: list[str]      # Files this task will create/modify
    priority: int                # 0 = highest
    progress: int                # 0-100
    result: TaskResult | None
    retry_count: int = 0
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

class TaskStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    GENERATING = "generating"
    VALIDATING = "validating"
    TESTING = "testing"
    BLOCKED = "blocked"
    FAILED = "failed"
    RETRYING = "retrying"
    COMPLETED = "completed"

@dataclass
class TaskResult:
    success: bool
    files_produced: list[str]
    files_modified: list[str]
    test_results: TestResults | None
    error: str | None
    duration_seconds: float
    tokens_used: int

# orchestrator/task_graph.py
class TaskGraph:
    """DAG engine for task dependency management."""

    tasks: dict[str, Task]
    edges: list[tuple[str, str]]   # (from_id, to_id) = dependency

    def add_task(self, task: Task) -> None
    def add_dependency(self, from_id: str, to_id: str) -> None
    def get_ready_tasks(self) -> list[Task]:
        """Return tasks whose ALL dependencies are completed."""
    def get_critical_path(self) -> list[Task]:
        """Return longest dependency chain (bottleneck)."""
    def mark_completed(self, task_id: str, result: TaskResult) -> None
    def mark_failed(self, task_id: str, error: str) -> None
    def get_blocked_tasks(self) -> list[Task]
    def to_dict(self) -> dict:
        """Serialize for checkpoint."""
    @classmethod
    def from_dict(cls, data: dict) -> "TaskGraph"
```

---

## 6. Tools — `tools/base.py`

```python
class BaseTool(ABC):
    name: str                    # Unique tool name
    description: str             # For LLM to understand what it does
    input_schema: dict           # JSON Schema for parameters
    allowed_tiers: list[AgentTier]  # Which tiers can use this
    requires_permission: bool = True

    @abstractmethod
    async def execute(self, params: dict, agent: BaseAgent, sandbox: Sandbox) -> ToolResult:
        """Execute the tool with given parameters."""

    def validate_input(self, params: dict) -> bool:
        """Validate params against input_schema."""

@dataclass
class ToolResult:
    success: bool
    output: str
    error: str | None = None
    files_changed: list[str] | None = None

# tools/registry.py
class ToolRegistry:
    tools: dict[str, BaseTool]

    def register(self, tool: BaseTool) -> None
    def get(self, name: str) -> BaseTool
    def get_for_tier(self, tier: AgentTier) -> list[BaseTool]
    def get_tool_schemas(self, tier: AgentTier) -> list[dict]:
        """Return OpenAI-compatible tool/function schemas for LLM."""
```

### Built-in Tools (Phase 1):

| Tool | File | Description |
|------|------|-------------|
| `FileRead` | `builtin/file_read.py` | Read file contents (with line range) |
| `FileWrite` | `builtin/file_write.py` | Create new file with content |
| `FileEdit` | `builtin/file_edit.py` | Replace specific content in existing file |
| `Terminal` | `builtin/terminal.py` | Execute shell command in tmux session |
| `Search` | `builtin/search.py` | ripgrep search across codebase |
| `Git` | `builtin/git.py` | Git operations (commit, branch, diff, log) |
| `Tree` | `builtin/tree.py` | List directory structure |

---

## 7. Model Router — `models/router.py`

```python
class ModelRouter:
    """Routes inference requests to the best available provider.
    Supports local, cloud, self-hosted, and custom model sources."""

    providers: dict[str, BaseProvider]  # provider_name → provider instance
    models_config: ModelsConfig        # Full model configuration
    vram_monitor: VRAMMonitor
    fallback_config: FallbackConfig

    async def infer(
        self,
        messages: list[dict],
        tier: AgentTier,
        tools: list[dict] | None = None,
        task_type: str | None = None,
    ) -> InferenceResult:
        """
        1. Check routing_rules for task_type-specific model override
        2. If no override → use tier's default model
        3. Get provider for that model
        4. Call provider.chat_completion(messages, tools)
        5. If FAILS and fallback enabled → retry with fallback model
        6. Track tokens used (for Ledger)
        7. Return result
        """

    async def infer_with_fallback(
        self, messages: list[dict], primary: ModelConfig,
        tools: list[dict] | None = None
    ) -> InferenceResult:
        """
        Try primary model → if fails N times → escalate to fallback.
        Fallback can be cloud model even if primary is local.
        """

    async def swap_model(self, tier: str, new_config: ModelConfig) -> None:
        """Hot-swap model for a tier. Called from Studio or CLI."""

    async def detect_available_models(self) -> list[ModelInfo]:
        """Query ALL registered providers for available models."""

    def get_vram_usage(self) -> VRAMReport:
        """Current VRAM allocation across loaded local models."""

    def get_model_for_task(self, tier: AgentTier, task_type: str = None) -> ModelConfig:
        """Resolve which model to use: routing_rules → tier default → fallback."""
```

### All Providers — `models/providers/`

```python
# models/providers/base.py
class BaseProvider(ABC):
    """Abstract base for all model providers."""
    name: str                          # Provider identifier
    supports_streaming: bool = True
    supports_tools: bool = True

    @abstractmethod
    async def chat_completion(
        self, model: str, messages: list[dict],
        tools: list[dict] | None, temperature: float = 0.3
    ) -> ProviderResponse

    @abstractmethod
    async def list_models(self) -> list[str]

    @abstractmethod
    async def is_available(self) -> bool

# ─── LOCAL PROVIDERS ───

# models/providers/ollama.py
class OllamaProvider(BaseProvider):
    """Local Ollama server. Default provider."""
    name = "ollama"
    base_url: str = "http://localhost:11434"
    # Uses: ollama Python client
    # Models: qwen2.5-coder, deepseek-coder-v2, codellama, etc.
    # VRAM: Managed by Ollama
    # Cost: FREE (local GPU)

    async def pull_model(self, model_name: str) -> None:
        """Pull new model from Ollama registry."""

    async def get_running_models(self) -> list[dict]:
        """Get currently loaded models with VRAM usage."""

# ─── CLOUD PROVIDERS ───

# models/providers/openai.py
class OpenAIProvider(BaseProvider):
    """OpenAI API — GPT-4o, GPT-4-turbo, o1, etc."""
    name = "openai"
    base_url: str = "https://api.openai.com/v1"
    # Uses: openai Python client
    # Auth: OPENAI_API_KEY env var

# models/providers/anthropic.py
class AnthropicProvider(BaseProvider):
    """Anthropic API — Claude 4, Sonnet, Haiku, etc."""
    name = "anthropic"
    # Uses: anthropic Python client
    # Auth: ANTHROPIC_API_KEY env var

# models/providers/google.py
class GoogleProvider(BaseProvider):
    """Google Gemini API — Gemini Pro, Flash, etc."""
    name = "google"
    # Uses: google-generativeai Python client
    # Auth: GOOGLE_API_KEY env var

# models/providers/groq.py
class GroqProvider(BaseProvider):
    """Groq cloud — ultra-fast inference."""
    name = "groq"
    base_url: str = "https://api.groq.com/openai/v1"
    # Uses: openai client (Groq is OpenAI-compatible)
    # Auth: GROQ_API_KEY env var

# models/providers/deepseek.py
class DeepSeekProvider(BaseProvider):
    """DeepSeek API — DeepSeek Coder, DeepSeek Chat."""
    name = "deepseek"
    base_url: str = "https://api.deepseek.com/v1"
    # Uses: openai client (DeepSeek is OpenAI-compatible)
    # Auth: DEEPSEEK_API_KEY env var

# ─── SELF-HOSTED PROVIDERS ───

# models/providers/vllm.py
class VLLMProvider(BaseProvider):
    """Self-hosted vLLM server. For custom fine-tuned or large models."""
    name = "vllm"
    # base_url set by user: http://your-gpu-server:8000
    # Uses: openai client (vLLM exposes OpenAI-compatible API)
    # Auth: Optional API key

# models/providers/openai_compat.py
class OpenAICompatProvider(BaseProvider):
    """ANY server that exposes OpenAI-compatible /v1/chat/completions.
    Works with: LM Studio, Jan, LocalAI, Tabby, text-gen-webui, TGI, etc."""
    name = "openai_compat"
    # base_url set by user: http://localhost:1234/v1
    # Uses: openai client with custom base_url
    # Auth: Optional

# ─── UNIVERSAL PROXY ───

# models/providers/litellm.py
class LiteLLMProvider(BaseProvider):
    """LiteLLM proxy — routes to 100+ providers via single API.
    Format: provider/model (e.g., 'openai/gpt-4o', 'anthropic/claude-3')"""
    name = "litellm"
    # base_url: http://localhost:4000 (LiteLLM proxy server)
    # Uses: openai client pointed at LiteLLM

# ─── PROVIDER REGISTRY ───

class ProviderRegistry:
    """Auto-discovers and manages all available providers."""

    _providers: dict[str, type[BaseProvider]] = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "groq": GroqProvider,
        "deepseek": DeepSeekProvider,
        "vllm": VLLMProvider,
        "openai_compat": OpenAICompatProvider,
        "litellm": LiteLLMProvider,
    }

    def get_provider(self, config: ModelConfig) -> BaseProvider:
        """Instantiate provider from config."""

    def register_custom(self, name: str, provider_class: type[BaseProvider]) -> None:
        """Register a custom provider (via Plugin SDK)."""

@dataclass
class InferenceResult:
    content: str
    tool_calls: list[dict] | None
    tokens_in: int
    tokens_out: int
    model: str
    provider: str
    latency_ms: int
    cost_usd: float | None     # Estimated cost (None for local)
```

---

## 8. Scheduler — `orchestrator/scheduler.py`

```python
class Scheduler:
    """VRAM-aware task scheduler. Decides what runs when and on which model."""

    config: SchedulerConfig
    vram_monitor: VRAMMonitor
    model_pool: ModelPool

    async def schedule(self, ready_tasks: list[Task]) -> list[Assignment]:
        """
        For each ready task:
        1. Determine required tier (master/domain/worker)
        2. Check if required model is loaded
        3. If not loaded and VRAM available → load model
        4. If VRAM full → queue task or evict least-used model
        5. Assign task to available agent slot
        6. Return list of assignments
        """

    def calculate_parallelism(self) -> int:
        """Based on VRAM: how many workers can run simultaneously."""

@dataclass
class Assignment:
    task: Task
    agent_id: str
    model: str
    priority: int

# models/vram.py
class VRAMMonitor:
    """Detects and monitors GPU VRAM usage."""

    def detect_gpus(self) -> list[GPUInfo]:
        """Use nvidia-smi / torch.cuda to detect GPUs."""

    def get_free_vram(self) -> int:
        """Free VRAM in MB across all GPUs."""

    def get_model_vram_estimate(self, model_name: str) -> int:
        """Estimate VRAM needed for a model (by parameter count)."""
```

---

## 9. Terminal Manager — `terminal/manager.py`

```python
class TerminalManager:
    """Manages tmux sessions for agent command execution."""

    server: libtmux.Server
    sessions: dict[str, TmuxSession]  # agent_id → session

    def create_session(self, agent_id: str, cwd: str) -> TmuxSession:
        """Create named tmux session for an agent."""

    def get_session(self, agent_id: str) -> TmuxSession | None:
        """Get existing session (survives Galaxy restarts)."""

    async def execute_command(
        self, agent_id: str, command: str, timeout: int = 60
    ) -> CommandResult:
        """
        1. Get or create tmux session for agent
        2. Send command to session
        3. Wait for output (with timeout)
        4. Parse and return result
        """

    def reattach_sessions(self, agent_terminal_map: dict) -> None:
        """On resume: reconnect agents to their existing tmux sessions."""

    def cleanup(self, agent_id: str) -> None:
        """Kill tmux session when agent terminates."""

@dataclass
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
```

---

## 10. Vault (Basic) — `vault/checkpoint.py`

```python
class VaultEngine:
    """Phase 1: Basic checkpointing. Phase 2: Full persistence."""

    async def create_checkpoint(self, trigger: str) -> Checkpoint:
        """
        Serialize current state:
        - Task graph (all tasks + statuses + DAG edges)
        - Agent registry (active agents, roles, assigned tasks)
        - Scheduler state (loaded models, VRAM allocation)
        Save to .galaxy/checkpoints/cp_{id}.json
        """

    async def load_checkpoint(self, checkpoint_id: str = None) -> Checkpoint:
        """Load specific or latest checkpoint."""

    def write_crash_marker(self) -> None:
        """Create .galaxy/runtime/crash_recovery_needed file."""

    def remove_crash_marker(self) -> None:
        """Delete crash marker on clean shutdown."""

    def check_crash_marker(self) -> bool:
        """Check if Galaxy crashed last time (marker exists)."""

    async def recover_from_crash(self) -> RecoveryReport:
        """
        1. Load last checkpoint
        2. Mark in-progress tasks for retry
        3. Discard partial file writes (git checkout)
        4. Return recovery report
        """

@dataclass
class Checkpoint:
    checkpoint_id: str
    timestamp: datetime
    trigger: str           # "task_completed" | "periodic" | "user_requested" | "shutdown"
    task_graph: dict
    agent_states: list[dict]
    scheduler_state: dict
```

---

## 11. Orchestrator — `orchestrator/orchestrator.py`

```python
class Orchestrator:
    """The main execution loop that ties everything together."""

    kernel: GalaxyKernel  # Reference to kernel for subsystem access
    task_graph: TaskGraph
    active_agents: dict[str, BaseAgent]

    async def execute_project(self, user_request: str) -> ProjectResult:
        """
        PHASE 1: PLANNING
        1. Spawn MasterAgent
        2. Master.execute(user_request) → architecture + domain tasks
        3. Build initial TaskGraph from Master's plan

        PHASE 2: DOMAIN PLANNING
        4. For each domain task (may be parallel if independent):
           a. Spawn DomainAgent
           b. DomainAgent.execute(domain_task) → worker tasks
           c. Add worker tasks to TaskGraph

        PHASE 3: EXECUTION
        5. Loop until all tasks completed or failed:
           a. Get ready tasks from TaskGraph
           b. Scheduler assigns tasks to agents
           c. For each assignment (parallel):
              - Spawn WorkerAgent
              - WorkerAgent.execute(task)
              - Validate output (ContinuousValidator)
              - Mark completed or failed
              - Checkpoint if milestone
           d. Handle failures via ESCALATION CHAIN:
              Worker retry (up to max_retries)
                  ↓ still fails
              Domain Agent analyzes + fixes
                  ↓ still fails
              Master Agent intervenes
                  ↓ still fails
              Escalate to stronger model (fallback)
                  ↓ still fails
              Report to user for manual intervention

        PHASE 4: FINALIZATION
        6. Run full project validation (build + test)
        7. Create final checkpoint
        8. Return ProjectResult
        """

    async def _execute_task(self, assignment: Assignment) -> TaskResult:
        """Execute a single task assignment with error handling."""

    async def _validate_output(self, task: Task, result: TaskResult) -> bool:
        """Run ContinuousValidator on task output."""

    async def _handle_failure(self, task: Task, error: str) -> None:
        """ESCALATION CHAIN: Worker → Domain → Master → Fallback → User."""
```

### Escalation Manager — `orchestrator/escalation.py`

```python
class EscalationManager:
    """Hierarchical error escalation: Worker → Domain → Master → Fallback → User."""

    async def handle_failure(self, task: Task, error: str, attempt: int) -> EscalationResult:
        """
        Level 1: WORKER RETRY (attempts 1-3)
          - Feed error context back to same worker
          - Include: error message, stack trace, fix suggestion
          - Worker regenerates with error awareness

        Level 2: DOMAIN INTERVENTION (attempt 4)
          - Domain agent receives: task + all worker attempts + errors
          - Domain can: rewrite the task, split it differently,
            add context files, change approach
          - Creates new sub-task(s) for worker to execute

        Level 3: MASTER INTERVENTION (attempt 5)
          - Master receives: task + domain analysis + all errors
          - Master can: restructure architecture, change interfaces,
            reassign to different domain, merge with another task
          - Master has full project context to make informed decisions

        Level 4: MODEL ESCALATION (attempt 6)
          - Switch to fallback model (e.g., local 7B → cloud GPT-4o)
          - Retry with stronger reasoning capability

        Level 5: USER ESCALATION (attempt 7+)
          - Pause execution
          - Present full error chain to user via Studio dashboard
          - User can: provide hints, skip task, modify approach, or fix manually
        """

    def determine_level(self, task: Task) -> EscalationLevel:
        """Based on retry count, determine current escalation level."""
        if task.retry_count <= 3:
            return EscalationLevel.WORKER_RETRY
        elif task.retry_count == 4:
            return EscalationLevel.DOMAIN_INTERVENTION
        elif task.retry_count == 5:
            return EscalationLevel.MASTER_INTERVENTION
        elif task.retry_count == 6:
            return EscalationLevel.MODEL_ESCALATION
        else:
            return EscalationLevel.USER_ESCALATION

    async def escalate_to_domain(self, task: Task, errors: list[str]) -> Task:
        """Domain agent analyzes failures and creates revised task."""

    async def escalate_to_master(self, task: Task, domain_analysis: str) -> Task:
        """Master agent restructures approach based on full context."""

    async def escalate_to_fallback(self, task: Task) -> Task:
        """Switch to stronger/cloud model and retry."""

    async def escalate_to_user(self, task: Task, full_context: dict) -> None:
        """Pause and present to user via Studio dashboard."""

class EscalationLevel(str, Enum):
    WORKER_RETRY = "worker_retry"           # Attempts 1-3
    DOMAIN_INTERVENTION = "domain_fix"      # Attempt 4
    MASTER_INTERVENTION = "master_fix"      # Attempt 5
    MODEL_ESCALATION = "model_upgrade"      # Attempt 6
    USER_ESCALATION = "user_help"           # Attempt 7+

@dataclass
class EscalationResult:
    level: EscalationLevel
    resolved: bool
    new_task: Task | None          # Revised task if restructured
    model_changed: bool            # Whether model was swapped
    user_input_required: bool      # Whether user needs to act
```

---

## 12. CLI — `cli/app.py`

```python
import typer
from rich.console import Console

app = typer.Typer(name="galaxy", help="Galaxy AI Engineering OS")
console = Console()

@app.command()
def setup():
    """First-time setup: auto-detect hardware, install deps, pull models."""
    # 1. Check Python version
    # 2. Check/install tmux (apt install tmux / brew install tmux)
    # 3. Check/install Ollama (curl -fsSL https://ollama.ai/install.sh | sh)
    # 4. Detect GPU (nvidia-smi) and available VRAM
    # 5. Auto-select models based on VRAM:
    #    - 24GB+ → qwen2.5-coder:14b (master+domain), 7b (worker)
    #    - 12-24GB → qwen2.5-coder:7b (all tiers)
    #    - 8-12GB → qwen2.5-coder:3b (all tiers)
    #    - No GPU → use cloud models or CPU inference
    # 6. Pull selected models via Ollama
    # 7. Generate galaxy.config.yaml
    # 8. Print summary + "Ready!"

@app.command()
def init(
    blueprint: str = typer.Option(None, help="Blueprint template name"),
    path: str = typer.Argument(".", help="Project path"),
):
    """Initialize a Galaxy workspace."""

@app.command()
def run(
    request: str = typer.Argument(..., help="What to build"),
    config: str = typer.Option(None, help="Config file path"),
    no_studio: bool = typer.Option(False, help="Disable web dashboard"),
):
    """Run Galaxy. Starts BOTH terminal CLI + web dashboard together."""
    # 1. Boot kernel (initializes all subsystems)
    # 2. Start Studio web server (FastAPI on port 8420) in background
    # 3. Auto-open browser to http://localhost:8420
    # 4. Run orchestrator.execute_project(request)
    # 5. CLI shows live progress with Rich formatting
    # 6. Studio shows real-time dashboard via WebSocket
    # Both run simultaneously until completion

@app.command()
def pause():
    """Pause current execution and save checkpoint."""

@app.command()
def resume(
    checkpoint: str = typer.Option(None, help="Specific checkpoint ID"),
    worker_model: str = typer.Option(None, help="Override worker model"),
):
    """Resume from last checkpoint. Starts Studio automatically."""

@app.command()
def status():
    """Show current project status (tasks, agents, progress)."""

@app.command()
def checkpoint():
    """Manually create a checkpoint."""

@app.command()
def studio(
    port: int = typer.Option(8420, help="Dashboard port"),
):
    """Open Studio dashboard for an idle project (view-only mode)."""

def main():
    app()
```

---

## 12.1 Terminal UX Rendering Engine — `cli/renderer.py` + `cli/views/`

> The terminal is the **primary user experience**. Built with Python's `rich` library.
> Updates in-place at 500ms intervals. Never scrolls during normal operation.

```python
# cli/renderer.py — Core rendering engine
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, BarColumn, TextColumn
from rich.spinner import Spinner
from rich.layout import Layout
import asyncio

console = Console()

class GalaxyRenderer:
    """Master renderer that manages all terminal views."""

    live: Live | None = None
    current_view: str = "dashboard"     # dashboard | activity | taskgraph
    verbosity: str = "normal"           # quiet | normal | verbose | debug

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.boot_renderer = BootRenderer()
        self.dashboard = DashboardView()
        self.activity = ActivityFeedView()
        self.taskgraph = TaskGraphView()
        self.status = StatusRenderer()
        self.completion = CompletionReport()
        self.escalation = EscalationRenderer()
        self.keyboard = KeyboardController(self)

    async def start(self) -> None:
        """Start the live rendering loop. Called after boot completes."""
        self.live = Live(console=console, refresh_per_second=2, screen=True)
        self.live.start()
        asyncio.create_task(self._render_loop())
        asyncio.create_task(self.keyboard.listen())

    async def _render_loop(self) -> None:
        """Main render loop — updates every 500ms."""
        while self.live:
            match self.current_view:
                case "dashboard":
                    self.live.update(self.dashboard.render())
                case "activity":
                    self.live.update(self.activity.render())
                case "taskgraph":
                    self.live.update(self.taskgraph.render())
            await asyncio.sleep(0.5)

    def switch_view(self, view: str) -> None:
        self.current_view = view

    def cycle_verbosity(self) -> None:
        cycle = ["quiet", "normal", "verbose", "debug"]
        idx = (cycle.index(self.verbosity) + 1) % len(cycle)
        self.verbosity = cycle[idx]

    async def stop(self) -> None:
        if self.live:
            self.live.stop()
            self.live = None
```

### Boot Renderer — `cli/views/boot.py`

```python
class BootRenderer:
    """Renders the Galaxy boot sequence with ASCII art + step-by-step checks."""

    GALAXY_LOGO = r'''
 ██████   █████  ██       █████  ██   ██ ██    ██
██       ██   ██ ██      ██   ██  ██ ██   ██  ██
██   ███ ███████ ██      ███████   ███     ████
██    ██ ██   ██ ██      ██   ██  ██ ██     ██
 ██████  ██   ██ ███████ ██   ██ ██   ██    ██
'''

    async def render_boot(self, steps: list[BootStep]) -> None:
        """Render each boot step with ✓/✗ status as it completes."""
        console.print(f"[bold cyan]{self.GALAXY_LOGO}[/]")
        console.print("  [bold cyan]AI Engineering Operating System[/]  v0.1.0\n")
        console.print("  [bold]⚡ Booting Galaxy...[/]\n")

        for step in steps:
            with console.status(f"  [dim]{step.label}[/]"):
                result = await step.execute()
            icon = "[green]✓[/]" if result.success else "[red]✗[/]"
            console.print(f"  {icon} {step.label:<30s} {result.detail}")

    async def render_project_header(self, project: str, model: str, workspace: str) -> None:
        """Render the project summary bar after boot."""
        console.print()
        console.rule(style="cyan")
        console.print(f"  📋 Project: \"{project}\"")
        console.print(f"  🤖 Master model: {model}")
        console.print(f"  📁 Workspace: {workspace}")
        console.rule(style="cyan")
        console.print()
```

### Dashboard View — `cli/views/dashboard.py`

```python
class DashboardView:
    """In-place live dashboard — the default runtime view."""

    agents: list[AgentStatus] = []
    recent_activity: list[ActivityEntry] = []
    resources: ResourceSnapshot = ResourceSnapshot()
    progress: tuple[int, int] = (0, 0)  # (completed, total)
    elapsed: float = 0.0

    def render(self) -> Panel:
        """Build the full dashboard panel. Called every 500ms by renderer."""
        layout = Layout()

        # Progress bar
        completed, total = self.progress
        pct = int(completed / total * 100) if total > 0 else 0
        filled = int(pct / 100 * 30)
        bar = f"  PROGRESS [green]{'▓' * filled}[/][dim]{'░' * (30 - filled)}[/]  {pct}%  ({completed}/{total})"

        # Agents table
        agent_table = Table(show_header=False, box=None, padding=(0, 1))
        for a in self.agents:
            icon = {"master": "🧠", "domain": "📋", "worker": "⚙️"}[a.tier]
            color = {"idle": "green", "working": "blue", "validating": "yellow",
                     "retrying": "yellow", "failed": "red", "queued": "dim"}[a.status]
            agent_table.add_row(
                f"  {icon} {a.name:<18s}",
                f"[{color}]{a.status:<12s}[/]",
                f"{a.current_task}"
            )

        # Activity feed (last 5)
        activity_lines = []
        for entry in self.recent_activity[-5:]:
            activity_lines.append(
                f"  {entry.time}  {entry.icon} {entry.agent:<12s} {entry.file:<28s} {entry.result}"
            )

        # Resource bars
        vram = self.resources.vram
        ram = self.resources.ram
        cpu = self.resources.cpu

        content = "\n".join([
            bar, "",
            Panel.fit("\n".join(str(r) for r in agent_table.rows) or "  No agents", title="AGENTS").text,
            Panel.fit("\n".join(activity_lines) or "  Waiting...", title="RECENT ACTIVITY").text,
            Panel.fit(
                f"  VRAM  {_bar(vram.used, vram.total)}  {vram.used:.1f}/{vram.total:.1f} GB\n"
                f"  RAM   {_bar(ram.used, ram.total)}  {ram.used:.1f}/{ram.total:.1f} GB\n"
                f"  CPU   {_bar(cpu.percent, 100)}  {cpu.percent:.0f}%",
                title="RESOURCES"
            ).text,
            "",
            "  [dim][p]ause  [s]tatus  [a]ctivity  [t]ask-graph  [l]og-level  [q]uit[/]"
        ])

        elapsed_str = _format_elapsed(self.elapsed)
        return Panel(content, title=f"Galaxy ─── {self.project_name} ──── {elapsed_str}")

def _bar(used: float, total: float, width: int = 20) -> str:
    pct = used / total if total > 0 else 0
    filled = int(pct * width)
    color = "green" if pct < 0.8 else ("yellow" if pct < 0.95 else "red")
    return f"[{color}]{'▓' * filled}[/][dim]{'░' * (width - filled)}[/]"
```

### Activity Feed — `cli/views/activity.py`

```python
class ActivityFeedView:
    """Scrolling log mode — shows every event with timestamps."""

    entries: list[ActivityEntry] = []
    filter_agent: str | None = None
    filter_domain: str | None = None

    # Icon mapping
    ICONS = {
        "master": "🧠", "domain": "📋", "worker": "⚙️",
        "writing": "✏️", "validating": "🔍", "passed": "✅",
        "failed": "❌", "retrying": "🔄", "fixing": "🔧",
        "escalating": "⬆️", "paused": "⏸️", "checkpoint": "💾",
    }

    def render(self) -> Panel:
        lines = []
        for e in self._filtered_entries()[-30:]:
            icon = self.ICONS.get(e.action_type, "•")
            line = f"  {e.timestamp}  {icon} {e.agent:<18s} {e.message}"
            lines.append(line)
            # Sub-steps (validation pipeline)
            for sub in e.sub_steps:
                result = "[green]✓[/]" if sub.passed else "[red]✗[/]"
                lines.append(f"                     │  {result} {sub.name:<12s} {sub.detail}")
        return Panel("\n".join(lines), title="Galaxy ─── Activity Feed ─── [d] dashboard  [f] filter")
```

### Task Graph View — `cli/views/taskgraph.py`

```python
class TaskGraphView:
    """ASCII DAG of all tasks using Rich Tree."""

    def render(self) -> Panel:
        tree = Tree("🧠 Master Plan")
        for domain in self.domains:
            status_icon = self._status_icon(domain.status)
            branch = tree.add(f"📋 {domain.name} {status_icon}")
            for task in domain.tasks:
                task_icon = self._status_icon(task.status)
                branch.add(f"⚙️ {task.file} {task_icon}")
        legend = "\n  Legend: ✅ done  🔵 running  🟡 validating  🟠 retrying  🔴 failed  ⚪ waiting"
        content = str(tree) + legend
        completed = sum(1 for d in self.domains for t in d.tasks if t.status == "done")
        total = sum(len(d.tasks) for d in self.domains)
        return Panel(content, title=f"Galaxy ─── Task Graph ─── {completed}/{total} complete")

    @staticmethod
    def _status_icon(status: str) -> str:
        return {"done": "✅", "running": "🔵", "validating": "🟡",
                "retrying": "🟠", "failed": "🔴", "waiting": "⚪", "queued": "⚪"}[status]
```

### Escalation Renderer — `cli/views/escalation.py`

```python
class EscalationRenderer:
    """Renders escalation chain events clearly in the activity feed."""

    LEVEL_LABELS = {
        1: ("🔄", "Worker Retry"),
        2: ("⬆️", "Domain Intervention"),
        3: ("⬆️", "Master Intervention"),
        4: ("⬆️", "Model Upgrade"),
        5: ("⏸️", "User Escalation"),
    }

    def render_escalation(self, event: EscalationEvent) -> list[str]:
        icon, label = self.LEVEL_LABELS[event.level]
        lines = [f"                     │  {icon} ESCALATION LEVEL {event.level}: {label}"]
        if event.detail:
            lines.append(f"                     │  {event.detail}")
        return lines

    def render_user_prompt(self, event: EscalationEvent) -> Panel:
        """Level 5: renders the interactive USER ACTION REQUIRED box."""
        return Panel(
            f"  Task: {event.task_description}\n"
            f"  File: {event.file}\n"
            f"  Error: {event.error}\n\n"
            f"  {event.attempts} attempts failed\n\n"
            f"  Options:\n"
            f"    [h] Provide hint / additional context\n"
            f"    [s] Skip this task\n"
            f"    [m] Modify the task description\n"
            f"    [f] Fix manually and mark complete\n"
            f"    [r] Retry with different approach",
            title="USER ACTION REQUIRED",
            border_style="red",
        )
```

### Completion Report — `cli/views/completion.py`

```python
class CompletionReport:
    """Renders the final build report when galaxy run completes."""

    def render(self, result: ProjectResult) -> None:
        status = "✅ Galaxy — BUILD COMPLETE" if result.all_passed else "⚠️  Galaxy — BUILD COMPLETE WITH WARNINGS"
        console.rule(f"[bold]{status}[/]", style="green" if result.all_passed else "yellow")

        # Files created
        console.print(Panel(
            f"  {result.source_files} source files\n"
            f"  {result.test_files} test files\n"
            f"  {result.config_files} config files\n"
            f"  ── ──────────────────\n"
            f"  {result.total_files} files total    {result.total_lines:,} lines of code",
            title="Files Created"
        ))

        # Quality
        console.print(Panel(
            f"  Tests:    {result.tests_passing}/{result.tests_total} passing  ({result.test_pct}%)\n"
            f"  Coverage: {result.coverage}%\n"
            f"  Lint:     {result.lint_warnings} warnings\n"
            f"  Trust:    avg {result.avg_trust} ({result.trust_band})",
            title="Quality"
        ))

        # Resources
        console.print(Panel(
            f"  Tokens:      {result.input_tokens:,} (in) + {result.output_tokens:,} (out)\n"
            f"  Models:      {result.models_used}\n"
            f"  Cost:        ${result.cost:.2f}\n"
            f"  Retries:     {result.retries}\n"
            f"  Escalations: {result.escalations}",
            title="Resources Used"
        ))

        # Next steps
        if result.next_steps:
            console.print(Panel("\n".join(f"  {s}" for s in result.next_steps), title="Next Steps"))
```

### Keyboard Controller — `cli/keyboard.py`

```python
class KeyboardController:
    """Handles keyboard input during execution. Non-blocking key listener."""

    KEY_MAP = {
        "d": ("dashboard", "Switch to dashboard"),
        "a": ("activity", "Switch to activity feed"),
        "t": ("taskgraph", "Show task graph"),
        "s": ("status", "Quick status snapshot"),
        "p": ("pause", "Graceful pause + checkpoint"),
        "r": ("resume", "Resume from pause"),
        "c": ("checkpoint", "Create manual checkpoint"),
        "l": ("log_level", "Cycle verbosity"),
        "w": ("workers", "Worker detail panel"),
        "m": ("memory", "Memory usage stats"),
        "v": ("vram", "GPU/VRAM detail panel"),
        "f": ("filter", "Filter activity by agent"),
        "q": ("quit", "Graceful shutdown"),
    }

    async def listen(self) -> None:
        """Non-blocking keyboard listener using asyncio."""
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                key = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.read, 1)
                await self._handle_key(key)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    async def _handle_key(self, key: str) -> None:
        if key in ("d", "a", "t"):
            self.renderer.switch_view(self.KEY_MAP[key][0])
        elif key == "l":
            self.renderer.cycle_verbosity()
        elif key == "p":
            await self.renderer.event_bus.publish(Event("galaxy.pause_requested"))
        elif key == "q":
            await self.renderer.event_bus.publish(Event("galaxy.quit_requested"))
        elif key == "c":
            await self.renderer.event_bus.publish(Event("galaxy.checkpoint_requested"))
```

### Color System — `cli/colors.py`

```python
# cli/colors.py — Centralized color constants for all terminal output
class GalaxyColors:
    """Design language constants for Rich markup."""
    BRAND = "bold cyan"
    SUCCESS = "green"
    ERROR = "red"
    WARNING = "yellow"
    RUNNING = "blue"
    QUEUED = "dim"
    ESCALATION = "magenta"
    FILE_PATH = "cyan"
    AGENT_NAME = "bold"
    TRUST_HIGH = "green"
    TRUST_MEDIUM = "yellow"
    TRUST_LOW = "red"
    PROGRESS_FILL = "green"
    PROGRESS_EMPTY = "dim"
    PANEL_BORDER = "bright_black"

# Convenience functions
def success(text: str) -> str: return f"[{GalaxyColors.SUCCESS}]✓ {text}[/]"
def error(text: str) -> str:   return f"[{GalaxyColors.ERROR}]✗ {text}[/]"
def warning(text: str) -> str: return f"[{GalaxyColors.WARNING}]⚠ {text}[/]"
def filepath(path: str) -> str: return f"[{GalaxyColors.FILE_PATH}]{path}[/]"
def agent(name: str) -> str:   return f"[{GalaxyColors.AGENT_NAME}]{name}[/]"
```

---

## 13. Phase 1 Build Order (Test-As-You-Build)

> **RULE: Every file gets a test BEFORE moving to the next file.**
> No file is considered "done" until its test passes.
> No module is considered "done" until its integration test passes.
> No phase is considered "done" until its E2E test passes.

### Testing Structure

```
For every source file:
  src/galaxy/core/config.py  →  tests/unit/test_core/test_config.py
  src/galaxy/events/bus.py   →  tests/unit/test_events/test_bus.py
  src/galaxy/agents/base.py  →  tests/unit/test_agents/test_base.py
  ... and so on for EVERY file
```

### Gate Rules

```
FILE GATE:    Write file → Write test → Test passes → ✅ Next file
MODULE GATE:  All files tested → Integration test → ✅ Next module
PHASE GATE:   All modules tested → E2E test → ✅ Next phase
```

### Week-by-Week Build + Test

```
Week 1-2: Core Foundation
  ├── core/config.py
  │   └── TEST: test_config.py
  │       ├── test_load_default_config()
  │       ├── test_load_from_yaml()
  │       ├── test_env_var_override()
  │       ├── test_invalid_config_raises()
  │       └── test_model_config_resolve_api_key()
  │
  ├── core/exceptions.py
  │   └── TEST: test_exceptions.py
  │       └── test_all_exceptions_have_messages()
  │
  ├── core/types.py
  │   └── TEST: test_types.py
  │       ├── test_agent_tier_enum()
  │       ├── test_task_status_transitions()
  │       └── test_dataclass_serialization()
  │
  ├── events/events.py
  │   └── TEST: test_events.py
  │       ├── test_event_creation()
  │       └── test_event_serialization()
  │
  ├── events/bus.py
  │   └── TEST: test_bus.py
  │       ├── test_publish_subscribe()
  │       ├── test_multiple_subscribers()
  │       ├── test_unsubscribe()
  │       ├── test_request_reply()
  │       └── test_topic_filtering()
  │
  ├── core/kernel.py (skeleton)
  │   └── TEST: test_kernel.py
  │       ├── test_boot_initializes_subsystems()
  │       └── test_shutdown_cleans_up()
  │
  ├── MODULE GATE: test_core_integration.py
  │   ├── test_kernel_boots_with_default_config()
  │   ├── test_event_bus_works_after_boot()
  │   └── test_kernel_boot_and_shutdown_lifecycle()
  │
  └── ✅ GATE PASSED → Move to Week 3

Week 3-4: Model + Agent Layer
  ├── models/vram.py
  │   └── TEST: test_vram.py
  │       ├── test_detect_gpus()
  │       ├── test_get_free_vram()
  │       ├── test_estimate_model_vram()
  │       └── test_no_gpu_returns_zero()
  │
  ├── models/providers/ollama.py
  │   └── TEST: test_ollama_provider.py
  │       ├── test_is_available_when_running()
  │       ├── test_is_available_when_not_running()
  │       ├── test_list_models()
  │       ├── test_chat_completion()
  │       ├── test_chat_completion_with_tools()
  │       └── test_timeout_handling()
  │
  ├── models/providers/openai.py
  │   └── TEST: test_openai_provider.py
  │       ├── test_api_key_from_env()
  │       ├── test_chat_completion_mock()
  │       └── test_handles_rate_limit()
  │
  ├── models/router.py
  │   └── TEST: test_router.py
  │       ├── test_route_by_tier()
  │       ├── test_route_by_task_type()
  │       ├── test_fallback_on_failure()
  │       ├── test_swap_model()
  │       └── test_detect_all_providers()
  │
  ├── agents/base.py
  │   └── TEST: test_base_agent.py
  │       ├── test_agent_creation()
  │       ├── test_invoke_llm()
  │       ├── test_use_tool()
  │       ├── test_checkpoint_serialization()
  │       └── test_from_checkpoint_restoration()
  │
  ├── agents/worker.py
  │   └── TEST: test_worker.py
  │       ├── test_worker_executes_simple_task()
  │       ├── test_worker_writes_file()
  │       └── test_worker_handles_failure()
  │
  ├── agents/domain.py + master.py
  │   └── TEST: test_domain.py, test_master.py
  │
  ├── agents/registry.py
  │   └── TEST: test_registry.py
  │       ├── test_register_agent()
  │       ├── test_get_agents_by_tier()
  │       ├── test_cleanup_idle_agents()
  │       └── test_agent_limits_enforced()
  │
  ├── MODULE GATE: test_agent_model_integration.py
  │   ├── test_agent_calls_model_via_router()
  │   ├── test_worker_generates_code_with_ollama()
  │   └── test_agent_lifecycle_spawn_to_terminate()
  │
  └── ✅ GATE PASSED → Move to Week 5

Week 5-6: Tools + Terminal
  ├── tools/base.py
  │   └── TEST: test_base_tool.py
  │       ├── test_tool_input_validation()
  │       └── test_tool_result_structure()
  │
  ├── tools/registry.py
  │   └── TEST: test_tool_registry.py
  │       ├── test_register_tool()
  │       ├── test_get_tools_for_tier()
  │       └── test_generate_openai_schemas()
  │
  ├── tools/builtin/file_read.py
  │   └── TEST: test_file_read.py
  │       ├── test_read_full_file()
  │       ├── test_read_line_range()
  │       ├── test_read_nonexistent_file()
  │       └── test_permission_denied_outside_workspace()
  │
  ├── tools/builtin/file_write.py
  │   └── TEST: test_file_write.py
  │       ├── test_write_new_file()
  │       ├── test_write_creates_directories()
  │       ├── test_overwrite_existing()
  │       └── test_blocked_outside_workspace()
  │
  ├── tools/builtin/file_edit.py
  │   └── TEST: test_file_edit.py
  │       ├── test_replace_content()
  │       ├── test_edit_nonexistent_file()
  │       └── test_target_content_not_found()
  │
  ├── tools/builtin/terminal.py
  │   └── TEST: test_terminal_tool.py
  │       ├── test_execute_simple_command()
  │       ├── test_command_timeout()
  │       └── test_blocked_dangerous_command()
  │
  ├── tools/builtin/search.py, git.py, tree.py
  │   └── TEST: test_search.py, test_git.py, test_tree.py
  │
  ├── terminal/manager.py
  │   └── TEST: test_terminal_manager.py
  │       ├── test_create_tmux_session()
  │       ├── test_execute_in_session()
  │       ├── test_cleanup_session()
  │       └── test_reattach_existing_session()
  │
  ├── MODULE GATE: test_tools_integration.py
  │   ├── test_agent_uses_file_tools()
  │   ├── test_agent_runs_terminal_command()
  │   └── test_permission_blocks_unauthorized_tool()
  │
  └── ✅ GATE PASSED → Move to Week 7

Week 7-8: Orchestrator + Vault + CLI
  ├── orchestrator/task.py
  │   └── TEST: test_task.py
  │       ├── test_task_creation()
  │       ├── test_task_status_transitions()
  │       └── test_task_serialization()
  │
  ├── orchestrator/task_graph.py
  │   └── TEST: test_task_graph.py
  │       ├── test_add_tasks_and_dependencies()
  │       ├── test_get_ready_tasks()
  │       ├── test_critical_path()
  │       ├── test_circular_dependency_detection()
  │       ├── test_mark_completed_unblocks_dependents()
  │       └── test_graph_serialization()
  │
  ├── orchestrator/scheduler.py
  │   └── TEST: test_scheduler.py
  │       ├── test_schedule_respects_vram()
  │       ├── test_calculate_parallelism()
  │       └── test_evict_least_used_model()
  │
  ├── orchestrator/orchestrator.py
  │   └── TEST: test_orchestrator.py
  │       ├── test_planning_phase()
  │       ├── test_execution_phase()
  │       ├── test_failure_retry()
  │       └── test_checkpoint_on_milestone()
  │
  ├── vault/checkpoint.py
  │   └── TEST: test_vault.py
  │       ├── test_create_checkpoint()
  │       ├── test_load_checkpoint()
  │       ├── test_crash_marker_lifecycle()
  │       ├── test_recover_from_crash()
  │       └── test_checkpoint_contains_full_state()
  │
  ├── cli/app.py
  │   └── TEST: test_cli.py
  │       ├── test_init_command()
  │       ├── test_run_command()
  │       ├── test_pause_command()
  │       ├── test_resume_command()
  │       └── test_status_command()
  │
  ├── MODULE GATE: test_orchestrator_integration.py
  │   ├── test_full_pipeline_plan_to_execute()
  │   ├── test_checkpoint_and_resume()
  │   └── test_parallel_worker_execution()
  │
  └── ✅ GATE PASSED → Move to Week 9

Week 9-10: E2E Testing + Polish
  ├── PHASE GATE: test_e2e_phase1.py
  │   ├── test_build_simple_python_script()
  │   ├── test_build_rest_api()
  │   ├── test_crash_and_recover()
  │   ├── test_pause_swap_model_resume()
  │   ├── test_multi_worker_parallel()
  │   └── test_pip_install_and_cli()
  │
  ├── Documentation
  ├── pip package build + test install
  └── ✅ PHASE 1 COMPLETE
```

### Test Commands

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific module tests
pytest tests/unit/test_core/ -v
pytest tests/unit/test_agents/ -v

# Run integration tests
pytest tests/integration/ -v

# Run E2E tests (requires Ollama running)
pytest tests/e2e/ -v --slow

# Run with coverage
pytest --cov=galaxy --cov-report=html

# Type checking
mypy src/galaxy/ --strict

# Linting
ruff check src/galaxy/
ruff format src/galaxy/
```

---

## 14. Galaxy's Own Continuous Validation Pipeline

> **Galaxy doesn't just generate code — it validates EVERY file immediately after creation.**
> Errors are caught file-by-file, not after the entire project is assembled.

### The Validate-As-You-Go Architecture

```
Worker generates file
      ↓
IMMEDIATE VALIDATION (before marking task complete)
      ↓
┌─────────────────────────────────────────────┐
│          VALIDATION PIPELINE                │
│                                             │
│  Step 1: SYNTAX CHECK                       │
│    Python → py_compile / ast.parse          │
│    TypeScript → tsc --noEmit                │
│    Other → language-specific parser         │
│    FAIL → retry with syntax error context   │
│                                             │
│  Step 2: IMPORT CHECK                       │
│    Verify all imports exist and resolve      │
│    Check for circular imports               │
│    FAIL → retry with missing import context │
│                                             │
│  Step 3: TYPE CHECK (if applicable)         │
│    Python → mypy / pyright                  │
│    TypeScript → tsc --noEmit                │
│    FAIL → retry with type error context     │
│                                             │
│  Step 4: LINT CHECK                         │
│    Python → ruff check                      │
│    TypeScript → eslint                      │
│    FAIL → auto-fix or retry                 │
│                                             │
│  Step 5: BUILD CHECK (incremental)          │
│    Does the overall project still compile?   │
│    FAIL → retry with build error context    │
│                                             │
│  Step 6: TEST RUN (if tests exist)          │
│    Run only tests related to this file       │
│    FAIL → retry with test failure context   │
│                                             │
│  Step 7: SENTINEL CHECK (Phase 3)           │
│    Style consistency                         │
│    Architecture rules                        │
│    WARN → fix in next iteration             │
│                                             │
│  ALL PASSED → Mark task COMPLETED ✅        │
│  ANY FAILED → Retry with error context      │
└─────────────────────────────────────────────┘
```

### Implementation — `forge/validator.py`

```python
class ContinuousValidator:
    """Validates every generated file immediately. Catches errors early."""

    async def validate_file(self, file_path: str, task: Task) -> ValidationResult:
        """
        Run full validation pipeline on a single file.
        Called IMMEDIATELY after worker writes the file.
        Returns pass/fail with detailed error context.
        """

    async def validate_syntax(self, file_path: str) -> StepResult:
        """
        Language-aware syntax check:
        - Python: ast.parse() or py_compile.compile()
        - TypeScript/JavaScript: tsc --noEmit or babel parse
        - Go: go vet
        - Rust: cargo check
        """

    async def validate_imports(self, file_path: str) -> StepResult:
        """
        Check all imports resolve:
        - Python: importlib check
        - TypeScript: tsc import resolution
        - Use Cortex import graph for cross-file validation
        """

    async def validate_types(self, file_path: str) -> StepResult:
        """
        Type checking:
        - Python: mypy --check-untyped-defs or pyright
        - TypeScript: tsc --noEmit --strict
        """

    async def validate_lint(self, file_path: str) -> StepResult:
        """
        Lint check:
        - Python: ruff check
        - TypeScript: eslint
        Auto-fix trivial issues (formatting, unused imports).
        """

    async def validate_build(self, project_path: str) -> StepResult:
        """
        Incremental build check:
        - Does the project still compile after this file was added?
        - Python: no compile step needed (just import check)
        - TypeScript/React: npm run build (incremental)
        - Go: go build ./...
        """

    async def validate_tests(self, file_path: str, task: Task) -> StepResult:
        """
        Run related tests only:
        - Find test files that import this file
        - Run only those tests (not full suite)
        - If this IS a test file, run it directly
        """

    async def validate_sentinel(self, file_path: str) -> StepResult:
        """
        Consistency check (Phase 3):
        - Style profile compliance
        - Architecture boundary check
        - Naming convention check
        """

@dataclass
class ValidationResult:
    file_path: str
    passed: bool
    steps: list[StepResult]
    total_duration_ms: int
    auto_fixed: list[str]       # Issues auto-fixed (formatting etc.)
    errors: list[ValidationError]  # Issues needing retry

@dataclass
class StepResult:
    step: str                   # "syntax" | "imports" | "types" | "lint" | "build" | "tests"
    passed: bool
    duration_ms: int
    errors: list[str]
    auto_fixed: bool            # Was it auto-fixed?

@dataclass
class ValidationError:
    file: str
    line: int | None
    step: str
    message: str
    suggestion: str | None      # AI-generated fix suggestion
```

### Retry With Error Context

```
Worker writes file → Validator finds error
      ↓
Error fed back to worker as CONTEXT:
  "Your previous output for auth/middleware.py had this error:
   Line 23: ImportError: module 'jwt' has no attribute 'decode'
   The correct usage is: jwt.decode(token, key, algorithms=['HS256'])
   Please fix this and regenerate the file."
      ↓
Worker regenerates with fix context → Re-validate
      ↓
Pass? → Task complete ✅
Fail again? → Retry (up to max_retry_loops)
      ↓
Max retries exceeded? → Escalate to Domain Agent or stronger model
```

### Validation Levels (Configurable)

```yaml
# galaxy.config.yaml
validation:
  level: standard               # minimal | standard | strict

  # minimal: syntax only (fastest)
  minimal:
    syntax: true
    imports: false
    types: false
    lint: false
    build: false
    tests: false

  # standard: syntax + imports + build (default)
  standard:
    syntax: true
    imports: true
    types: false
    lint: true
    build: true
    tests: false

  # strict: everything (slowest but safest)
  strict:
    syntax: true
    imports: true
    types: true
    lint: true
    build: true
    tests: true
    sentinel: true

  auto_fix:
    formatting: true            # Auto-fix formatting issues
    unused_imports: true        # Auto-remove unused imports
    simple_lint: true           # Auto-fix simple lint issues

  retry:
    max_retries: 3
    include_error_in_context: true
    escalate_to_stronger_model: true
```

### Dashboard Validation View

```
┌─────────────────────────────────────────────┐
│        FILE VALIDATION STATUS               │
├─────────────────────────────────────────────┤
│                                             │
│  auth/middleware.py    ✅ All 6 checks pass │
│  auth/models.py        ✅ All 6 checks pass │
│  auth/routes.py        🔄 Retry #2 (type)  │
│  auth/utils.py         ✅ All 6 checks pass │
│  core/config.py        ✅ All 6 checks pass │
│  core/database.py      ❌ Import error      │
│                                             │
│  Pass rate: 83% (5/6)                       │
│  Auto-fixed: 3 files (formatting)           │
│  Retrying: 1 file (type error)              │
│                                             │
│  [View Errors] [Force Retry] [Skip]         │
└─────────────────────────────────────────────┘
```

---

**Next: Part 3 — Phase 2 Implementation (Memory, Cortex, Full Vault)**

> [!NOTE]
> **New subsystems introduced later:**
> - **Phase 3:** Galaxy Scribe (Documentation Generation) — auto-generates docs alongside code
> - **Phase 5-6:** Galaxy Compass (Strategic Intent Layer) — priorities, constraints, tradeoffs shape every agent decision
