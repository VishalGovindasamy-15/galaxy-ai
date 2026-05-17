"""Tests for galaxy.cognitive.synthesizer."""

from galaxy.cognitive.synthesizer import PlanSynthesizer
from galaxy.cognitive.types import (
    ExecutionPlan,
    ExpandedSpec,
    PlanNode,
    ReflectionResult,
    RetrievedContext,
)


class TestPlanSynthesizer:
    def _make_inputs(self):
        spec = ExpandedSpec(
            original_prompt="Build a REST API",
            project_type="REST API",
            tech_stack=["FastAPI", "PostgreSQL"],
            features=["User auth", "CRUD"],
            constraints=["Must use PostgreSQL"],
            domains=["backend", "auth"],
        )
        n1 = PlanNode(name="DB Setup", domain="database", priority=1)
        n2 = PlanNode(name="Auth", domain="auth", priority=1, dependencies=[n1.id])
        plan = ExecutionPlan(
            nodes=[n1, n2],
            execution_order=[n1.id, n2.id],
            domains=["database", "auth"],
            estimated_total_chunks=6,
        )
        context = RetrievedContext(
            patterns=["FastAPI project"],
            documentation=["Use async routes"],
        )
        reflection = ReflectionResult(
            confidence=0.85,
            approved=True,
            suggestions=["Add error handling"],
        )
        return spec, plan, context, reflection

    def test_synthesize_produces_output(self) -> None:
        synth = PlanSynthesizer()
        spec, plan, ctx, refl = self._make_inputs()
        output = synth.synthesize(spec, plan, ctx, refl)
        assert len(output) > 100
        assert "REST API" in output

    def test_output_has_sections(self) -> None:
        synth = PlanSynthesizer()
        spec, plan, ctx, refl = self._make_inputs()
        output = synth.synthesize(spec, plan, ctx, refl)
        assert "# Project Plan" in output
        assert "## Technology Stack" in output
        assert "## Execution Plan" in output
        assert "## Summary" in output

    def test_output_includes_tech(self) -> None:
        synth = PlanSynthesizer()
        spec, plan, ctx, refl = self._make_inputs()
        output = synth.synthesize(spec, plan, ctx, refl)
        assert "FastAPI" in output
        assert "PostgreSQL" in output

    def test_output_includes_plan_nodes(self) -> None:
        synth = PlanSynthesizer()
        spec, plan, ctx, refl = self._make_inputs()
        output = synth.synthesize(spec, plan, ctx, refl)
        assert "DB Setup" in output
        assert "Auth" in output

    def test_output_includes_context(self) -> None:
        synth = PlanSynthesizer()
        spec, plan, ctx, refl = self._make_inputs()
        output = synth.synthesize(spec, plan, ctx, refl)
        assert "FastAPI project" in output

    def test_output_includes_reflection(self) -> None:
        synth = PlanSynthesizer()
        spec, plan, ctx, refl = self._make_inputs()
        output = synth.synthesize(spec, plan, ctx, refl)
        assert "Add error handling" in output

    def test_approved_status(self) -> None:
        synth = PlanSynthesizer()
        spec, plan, ctx, refl = self._make_inputs()
        output = synth.synthesize(spec, plan, ctx, refl)
        assert "APPROVED" in output

    def test_stage_result(self) -> None:
        synth = PlanSynthesizer()
        spec, plan, ctx, refl = self._make_inputs()
        result = synth.synthesize_to_stage_result(spec, plan, ctx, refl)
        assert result.status.name == "COMPLETED"
        assert result.duration_ms >= 0
        assert result.metadata["confidence"] == 0.85
