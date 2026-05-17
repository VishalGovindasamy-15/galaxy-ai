"""Tests for galaxy.cognitive.reflection."""

from galaxy.cognitive.reflection import PlanReflection
from galaxy.cognitive.types import (
    ExecutionPlan,
    ExpandedSpec,
    PlanNode,
)


class TestPlanReflection:
    def _make_spec_and_plan(self):
        spec = ExpandedSpec(
            features=["User auth", "CRUD endpoints"],
            domains=["backend", "auth", "database"],
            tech_stack=["FastAPI"],
        )
        n1 = PlanNode(name="Database Setup", domain="database")
        n2 = PlanNode(name="Auth System", domain="auth", dependencies=[n1.id])
        n3 = PlanNode(name="CRUD endpoints", domain="backend", dependencies=[n1.id])
        plan = ExecutionPlan(
            nodes=[n1, n2, n3],
            execution_order=[n1.id, n2.id, n3.id],
            domains=["database", "auth", "backend"],
        )
        return spec, plan

    def test_reflect_good_plan(self) -> None:
        reflection = PlanReflection()
        spec, plan = self._make_spec_and_plan()
        result = reflection.reflect(spec, plan)
        assert result.confidence > 0.5
        assert isinstance(result.issues, list)

    def test_detect_missing_dependency(self) -> None:
        reflection = PlanReflection()
        spec = ExpandedSpec(features=["Test"], domains=["backend"])
        bad_node = PlanNode(name="Bad", domain="backend", dependencies=["nonexistent"])
        plan = ExecutionPlan(nodes=[bad_node])
        result = reflection.reflect(spec, plan)
        assert len(result.issues) > 0
        assert any("missing" in i.lower() for i in result.issues)

    def test_suggest_tests(self) -> None:
        reflection = PlanReflection()
        spec = ExpandedSpec(features=["API"], domains=["backend"])
        plan = ExecutionPlan(nodes=[PlanNode(name="API", domain="backend")])
        result = reflection.reflect(spec, plan)
        assert any("test" in s.lower() for s in result.suggestions)

    def test_high_confidence_approved(self) -> None:
        reflection = PlanReflection()
        spec, plan = self._make_spec_and_plan()
        result = reflection.reflect(spec, plan)
        if result.confidence >= 0.7 and len(result.issues) == 0:
            assert result.approved

    def test_low_confidence_not_approved(self) -> None:
        reflection = PlanReflection()
        spec = ExpandedSpec(features=["A", "B", "C", "D", "E"], domains=["backend"])
        # Many missing deps = low confidence
        nodes = [PlanNode(name=f"N{i}", domain="backend", dependencies=["missing"]) for i in range(5)]
        plan = ExecutionPlan(nodes=nodes)
        result = reflection.reflect(spec, plan)
        assert not result.approved

    def test_stage_result(self) -> None:
        reflection = PlanReflection()
        spec, plan = self._make_spec_and_plan()
        result = reflection.reflect_to_stage_result(spec, plan)
        assert result.status.name == "COMPLETED"
        assert "Confidence" in result.output_data
