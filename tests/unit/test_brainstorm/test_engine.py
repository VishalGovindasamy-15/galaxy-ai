"""Tests for galaxy.brainstorm.engine."""

from pathlib import Path

from galaxy.brainstorm.engine import BrainstormEngine
from galaxy.brainstorm.types import (
    BrainstormMode,
    BrainstormPhase,
    DecisionType,
    IdeaCategory,
    IdeaStatus,
)


class TestBrainstormEngineSession:
    """Test session management."""

    def test_start_session(self) -> None:
        engine = BrainstormEngine()
        session = engine.start_session("Build an API", project_name="my-api")
        assert session.prompt == "Build an API"
        assert session.project_name == "my-api"
        assert session.phase == BrainstormPhase.IDEATION
        assert not session.is_complete

    def test_start_session_with_mode(self) -> None:
        engine = BrainstormEngine()
        session = engine.start_session("Test", mode=BrainstormMode.FREE_FORM)
        assert session.mode == BrainstormMode.FREE_FORM

    def test_start_session_logs_decision(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        assert engine.decision_log.count == 1
        records = engine.decision_log.list_all()
        assert records[0].decision_type == DecisionType.SESSION_STARTED

    def test_end_session(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        engine.add_idea("Idea 1")
        summary = engine.end_session()
        assert summary.total_ideas == 1
        assert engine.session.is_complete

    def test_end_session_without_start(self) -> None:
        engine = BrainstormEngine()
        summary = engine.end_session()
        assert summary.total_ideas == 0

    def test_advance_phase(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        phase = engine.advance_phase()
        assert phase == BrainstormPhase.REFINEMENT

    def test_advance_phase_without_session(self) -> None:
        engine = BrainstormEngine()
        assert engine.advance_phase() is None


class TestBrainstormEngineIdeas:
    """Test idea lifecycle management."""

    def test_add_idea(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        idea = engine.add_idea("JWT Auth", "Token-based authentication")
        assert idea.title == "JWT Auth"
        assert idea.status == IdeaStatus.DRAFT
        assert engine.temp_store.count == 1

    def test_add_idea_with_category(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        idea = engine.add_idea("Encrypt", category=IdeaCategory.SECURITY)
        assert idea.category == IdeaCategory.SECURITY

    def test_add_idea_tracks_in_session(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        idea = engine.add_idea("Test idea")
        assert idea.id in engine.session.idea_ids

    def test_add_idea_logs_decision(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        idea = engine.add_idea("Test idea")
        records = engine.decision_log.query(idea_id=idea.id)
        assert len(records) == 1
        assert records[0].decision_type == DecisionType.IDEA_CREATED

    def test_approve_idea(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        idea = engine.add_idea("Good idea")
        approved = engine.approve_idea(idea.id, reason="Critical for MVP")
        assert approved is not None
        assert approved.status == IdeaStatus.APPROVED
        assert engine.temp_store.count == 0
        assert engine.permanent_store.count == 1

    def test_approve_nonexistent(self) -> None:
        engine = BrainstormEngine()
        assert engine.approve_idea("nonexistent") is None

    def test_approve_logs_decision(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        idea = engine.add_idea("Test")
        engine.approve_idea(idea.id, reason="Good idea")
        records = engine.decision_log.query(
            idea_id=idea.id,
            decision_type=DecisionType.IDEA_APPROVED,
        )
        assert len(records) == 1
        assert records[0].reason == "Good idea"

    def test_reject_idea(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        idea = engine.add_idea("Bad idea")
        rejected = engine.reject_idea(idea.id, reason="Too complex")
        assert rejected is not None
        assert rejected.status == IdeaStatus.REJECTED
        assert engine.temp_store.count == 1  # Still in temp, just rejected

    def test_reject_nonexistent(self) -> None:
        engine = BrainstormEngine()
        assert engine.reject_idea("nonexistent") is None

    def test_defer_idea(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        idea = engine.add_idea("Maybe later")
        deferred = engine.defer_idea(idea.id, reason="V2 feature")
        assert deferred is not None
        assert deferred.status == IdeaStatus.DEFERRED

    def test_defer_nonexistent(self) -> None:
        engine = BrainstormEngine()
        assert engine.defer_idea("nonexistent") is None


class TestBrainstormEngineRuntimeUpdate:
    """Test updating permanent ideas during project creation."""

    def test_update_permanent_idea(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        idea = engine.add_idea("REST API", description="Basic REST")
        engine.approve_idea(idea.id)
        updated = engine.update_permanent_idea(idea.id, description="REST + GraphQL")
        assert updated is not None
        assert updated.description == "REST + GraphQL"

    def test_update_permanent_logs_decision(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        idea = engine.add_idea("Test")
        engine.approve_idea(idea.id)
        engine.update_permanent_idea(idea.id, title="Updated")
        records = engine.decision_log.query(
            idea_id=idea.id,
            decision_type=DecisionType.IDEA_UPDATED,
        )
        assert len(records) == 1

    def test_update_nonexistent_permanent(self) -> None:
        engine = BrainstormEngine()
        assert engine.update_permanent_idea("nope", title="X") is None


class TestBrainstormEngineSpec:
    """Test project spec generation."""

    def test_empty_spec(self) -> None:
        engine = BrainstormEngine()
        spec = engine.get_project_spec()
        assert spec["features"] == []

    def test_spec_from_approved_ideas(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        engine.add_idea("Login", category=IdeaCategory.FEATURE)
        engine.add_idea("Use PostgreSQL", category=IdeaCategory.CONSTRAINT)
        engine.add_idea("Encrypt passwords", category=IdeaCategory.SECURITY)

        # Approve all
        for idea in engine.temp_store.list_all():
            engine.approve_idea(idea.id)

        spec = engine.get_project_spec()
        assert len(spec["features"]) == 1
        assert len(spec["constraints"]) == 1
        assert len(spec["security"]) == 1

    def test_spec_excludes_rejected(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        good = engine.add_idea("Good")
        bad = engine.add_idea("Bad")
        engine.approve_idea(good.id)
        engine.reject_idea(bad.id)
        spec = engine.get_project_spec()
        assert len(spec["features"]) == 1


class TestBrainstormEngineSummary:
    """Test summary generation."""

    def test_summary_counts(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        a = engine.add_idea("A", category=IdeaCategory.FEATURE)
        b = engine.add_idea("B", category=IdeaCategory.SECURITY)
        c = engine.add_idea("C", category=IdeaCategory.FEATURE)
        engine.approve_idea(a.id)
        engine.reject_idea(b.id)
        engine.defer_idea(c.id)

        summary = engine.end_session()
        assert summary.approved_ideas == 1
        assert summary.rejected_ideas == 1
        assert summary.deferred_ideas == 1
        assert summary.total_ideas == 3

    def test_summary_categories(self) -> None:
        engine = BrainstormEngine()
        engine.start_session("Test")
        engine.add_idea("A", category=IdeaCategory.FEATURE)
        engine.add_idea("B", category=IdeaCategory.FEATURE)
        engine.add_idea("C", category=IdeaCategory.SECURITY)
        summary = engine.end_session()
        assert summary.categories.get("feature", 0) == 2
        assert summary.categories.get("security", 0) == 1


class TestBrainstormEnginePersistence:
    """Test full save/load cycle."""

    def test_save_and_load(self, tmp_path: Path) -> None:
        # Create and populate
        engine = BrainstormEngine(workspace=tmp_path)
        engine.start_session("Test")
        a = engine.add_idea("Idea A")
        engine.add_idea("Idea B")
        engine.approve_idea(a.id)
        engine.save()

        # Load into new engine
        engine2 = BrainstormEngine(workspace=tmp_path)
        counts = engine2.load()
        assert counts["temp_ideas"] == 1
        assert counts["permanent_ideas"] == 1
        assert counts["decisions"] >= 3  # session_start + 2 creates + 1 approve

    def test_full_workflow(self, tmp_path: Path) -> None:
        """Test complete brainstorming workflow end-to-end."""
        engine = BrainstormEngine(workspace=tmp_path)

        # Start
        session = engine.start_session(
            "Build a REST API with auth",
            project_name="my-api",
            mode=BrainstormMode.STRUCTURED,
        )
        assert session.phase == BrainstormPhase.IDEATION

        # Add ideas
        jwt = engine.add_idea("JWT Authentication", category=IdeaCategory.SECURITY)
        crud = engine.add_idea("CRUD Endpoints", category=IdeaCategory.FEATURE)
        graphql = engine.add_idea("GraphQL Gateway", category=IdeaCategory.ARCHITECTURE)
        postgres = engine.add_idea("Use PostgreSQL", category=IdeaCategory.CONSTRAINT)

        assert engine.temp_store.count == 4

        # Advance to evaluation
        engine.advance_phase()  # → refinement
        engine.advance_phase()  # → evaluation

        # Approve some, reject others
        engine.approve_idea(jwt.id, reason="Required for security")
        engine.approve_idea(crud.id, reason="Core functionality")
        engine.reject_idea(graphql.id, reason="Too complex for MVP")
        engine.approve_idea(postgres.id, reason="Client requirement")

        assert engine.permanent_store.count == 3
        assert engine.temp_store.count == 1  # Only rejected graphql

        # Get spec
        spec = engine.get_project_spec()
        assert len(spec["security"]) == 1
        assert len(spec["features"]) == 1
        assert len(spec["constraints"]) == 1

        # End session
        summary = engine.end_session()
        assert summary.approved_ideas == 3
        assert summary.rejected_ideas == 1
        assert summary.total_decisions > 5

        # Verify persistence
        engine2 = BrainstormEngine(workspace=tmp_path)
        engine2.load()
        assert engine2.permanent_store.count == 3
