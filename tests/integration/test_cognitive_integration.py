"""Integration test: Full cognitive pipeline end-to-end.

MODULE GATE for Week 15-16: Cognitive Pipeline.
Tests brainstorm → cognitive pipeline → contract generation flow.
"""

from pathlib import Path

from galaxy.brainstorm.engine import BrainstormEngine
from galaxy.cognitive.pipeline import CognitivePipeline
from galaxy.cognitive.types import CognitiveMode, StageStatus
from galaxy.contracts.builder import ContractBuilder
from galaxy.contracts.types import ChunkOperation
from galaxy.integrator.engine import IntegratorEngine


class TestBrainstormToCognitivePipeline:
    """Test brainstorm output feeding into the cognitive pipeline."""

    def test_brainstorm_to_pipeline(self, tmp_path: Path) -> None:
        """Brainstorm ideas → project spec → cognitive pipeline → plan."""
        # Step 1: Brainstorm
        engine = BrainstormEngine(workspace=tmp_path)
        engine.start_session("Build a REST API with auth")
        engine.add_idea("JWT Authentication")
        engine.add_idea("CRUD Endpoints")
        engine.add_idea("PostgreSQL Database")

        # Approve all
        for idea in engine.temp_store.list_all():
            engine.approve_idea(idea.id)

        spec = engine.get_project_spec()
        assert len(spec["features"]) >= 2

        # Step 2: Feed into cognitive pipeline
        spec_text = "\n".join(
            f"- {item['title']}: {item.get('description', '')}"
            for cat_items in spec.values()
            for item in cat_items
        )

        pipeline = CognitivePipeline(workspace=tmp_path)
        state = pipeline.run(
            "Build a REST API with auth",
            mode=CognitiveMode.REASONING,
            context=spec_text,
        )

        assert state.success
        assert len(state.stage_results) == 5
        assert state.final_plan
        assert "Execution Plan" in state.final_plan


class TestFullPipelineToContracts:
    """Test cognitive pipeline output feeding into contract creation."""

    def test_pipeline_to_contracts(self) -> None:
        """Pipeline plan → domain contracts → integrator."""
        # Step 1: Run pipeline
        pipeline = CognitivePipeline()
        state = pipeline.run(
            "Build a REST API with JWT auth and user CRUD",
            mode=CognitiveMode.REASONING,
        )
        assert state.success

        # Step 2: Extract plan nodes and create contracts
        # (In production, Master agent does this. Here we simulate.)
        contracts = []
        builder = ContractBuilder("backend")

        # Create contracts based on the plan
        c1 = (
            builder.reset()
            .target("auth/service.py", "create_token")
            .operation(ChunkOperation.CREATE_FUNCTION)
            .description("Create JWT authentication token")
            .param("user_id", "int")
            .returns("str")
            .build()
        )
        contracts.append(c1)

        c2 = (
            builder.reset()
            .target("routes/users.py", "get_users")
            .operation(ChunkOperation.CREATE_FUNCTION)
            .description("Get all users endpoint")
            .returns("list[dict]")
            .build()
        )
        contracts.append(c2)

        assert len(contracts) == 2

        # Verify contracts have valid worker prompts
        for contract in contracts:
            prompt = contract.to_worker_prompt()
            assert contract.function_name in prompt
            assert "No explanations" in prompt


class TestEndToEndPipelineQuality:
    """Test pipeline output quality."""

    def test_complex_prompt_produces_rich_plan(self) -> None:
        pipeline = CognitivePipeline()
        state = pipeline.run(
            "Build a production-grade REST API with JWT authentication, "
            "PostgreSQL database, user CRUD endpoints, role-based access control, "
            "Docker deployment, and comprehensive pytest test suite",
            mode=CognitiveMode.REASONING,
        )
        assert state.success
        plan = state.final_plan

        # Should contain multiple sections
        assert "Technology Stack" in plan
        assert "Execution Plan" in plan
        assert "Summary" in plan

        # Should detect multiple domains
        assert "auth" in plan.lower() or "authentication" in plan.lower()

    def test_pipeline_performance(self) -> None:
        """Pipeline should complete quickly (no LLM calls)."""
        pipeline = CognitivePipeline()
        state = pipeline.run("Build API", mode=CognitiveMode.REASONING)
        # Should complete in under 1 second (keyword-based, no LLM)
        assert state.total_duration_ms < 1000
        assert state.success

    def test_normal_vs_reasoning_mode(self) -> None:
        """Normal mode should be faster with fewer stages."""
        pipeline = CognitivePipeline()

        normal = pipeline.run("Build API", mode=CognitiveMode.NORMAL)
        reasoning = pipeline.run("Build API", mode=CognitiveMode.REASONING)

        assert len(normal.stage_results) == 2
        assert len(reasoning.stage_results) == 5
        assert normal.total_duration_ms <= reasoning.total_duration_ms + 10  # Allow margin
