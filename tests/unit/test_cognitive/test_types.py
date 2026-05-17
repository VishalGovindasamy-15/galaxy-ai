"""Tests for galaxy.cognitive.types."""

from galaxy.cognitive.types import (
    CognitiveMode,
    ExpandedSpec,
    ExecutionPlan,
    PipelineStage,
    PipelineState,
    PlanNode,
    ReflectionResult,
    RetrievedContext,
    StageResult,
    StageStatus,
)


class TestEnums:
    def test_cognitive_modes(self) -> None:
        assert len(CognitiveMode) == 2
        assert CognitiveMode.NORMAL.description
        assert CognitiveMode.REASONING.description

    def test_pipeline_stages(self) -> None:
        assert len(PipelineStage) == 5
        assert PipelineStage.EXPAND.order == 0
        assert PipelineStage.SYNTHESIZE.order == 4

    def test_stage_status_terminal(self) -> None:
        assert StageStatus.COMPLETED.is_terminal()
        assert StageStatus.FAILED.is_terminal()
        assert StageStatus.SKIPPED.is_terminal()
        assert not StageStatus.PENDING.is_terminal()
        assert not StageStatus.RUNNING.is_terminal()


class TestStageResult:
    def test_default(self) -> None:
        r = StageResult()
        assert r.status == StageStatus.PENDING

    def test_complete(self) -> None:
        r = StageResult(stage=PipelineStage.EXPAND)
        r.complete("output data", 42.5)
        assert r.status == StageStatus.COMPLETED
        assert r.output_data == "output data"
        assert r.duration_ms == 42.5

    def test_fail(self) -> None:
        r = StageResult()
        r.fail("something broke")
        assert r.status == StageStatus.FAILED
        assert r.error == "something broke"

    def test_to_dict(self) -> None:
        r = StageResult(stage=PipelineStage.PLAN)
        r.complete("plan output", 10.0)
        d = r.to_dict()
        assert d["stage"] == "plan"
        assert d["status"] == "completed"


class TestExpandedSpec:
    def test_default(self) -> None:
        spec = ExpandedSpec()
        assert spec.features == []
        assert spec.tech_stack == []

    def test_to_prompt(self) -> None:
        spec = ExpandedSpec(
            project_type="REST API",
            tech_stack=["FastAPI", "PostgreSQL"],
            features=["User auth", "CRUD endpoints"],
        )
        prompt = spec.to_prompt()
        assert "REST API" in prompt
        assert "FastAPI" in prompt
        assert "User auth" in prompt

    def test_roundtrip(self) -> None:
        original = ExpandedSpec(
            original_prompt="Build API",
            project_type="REST API",
            tech_stack=["Python"],
            features=["Auth"],
            domains=["backend"],
        )
        restored = ExpandedSpec.from_dict(original.to_dict())
        assert restored.project_type == "REST API"
        assert restored.features == ["Auth"]


class TestPlanNode:
    def test_default(self) -> None:
        n = PlanNode()
        assert n.id
        assert n.dependencies == []

    def test_roundtrip(self) -> None:
        original = PlanNode(name="Auth", domain="backend", priority=1)
        restored = PlanNode.from_dict(original.to_dict())
        assert restored.name == "Auth"
        assert restored.domain == "backend"


class TestExecutionPlan:
    def test_get_roots(self) -> None:
        n1 = PlanNode(name="DB")
        n2 = PlanNode(name="Auth", dependencies=[n1.id])
        plan = ExecutionPlan(nodes=[n1, n2])
        roots = plan.get_roots()
        assert len(roots) == 1
        assert roots[0].name == "DB"

    def test_get_dependents(self) -> None:
        n1 = PlanNode(name="DB")
        n2 = PlanNode(name="Auth", dependencies=[n1.id])
        n3 = PlanNode(name="API", dependencies=[n1.id])
        plan = ExecutionPlan(nodes=[n1, n2, n3])
        deps = plan.get_dependents(n1.id)
        assert len(deps) == 2

    def test_get_node(self) -> None:
        n = PlanNode(name="Test")
        plan = ExecutionPlan(nodes=[n])
        assert plan.get_node(n.id) is not None
        assert plan.get_node("nope") is None


class TestRetrievedContext:
    def test_to_prompt(self) -> None:
        ctx = RetrievedContext(
            patterns=["FastAPI project"],
            documentation=["Use async routes"],
        )
        prompt = ctx.to_prompt()
        assert "FastAPI project" in prompt
        assert "async routes" in prompt


class TestReflectionResult:
    def test_default(self) -> None:
        r = ReflectionResult()
        assert not r.has_issues
        assert r.approved

    def test_with_issues(self) -> None:
        r = ReflectionResult(issues=["Missing auth"])
        assert r.has_issues


class TestPipelineState:
    def test_default(self) -> None:
        s = PipelineState()
        assert not s.is_complete
        assert s.current_stage is None

    def test_with_completed_stages(self) -> None:
        r1 = StageResult(stage=PipelineStage.EXPAND)
        r1.complete("done")
        r2 = StageResult(stage=PipelineStage.PLAN)
        r2.complete("done")
        s = PipelineState(stage_results=[r1, r2])
        assert s.is_complete
        assert s.success

    def test_with_failed_stage(self) -> None:
        r1 = StageResult(stage=PipelineStage.EXPAND)
        r1.fail("error")
        s = PipelineState(stage_results=[r1])
        assert s.is_complete
        assert not s.success
