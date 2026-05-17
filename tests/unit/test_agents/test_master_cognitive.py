"""Tests for MasterAgent cognitive pipeline integration."""

from galaxy.agents.master import MasterAgent
from galaxy.cognitive.types import CognitiveMode


class TestMasterCognitive:
    def test_plan_with_cognition_reasoning(self) -> None:
        master = MasterAgent(name="test-master")
        state = master.plan_with_cognition("Build a REST API with auth")
        assert state.success
        assert len(state.stage_results) == 5
        assert state.final_plan
        assert master.last_pipeline_state is state

    def test_plan_with_cognition_normal(self) -> None:
        master = MasterAgent(name="test-master")
        state = master.plan_with_cognition("Build API", mode=CognitiveMode.NORMAL)
        assert state.success
        assert len(state.stage_results) == 2

    def test_plan_with_context(self) -> None:
        master = MasterAgent(name="test-master")
        state = master.plan_with_cognition(
            "Build API",
            context="User wants JWT auth and PostgreSQL",
        )
        assert state.success

    def test_pipeline_property(self) -> None:
        master = MasterAgent(name="test-master")
        assert master.pipeline is not None

    def test_last_state_none_initially(self) -> None:
        master = MasterAgent(name="test-master")
        assert master.last_pipeline_state is None
