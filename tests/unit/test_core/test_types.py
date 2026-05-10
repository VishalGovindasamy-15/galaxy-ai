"""Tests for galaxy.core.types."""

from datetime import datetime, timezone

from galaxy.core.types import (
    AgentInfo,
    AgentStatus,
    AgentTier,
    EscalationLevel,
    MemoryLevel,
    ResourceSnapshot,
    SchedulerMode,
    Task,
    TaskStatus,
    ToolResult,
    TrustBand,
    TrustScore,
    ValidationResult,
    ValidationStep,
)


class TestAgentTierEnum:
    """Test AgentTier enum values."""

    def test_master_value(self) -> None:
        assert AgentTier.MASTER.value == "master"

    def test_domain_value(self) -> None:
        assert AgentTier.DOMAIN.value == "domain"

    def test_worker_value(self) -> None:
        assert AgentTier.WORKER.value == "worker"

    def test_string_comparison(self) -> None:
        assert AgentTier.MASTER == "master"

    def test_all_tiers(self) -> None:
        assert len(AgentTier) == 3


class TestTaskStatusTransitions:
    """Test TaskStatus enum and transition helpers."""

    def test_pending_is_not_terminal(self) -> None:
        assert not TaskStatus.PENDING.is_terminal()

    def test_completed_is_terminal(self) -> None:
        assert TaskStatus.COMPLETED.is_terminal()

    def test_failed_is_terminal(self) -> None:
        assert TaskStatus.FAILED.is_terminal()

    def test_skipped_is_terminal(self) -> None:
        assert TaskStatus.SKIPPED.is_terminal()

    def test_running_is_active(self) -> None:
        assert TaskStatus.RUNNING.is_active()

    def test_validating_is_active(self) -> None:
        assert TaskStatus.VALIDATING.is_active()

    def test_retrying_is_active(self) -> None:
        assert TaskStatus.RETRYING.is_active()

    def test_pending_is_not_active(self) -> None:
        assert not TaskStatus.PENDING.is_active()

    def test_all_statuses(self) -> None:
        assert len(TaskStatus) == 9


class TestEscalationLevel:
    """Test 5-level escalation chain enum."""

    def test_levels_ordered(self) -> None:
        levels = list(EscalationLevel)
        for i in range(len(levels) - 1):
            assert levels[i].value < levels[i + 1].value

    def test_five_levels(self) -> None:
        assert len(EscalationLevel) == 5

    def test_user_is_highest(self) -> None:
        assert EscalationLevel.USER_INTERVENTION.value == 5


class TestTask:
    """Test Task dataclass."""

    def test_task_creation(self) -> None:
        task = Task(description="Create user model", file_path="models/user.py")
        assert task.description == "Create user model"
        assert task.file_path == "models/user.py"
        assert task.status == TaskStatus.PENDING
        assert task.id  # auto-generated

    def test_task_has_unique_id(self) -> None:
        t1 = Task(description="a")
        t2 = Task(description="b")
        assert t1.id != t2.id

    def test_mark_running(self) -> None:
        task = Task(description="test")
        task.mark_running("agent_01")
        assert task.status == TaskStatus.RUNNING
        assert task.assigned_agent == "agent_01"

    def test_mark_completed(self) -> None:
        task = Task(description="test")
        task.mark_completed()
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None

    def test_mark_failed(self) -> None:
        task = Task(description="test")
        task.mark_failed("syntax error on line 5")
        assert task.status == TaskStatus.FAILED
        assert task.error == "syntax error on line 5"
        assert task.completed_at is not None

    def test_mark_retrying(self) -> None:
        task = Task(description="test")
        assert task.retry_count == 0
        task.mark_retrying()
        assert task.retry_count == 1
        assert task.status == TaskStatus.RETRYING

    def test_can_retry(self) -> None:
        task = Task(description="test", max_retries=2)
        assert task.can_retry()
        task.retry_count = 2
        assert not task.can_retry()

    def test_task_serialization(self) -> None:
        task = Task(
            description="Create file",
            file_path="src/main.py",
            domain="backend",
            dependencies=["task_01"],
        )
        data = task.to_dict()
        assert data["description"] == "Create file"
        assert data["file_path"] == "src/main.py"
        assert data["domain"] == "backend"
        assert data["dependencies"] == ["task_01"]
        assert data["status"] == "pending"

    def test_task_deserialization(self) -> None:
        task = Task(description="Original", file_path="test.py")
        task.mark_running("agent_01")
        data = task.to_dict()
        restored = Task.from_dict(data)
        assert restored.description == "Original"
        assert restored.status == TaskStatus.RUNNING
        assert restored.assigned_agent == "agent_01"
        assert restored.id == task.id

    def test_roundtrip_serialization(self) -> None:
        task = Task(
            description="Test roundtrip",
            file_path="app.py",
            domain="api",
            dependencies=["dep1", "dep2"],
            metadata={"priority": "high"},
        )
        task.mark_running("w1")
        task.mark_completed()
        data = task.to_dict()
        restored = Task.from_dict(data)
        assert restored.to_dict() == data


class TestTrustScore:
    """Test TrustScore composite calculation."""

    def test_composite_high(self) -> None:
        score = TrustScore(
            generation_confidence=90,
            validation_quality=95,
            risk_score=10,
            stability_estimate=90,
            intent_alignment=95,
        )
        assert score.composite >= 85
        assert score.band == TrustBand.HIGH

    def test_composite_medium(self) -> None:
        score = TrustScore(
            generation_confidence=70,
            validation_quality=70,
            risk_score=40,
            stability_estimate=65,
            intent_alignment=70,
        )
        assert 60 <= score.composite < 85
        assert score.band == TrustBand.MEDIUM

    def test_composite_low(self) -> None:
        score = TrustScore(
            generation_confidence=40,
            validation_quality=50,
            risk_score=70,
            stability_estimate=40,
            intent_alignment=40,
        )
        assert score.band in (TrustBand.LOW, TrustBand.CRITICAL)

    def test_zero_scores(self) -> None:
        score = TrustScore()
        assert score.composite == 20  # 100-0=100 risk inverted * 0.20 = 20
        assert score.band == TrustBand.CRITICAL


class TestToolResult:
    """Test ToolResult dataclass."""

    def test_success_result(self) -> None:
        r = ToolResult(success=True, output="file written")
        assert r.success
        assert r.output == "file written"
        assert r.error == ""

    def test_failure_result(self) -> None:
        r = ToolResult(success=False, error="permission denied")
        assert not r.success
        assert r.error == "permission denied"


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_passed_result(self) -> None:
        r = ValidationResult(step=ValidationStep.SYNTAX, passed=True)
        assert r.passed
        assert r.step == ValidationStep.SYNTAX

    def test_failed_result(self) -> None:
        r = ValidationResult(
            step=ValidationStep.LINT,
            passed=False,
            message="3 warnings",
            duration_ms=150.5,
        )
        assert not r.passed
        assert r.duration_ms == 150.5


class TestAgentInfo:
    """Test AgentInfo dataclass."""

    def test_creation(self) -> None:
        info = AgentInfo(name="worker_01", tier=AgentTier.WORKER, model="qwen:7b")
        assert info.name == "worker_01"
        assert info.tier == AgentTier.WORKER
        assert info.status == AgentStatus.IDLE
        assert info.id  # auto-generated


class TestResourceSnapshot:
    """Test ResourceSnapshot dataclass."""

    def test_defaults(self) -> None:
        snap = ResourceSnapshot()
        assert snap.vram_used_gb == 0.0
        assert snap.cpu_percent == 0.0
        assert snap.active_models == []
