"""Tests for galaxy.cognitive.pipeline."""

from pathlib import Path

from galaxy.cognitive.pipeline import CognitivePipeline
from galaxy.cognitive.types import CognitiveMode, StageStatus


class TestCognitivePipelineNormal:
    def test_normal_mode(self) -> None:
        pipeline = CognitivePipeline()
        state = pipeline.run("Build a REST API", mode=CognitiveMode.NORMAL)
        assert len(state.stage_results) == 2  # expand + plan
        assert state.final_plan
        assert state.total_duration_ms >= 0

    def test_normal_mode_has_output(self) -> None:
        pipeline = CognitivePipeline()
        state = pipeline.run("Build an API with auth", mode=CognitiveMode.NORMAL)
        assert "REST API" in state.final_plan or "API" in state.final_plan
        assert state.success


class TestCognitivePipelineReasoning:
    def test_reasoning_mode(self) -> None:
        pipeline = CognitivePipeline()
        state = pipeline.run(
            "Build a REST API with user authentication, CRUD endpoints, and tests",
            mode=CognitiveMode.REASONING,
        )
        assert len(state.stage_results) == 5  # all 5 stages
        assert state.final_plan
        assert state.total_duration_ms >= 0

    def test_reasoning_all_stages_complete(self) -> None:
        pipeline = CognitivePipeline()
        state = pipeline.run("Build API", mode=CognitiveMode.REASONING)
        for result in state.stage_results:
            assert result.status == StageStatus.COMPLETED

    def test_reasoning_produces_plan_document(self) -> None:
        pipeline = CognitivePipeline()
        state = pipeline.run(
            "Build a REST API with PostgreSQL and JWT auth",
            mode=CognitiveMode.REASONING,
        )
        plan = state.final_plan
        assert "# Project Plan" in plan
        assert "Execution Plan" in plan
        assert "Summary" in plan

    def test_reasoning_with_workspace(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")
        (tmp_path / "requirements.txt").write_text("fastapi\n")

        pipeline = CognitivePipeline(workspace=tmp_path)
        state = pipeline.run("Build API", mode=CognitiveMode.REASONING)
        assert state.success
        assert len(state.stage_results) == 5


class TestCognitivePipelineState:
    def test_is_complete(self) -> None:
        pipeline = CognitivePipeline()
        state = pipeline.run("Test", mode=CognitiveMode.NORMAL)
        assert state.is_complete

    def test_success(self) -> None:
        pipeline = CognitivePipeline()
        state = pipeline.run("Test", mode=CognitiveMode.NORMAL)
        assert state.success

    def test_original_prompt_preserved(self) -> None:
        pipeline = CognitivePipeline()
        state = pipeline.run("My custom project", mode=CognitiveMode.NORMAL)
        assert state.original_prompt == "My custom project"

    def test_default_is_reasoning(self) -> None:
        pipeline = CognitivePipeline()
        state = pipeline.run("Test")
        assert state.mode == CognitiveMode.REASONING
        assert len(state.stage_results) == 5
